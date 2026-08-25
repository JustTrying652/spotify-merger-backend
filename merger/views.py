import uuid
import json
from django.shortcuts import redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import MergeHistory
from .services.spotipy_official import OfficialSpotipyClient
from .services.dedup import extract_tracks, merge_unique, find_overlap, find_near_duplicates, format_duration, apply_selections

client = OfficialSpotipyClient()

FRONTEND_URL = "http://127.0.0.1:5173"

def _get_two_playlists_tracks(token, playlist_a_id, playlist_b_id):
    raw_a = client.get_playlist_tracks(token, playlist_a_id)
    raw_b = client.get_playlist_tracks(token, playlist_b_id)
    return extract_tracks(raw_a), extract_tracks(raw_b)


@api_view(["GET"])
def login(request):
    state = str(uuid.uuid4())
    request.session["spotify_auth_state"] = state
    return Response({"auth_url": client.get_auth_url(state)})


@api_view(["GET"])
def callback(request):
    code = request.GET.get("code")
    if not code:
        return Response({"error": "Missing code"}, status=400)
    token_info = client.exchange_code(code)
    request.session["spotify_token"] = token_info["access_token"]
    request.session["spotify_refresh_token"] = token_info.get("refresh_token")
    return redirect(FRONTEND_URL)

@api_view(["GET"])
def my_playlists(request):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)
    playlists = client.get_user_playlists(token)
    print(json.dumps(playlists, indent=2))  # TEMP DEBUG
    return Response({"playlists": playlists})

@api_view(["GET"])
def export_playlist(request, playlist_id):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)

    filetype = request.GET.get("filetype", "json")
    raw = client.get_playlist_tracks(token, playlist_id)
    tracks = extract_tracks(raw)
    playlist_name = client.get_playlist_name(token, playlist_id)

    if filetype == "csv":
        from .services.dedup import tracks_to_csv
        csv_content = tracks_to_csv(tracks)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{playlist_name}.csv"'
        return response

    return Response({
        "playlist_name": playlist_name,
        "track_count": len(tracks),
        "tracks": [
            {"name": t.name, "artists": t.artists, "uri": t.uri, "duration_ms": t.duration_ms}
            for t in tracks
        ],
    })

@api_view(["POST"])
def find_duplicates(request):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)

    playlist_a_id = request.data.get("playlist_a_id")
    playlist_b_id = request.data.get("playlist_b_id")
    if not playlist_a_id or not playlist_b_id:
        return Response({"error": "playlist_a_id and playlist_b_id are required"}, status=400)

    tracks_a, tracks_b = _get_two_playlists_tracks(token, playlist_a_id, playlist_b_id)
    overlap = find_overlap(tracks_a, tracks_b)
    near_dupes = find_near_duplicates(tracks_a, tracks_b)

    return Response({
        "duplicate_count": len(overlap),
        "duplicates": [
            {"name": t.name, "artists": t.artists, "uri": t.uri, "image": t.album_image}
            for t in overlap
        ],
        "near_duplicate_count": len(near_dupes),
        "near_duplicates": [
            {
                "a": {"name": a.name, "artists": a.artists, "image": a.album_image, "uri": a.uri},
                "b": {"name": b.name, "artists": b.artists, "image": b.album_image, "uri": b.uri},
            }
            for a, b in near_dupes
        ],
    })

@api_view(["POST"])
def preview_merge(request):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)

    playlist_a_id = request.data.get("playlist_a_id")
    playlist_b_id = request.data.get("playlist_b_id")
    excluded_ids = set(request.data.get("excluded_ids", []))
    near_duplicate_resolutions = request.data.get("near_duplicate_resolutions", [])

    if not playlist_a_id or not playlist_b_id:
        return Response({"error": "playlist_a_id and playlist_b_id are required"}, status=400)

    tracks_a, tracks_b = _get_two_playlists_tracks(token, playlist_a_id, playlist_b_id)
    overlap = find_overlap(tracks_a, tracks_b)
    merged = merge_unique(tracks_a, tracks_b)
    final = apply_selections(merged, excluded_ids, near_duplicate_resolutions)
    total_duration_ms = sum(t.duration_ms for t in final)

    return Response({
        "total_tracks": len(final),
        "duplicates_removed": len(overlap),
        "total_duration": format_duration(total_duration_ms),
    })

@api_view(["POST"])
def merge_playlists(request):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)

    playlist_a_id = request.data.get("playlist_a_id")
    playlist_b_id = request.data.get("playlist_b_id")
    new_name = request.data.get("new_name", "Merged Playlist")
    is_public = request.data.get("public", False)
    excluded_ids = set(request.data.get("excluded_ids", []))
    near_duplicate_resolutions = request.data.get("near_duplicate_resolutions", [])

    if not playlist_a_id or not playlist_b_id:
        return Response({"error": "playlist_a_id and playlist_b_id are required"}, status=400)

    tracks_a, tracks_b = _get_two_playlists_tracks(token, playlist_a_id, playlist_b_id)
    overlap = find_overlap(tracks_a, tracks_b)
    merged = merge_unique(tracks_a, tracks_b)
    final = apply_selections(merged, excluded_ids, near_duplicate_resolutions)

    user_id = client.get_current_user_id(token)
    playlist_a_name = client.get_playlist_name(token, playlist_a_id)
    playlist_b_name = client.get_playlist_name(token, playlist_b_id)

    new_playlist = client.create_playlist(token, user_id, new_name, description="Created by Playlist Merger", public=is_public)
    client.add_tracks(token, new_playlist["id"], [t.uri for t in final])

    MergeHistory.objects.create(
        spotify_user_id=user_id,
        source_playlist_a_name=playlist_a_name,
        source_playlist_b_name=playlist_b_name,
        new_playlist_id=new_playlist["id"],
        new_playlist_name=new_name,
        track_count=len(final),
        duplicates_removed=len(overlap),
    )

    return Response({
        "new_playlist_id": new_playlist["id"],
        "new_playlist_url": new_playlist.get("external_urls", {}).get("spotify"),
        "total_tracks": len(final),
        "duplicates_removed": len(overlap),
    })
import uuid
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import MergeHistory
from .services.spotipy_official import OfficialSpotipyClient
from .services.dedup import extract_tracks, merge_unique, find_overlap

client = OfficialSpotipyClient()


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
    # Redirect back to the React app once that exists; for now, confirm in JSON
    return Response({"status": "logged_in"})


@api_view(["GET"])
def my_playlists(request):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)
    return Response({"playlists": client.get_user_playlists(token)})

@api_view(["POST"])
def merge_playlists(request):
    token = request.session.get("spotify_token")
    if not token:
        return Response({"error": "Not authenticated"}, status=401)

    playlist_a_id = request.data.get("playlist_a_id")
    playlist_b_id = request.data.get("playlist_b_id")
    new_name = request.data.get("new_name", "Merged Playlist")

    if not playlist_a_id or not playlist_b_id:
        return Response({"error": "playlist_a_id and playlist_b_id are required"}, status=400)

    raw_a = client.get_playlist_tracks(token, playlist_a_id)
    raw_b = client.get_playlist_tracks(token, playlist_b_id)
    tracks_a = extract_tracks(raw_a)
    tracks_b = extract_tracks(raw_b)

    overlap = find_overlap(tracks_a, tracks_b)
    merged = merge_unique(tracks_a, tracks_b)

    user_id = client.get_current_user_id(token)
    new_playlist = client.create_playlist(token, user_id, new_name, description="Created by Playlist Merger")
    client.add_tracks(token, new_playlist["id"], [t.uri for t in merged])

    MergeHistory.objects.create(
        spotify_user_id=user_id,
        source_playlist_a_name=playlist_a_id,
        source_playlist_b_name=playlist_b_id,
        new_playlist_id=new_playlist["id"],
        new_playlist_name=new_name,
        track_count=len(merged),
        duplicates_removed=len(overlap),
    )

    return Response({
        "new_playlist_id": new_playlist["id"],
        "new_playlist_url": new_playlist.get("external_urls", {}).get("spotify"),
        "total_tracks": len(merged),
        "duplicates_removed": len(overlap),
    })
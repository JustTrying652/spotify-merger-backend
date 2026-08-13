import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from .base import SpotifyClient


class OfficialSpotipyClient(SpotifyClient):
    def _oauth(self):
        return SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="playlist-read-private playlist-modify-public playlist-modify-private",
        )

    def get_auth_url(self, state: str) -> str:
        return self._oauth().get_authorize_url(state=state)

    def exchange_code(self, code: str) -> dict:
        return self._oauth().get_access_token(code, as_dict=True)

    def get_current_user_id(self, access_token: str) -> str:
        sp = spotipy.Spotify(auth=access_token)
        return sp.current_user()["id"]

    def get_playlist_tracks(self, access_token: str, playlist_id: str) -> list[dict]:
        sp = spotipy.Spotify(auth=access_token)
        items, results = [], sp.playlist_items(playlist_id)
        items.extend(results["items"])
        while results["next"]:
            results = sp.next(results)
            items.extend(results["items"])
        return items

    def create_playlist(self, access_token: str, user_id: str, name: str, description: str = "") -> dict:
        sp = spotipy.Spotify(auth=access_token)
        return sp.user_playlist_create(user_id, name, public=False, description=description)

    def add_tracks(self, access_token: str, playlist_id: str, uris: list[str]) -> None:
        sp = spotipy.Spotify(auth=access_token)
        for i in range(0, len(uris), 100):  # Spotify's 100-URI cap per request
            sp.playlist_add_items(playlist_id, uris[i:i + 100])

    def get_user_playlists(self, access_token: str) -> list[dict]:
        sp = spotipy.Spotify(auth=access_token)
        playlists, results = [], sp.current_user_playlists()
        playlists.extend(results["items"])
        while results["next"]:
            results = sp.next(results)
            playlists.extend(results["items"])

        cleaned = []
        for p in playlists:
            if not p:  # Spotify can return null for an unavailable/deleted playlist slot
                continue
            cleaned.append({
                "id": p.get("id"),
                "name": p.get("name", "Untitled"),
                "track_count": p.get("tracks", {}).get("total", 0),
                "image": (p["images"][0]["url"] if p.get("images") else None),
            })
        return cleaned
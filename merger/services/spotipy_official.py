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
            scope="playlist-read-private playlist-modify-public playlist-modify-private user-library-modify",
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
        items, results = [], sp._get(f"playlists/{playlist_id}/items")
        items.extend(results["items"])
        while results.get("next"):
            results = sp._get(results["next"])
            items.extend(results["items"])
        return items

    def create_playlist(self, access_token: str, user_id: str, name: str, description: str = "", public: bool = False) -> dict:
        sp = spotipy.Spotify(auth=access_token)
        return sp._post("me/playlists", payload={
            "name": name,
            "public": public,
            "description": description,
        })

    def add_tracks(self, access_token: str, playlist_id: str, uris: list[str]) -> None:
        sp = spotipy.Spotify(auth=access_token)
        for i in range(0, len(uris), 100):
            sp._post(f"playlists/{playlist_id}/items", payload={"uris": uris[i:i + 100]})

    def get_user_playlists(self, access_token: str) -> list[dict]:
        sp = spotipy.Spotify(auth=access_token)
        playlists, results = [], sp.current_user_playlists()
        playlists.extend(results["items"])
        while results["next"]:
            results = sp.next(results)
            playlists.extend(results["items"])

        cleaned = []
        for p in playlists:
            if not p:
                continue
            cleaned.append({
                "id": p.get("id"),
                "name": p.get("name", "Untitled"),
                "track_count": p.get("items", {}).get("total", 0),
                "image": (p["images"][0]["url"] if p.get("images") else None),
                "owner": p.get("owner", {}).get("display_name", "Unknown"),
            })
        return cleaned

    def get_playlist_name(self, access_token: str, playlist_id: str) -> str:
        sp = spotipy.Spotify(auth=access_token)
        result = sp._get(f"playlists/{playlist_id}", params={"fields": "name"})
        return result.get("name", "Untitled")

    def delete_playlist(self, access_token: str, playlist_id: str, playlist_uri: str) -> None:
        sp = spotipy.Spotify(auth=access_token)
        sp._delete(f"playlists/{playlist_id}/followers")
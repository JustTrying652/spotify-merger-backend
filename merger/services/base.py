"""
Abstract interface every Spotify client implementation must satisfy.
Views and dedup logic depend on THIS, never on spotipyFree or spotipy
directly — so swapping the underlying library later is a one-file change.
"""
from abc import ABC, abstractmethod


class SpotifyClient(ABC):
    @abstractmethod
    def get_auth_url(self, state: str) -> str:
        """Return the URL to redirect the user to for login/consent."""
        ...

    @abstractmethod
    def exchange_code(self, code: str) -> dict:
        """Exchange an auth callback code for a token dict (access_token, refresh_token, etc.)."""
        ...

    @abstractmethod
    def get_current_user_id(self, access_token: str) -> str:
        ...

    @abstractmethod
    def get_playlist_tracks(self, access_token: str, playlist_id: str) -> list[dict]:
        """Return raw track items in the shape merger.services.dedup.extract_tracks expects."""
        ...

    @abstractmethod
    def create_playlist(self, access_token: str, user_id: str, name: str, description: str = "") -> dict:
        """Return the created playlist object (must include 'id')."""
        ...

    @abstractmethod
    def add_tracks(self, access_token: str, playlist_id: str, uris: list[str]) -> None:
        """Spotify caps this at 100 URIs per call — implementation must chunk internally."""
        ...

    @abstractmethod
    def get_user_playlists(self, access_token: str) -> list[dict]:
        """Return the current user's playlists (id, name, track count, etc.)."""
        ...
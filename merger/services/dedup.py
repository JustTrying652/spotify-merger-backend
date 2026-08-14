# merger/services/dedup.py
"""
Core product logic: given two lists of Spotify track objects, return the
unique set to put in the merged playlist.

Dedup key: Spotify track ID. NOT track name/artist string matching, because
titles have (Remastered), feat. variants, etc. that make string comparison
unreliable. Track ID is stable and exact.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    artists: str  # "Artist A, Artist B" — joined for display only
    uri: str      # spotify:track:<id> — this is what we actually send back to the API


def extract_tracks(raw_playlist_items: list[dict]) -> list[Track]:
    """
    Normalizes raw Spotify API playlist-track payloads into Track objects.
    Skips local files / removed tracks (they show up as track: null).

    NOTE: Spotify's Feb 2026 API migration renamed the nested track key from
    "track" to "item" on the /playlists/{id}/items endpoint. We check both so
    this keeps working if a cached/older response shape ever shows up.
    """
    tracks = []
    for entry in raw_playlist_items:
        t = entry.get("item") or entry.get("track")
        if not t or not t.get("id") or t.get("type") != "track":
            continue  # local file, podcast episode, or unavailable track
        tracks.append(
            Track(
                id=t["id"],
                name=t["name"],
                artists=", ".join(a["name"] for a in t.get("artists", [])),
                uri=t["uri"],
            )
        )
    return tracks


def merge_unique(playlist_a: list[Track], playlist_b: list[Track]) -> list[Track]:
    """
    Returns every track that appears in EITHER playlist, exactly once,
    keeping first-seen order (A's order first, then any new tracks from B).
    """
    seen: set[str] = set()
    result: list[Track] = []
    for track in [*playlist_a, *playlist_b]:
        if track.id not in seen:
            seen.add(track.id)
            result.append(track)
    return result


def find_overlap(playlist_a: list[Track], playlist_b: list[Track]) -> list[Track]:
    """Tracks present in both — useful for a preview screen before merging."""
    ids_b = {t.id for t in playlist_b}
    return [t for t in playlist_a if t.id in ids_b]
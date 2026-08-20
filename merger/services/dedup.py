import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    artists: str
    uri: str
    album_image: str | None = None
    duration_ms: int = 0


def extract_tracks(raw_playlist_items: list[dict]) -> list[Track]:
    tracks = []
    for entry in raw_playlist_items:
        t = entry.get("item") or entry.get("track")
        if not t or not t.get("id") or t.get("type") != "track":
            continue
        album = t.get("album", {})
        images = album.get("images", [])
        tracks.append(
            Track(
                id=t["id"],
                name=t["name"],
                artists=", ".join(a["name"] for a in t.get("artists", [])),
                uri=t["uri"],
                album_image=(images[-1]["url"] if images else None),  # smallest image, good enough for a thumbnail
                duration_ms=t.get("duration_ms", 0),
            )
        )
    return tracks


def merge_unique(playlist_a: list[Track], playlist_b: list[Track]) -> list[Track]:
    seen: set[str] = set()
    result: list[Track] = []
    for track in [*playlist_a, *playlist_b]:
        if track.id not in seen:
            seen.add(track.id)
            result.append(track)
    return result


def find_overlap(playlist_a: list[Track], playlist_b: list[Track]) -> list[Track]:
    ids_b = {t.id for t in playlist_b}
    return [t for t in playlist_a if t.id in ids_b]


_REMASTER_PATTERN = re.compile(
    r"\s*[\(\[-].*?(remaster(ed)?|live|acoustic|deluxe|mono|stereo|version|edit|mix|\d{4}).*?[\)\]]?\s*$",
    re.IGNORECASE,
)


def _normalize_title(name: str) -> str:
    """Strips trailing parenthetical/hyphen qualifiers like '(2011 Remaster)' or '- Live'."""
    stripped = _REMASTER_PATTERN.sub("", name).strip().lower()
    return stripped or name.strip().lower()  # never return empty


def _primary_artist(artists: str) -> str:
    return artists.split(",")[0].strip().lower()


def find_near_duplicates(playlist_a: list[Track], playlist_b: list[Track]) -> list[tuple[Track, Track]]:
    """
    Catches same-song-different-release pairs that exact ID matching misses —
    e.g. 'Song' vs 'Song (2011 Remaster)' by the same primary artist.
    Excludes exact-ID matches (those belong to find_overlap, not here) so the
    two lists never overlap.
    """
    exact_ids = {t.id for t in playlist_a} & {t.id for t in playlist_b}
    b_by_key: dict[tuple[str, str], Track] = {}
    for t in playlist_b:
        if t.id in exact_ids:
            continue
        key = (_normalize_title(t.name), _primary_artist(t.artists))
        b_by_key.setdefault(key, t)

    pairs = []
    seen_a_ids = set()
    for t in playlist_a:
        if t.id in exact_ids or t.id in seen_a_ids:
            continue
        key = (_normalize_title(t.name), _primary_artist(t.artists))
        match = b_by_key.get(key)
        if match:
            pairs.append((t, match))
            seen_a_ids.add(t.id)
    return pairs

def format_duration(total_ms: int) -> str:
    total_seconds = total_ms // 1000
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
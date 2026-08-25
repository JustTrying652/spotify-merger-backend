from merger.services.dedup import Track, merge_unique, find_overlap, extract_tracks, find_near_duplicates, apply_selections


def _t(id_, name="Song", artists="Artist"):
    return Track(id=id_, name=name, artists=artists, uri=f"spotify:track:{id_}")


def test_merge_unique_removes_duplicates():
    a = [_t("1"), _t("2"), _t("3")]
    b = [_t("2"), _t("3"), _t("4")]
    result = merge_unique(a, b)
    assert [t.id for t in result] == ["1", "2", "3", "4"]


def test_merge_unique_preserves_order_a_first():
    a = [_t("3"), _t("1")]
    b = [_t("2")]
    result = merge_unique(a, b)
    assert [t.id for t in result] == ["3", "1", "2"]


def test_find_overlap():
    a = [_t("1"), _t("2")]
    b = [_t("2"), _t("3")]
    assert [t.id for t in find_overlap(a, b)] == ["2"]


def test_extract_tracks_skips_local_and_removed():
    raw = [
        {"item": {"id": "1", "name": "A", "uri": "spotify:track:1", "type": "track", "artists": [{"name": "X"}]}},
        {"item": None},
        {"item": {"id": None, "type": "track"}},
        {"item": {"id": "2", "name": "Ep", "uri": "spotify:episode:2", "type": "episode", "artists": []}},
    ]
    result = extract_tracks(raw)
    assert len(result) == 1
    assert result[0].id == "1"


def test_find_near_duplicates_catches_remaster():
    a = [_t("1", name="Yesterday", artists="The Beatles")]
    b = [_t("2", name="Yesterday - 2009 Remaster", artists="The Beatles")]
    pairs = find_near_duplicates(a, b)
    assert len(pairs) == 1
    assert pairs[0][0].id == "1"
    assert pairs[0][1].id == "2"


def test_find_near_duplicates_excludes_exact_matches():
    a = [_t("1", name="Song", artists="Artist")]
    b = [_t("1", name="Song", artists="Artist")]  # exact same track ID
    assert find_near_duplicates(a, b) == []


def test_find_near_duplicates_ignores_different_songs_same_artist():
    a = [_t("1", name="Song A", artists="Artist")]
    b = [_t("2", name="Song B", artists="Artist")]
    assert find_near_duplicates(a, b) == []

def test_apply_selections_excludes_by_id():
    merged = [_t("1"), _t("2"), _t("3")]
    result = apply_selections(merged, {"2"}, [])
    assert [t.id for t in result] == ["1", "3"]


def test_apply_selections_near_dup_keep_a_drops_b():
    a = _t("1", name="Song")
    b = _t("2", name="Song Remaster")
    merged = [a, b]
    resolutions = [{"a_uri": a.uri, "b_uri": b.uri, "keep": "a"}]
    result = apply_selections(merged, set(), resolutions)
    assert [t.id for t in result] == ["1"]

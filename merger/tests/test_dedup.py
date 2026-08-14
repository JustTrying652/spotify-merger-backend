from merger.services.dedup import Track, merge_unique, find_overlap, extract_tracks


def _t(id_, name="Song"):
    return Track(id=id_, name=name, artists="Artist", uri=f"spotify:track:{id_}")


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
        {"item": None},                                  # removed track
        {"item": {"id": None, "type": "track"}},          # local file, no Spotify ID
        {"item": {"id": "2", "name": "Ep", "uri": "spotify:episode:2", "type": "episode", "artists": []}},  # podcast episode
    ]
    result = extract_tracks(raw)
    assert len(result) == 1
    assert result[0].id == "1"
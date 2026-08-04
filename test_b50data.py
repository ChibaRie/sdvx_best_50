import json
from b50data import (MusicRecord, parse_db, detect_refid, extract_music, load_profile_name,
                        load_skill, select_best50, load_mdb, diff_label, diff_level, build_rows,
                        find_music_folder, resolve_cover)


def make_db_line(obj):
    return json.dumps(obj, ensure_ascii=False)


def make_fixture(tmp_path):
    lines = [
        make_db_line({"collection": "profile", "__refid": "REFID1", "version": 7, "name": "Tester", "_id": "a"}),
        make_db_line({"collection": "music", "__refid": "REFID1", "version": 7, "mid": 1, "type": 0,
                      "score": 100, "exscore": 0, "volforce": 10, "clear": 2, "grade": 3, "_id": "b"}),
        make_db_line({"collection": "music", "__refid": "REFID1", "version": 7, "mid": 2, "type": 1,
                      "score": 200, "exscore": 0, "volforce": 20, "clear": 4, "grade": 5, "_id": "c"}),
        make_db_line({"collection": "music", "__refid": "REFID1", "version": 6, "mid": 3, "type": 1,
                      "score": 300, "exscore": 0, "volforce": 30, "clear": 5, "grade": 6, "_id": "d"}),
        make_db_line({"collection": "item", "__refid": "REFID1", "version": 7, "type": 1, "id": 1, "param": 1, "_id": "e"}),
    ]
    p = tmp_path / "db.json"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_parse_db_returns_all_records(tmp_path):
    p = make_fixture(tmp_path)
    assert len(parse_db(str(p))) == 5


def test_detect_refid_most_common(tmp_path):
    p = make_fixture(tmp_path)
    assert detect_refid(parse_db(str(p))) == "REFID1"


def test_detect_refid_empty(tmp_path):
    import pytest as _pytest
    p = tmp_path / "empty.json"
    p.write_text("", encoding="utf-8")
    with _pytest.raises(ValueError):
        detect_refid(parse_db(str(p)))


def test_extract_music_filters(tmp_path):
    p = make_fixture(tmp_path)
    recs = extract_music(parse_db(str(p)), "REFID1", version=7)
    assert len(recs) == 2
    assert recs[0] == MusicRecord(mid=1, type=0, score=100, exscore=0, volforce=10, clear=2, grade=3)
    assert recs[1].mid == 2 and recs[1].clear == 4


def test_load_profile_name(tmp_path):
    p = make_fixture(tmp_path)
    assert load_profile_name(parse_db(str(p)), "REFID1") == "Tester"
    assert load_profile_name(parse_db(str(p)), "UNKNOWN") == "PLAYER"


def test_select_best50_sorts_and_truncates():
    recs = [MusicRecord(mid=i, type=0, score=0, exscore=0, volforce=float(i), clear=0, grade=0)
            for i in range(60)]  # volforce = mid value
    top, total = select_best50(recs)
    assert len(top) == 50
    assert top[0].mid == 59 and top[49].mid == 10  # descending
    assert total == 1.725


def test_select_best50_under_50():
    recs = [MusicRecord(mid=i, type=0, score=0, exscore=0, volforce=float(i), clear=0, grade=0)
            for i in range(5)]
    top, total = select_best50(recs)
    assert len(top) == 5
    assert total == round((4 + 3 + 2 + 1 + 0) / 1000, 3)


def test_select_best50_empty():
    top, total = select_best50([])
    assert top == [] and total == 0.0


def test_select_best50_dedup_by_mid_type():
    recs = [
        MusicRecord(mid=1, type=0, score=0, exscore=0, volforce=10.0, clear=0, grade=0),
        MusicRecord(mid=1, type=0, score=0, exscore=0, volforce=20.0, clear=0, grade=0),
        MusicRecord(mid=1, type=1, score=0, exscore=0, volforce=30.0, clear=0, grade=0),
    ]
    top, total = select_best50(recs)
    assert len(top) == 2
    assert top[0].volforce == 30.0
    assert top[1].volforce == 20.0
    assert total == round(50.0 / 1000, 3)


# ---------------------------------------------------------------------------
# Task 3 tests
# ---------------------------------------------------------------------------

def test_load_mdb(tmp_path):
    p = tmp_path / "mdb.json"
    p.write_text('{"mdb":{"music":[{"id":"1","info":{"title_name":"SONG"},"difficulty":[{},{"novice":"5"}]}]}}', encoding="utf-8")
    mdb = load_mdb(str(p))
    assert mdb["1"]["info"]["title_name"] == "SONG"


def test_diff_label():
    assert diff_label("7", 0) == "NOV"
    assert diff_label("7", 3) == "NBL"
    assert diff_label("2", 3) == "INF"
    assert diff_label("4", 4) == "MXM"


def test_diff_level():
    entry = {"difficulty": [{}, {}, {}, {}, {}, {}, {},
              {"novice": "5", "advanced": "12", "exhaust": "14", "maximum": "17.5"}]}
    assert diff_level(entry, 1, 7) == "12"
    assert diff_level(entry, 0, 7) == "5"
    # infinite key missing -> fallback to difficulty[0] also missing -> "?"
    assert diff_level(entry, 3, 7) == "?"
    # value is "0" → fallback
    entry0 = {"difficulty": [{}, {}, {}, {}, {}, {}, {}, {"novice": "0"}, {"novice": "7"}]}
    assert diff_level(entry0, 0, 7) == "?"


def test_build_rows(tmp_path):
    mdb = {"1": {"info": {"title_name": "T1", "inf_ver": "7"},
                 "difficulty": [{}, {}, {}, {}, {}, {}, {}, {"novice": "5"}]}}
    rows = build_rows([MusicRecord(mid=1, type=0, score=900, exscore=800, volforce=100.0, clear=6, grade=10)], mdb)
    assert rows[0]["title"] == "T1"
    assert rows[0]["label"] == "NOV"
    assert rows[0]["level"] == "5"
    assert rows[0]["clear_name"] == "PUC"
    assert rows[0]["grade_name"] == "S"
    # unknown track
    rows2 = build_rows([MusicRecord(mid=99999, type=0, score=0, exscore=0, volforce=1.0, clear=0, grade=0)], mdb)
    assert rows2[0]["title"] == "Unknown" and rows2[0]["level"] == "?"


# ---------------------------------------------------------------------------
# Task 4 tests
# ---------------------------------------------------------------------------

def _make_music_tree(tmp_path):
    root = tmp_path / "music"
    d1 = root / "0001_alpha"
    d1.mkdir(parents=True)
    (d1 / "jk_0001_1.png").write_bytes(b"P")
    (d1 / "jk_0001_2.png").write_bytes(b"P")
    d2 = root / "2398_beta"
    d2.mkdir(parents=True)
    (d2 / "jk_2398_1.png").write_bytes(b"P")
    return str(root)


def test_find_music_folder_zero_pad(tmp_path):
    root = _make_music_tree(tmp_path)
    assert find_music_folder(root, 1) is not None
    assert find_music_folder(root, 1).endswith("0001_alpha")
    assert find_music_folder(root, 2398) is not None


def test_find_music_folder_missing(tmp_path):
    root = _make_music_tree(tmp_path)
    assert find_music_folder(root, 99999) is None


def test_resolve_cover_exact(tmp_path):
    root = _make_music_tree(tmp_path)
    p = resolve_cover(root, 1, 1)   # ADV -> _2
    assert p is not None and p.endswith("jk_0001_2.png")


def test_resolve_cover_fallback(tmp_path):
    root = _make_music_tree(tmp_path)
    p = resolve_cover(root, 2398, 2)  # EXH -> _3 nonexistent -> fallback _1
    assert p is not None and p.endswith("jk_2398_1.png")


def test_resolve_cover_none(tmp_path):
    root = tmp_path / "empty_music"
    root.mkdir()
    assert resolve_cover(str(root), 1, 0) is None


def test_find_music_folder_skips_files(tmp_path):
    root = tmp_path / "music"
    root.mkdir()
    (root / "0042_fake.png").write_bytes(b"not a dir")   # file with 0042_ prefix but not a directory
    d = root / "0042_real"
    d.mkdir()
    (d / "jk_0042_1.png").write_bytes(b"P")
    assert find_music_folder(str(root), 42) is not None          # hits directory, not the file
    p = resolve_cover(str(root), 42, 0)
    assert p is not None and p.endswith("jk_0042_1.png")


# ---------------------------------------------------------------------------
# Task 1 tests: load_skill
# ---------------------------------------------------------------------------

def make_skill_line(refid, name, version=7):
    return json.dumps({"collection": "skill", "__refid": refid, "version": version,
                       "name": name, "level": 5, "base": 1, "type": 1, "_id": "x"},
                      ensure_ascii=False)


def test_load_skill_found(tmp_path):
    p = tmp_path / "db.json"
    lines = [
        make_db_line({"collection": "profile", "__refid": "R1", "version": 7, "name": "RIE", "_id": "a"}),
        make_skill_line("R1", "蒼穹"),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert load_skill(parse_db(str(p)), "R1") == "蒼穹"


def test_load_skill_missing(tmp_path):
    p = tmp_path / "db.json"
    p.write_text(make_db_line({"collection": "profile", "__refid": "R1", "version": 7, "name": "RIE", "_id": "a"}) + "\n", encoding="utf-8")
    assert load_skill(parse_db(str(p)), "R1") == ""


def test_load_skill_wrong_refid(tmp_path):
    p = tmp_path / "db.json"
    lines = [
        make_db_line({"collection": "profile", "__refid": "R1", "version": 7, "name": "RIE", "_id": "a"}),
        make_skill_line("R2", "絶空"),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert load_skill(parse_db(str(p)), "R1") == ""


def test_load_skill_name_zero(tmp_path):
    p = tmp_path / "db.json"
    lines = [
        make_db_line({"collection": "profile", "__refid": "R1", "version": 7, "name": "RIE", "_id": "a"}),
        make_skill_line("R1", 0),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert load_skill(parse_db(str(p)), "R1") == ""


def test_load_skill_name_neg_one(tmp_path):
    p = tmp_path / "db.json"
    lines = [
        make_db_line({"collection": "profile", "__refid": "R1", "version": 7, "name": "RIE", "_id": "a"}),
        make_skill_line("R1", -1),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert load_skill(parse_db(str(p)), "R1") == ""


# ---------------------------------------------------------------------------
# vf_pct contribution tests
# ---------------------------------------------------------------------------

def test_build_rows_vf_pct_uneven():
    recs = [
        MusicRecord(mid=1, type=0, score=0, exscore=0, volforce=300.0, clear=0, grade=0),
        MusicRecord(mid=2, type=1, score=0, exscore=0, volforce=100.0, clear=0, grade=0),
    ]
    rows = build_rows(recs, {})
    assert rows[0]["vf_pct"] == 75.0
    assert rows[1]["vf_pct"] == 25.0
    assert sum(r["vf_pct"] for r in rows) == 100.0


def test_build_rows_vf_pct_zero_sum():
    recs = [MusicRecord(mid=1, type=0, score=0, exscore=0, volforce=0.0, clear=0, grade=0)]
    rows = build_rows(recs, {})
    assert rows[0]["vf_pct"] == 0.0


def test_build_rows_vf_pct_four_decimals():
    recs = [
        MusicRecord(mid=1, type=0, score=0, exscore=0, volforce=100.0, clear=0, grade=0),
        MusicRecord(mid=2, type=1, score=0, exscore=0, volforce=200.0, clear=0, grade=0),
    ]
    rows = build_rows(recs, {})
    assert rows[0]["vf_pct"] == 33.3333
    assert rows[1]["vf_pct"] == 66.6667

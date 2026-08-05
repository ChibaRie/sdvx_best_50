import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MusicRecord:
    mid: int
    type: int
    score: int
    exscore: int
    volforce: float
    clear: int
    grade: int


def parse_db(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def detect_refid(records: list[dict]) -> str:
    counts: dict[str, int] = {}
    for r in records:
        refid = r.get("__refid")
        if refid:
            counts[refid] = counts.get(refid, 0) + 1
    if not counts:
        raise ValueError("no player refid found in database (empty or invalid save data)")
    return max(counts, key=counts.get)


def extract_music(records: list[dict], refid: str, version: int = 7) -> list[MusicRecord]:
    result = []
    for r in records:
        if (r.get("collection") == "music"
                and r.get("__refid") == refid
                and r.get("version") == version):
            result.append(MusicRecord(
                mid=int(r["mid"]),
                type=int(r["type"]),
                score=int(r.get("score", 0)),
                exscore=int(r.get("exscore", 0)),
                volforce=float(r.get("volforce", 0)),
                clear=int(r.get("clear", 0)),
                grade=int(r.get("grade", 0)),
            ))
    return result


def load_profile_name(records: list[dict], refid: str, version: int = 7) -> str:
    for r in records:
        if (r.get("collection") == "profile"
                and r.get("__refid") == refid
                and r.get("version") == version
                and "name" in r):
            return r["name"]
    return "PLAYER"


def load_skill(records: list[dict], refid: str, version: int = 7) -> str:
    for r in records:
        if (r.get("collection") == "skill"
                and r.get("__refid") == refid
                and r.get("version") == version):
            name = r.get("name", "")
            # SDVX uses 0 / -1 for "no skill name set"
            if name is None or name in (0, -1, "0", "-1"):
                return ""
            return str(name)
    return ""


def select_best50(records: list[MusicRecord]) -> tuple[list[MusicRecord], float]:
    best: dict[tuple[int, int], MusicRecord] = {}
    for r in records:
        key = (r.mid, r.type)
        if key not in best or r.volforce > best[key].volforce:
            best[key] = r
    unique = list(best.values())
    sorted_recs = sorted(unique, key=lambda r: r.volforce, reverse=True)
    top = sorted_recs[:50]
    total = round(sum(r.volforce for r in top) / 1000, 3)
    return top, total


# ---------------------------------------------------------------------------
# Task 3: mdb loading & row assembly
# ---------------------------------------------------------------------------
#
# VF (VOLFORCE) formula reference — computed by asphyxia, stored in DB:
#   VF = 难度等级 × (score / 10,000,000)² × GRADE系数 × CLEAR系数
#
# CLEAR coefficients:
#   0: No Data         → 不计算
#   1: PLAYED          → 0.50
#   2: EFFECTIVE CLEAR → 1.00
#   3: EXCESSIVE CLEAR → 1.02
#   4: MAXXIVE CLEAR   → 1.04
#   5: UC              → 1.06
#   6: PUC             → 1.10
#
# GRADE coefficients (by required score):
#   D   : —            0.80
#   C   : 6,500,000    0.82
#   B   : 7,500,000    0.85
#   A   : 8,700,000    0.88
#   A+  : 9,000,000    0.91
#   AA  : 9,300,000    0.94
#   AA+ : 9,500,000    0.97
#   AAA : 9,700,000    1.00
#   AAA+: 9,800,000    1.02
#   S   : 9,900,000    1.05
#
# Total VOLFORCE = sum(单曲VF) / 1000

TYPE_KEYS = {0: "novice", 1: "advanced", 2: "exhaust", 3: "infinite", 4: "maximum", 5: "ultimate"}

CLEAR_NAMES = {
    0: "No Data", 1: "PLAYED", 2: "EFFECTIVE CLEAR", 3: "EXCESSIVE CLEAR",
    4: "MAXXIVE CLEAR", 5: "UC", 6: "PUC",
}

GRADE_NAMES = {
    0: "No Grade", 1: "D", 2: "C", 3: "B", 4: "A", 5: "A+",
    6: "AA", 7: "AA+", 8: "AAA", 9: "AAA+", 10: "S",
}

INF_LABELS = {2: "INF", 3: "GRV", 4: "HVN", 5: "VVD", 6: "XCD", 7: "NBL"}
BASE_LABELS = {0: "NOV", 1: "ADV", 2: "EXH", 4: "MXM", 5: "ULT"}


def load_mdb(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    music = data["mdb"]["music"]
    return {str(m["id"]): m for m in music}


def diff_label(inf_ver: str, mtype: int) -> str:
    if mtype == 3:
        return INF_LABELS.get(int(inf_ver or 0), "INF")
    return BASE_LABELS.get(mtype, "?")


def diff_level(entry: dict, mtype: int, version: int = 7) -> str:
    key = TYPE_KEYS.get(mtype)
    if not key:
        return "?"
    for v in (version, 0):
        try:
            d = entry["difficulty"][v]
        except (IndexError, KeyError):
            continue
        if key in d:
            val = d[key]
            if val not in ("0", 0, None, ""):
                return str(val)
    return "?"


def build_rows(top: list[MusicRecord], mdb: dict[str, dict], version: int = 7) -> list[dict]:
    vf_sum = sum(r.volforce for r in top)
    rows = []
    for rec in top:
        entry = mdb.get(str(rec.mid))
        if entry is None:
            title, label, level = "Unknown", "?", "?"
        else:
            info = entry.get("info", {})
            title = info.get("title_name", "Unknown")
            label = diff_label(info.get("inf_ver", "7"), rec.type)
            level = diff_level(entry, rec.type, version)
        pct = round(rec.volforce / vf_sum * 100, 4) if vf_sum > 0 else 0.0
        rows.append({
            "mid": rec.mid, "type": rec.type, "title": title, "label": label,
            "level": level, "score": rec.score, "exscore": rec.exscore,
            "volforce": rec.volforce, "vf_pct": pct, "clear": rec.clear, "grade": rec.grade,
            "clear_name": CLEAR_NAMES.get(rec.clear, "No Data"),
            "grade_name": GRADE_NAMES.get(rec.grade, "No Grade"),
        })
    return rows


# ---------------------------------------------------------------------------
# Task 4: cover file resolution
# ---------------------------------------------------------------------------

TYPE_COVER_SUFFIX = {0: "1", 1: "2", 2: "3", 3: "4", 4: "5"}


def find_music_folder(music_root: str, mid: int) -> str | None:
    if not os.path.isdir(music_root):
        return None
    for entry in os.listdir(music_root):
        if entry.startswith(f"{mid:04d}_"):
            full = os.path.join(music_root, entry)
            if os.path.isdir(full):
                return full
    for entry in os.listdir(music_root):
        if entry.startswith(f"{mid}_"):
            full = os.path.join(music_root, entry)
            if os.path.isdir(full):
                return full
    return None


def resolve_cover(music_root: str, mid: int, mtype: int) -> str | None:
    folder = find_music_folder(music_root, mid)
    if not folder:
        return None
    suffix = TYPE_COVER_SUFFIX.get(mtype)
    if suffix:
        target = os.path.join(folder, f"jk_{mid:04d}_{suffix}.png")
        if os.path.isfile(target):
            return target
    # fallback: _1 preferred, then any jk_*.png
    best = None
    for name in os.listdir(folder):
        if name.startswith(f"jk_{mid:04d}_") and name.endswith(".png"):
            if best is None or name == f"jk_{mid:04d}_1.png":
                best = os.path.join(folder, name)
    return best

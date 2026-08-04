import os
import sys

from b50data import (parse_db, detect_refid, extract_music, load_profile_name,
                     select_best50, load_mdb, build_rows, resolve_cover, load_skill)
from render_html import render_html
from render_png import render_png

def main():
    cwd = os.getcwd()
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(cwd, "asphyxia", "savedata", "sdvx@asphyxia.db")
    mdb_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(cwd, "asphyxia", "plugins", "sdvx@asphyxia", "webui", "asset", "json", "music_db.json")
    music_root = sys.argv[3] if len(sys.argv) > 3 else os.path.join(cwd, "contents", "data", "music")
    out_dir = sys.argv[4] if len(sys.argv) > 4 else os.path.join(cwd, "b50_output")
    font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msyh.ttc")

    try:
        records = parse_db(db_path)
    except OSError as e:
        print(f"error: cannot read save database: {e}")
        sys.exit(1)
    refid = detect_refid(records)
    player = load_profile_name(records, refid)
    skill = load_skill(records, refid)
    top, total_vf = select_best50(extract_music(records, refid))
    try:
        mdb = load_mdb(mdb_path)
    except OSError as e:
        print(f"error: cannot read music database: {e}")
        sys.exit(1)
    rows = build_rows(top, mdb)
    rows = [
        {**r, "cover_path": resolve_cover(music_root, r["mid"], r["type"])}
        for r in rows
    ]

    os.makedirs(out_dir, exist_ok=True)
    jpg = os.path.join(out_dir, "b50.jpg")
    htm = os.path.join(out_dir, "b50.html")
    render_png(rows, player, total_vf, jpg, skill=skill, font_path=font_path)
    render_html(rows, player, total_vf, htm, skill=skill)
    print(f"player={player}  top={len(rows)}  total_vf={total_vf}")
    print(f"written: {jpg}")
    print(f"written: {htm}")

if __name__ == "__main__":
    main()

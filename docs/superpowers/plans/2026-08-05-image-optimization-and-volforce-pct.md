# Image Lightweighting + Volforce Contribution Percentage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Shrink the generated B50 image to 800px-wide JPEG (~0.4-0.6MB) and display each song's share of total VOLFORCE as a percentage on its card.

**Architecture:** Two independent changes to the existing pipeline. (1) `b50data.build_rows` gains a `vf_pct` field per row (single source of truth). (2) `render_png` scales layout constants to 800px and saves JPEG; `render_png`/`render_html` display `vf_pct`. `gen_b50.py` renames output to `b50.jpg`.

**Tech Stack:** Python 3, Pillow (PNG→JPEG conversion, layout scaling).

## Global Constraints

- Python 3.10+, Pillow only (no new dependencies).
- TDD: write the failing test first (RED → GREEN).
- Immutability: never mutate dicts/records in place; build new rows.
- Commit messages follow `<type>: <description>` (feat/fix/refactor/docs/test/chore).
- Spec: `docs/superpowers/specs/2026-08-05-image-optimization-and-volforce-pct-design.md`.
- `vf_pct` is 1 decimal place, percentage of exact VF sum (`sum(volforce)`), NOT the rounded `total_vf`; guard `vf_sum == 0 → pct 0.0`.

---

### Task 1: Add `vf_pct` to `build_rows`

**Files:**
- Modify: `b50data.py:142-160` (`build_rows`)
- Test: `test_b50data.py` (append new tests)

**Interfaces:**
- Consumes: `MusicRecord` (has `.volforce: float`), `mdb: dict[str, dict]`.
- Produces: `build_rows(top, mdb, version=7) -> list[dict]` where every row dict now additionally contains `"vf_pct": float` (0.0-100.0, 1 decimal). Later tasks read `r["vf_pct"]`.

- [ ] **Step 1: Write the failing tests** (append to `test_b50data.py`)

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest test_b50data.py -k vf_pct -v`
Expected: FAIL — `KeyError: 'vf_pct'` (key does not exist yet).

- [ ] **Step 3: Implement**

In `build_rows`, compute the exact sum once and add the field:

```python
def build_rows(top, mdb, version=7):
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
        pct = round(rec.volforce / vf_sum * 100, 1) if vf_sum > 0 else 0.0
        rows.append({
            "mid": rec.mid, "type": rec.type, "title": title, "label": label,
            "level": level, "score": rec.score, "exscore": rec.exscore,
            "volforce": rec.volforce, "vf_pct": pct, "clear": rec.clear, "grade": rec.grade,
            "clear_name": CLEAR_NAMES.get(rec.clear, "No Data"),
            "grade_name": GRADE_NAMES.get(rec.grade, "No Grade"),
        })
    return rows
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest test_b50data.py -v`
Expected: PASS (new + all existing `test_b50data` cases).

- [ ] **Step 5: Commit**

```bash
git add b50data.py test_b50data.py
git commit -m "feat: add vf_pct contribution field to b50 rows"
```

---

### Task 2: Scale PNG layout to 800px and output JPEG

**Files:**
- Modify: `render_png.py` (constants block `:13-21`, fonts `:149-155`, header `:157-181`, save `:253-257`)
- Test: `test_render_png.py`

**Interfaces:**
- Consumes: nothing new (same `render_png` signature).
- Produces: `render_png(...)` now renders an 800px-wide canvas and writes a JPEG (quality=90, optimize, progressive). Task 3 reuses the same function.

- [ ] **Step 1: Update the failing layout tests**

In `test_render_png.py`, all four width assertions must change from 1200 to 800:
- `test_render_png_card_grid_no_overlap` (line 17) — also height `>= 3100` → `>= 2000`:

```python
    img = Image.open(out)
    assert img.width == 800
    # 高度 = 头部 56 + 边距 14 + 10*(200+10) - 10 + 14 = 2174
    assert img.height >= 2000
    img.close()
```

- `test_render_png_renders_exscore` (line 33)
- `test_render_png_long_title_does_not_crash` (line 46)
- `test_render_png_with_skill_no_crash` (line 59)

Each of these three has `assert img.width == 1200` → `assert img.width == 800` (no height assertion in these).

- [ ] **Step 2: Add JPEG-format test** (append to `test_render_png.py`; add `import os` at top)

```python
def test_render_png_outputs_jpeg(tmp_path):
    rows = [{
        "mid": i + 1, "type": 0, "title": "T", "label": "NOV", "level": "5",
        "score": 9_000_000, "exscore": 9000, "volforce": 20.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S", "cover_path": None,
    } for i in range(50)]
    out = tmp_path / "b50.jpg"
    render_png(rows, "Tester", 11.0, str(out))
    img = Image.open(out)
    assert img.format == "JPEG"
    assert img.width == 800
    img.close()
    assert os.path.getsize(str(out)) < 300_000
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest test_render_png.py -v`
Expected: FAIL — width is 1200 (not 800) and format is PNG (not JPEG).

- [ ] **Step 4: Implement** in `render_png.py`

Layout constants:

```python
CANVAS_W = 800
MARGIN_X = 15
MARGIN_Y = 14
HEADER_H = 56
CARD_W = 146
CARD_H = 200
COVER_H = 146
CARD_GAP = 10
COLS = 5
```

Fonts (inside `render_png`):

```python
    header_name_font = _font(font_path, 18)
    header_meta_font = _font(font_path, 11)
    title_font = _font(font_path, 10)
    small_font = _font(font_path, 8)
    vf_font = _font(font_path, 9)
    ex_font = _font(font_path, 7)
```

Header bar block (scaled from `:157-181`):

```python
    draw.rectangle([(0, 0), (CANVAS_W, HEADER_H)], fill=HEADER_BG)
    draw.ellipse(
        [(MARGIN_X, 11), (MARGIN_X + 32, 43)],
        fill=AVATAR_BG, outline=AVATAR_BORDER, width=2,
    )
    _draw_text_within(
        draw, player_name, header_name_font,
        MARGIN_X + 42, 9, CANVAS_W - MARGIN_X - 42 - 130, TEXT_PRIMARY,
    )
    vf_text = f"VOLFORCE {total_vf}"
    draw.text((MARGIN_X + 42, 33), vf_text, font=header_meta_font, fill=VF_COLOR)
    if skill:
        skill_text = f"SKILL {skill}"
        skill_w = int(draw.textlength(skill_text, font=header_meta_font))
        _draw_text_within(
            draw, skill_text, header_meta_font,
            CANVAS_W - MARGIN_X - skill_w, 22,
            CANVAS_W - MARGIN_X, TEXT_PRIMARY,
        )
```

Card text-area offsets (inside the grid loop): change the four Y offsets so title/tag/bottom rows stack without overlap in the 54px text area (CARD_H 200 − COVER_H 146):

```python
        title_y = cy + COVER_H + 6
        ...
        tag_y = cy + COVER_H + 20
        ...
        bottom_y = cy + CARD_H - 18
```

(Keep the existing `_draw_text_within` calls and right-aligned score/VF logic — only these three Y offsets change.)

Save block (`:253-257`):

```python
    canvas.save(out_path, "JPEG", quality=90, optimize=True, progressive=True)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest test_render_png.py -v`
Expected: PASS. Also do a quick visual check of one rendered JPEG (any aspect overlap should be visible); if the title/tag/EX rows collide, nudge the three Y offsets (e.g. `tag_y = title_y + 14`, `bottom_y = CARD_H - 16`).

- [ ] **Step 6: Commit**

```bash
git add render_png.py test_render_png.py
git commit -m "feat: shrink PNG layout to 800px and output optimized JPEG"
```

---

### Task 3: Show VF percentage on PNG cards

**Files:**
- Modify: `render_png.py` (add helper + VF text)
- Test: `test_render_png.py` (append)

**Interfaces:**
- Consumes: row dicts from Task 1 — `volforce: float`, `vf_pct: float`.
- Produces: `format_vf(vf: float, pct: float) -> str` helper (module-level), used by the card VF text.

- [ ] **Step 1: Write the failing tests** (append to `test_render_png.py`)

```python
from render_png import format_vf  # add to existing import


def test_format_vf_appends_pct():
    assert format_vf(250.0, 12.3) == "250.0 ·12.3%"
    assert format_vf(1.5, 0.1) == "1.5 ·0.1%"
    assert format_vf(0.0, 0.0) == "0.0 ·0.0%"


def test_render_png_with_vf_pct_no_crash(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "T", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "vf_pct": 100.0,
        "clear": 6, "grade": 10, "clear_name": "PUC", "grade_name": "S",
        "cover_path": None,
    }]
    out = tmp_path / "b50.jpg"
    render_png(rows, "Tester", 1.0, str(out))
    img = Image.open(out)
    assert img.format == "JPEG"
    assert img.width == 800
    img.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest test_render_png.py -k "format_vf or vf_pct" -v`
Expected: FAIL — `ImportError: cannot import name 'format_vf'`.

- [ ] **Step 3: Implement** in `render_png.py`

Add a module-level helper (near `_hex_to_rgb`):

```python
def format_vf(vf: float, pct: float) -> str:
    """Format the VF value plus its share of total VOLFORCE, e.g. '250.0 ·12.3%'."""
    return f"{vf} ·{pct}%"
```

In the card grid loop, replace the VF text construction:

```python
        vf_text = format_vf(r["volforce"], r.get("vf_pct", 0.0))
```

(The `vf_w = int(draw.textlength(vf_text, font=vf_font))` line that follows stays as-is.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest test_render_png.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add render_png.py test_render_png.py
git commit -m "feat: show volforce contribution percentage on PNG cards"
```

---

### Task 4: Add VF contribution column to HTML

**Files:**
- Modify: `render_html.py:7,19,25-26`
- Test: `test_render_html.py` (append)

**Interfaces:**
- Consumes: row dicts from Task 1 — `vf_pct: float`.
- Produces: HTML table with a `VF占比` column showing e.g. `12.3%`.

- [ ] **Step 1: Write the failing test** (append to `test_render_html.py`)

```python
def test_render_html_includes_vf_pct_column(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "T", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "vf_pct": 100.0,
        "clear": 6, "grade": 10, "clear_name": "PUC", "grade_name": "S",
    }]
    out = tmp_path / "b50.html"
    render_html(rows, "Tester", 1.725, str(out))
    text = out.read_text(encoding="utf-8")
    assert "VF占比" in text
    assert "100.0%" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest test_render_html.py -k vf_pct -v`
Expected: FAIL — "VF占比" not in text.

- [ ] **Step 3: Implement** in `render_html.py`

Header (`:7`):

```python
    thead = "<tr><th>#</th><th>封面</th><th>曲名</th><th>难度</th><th>等级</th><th>SCORE</th><th>EX SCORE</th><th>GRADE</th><th>VF</th><th>VF占比</th></tr>"
```

Body row (`:25-26`): after the VF cell, add

```python
            f'<td>{r["volforce"]}</td>'
            f'<td>{r.get("vf_pct", 0.0)}%</td>'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest test_render_html.py -v`
Expected: PASS (existing tests unaffected — extra column is harmless).

- [ ] **Step 5: Commit**

```bash
git add render_html.py test_render_html.py
git commit -m "feat: add volforce contribution column to HTML output"
```

---

### Task 5: Rename output to `b50.jpg` and update docs

**Files:**
- Modify: `gen_b50.py:38-44`
- Modify: `README.md` (usage tree `:26-28`, output spec table `:49-54`, project structure comment `:84`)

**Interfaces:**
- Consumes: `render_png` now writes JPEG regardless of extension.
- Produces: CLI writes `b50_output/b50.jpg`; docs reflect 800px / JPEG / ~0.4MB.

- [ ] **Step 1: Rename the output path** in `gen_b50.py`

```python
    jpg = os.path.join(out_dir, "b50.jpg")
    ...
    render_png(rows, player, total_vf, jpg, skill=skill, font_path=font_path)
    render_html(rows, player, total_vf, htm, skill=skill)
    print(f"player={player}  top={len(rows)}  total_vf={total_vf}")
    print(f"written: {jpg}")
    print(f"written: {htm}")
```

- [ ] **Step 2: Verify CLI runs** (no save data available → expect graceful error path only if no db)

Run: `python -c "import ast; ast.parse(open('gen_b50.py', encoding='utf-8').read())"` and
`python -m pytest -q`
Expected: syntax OK; all tests pass.

- [ ] **Step 3: Update README** — the three spots:

`:26-28` directory tree: `b50.png` → `b50.jpg`
`:49-54` spec table:

| 规格 | 值 |
|------|-----|
| 尺寸 | 800 × ~2174 px |
| 格式 | JPEG（quality 90） |
| 体积 | ~0.4-0.6MB |
| 布局 | 5 列 × 10 行，每卡正方形封面 146×146 |
| 信息 | 封面 / 曲名 / 难度标签(着色) / 分数 / EX SCORE / GRADE / VF·占比 |

`:84` project-structure comment: `b50.png` → `b50.jpg`.

Also update the "工作原理" step 6 comment: `渲染卡片网格 PNG` → `渲染卡片网格 JPEG + 自包含 HTML`.

- [ ] **Step 4: Regenerate preview assets (requires real save data)**

Note for the user — run with real game data:
```bash
python gen_b50.py
# then produce 800px JPEG and thumbnails for assets/preview.png / preview_sm.png
```
The repo has no sample save data, so this step is a manual user action (or a small synthetic-data script if a placeholder-based preview is acceptable). If skipped, README preview still references the old 1200px image — flag this as a known limitation in the PR/commit.

- [ ] **Step 5: Commit**

```bash
git add gen_b50.py README.md
git commit -m "docs: rename output to b50.jpg, update README for 800px JPEG"
```

---

### Task 6: Full verification

**Files:** none (run-only)

- [ ] **Step 1: Run the entire suite**

Run: `python -m pytest -q`
Expected: all tests pass (32 existing + ~8 new).

- [ ] **Step 2: Render one real image end-to-end if save data is available**

Run: `python gen_b50.py` (or with explicit paths) and inspect `b50_output/b50.jpg`:
- dimensions ≈ 800 × 2174
- file size in the 0.4-0.6MB range
- every card shows `VF ·X.X%`
- no text overlap on cards
If save data is unavailable, note the visual check as pending for the user.

- [ ] **Step 3: Final review pass**

Run: `git log --oneline` — confirm 5 feature commits (Tasks 1-5) with clean messages.

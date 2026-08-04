"""Card-grid PNG renderer for SDVX B50.

Outputs a 1200px-wide image with a player header bar and a 5×10 card grid.
Long text is truncated with ellipsis.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
CANVAS_W = 800
MARGIN_X = 15
MARGIN_Y = 14
HEADER_H = 56
CARD_W = 146
CARD_H = 200
COVER_H = 146
CARD_GAP = 10
COLS = 5

BG_COLOR = (26, 26, 26)          # #1a1a1a
CARD_BG = (37, 37, 37)           # #252525
HEADER_BG = (37, 37, 37)         # #252525
TEXT_PRIMARY = (255, 255, 255)
TEXT_SECONDARY = (200, 200, 200)
TEXT_MUTED = (170, 170, 170)
VF_COLOR = (78, 205, 196)        # #4ecdc4
AVATAR_BG = (85, 85, 85)
AVATAR_BORDER = (120, 120, 120)

DIFF_COLORS: dict[int, str] = {
    0: "#4ade80",  # NOV
    1: "#38bdf8",  # ADV
    2: "#f472b6",  # EXH
    3: "#a78bfa",  # INF/GRV/HVN/VVD/XCD/NBL
    4: "#fbbf24",  # MXM
    5: "#f87171",  # ULT
}

# Resampling constant: prefer the modern enum, fall back for old Pillow.
try:
    _RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover
    _RESAMPLE = Image.LANCZOS


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path, size)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _difficulty_color(mtype: int) -> str:
    """Return the hex color for a given difficulty type."""
    return DIFF_COLORS.get(mtype, "#888888")


def _draw_text_within(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    max_w: int,
    fill: tuple[int, int, int],
) -> None:
    """Draw *text* at (x, y), truncating with '...' if it exceeds *max_w*."""
    # Use textbbox for more accurate width measurement than textlength
    bbox = draw.textbbox((0, 0), text, font=font)
    if bbox[2] - bbox[0] <= max_w:
        draw.text((x, y), text, font=font, fill=fill)
        return
    ellipsis = "..."
    ew = draw.textbbox((0, 0), ellipsis, font=font)[2]
    # Safety margin: textbbox can be slightly narrower than actual render
    safe_max = max_w - 8
    low, high = 0, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        if draw.textbbox((0, 0), text[:mid], font=font)[2] + ew <= safe_max:
            low = mid
        else:
            high = mid - 1
    draw.text((x, y), text[:low] + ellipsis, font=font, fill=fill)


def _paste_cover(card_img: Image.Image, cover_path: str | None) -> None:
    """Paste the cover image onto the top of *card_img*, or draw a placeholder."""
    card_draw = ImageDraw.Draw(card_img)
    if cover_path and os.path.isfile(cover_path):
        try:
            with Image.open(cover_path) as im:
                im = im.convert("RGB")
                im = im.resize((CARD_W, COVER_H), _RESAMPLE)
                card_img.paste(im, (0, 0))
                return
        except OSError:
            pass
    # Placeholder gradient
    for y in range(COVER_H):
        shade = int(60 + (80 - 60) * y / COVER_H)
        card_draw.line([(0, y), (CARD_W, y)], fill=(shade, shade, shade))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_png(
    rows: list[dict],
    player_name: str,
    total_vf: float,
    out_path: str,
    skill: str = "",
    font_path: str = "C:/Windows/Fonts/msyh.ttc",
) -> None:
    """Render *rows* into a card-grid PNG at *out_path*.

    Parameters
    ----------
    rows:
        List of song dicts (mid, type, title, label, level, score, volforce,
        clear_name, grade_name, cover_path).
    player_name:
        Player display name shown in the header bar.
    total_vf:
        Total VOLFORCE shown in the header bar.
    out_path:
        Destination PNG file path.
    skill:
        Optional SKILL name shown on the right side of the header bar.
    font_path:
        Path to a TrueType/OpenType font supporting CJK glyphs.
    """
    n = max(1, len(rows))
    grid_rows = math.ceil(n / COLS)
    total_h = HEADER_H + MARGIN_Y + grid_rows * (CARD_H + CARD_GAP) - CARD_GAP + MARGIN_Y

    canvas = Image.new("RGB", (CANVAS_W, total_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    header_name_font = _font(font_path, 18)
    header_meta_font = _font(font_path, 11)
    title_font = _font(font_path, 10)
    small_font = _font(font_path, 8)
    vf_font = _font(font_path, 9)
    ex_font = _font(font_path, 7)

    # ---- Header bar --------------------------------------------------------
    draw.rectangle([(0, 0), (CANVAS_W, HEADER_H)], fill=HEADER_BG)
    # Avatar placeholder
    draw.ellipse(
        [(MARGIN_X, 11), (MARGIN_X + 32, 43)],
        fill=AVATAR_BG, outline=AVATAR_BORDER, width=2,
    )
    # Player name (truncated if too long)
    _draw_text_within(
        draw, player_name, header_name_font,
        MARGIN_X + 42, 9, CANVAS_W - MARGIN_X - 42 - 130, TEXT_PRIMARY,
    )
    # VOLFORCE
    vf_text = f"VOLFORCE {total_vf}"
    draw.text((MARGIN_X + 42, 33), vf_text, font=header_meta_font, fill=VF_COLOR)

    # SKILL (right-aligned, only when non-empty)
    if skill:
        skill_text = f"SKILL {skill}"
        skill_w = int(draw.textlength(skill_text, font=header_meta_font))
        _draw_text_within(
            draw, skill_text, header_meta_font,
            CANVAS_W - MARGIN_X - skill_w, 22,
            CANVAS_W - MARGIN_X, TEXT_PRIMARY,
        )

    # ---- Card grid ---------------------------------------------------------
    for idx, r in enumerate(rows):
        col = idx % COLS
        row = idx // COLS
        cx = MARGIN_X + col * (CARD_W + CARD_GAP)
        cy = HEADER_H + MARGIN_Y + row * (CARD_H + CARD_GAP)

        # Card background with rounded corners
        draw.rounded_rectangle(
            [(cx, cy), (cx + CARD_W, cy + CARD_H)],
            radius=10, fill=CARD_BG,
        )

        # Cover area (rounded top corners via mask)
        card_img = Image.new("RGB", (CARD_W, CARD_H), CARD_BG)
        _paste_cover(card_img, r.get("cover_path"))
        mask = Image.new("L", (CARD_W, COVER_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(0, 0), (CARD_W, COVER_H + 10)], radius=10, fill=255,
        )
        canvas.paste(card_img.crop((0, 0, CARD_W, COVER_H)), (cx, cy), mask)

        # Title + GRADE (top-right of text area)
        title_y = cy + COVER_H + 6
        grade_w = int(draw.textlength(r["grade_name"], font=small_font))
        draw.text(
            (cx + CARD_W - 8 - grade_w, title_y),
            r["grade_name"], font=small_font, fill=TEXT_MUTED,
        )
        _draw_text_within(
            draw, r["title"], title_font,
            cx + 8, title_y, CARD_W - 16 - grade_w - 8, TEXT_PRIMARY,
        )

        # Difficulty tag
        tag_y = cy + COVER_H + 20
        mtype = r.get("type", 0)
        tag_color = _hex_to_rgb(_difficulty_color(mtype))
        tag_text = f"{r['label']} {r['level']}"
        tag_w = int(draw.textlength(tag_text, font=small_font)) + 10
        draw.rounded_rectangle(
            [(cx + 8, tag_y), (cx + 8 + tag_w, tag_y + 18)],
            radius=4, fill=tag_color,
        )
        tag_text_color = (0, 0, 0) if mtype in (0, 1, 4) else (255, 255, 255)
        draw.text((cx + 13, tag_y + 3), tag_text, font=small_font, fill=tag_text_color)

        # Score (full number)
        score_text = f"{r['score']}"
        score_w = int(draw.textlength(score_text, font=small_font))
        draw.text(
            (cx + CARD_W - 8 - score_w, tag_y + 3),
            score_text, font=small_font, fill=TEXT_SECONDARY,
        )

        # Bottom row: EX SCORE / VF
        bottom_y = cy + CARD_H - 18
        vf_text = f"{r['volforce']}"
        vf_w = int(draw.textlength(vf_text, font=vf_font))
        draw.text(
            (cx + CARD_W - 8 - vf_w, bottom_y + 2),
            vf_text, font=vf_font, fill=VF_COLOR,
        )
        ex_text = f"EX: {r.get('exscore', 0)}"
        _draw_text_within(
            draw, ex_text, ex_font,
            cx + 8, bottom_y + 4, CARD_W - 16 - vf_w - 8, TEXT_SECONDARY,
        )

    # ---- Save --------------------------------------------------------------
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    canvas.save(out_path, "JPEG", quality=90, optimize=True, progressive=True)

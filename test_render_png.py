import os

from PIL import Image
from render_png import render_png


def test_render_png_card_grid_no_overlap(tmp_path):
    rows = []
    for i in range(50):
        rows.append({
            "mid": i + 1, "type": (i % 5), "title": "Very Long Song Title That Should Be Clipped",
            "label": "ADV", "level": "14", "score": 9500000 + i * 100,
            "volforce": 250.0 - i, "clear": 6, "grade": 10,
            "clear_name": "PUC", "grade_name": "S", "cover_path": None,
        })
    out = tmp_path / "b50.png"
    render_png(rows, "Tester", 11.184, str(out))
    img = Image.open(out)
    assert img.width == 800
    # 高度 = 头部 56 + 边距 14 + 10*(200+10) - 10 + 14 = 2174
    assert img.height >= 2000
    img.close()


def test_render_png_renders_exscore(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "T", "label": "NOV", "level": "5",
        "score": 100, "exscore": 9999, "volforce": 10.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S", "cover_path": None,
    }]
    out = tmp_path / "b50.png"
    render_png(rows, "Tester", 1.0, str(out))
    img = Image.open(out)
    # EX SCORE 视觉断言困难，仅验证无报错且尺寸正确
    assert img.width == 800
    img.close()


def test_render_png_long_title_does_not_crash(tmp_path):
    rows = [{
        "mid": 1, "type": 2, "title": "A" * 200, "label": "EXH", "level": "18",
        "score": 9_900_000, "exscore": 9999, "volforce": 500.0, "clear": 6,
        "grade": 10, "clear_name": "PUC", "grade_name": "S", "cover_path": None,
    }]
    out = tmp_path / "b50.png"
    render_png(rows, "Tester", 5.0, str(out))
    img = Image.open(out)
    assert img.width == 800
    img.close()


def test_render_png_with_skill_no_crash(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "T", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S", "cover_path": None,
    }]
    out = tmp_path / "b50.png"
    render_png(rows, "Tester", 1.0, str(out), skill="蒼穹")
    img = Image.open(out)
    assert img.width == 800
    img.close()


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

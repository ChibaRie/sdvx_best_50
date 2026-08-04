from render_html import render_html


def test_render_html_creates_file_with_content(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "テスト曲", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S",
    }]
    out = tmp_path / "b50.html"
    render_html(rows, "Tester", 1.725, str(out))
    text = out.read_text(encoding="utf-8")
    assert "Tester" in text and "テスト曲" in text
    assert "1.725" in text
    assert "EX SCORE" in text              # EX SCORE 列已恢复
    assert "<td>90</td>" in text              # exscore 值应渲染
    # CLEAR column removed — PUC (clear_name) should not render
    assert "<td>PUC</td>" not in text


def test_render_html_missing_cover_does_not_crash(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "T", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S", "cover_path": str(tmp_path / "nope.png"),
    }]
    out = tmp_path / "b50.html"
    render_html(rows, "Tester", 1.725, str(out))
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "T" in text
    assert "EX SCORE" in text
    assert "<td>90</td>" in text


def test_render_html_with_skill_in_title(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "テスト曲", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S",
    }]
    out = tmp_path / "b50.html"
    render_html(rows, "Tester", 1.725, str(out), skill="蒼穹")
    text = out.read_text(encoding="utf-8")
    assert "[SKILL 蒼穹]" in text
    assert "<h1>" in text


def test_render_html_without_skill_omits_bracket(tmp_path):
    rows = [{
        "mid": 1, "type": 0, "title": "テスト曲", "label": "NOV", "level": "5",
        "score": 100, "exscore": 90, "volforce": 10.0, "clear": 6, "grade": 10,
        "clear_name": "PUC", "grade_name": "S",
    }]
    out = tmp_path / "b50.html"
    render_html(rows, "Tester", 1.725, str(out))
    text = out.read_text(encoding="utf-8")
    assert "[SKILL" not in text


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
    assert "100.0000%" in text

import base64
import html
import os


def render_html(rows: list[dict], player_name: str, total_vf: float, out_path: str, skill: str = "") -> None:
    thead = "<tr><th>#</th><th>封面</th><th>曲名</th><th>难度</th><th>等级</th><th>SCORE</th><th>EX SCORE</th><th>GRADE</th><th>VF</th><th>VF占比</th></tr>"
    body = []
    for i, r in enumerate(rows, 1):
        cover = '<td style="color:#999">无</td>'
        cp = r.get("cover_path")
        if cp:
            try:
                with open(cp, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                cover = f'<td><img src="data:image/png;base64,{b64}" style="width:48px;height:48px;object-fit:cover"></td>'
            except OSError:
                pass
        body.append(
            "<tr>"
            f'<td>{i}</td>{cover}'
            f'<td>{html.escape(r["title"])}</td>'
            f'<td>{r["label"]}</td><td>{r["level"]}</td>'
            f'<td>{r["score"]}</td><td>{r["exscore"]}</td>'
            f'<td>{r["grade_name"]}</td>'
            f'<td>{r["volforce"]}</td>'
            f'<td>{r.get("vf_pct", 0.0)}%</td>'
            "</tr>"
        )
    h1 = f"{html.escape(player_name)} - VOLFORCE {total_vf}"
    if skill:
        h1 += f" [SKILL {html.escape(skill)}]"
    doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>B50 - {html.escape(player_name)}</title>
<style>body{{font-family:'Yu Gothic','Meiryo','Microsoft YaHei',sans-serif;margin:2em}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:6px;text-align:center}}
th{{background:#222;color:#fff}}h1{{font-size:1.4em}}</style></head>
<body><h1>{h1}</h1>
<table><thead>{thead}</thead><tbody>{''.join(body)}</tbody></table></body></html>"""
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)

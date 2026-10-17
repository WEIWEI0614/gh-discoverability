"""Report renderers: terminal, markdown, and a standalone dark HTML page."""
from __future__ import annotations

import html
import json

BAR = "█"


def terminal(result: dict) -> str:
    out = [f"\n  {result['repo']}  ·  {result['total']}/100  [{result['grade']}]\n"]
    for d in result["dimensions"]:
        frac = d["score"] / d["weight"] if d["weight"] else 0
        filled = round(frac * 18)
        out.append(f"  {d['label']:<8} {d['score']:>5.1f}/{d['weight']:<3} "
                   f"{BAR * filled}{'·' * (18 - filled)}")
    if result["findings"]:
        out.append("\n  按可回收分数排序的修改项：")
        for i, f in enumerate(result["findings"], 1):
            out.append(f"   {i}. [{f['recoverable']:+.1f} 分] {f['dimension']}")
            for n in f["notes"]:
                out.append(f"        · {n}")
    else:
        out.append("\n  没有明显可回收项。")
    out.append("")
    return "\n".join(out)


def markdown(result: dict) -> str:
    lines = [
        f"# Discoverability audit — `{result['repo']}`",
        "",
        f"**Score {result['total']}/100 · grade {result['grade']}**",
        "",
        "| Dimension | Score | Weight |",
        "|---|---|---|",
    ]
    for d in result["dimensions"]:
        lines.append(f"| {d['label']} | {d['score']} | {d['weight']} |")
    lines += ["", "## Fixes, by recoverable points", ""]
    if not result["findings"]:
        lines.append("_Nothing worth changing._")
    for f in result["findings"]:
        lines.append(f"### {f['dimension']} (+{f['recoverable']})")
        for n in f["notes"]:
            lines.append(f"- {n}")
        lines.append("")
    return "\n".join(lines)


def html_report(result: dict, trending: dict | None = None) -> str:
    rows = []
    for d in result["dimensions"]:
        pct = round(d["score"] / d["weight"] * 100) if d["weight"] else 0
        color = "#5dcaa5" if pct >= 75 else ("#ef9f27" if pct >= 45 else "#e26d6b")
        rows.append(
            f'<div class="dim"><div class="dl"><span>{html.escape(d["label"])}</span>'
            f'<b>{d["score"]:g}<span class="w">/{d["weight"]}</span></b></div>'
            f'<div class="track"><i style="width:{pct}%;background:{color}"></i></div></div>'
        )

    fixes = []
    for i, f in enumerate(result["findings"], 1):
        items = "".join(f"<li>{html.escape(n)}</li>" for n in f["notes"])
        fixes.append(f'<div class="fix"><div class="fh"><span class="n">{i}</span>'
                     f'<span class="t">{html.escape(f["dimension"])}</span>'
                     f'<span class="p">+{f["recoverable"]:g}</span></div>'
                     f'<ul>{items}</ul></div>')

    tb = ""
    if trending:
        cells = "".join(
            f"<tr><td>{html.escape(k)}</td><td>{v.get('min')}</td>"
            f"<td>{v.get('median')}</td><td>{v.get('max')}</td></tr>"
            for k, v in trending.items()
        )
        tb = (f'<h2>Live trending floors</h2><table><thead><tr><th>bucket</th>'
              f'<th>min</th><th>median</th><th>max</th></tr></thead><tbody>{cells}</tbody></table>'
              f'<p class="note">GitHub publishes no trending formula. These numbers are measured '
              f'from the live page and drift daily — re-run <code>discover trending</code>.</p>')

    return f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Discoverability — {html.escape(result['repo'] or '')}</title>
<style>
:root{{--bg:#16171a;--panel:#1e1f24;--line:#33353c;--tx:#e8e6e2;--tx2:#a8a7a3;--amber:#ef9f27;--teal:#5dcaa5}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:40px 22px 80px}}
h1{{font-size:19px;font-weight:600;margin:0 0 4px}}
h2{{font-size:15px;font-weight:600;margin:34px 0 12px;color:var(--tx2)}}
code{{background:#25272d;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.hero{{display:flex;align-items:baseline;gap:14px;margin:18px 0 26px}}
.score{{font-size:52px;font-weight:600;line-height:1;color:var(--amber)}}
.score small{{font-size:16px;color:var(--tx2);font-weight:400}}
.grade{{font-size:13px;border:1px solid var(--line);border-radius:99px;padding:2px 11px;color:var(--tx2)}}
.dim{{margin:13px 0}}
.dl{{display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px}}
.dl b{{font-weight:500}}.w{{color:var(--tx2);font-weight:400}}
.track{{height:6px;background:#25272d;border-radius:99px;overflow:hidden}}
.track i{{display:block;height:100%;border-radius:99px}}
.fix{{background:var(--panel);border:0.5px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:9px}}
.fh{{display:flex;align-items:center;gap:9px;margin-bottom:6px}}
.n{{width:19px;height:19px;border-radius:50%;background:#25272d;color:var(--tx2);font-size:11px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}}
.t{{font-weight:500;font-size:13.5px}}
.p{{margin-left:auto;color:var(--teal);font-size:12.5px}}
.fix ul{{margin:0;padding-left:33px;color:var(--tx2);font-size:13px}}
.fix li{{margin:3px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:7px 10px;border-bottom:0.5px solid var(--line)}}
th{{color:var(--tx2);font-weight:500;font-size:12px}}
.note{{color:var(--tx2);font-size:12px;margin-top:10px}}
footer{{margin-top:46px;color:#7a7975;font-size:12px}}
</style></head><body><div class="wrap">
<h1>Discoverability audit</h1>
<p style="color:var(--tx2);margin:0"><code>{html.escape(result['repo'] or '')}</code></p>
<div class="hero"><div class="score">{result['total']:g}<small>/100</small></div>
<span class="grade">grade {result['grade']}</span></div>
<h2>Dimensions</h2>
{''.join(rows)}
<h2>What to fix, by recoverable points</h2>
{''.join(fixes) or '<p class="note">Nothing worth changing.</p>'}
{tb}
<footer>gh-discoverability · rules trace to measured behaviour, see references/</footer>
</div></body></html>"""


def to_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)

"""Report renderers: terminal, markdown, and a standalone dark HTML page.

Labels and notes are produced by rules.py in the requested language, so these renderers stay
language-agnostic — they only need the chrome strings from i18n.
"""
from __future__ import annotations

import html
import json
import unicodedata

from .i18n import t

BAR = "█"


def _pad(text: str, width: int) -> str:
    """Pad by terminal display width — CJK glyphs occupy two columns."""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)
    return text + " " * max(0, width - w)


def terminal(result: dict, lang: str = "zh") -> str:
    out = [f"\n  {result['repo']}  ·  {result['total']}/100  [{result['grade']}]\n"]
    for d in result["dimensions"]:
        frac = d["score"] / d["weight"] if d["weight"] else 0
        filled = round(frac * 18)
        out.append(f"  {_pad(d['label'], 16)}{d['score']:>5.1f}/{d['weight']:<3} "
                   f"{BAR * filled}{'·' * (18 - filled)}")
    if result["findings"]:
        out.append(f"\n  {t('r.fixes', lang)}")
        for i, f in enumerate(result["findings"], 1):
            out.append(f"   {i}. [{f['recoverable']:+.1f}] {f['dimension']}")
            for n in f["notes"]:
                out.append(f"        · {n}")
    else:
        out.append(f"\n  {t('r.none', lang)}")
    out.append("")
    return "\n".join(out)


def markdown(result: dict, lang: str = "zh") -> str:
    lines = [
        f"# {t('r.title', lang)} — `{result['repo']}`",
        "",
        f"**{t('r.score', lang)} {result['total']}/100 · {t('r.grade', lang)} {result['grade']}**",
        "",
        f"| {t('r.dims', lang)} | {t('r.score', lang)} | |",
        "|---|---|---|",
    ]
    for d in result["dimensions"]:
        lines.append(f"| {d['label']} | {d['score']} | /{d['weight']} |")
    lines += ["", f"## {t('r.fixes', lang)}", ""]
    if not result["findings"]:
        lines.append(f"_{t('r.none', lang)}_")
    for f in result["findings"]:
        lines.append(f"### {f['dimension']} (+{f['recoverable']})")
        for n in f["notes"]:
            lines.append(f"- {n}")
        lines.append("")
    return "\n".join(lines)


def _dims(result: dict) -> str:
    rows = []
    for d in result["dimensions"]:
        pct = round(d["score"] / d["weight"] * 100) if d["weight"] else 0
        color = "#5dcaa5" if pct >= 75 else ("#ef9f27" if pct >= 45 else "#e26d6b")
        rows.append(
            f'<div class="dim"><div class="dl"><span>{html.escape(d["label"])}</span>'
            f'<b>{d["score"]:g}<span class="w">/{d["weight"]}</span></b></div>'
            f'<div class="track"><i style="width:{pct}%;background:{color}"></i></div></div>'
        )
    return "".join(rows)


def _fixes(result: dict) -> str:
    if not result["findings"]:
        return ""
    out = []
    for i, f in enumerate(result["findings"], 1):
        items = "".join(f"<li>{html.escape(n)}</li>" for n in f["notes"])
        out.append(f'<div class="fix"><div class="fh"><span class="n">{i}</span>'
                   f'<span class="t">{html.escape(f["dimension"])}</span>'
                   f'<span class="p">+{f["recoverable"]:g}</span></div>'
                   f'<ul>{items}</ul></div>')
    return "".join(out)


def _ranks(result: dict, lang: str) -> str:
    queries = result.get("queries") or []
    if not queries:
        return ""
    ranks = result.get("ranks") or {}
    rows = []
    for q in queries:
        r = ranks.get(q)
        shown = str(r) if r else t("r.absent_mark", lang)
        cls = ' class="ok"' if r and r <= 10 else ""
        rows.append(f"<tr><td><code>{html.escape(q)}</code></td><td{cls}>{shown}</td></tr>")
    return (f'<h2>{t("r.queries", lang)}</h2><table><thead><tr>'
            f'<th>{t("r.query", lang)}</th><th>{t("r.rank", lang)}</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
            f'<p class="note">{t("r.two_stage", lang)}</p>')


def _floors(trending: dict, lang: str) -> str:
    cells = "".join(
        f"<tr><td>{html.escape(str(k))}</td><td>{v.get('min')}</td>"
        f"<td>{v.get('median')}</td><td>{v.get('max')}</td></tr>"
        for k, v in trending.items()
    )
    return (f'<h2>{t("r.floors", lang)}</h2><table><thead><tr><th>{t("r.bucket", lang)}</th>'
            f'<th>{t("r.min", lang)}</th><th>{t("r.median", lang)}</th>'
            f'<th>{t("r.max", lang)}</th></tr></thead><tbody>{cells}</tbody></table>'
            f'<p class="note">{t("r.floors_note", lang)}</p>')


def html_report(result: dict, trending: dict | None = None, lang: str = "zh",
                alt_href: str | None = None, alt_label: str | None = None) -> str:
    switcher = ""
    if alt_href and alt_label:
        switcher = (f'<a class="lang" href="{html.escape(alt_href)}">{html.escape(alt_label)}</a>')

    body = (
        f'<h1>{t("r.title", lang)}</h1>'
        f'<p class="repo"><code>{html.escape(result["repo"] or "")}</code></p>'
        f'<div class="hero"><div class="score">{result["total"]:g}<small>/100</small></div>'
        f'<span class="grade">{t("r.grade", lang)} {result["grade"]}</span></div>'
        f'<h2>{t("r.dims", lang)}</h2>{_dims(result)}'
        f'<h2>{t("r.fixes", lang)}</h2>{_fixes(result) or f"<p class=note>{t('r.none', lang)}</p>"}'
        f'{_ranks(result, lang)}'
        f'{_floors(trending, lang) if trending else ""}'
    )

    return f"""<!DOCTYPE html><html lang="{'zh-CN' if lang == 'zh' else 'en'}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t('r.title', lang)} — {html.escape(result['repo'] or '')}</title>
<style>
:root{{--bg:#16171a;--panel:#1e1f24;--line:#33353c;--tx:#e8e6e2;--tx2:#a8a7a3;--amber:#ef9f27;--teal:#5dcaa5}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
.wrap{{max-width:860px;margin:0 auto;padding:40px 22px 80px;position:relative}}
.lang{{position:absolute;top:42px;right:22px;font-size:12.5px;color:var(--tx2);text-decoration:none;border:0.5px solid var(--line);border-radius:99px;padding:3px 12px}}
.lang:hover{{color:var(--tx);border-color:var(--tx2)}}
h1{{font-size:19px;font-weight:600;margin:0 0 4px}}
h2{{font-size:15px;font-weight:600;margin:34px 0 12px;color:var(--tx2)}}
code{{background:#25272d;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.repo{{color:var(--tx2);margin:0}}
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
td.ok{{color:var(--teal);font-weight:500}}
.note{{color:var(--tx2);font-size:12px;margin-top:10px}}
footer{{margin-top:46px;color:#7a7975;font-size:12px}}
</style></head><body><div class="wrap">
{switcher}{body}
<footer>{t('r.footer', lang)}</footer>
</div></body></html>"""


def to_json(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)

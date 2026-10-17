"""CLI: `discover <command>`."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import api, report, rules, skillhub, trending


def _split(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.replace("\n", ";").split(";") if p.strip()]


def _pace(i: int) -> None:
    """GitHub search allows 30 req/min. Pace so a 20-topic deep scan doesn't 403."""
    if i and i % 8 == 0:
        time.sleep(4)


def cmd_audit(a) -> int:
    repo = api.repo(a.repo)
    queries = _split(a.queries) or list(repo.get("topics") or [])[:8]

    ranks: dict[str, int | None] = {}
    if queries and not a.no_queries:
        owner = a.repo.split("/")[0]
        for i, q in enumerate(queries):
            _pace(i)
            try:
                rank, _, _ = api.search_rank(q, owner)
                ranks[q] = rank
            except RuntimeError:
                ranks[q] = None

    topic_counts = None
    if a.deep:
        topic_counts = {}
        for i, t in enumerate(repo.get("topics") or []):
            _pace(i)
            try:
                topic_counts[t] = api.search_count(f"topic:{t}")
            except RuntimeError:
                pass

    readme_cjk = None if a.no_readme else api.readme_ratio(a.repo)
    has_demo = bool(a.demo or repo.get("homepage"))

    result = rules.audit(
        repo, queries=queries, ranks=ranks, topic_counts=topic_counts,
        readme_cjk=readme_cjk, has_demo=has_demo, profile_location=a.profile,
        lang=a.lang, limit=a.limit,
    )
    result["queries"] = queries
    result["ranks"] = ranks
    result["topic_counts"] = topic_counts

    if a.json:
        print(report.to_json(result))
    else:
        print(report.terminal(result, a.lang))

    if a.md:
        Path(a.md).write_text(report.markdown(result, a.lang), encoding="utf-8")
        print(f"  markdown -> {a.md}")

    tb = trending.measure(["global", "python", "zh"]) if (a.html or a.site) and a.with_trending else None

    if a.html:
        alt = "en" if a.lang == "zh" else "zh"
        Path(a.html).write_text(
            report.html_report(result, tb, lang=a.lang,
                               alt_href=a.alt_href, alt_label=a.alt_label or ("English" if alt == "en" else "中文")),
            encoding="utf-8")
        print(f"  html     -> {a.html}")

    if a.site:
        d = Path(a.site)
        d.mkdir(parents=True, exist_ok=True)
        other = dict(result)
        other.update(rules.audit(
            repo, queries=queries, ranks=ranks, topic_counts=topic_counts,
            readme_cjk=readme_cjk, has_demo=has_demo, profile_location=a.profile,
            lang="en" if a.lang == "zh" else "zh", limit=a.limit))
        other["queries"], other["ranks"] = queries, ranks
        zh, en = (result, other) if a.lang == "zh" else (other, result)
        (d / "index.html").write_text(
            report.html_report(zh, tb, lang="zh", alt_href="en.html", alt_label="English"),
            encoding="utf-8")
        (d / "en.html").write_text(
            report.html_report(en, tb, lang="en", alt_href="index.html", alt_label="中文"),
            encoding="utf-8")
        print(f"  site     -> {d}/index.html (zh) + {d}/en.html (en)")
    return 0


def cmd_trending(a) -> int:
    buckets = [b.strip() for b in (a.buckets or "global,python,zh").split(",") if b.strip()]
    data = trending.measure(buckets, a.since)
    if a.json:
        print(report.to_json(data))
        return 0
    print(f"\n  GitHub Trending · since={a.since}  ({time.strftime('%Y-%m-%d %H:%M')})\n")
    print(f"  {'bucket':<12}{'n':>4}{'min':>8}{'median':>9}{'max':>8}")
    for b, s in data.items():
        print(f"  {b:<12}{s['count']:>4}{str(s['min']):>8}{str(s['median']):>9}{str(s['max']):>8}")
    print("\n  GitHub publishes no formula. These are measured from the live page and drift daily.\n")
    return 0


def cmd_topics(a) -> int:
    print(f"\n  {'topic':<30}{'repos':>8}")
    for i, t in enumerate(a.topics):
        _pace(i)
        try:
            n = api.search_count(f"topic:{t}")
        except RuntimeError as e:
            print(f"  {t:<30}{'ERR':>8}  {e}")
            continue
        flag = "  <- narrow" if n <= 50 else ("" if n <= 500 else "  <- crowded")
        print(f"  {t:<30}{n:>8}{flag}")
    print("\n  Topic pages list repositories by stars. Narrow topics put a 0-star repo on page 1.\n")
    return 0


def cmd_queries(a) -> int:
    repo = api.repo(a.repo)
    owner = a.repo.split("/")[0]
    queries = _split(a.queries) or list(repo.get("topics") or [])[:8]
    print(f"\n  {a.repo}  ·  search rank check\n")
    print(f"  {'query':<42}{'total':>8}{'rank':>7}")
    for i, q in enumerate(queries):
        _pace(i)
        try:
            rank, total, _ = api.search_rank(q, owner, limit=a.limit)
        except RuntimeError as e:
            print(f"  {q:<42}{'ERR':>8}  {e}")
            continue
        print(f"  {q:<42}{total:>8}{(rank if rank else '—'):>7}")
    print("\n  Words decide whether you enter the candidate set; stars decide where you land in it.\n")
    return 0


def cmd_skill(a) -> int:
    queries = _split(a.queries)
    if not queries:
        print("  --queries is required, e.g. --queries 'job radar;resume gap'")
        return 2
    res = skillhub.audit_skill(a.slug, queries)
    print(f"\n  skillhub: {a.slug}  ·  hit rate {res['hit_rate']:.0%}\n")
    print(f"  {'query':<34}{'rank':>6}{'top score':>11}")
    for r in res["queries"]:
        print(f"  {r['query']:<34}{(r['rank'] or '—'):>6}{r['top_score'] if r['top_score'] is not None else '—':>11}")
    print("\n  score >= 0.055 means it matched you; below that you are popularity filler.\n")
    return 0


def cmd_skill_probe(a) -> int:
    for q in _split(a.queries):
        d = skillhub.diagnose(skillhub.search(q, 10))
        print(f"\n  q={q!r}")
        if d.get("empty"):
            print("    (no results)")
            continue
        print(f"    top score {d['top_score']}  ·  genuine hits {len(d['hits'])}  ·  filler {d['filler_count']}")
        for h in d["hits"][:5]:
            print(f"      {h['score']:.4f}  {h['slug']:<30} dl={h['downloads']}")
        if d["floor_prone"]:
            print("    ⚠ no semantic hit — list degraded to the global download ranking")
    print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="discover", description="Why nobody finds your repo.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("audit", help="score a repository and list fixes by recoverable points")
    a.add_argument("repo", help="owner/name")
    a.add_argument("--queries", help="target search phrases, separated by ;")
    a.add_argument("--deep", action="store_true", help="also count repositories per topic (slower)")
    a.add_argument("--demo", help="live demo URL, if the homepage field is empty")
    a.add_argument("--profile", help="your GitHub profile location, if set")
    a.add_argument("--no-queries", action="store_true", help="skip the search-rank probes")
    a.add_argument("--no-readme", action="store_true", help="skip the README language probe")
    a.add_argument("--with-trending", action="store_true", help="embed live trending floors in the HTML")
    a.add_argument("--lang", default="zh", choices=["zh", "en"], help="report language (default: zh)")
    a.add_argument("--limit", type=int, default=60, help="how many search results to scan per phrase")
    a.add_argument("--json", action="store_true")
    a.add_argument("--md", help="write a markdown report here")
    a.add_argument("--html", help="write a standalone dark HTML report here (in --lang)")
    a.add_argument("--alt-href", help="with --html: link to the other-language report")
    a.add_argument("--alt-label", help="with --html: label for that link")
    a.add_argument("--site", help="write both languages (index.html + en.html) into this directory")
    a.set_defaults(func=cmd_audit)

    t = sub.add_parser("trending", help="measure live star thresholds per bucket")
    t.add_argument("--buckets", help="global,zh,en,python,typescript")
    t.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    t.add_argument("--json", action="store_true")
    t.set_defaults(func=cmd_trending)

    tp = sub.add_parser("topics", help="competition count for candidate topics")
    tp.add_argument("topics", nargs="+")
    tp.set_defaults(func=cmd_topics)

    q = sub.add_parser("queries", help="where do you rank for these phrases, right now")
    q.add_argument("repo")
    q.add_argument("--queries")
    q.add_argument("--limit", type=int, default=60)
    q.set_defaults(func=cmd_queries)

    s = sub.add_parser("skill", help="SkillHub rank check for a skill slug")
    s.add_argument("slug")
    s.add_argument("--queries", required=True)
    s.set_defaults(func=cmd_skill)

    sp = sub.add_parser("skill-probe", help="show whether a SkillHub query even matched anything")
    sp.add_argument("--queries", required=True)
    sp.set_defaults(func=cmd_skill_probe)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RuntimeError as e:
        print(f"  error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

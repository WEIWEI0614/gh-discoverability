"""Scoring and fix rules.

Every weight here traces back to a measured fact, not to folklore. The evidence lives in
references/ — if you change a number, change the reference too.

The model is deliberately split into "what you control" (fields you can edit in 5 minutes)
and "what compounds" (stars, community), because telling someone to get 900 stars is not
advice, it is a shrug.
"""
from __future__ import annotations

from .i18n import t

CJK = lambda s: any("\u4e00" <= ch <= "\u9fff" for ch in (s or ""))

# GitHub's documented limits.
DESC_MAX = 350
TOPICS_MAX = 20
TOPIC_MAXLEN = 50

CJK_STARTS = ("中", "技", "求")


def _pct(part: float, whole: float) -> float:
    return 0.0 if whole <= 0 else max(0.0, min(1.0, part / whole))


def score_search_surface(repo: dict, queries: list[str], ranks: dict[str, int | None],
                         lang: str = "zh") -> tuple[float, list[str]]:
    """30 pts — can the repo even enter a candidate set?

    GitHub repository search matches name + description + topics ONLY (README needs an
    explicit `in:readme`). So the whole game is: do your target phrases literally appear?
    """
    notes: list[str] = []
    desc = (repo.get("description") or "").lower()
    topics = [x.lower() for x in repo.get("topics") or []]
    name = (repo.get("name") or "").lower().replace("-", " ").replace("_", " ")

    queries = queries or list(topics)
    if not queries:
        return 0.0, [t("ss.no_queries", lang)]

    hits = 0
    for q in queries:
        terms = [x for x in q.lower().replace("-", " ").split() if x]
        if all(x in desc for x in terms) or q.lower() in topics or all(x in name for x in terms):
            hits += 1
    surface = _pct(hits, len(queries))

    used = len(repo.get("description") or "")
    length_pen = 0.0 if used >= 300 else (0.15 if used >= 200 else 0.4)

    score = 30 * surface * (1 - length_pen)
    if hits < len(queries):
        notes.append(t("ss.missing", lang, n=len(queries) - hits, m=len(queries)))
    if used < 300:
        notes.append(t("ss.short_desc", lang, used=used, max=DESC_MAX, rest=DESC_MAX - used))
    return round(score, 1), notes


def score_topic_layout(repo: dict, topic_counts: dict[str, int] | None,
                       lang: str = "zh") -> tuple[float, list[str]]:
    """20 pts — 20 slots are free real estate; most repos use 12 and waste the rest."""
    notes: list[str] = []
    topics = repo.get("topics") or []
    n = len(topics)
    slot = _pct(n, TOPICS_MAX) * 12

    niche = 6.0
    if topic_counts:
        counts = [c for k, c in topic_counts.items() if k in topics]
        if counts:
            narrow = sum(1 for c in counts if c <= 200)
            niche = 6 * _pct(narrow, len(counts))
            if narrow == 0:
                notes.append(t("tl.crowded", lang))
        else:
            niche = 0.0
    elif n:
        niche = 3.0

    if n < TOPICS_MAX:
        notes.append(t("tl.unused", lang, n=n, max=TOPICS_MAX, rest=TOPICS_MAX - n))
    long_topics = [x for x in topics if len(x) > TOPIC_MAXLEN]
    if long_topics:
        notes.append(t("tl.too_long", lang, max=TOPIC_MAXLEN, list=long_topics))
    return round(min(20.0, slot + niche), 1), notes


def score_bucket_signal(repo: dict, readme_cjk: float | None, has_demo: bool,
                        profile_location: str | None, lang: str = "zh") -> tuple[float, list[str]]:
    """20 pts — odds of being classified into the low-competition Chinese trending bucket.

    Honest caveat: classification is not fully controllable. Of 21 repos in the zh bucket on
    2026-10-17, 14 had CJK descriptions and 7 had pure-English descriptions AND English
    READMEs — so the classifier uses more than the two fields we can see. We stack what we can.
    """
    notes: list[str] = []
    score = 0.0
    desc = repo.get("description") or ""

    if CJK(desc):
        score += 9
        if not desc.lstrip().startswith(CJK_STARTS):
            notes.append(t("bs.cjk_not_first", lang))
    else:
        notes.append(t("bs.no_cjk", lang))

    if readme_cjk is not None:
        if readme_cjk > 0.05:
            score += 5
        else:
            notes.append(t("bs.readme_en", lang, pct=round(readme_cjk * 100, 1)))

    if has_demo:
        score += 4
    else:
        notes.append(t("bs.no_demo", lang))

    if profile_location:
        score += 2
    else:
        notes.append(t("bs.no_location", lang))
    return round(min(20.0, score), 1), notes


def score_conversion(repo: dict, has_demo: bool, lang: str = "zh") -> tuple[float, list[str]]:
    """15 pts — after they click, do they star?"""
    notes: list[str] = []
    score = 0.0
    if repo.get("license"):
        score += 4
    else:
        notes.append(t("cv.no_license", lang))
    if has_demo:
        score += 5
    if repo.get("topics") or []:
        score += 3
    if repo.get("has_issues", True):
        score += 3
    return round(score, 1), notes


def score_query_reach(queries: list[str], ranks: dict[str, int | None],
                      lang: str = "zh", limit: int = 60) -> tuple[float, list[str]]:
    """15 pts — do you actually rank, right now, for the phrases you claim to own?"""
    if not queries:
        return 0.0, []
    notes: list[str] = []
    wins = sum(1 for r in ranks.values() if r is not None and r <= 10)
    shown = sum(1 for r in ranks.values() if r is not None)
    score = 15 * (0.7 * _pct(wins, len(queries)) + 0.3 * _pct(shown, len(queries)))
    if wins == 0:
        notes.append(t("qr.no_top10", lang))
    for q, r in ranks.items():
        if r is None:
            notes.append(t("qr.absent", lang, q=q, limit=limit))
    return round(score, 1), notes


def audit(repo: dict, *, queries: list[str] | None = None, ranks: dict[str, int | None] | None = None,
          topic_counts: dict[str, int] | None = None, readme_cjk: float | None = None,
          has_demo: bool = False, profile_location: str | None = None,
          lang: str = "zh", limit: int = 60) -> dict:
    queries = queries or []
    ranks = ranks or {}

    checks = [
        ("search_surface", 30, *score_search_surface(repo, queries, ranks, lang)),
        ("topic_layout", 20, *score_topic_layout(repo, topic_counts, lang)),
        ("bucket_signal", 20, *score_bucket_signal(repo, readme_cjk, has_demo, profile_location, lang)),
        ("conversion", 15, *score_conversion(repo, has_demo, lang)),
        ("query_reach", 15, *score_query_reach(queries, ranks, lang, limit)),
    ]
    total = sum(c[2] for c in checks)
    return {
        "repo": repo.get("full_name"),
        "lang": lang,
        "total": round(total, 1),
        "grade": _grade(total),
        "dimensions": [
            {"key": k, "label": t(f"dim.{k}", lang), "weight": w, "score": s, "notes": notes}
            for k, w, s, notes in checks
        ],
        "findings": _prioritize(checks, lang),
    }


def _grade(total: float) -> str:
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 55:
        return "C"
    if total >= 40:
        return "D"
    return "F"


def _prioritize(checks, lang: str) -> list[dict]:
    """Order fixes by recoverable points, so the 5-minute wins come first."""
    out: list[dict] = []
    for key, weight, score, notes in checks:
        lost = weight - score
        if lost <= 0.5 or not notes:
            continue
        out.append({"dimension": t(f"dim.{key}", lang), "recoverable": round(lost, 1), "notes": notes})
    return sorted(out, key=lambda d: -d["recoverable"])

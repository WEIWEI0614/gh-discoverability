"""Scoring and fix rules.

Every weight here traces back to a measured fact, not to folklore. The evidence lives in
references/ — if you change a number, change the reference too.

The model is deliberately split into "what you control" (fields you can edit in 5 minutes)
and "what compounds" (stars, community), because telling someone to get 900 stars is not
advice, it is a shrug.
"""
from __future__ import annotations

CJK = lambda s: any("\u4e00" <= ch <= "\u9fff" for ch in (s or ""))

# GitHub's documented limits.
DESC_MAX = 350
TOPICS_MAX = 20
TOPIC_MAXLEN = 50

# Trending floors measured 2026-10-17 (see references/github-trending.md). They drift; the
# `trending` command re-measures them, these are only the fallback wording.
BUCKET_FLOORS = {"global": "36–2300 stars/day", "python": "32+ stars/day", "zh": "2–75 stars/day"}


def _pct(part: float, whole: float) -> float:
    return 0.0 if whole <= 0 else max(0.0, min(1.0, part / whole))


def score_search_surface(repo: dict, queries: list[str], ranks: dict[str, int | None]) -> tuple[float, list[str]]:
    """30 pts — can the repo even enter a candidate set?

    GitHub repository search matches name + description + topics ONLY (README needs an
    explicit `in:readme`). So the whole game is: do your target phrases literally appear?
    """
    notes: list[str] = []
    desc = (repo.get("description") or "").lower()
    topics = [t.lower() for t in repo.get("topics") or []]
    name = (repo.get("name") or "").lower().replace("-", " ").replace("_", " ")

    if not queries:
        # Fall back to topic-as-query coverage.
        queries = list(topics)
    if not queries:
        return 0.0, ["没有可用的目标查询词 —— 先确定用户会搜什么"]

    hits = 0
    for q in queries:
        terms = [t for t in q.lower().replace("-", " ").split() if t]
        in_desc = all(t in desc for t in terms)
        in_topic = q.lower() in topics
        in_name = all(t in name for t in terms)
        if in_desc or in_topic or in_name:
            hits += 1
    surface = _pct(hits, len(queries))

    # A description that stops well short of 350 chars leaves free exact-match room.
    used = len(repo.get("description") or "")
    length_pen = 0.0 if used >= 300 else (0.15 if used >= 200 else 0.4)

    score = 30 * surface * (1 - length_pen)
    if surface < 1.0:
        notes.append(f"{len(queries) - hits}/{len(queries)} 个目标查询词在 name/description/topics 里完全不出现")
    if used < 300:
        notes.append(f"description 只用了 {used}/{DESC_MAX} 字符，还空着 {DESC_MAX - used} 个字符的精确匹配位")
    return round(score, 1), notes


def score_topic_layout(repo: dict, topic_counts: dict[str, int] | None) -> tuple[float, list[str]]:
    """20 pts — 20 slots are free real estate; most repos use 12 and waste the rest."""
    notes: list[str] = []
    topics = repo.get("topics") or []
    n = len(topics)
    slot = _pct(n, TOPICS_MAX) * 12  # 12 pts for filling the slots

    niche = 6.0
    if topic_counts:
        counts = [c for t, c in topic_counts.items() if t in topics]
        if counts:
            # A topic page lists repos by stars. Crowded topics bury a new repo; narrow ones
            # put it on page 1 immediately.
            narrow = sum(1 for c in counts if c <= 200)
            niche = 6 * _pct(narrow, len(counts))
            if narrow == 0:
                notes.append("所有 topic 都是千级以上的红海话题，新仓库在话题页会被 star 排序压到底")
        else:
            niche = 0.0
    elif n:
        niche = 3.0  # unknown, half credit

    if n < TOPICS_MAX:
        notes.append(f"topics 只用了 {n}/{TOPICS_MAX} 个，白扔 {TOPICS_MAX - n} 个精确匹配面")
    long_topics = [t for t in topics if len(t) > TOPIC_MAXLEN]
    if long_topics:
        notes.append(f"有 topic 超过 {TOPIC_MAXLEN} 字符上限：{long_topics}")
    return round(min(20.0, slot + niche), 1), notes


def score_bucket_signal(repo: dict, readme_cjk: float | None, has_demo: bool,
                        profile_location: str | None) -> tuple[float, list[str]]:
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
    else:
        notes.append("description 无中文 —— 中文桶 21 个仓库里 14 个有中文描述，这是你能控制的最强信号")

    if CJK(desc) and not desc.lstrip().startswith(("中", "技", "求")):
        notes.append("中文不在 description 开头，判定时可能被前面的英文带偏")

    if readme_cjk is not None:
        if readme_cjk > 0.05:
            score += 5
        else:
            notes.append("默认 README 是纯英文（中文占比 %.1f%%）—— 只作弱信号，但补上零成本" % (readme_cjk * 100))

    if has_demo:
        score += 4
    else:
        notes.append("没有在线 demo —— 访客无法在 10 秒内判断它值不值得 star")

    if profile_location:
        score += 2
    else:
        notes.append("GitHub 主页 location 为空 —— 中文桶 21 个仓库里 9 个明写中国地址")
    return round(min(20.0, score), 1), notes


def score_conversion(repo: dict, has_demo: bool) -> tuple[float, list[str]]:
    """15 pts — after they click, do they star?"""
    notes: list[str] = []
    score = 0.0
    if repo.get("license"):
        score += 4
    else:
        notes.append("没有 LICENSE —— 企业用户和部分开发者会直接跳过")
    if has_demo:
        score += 5
    if (repo.get("topics") or []):
        score += 3
    if repo.get("open_issues_count") is not None and repo.get("has_issues", True):
        score += 3
    return round(score, 1), notes


def score_query_reach(queries: list[str], ranks: dict[str, int | None]) -> tuple[float, list[str]]:
    """15 pts — do you actually rank, right now, for the phrases you claim to own?"""
    if not queries:
        return 0.0, []
    notes: list[str] = []
    wins = sum(1 for r in ranks.values() if r is not None and r <= 10)
    shown = sum(1 for r in ranks.values() if r is not None)
    score = 15 * (0.7 * _pct(wins, len(queries)) + 0.3 * _pct(shown, len(queries)))
    if wins == 0:
        notes.append("没有任何目标查询词进前 10 —— 先打长尾词，短词要等 star 攒起来")
    for q, r in ranks.items():
        if r is None:
            notes.append(f"`{q}` 前 60 名之外（候选集可能上千，0 star 进不去）")
    return round(score, 1), notes


def audit(repo: dict, *, queries: list[str] | None = None, ranks: dict[str, int | None] | None = None,
          topic_counts: dict[str, int] | None = None, readme_cjk: float | None = None,
          has_demo: bool = False, profile_location: str | None = None) -> dict:
    queries = queries or []
    ranks = ranks or {}

    checks = [
        ("search_surface", "可搜索面", 30, *score_search_surface(repo, queries, ranks)),
        ("topic_layout", "话题布局", 20, *score_topic_layout(repo, topic_counts)),
        ("bucket_signal", "入桶信号", 20, *score_bucket_signal(repo, readme_cjk, has_demo, profile_location)),
        ("conversion", "转化面", 15, *score_conversion(repo, has_demo)),
        ("query_reach", "查询命中", 15, *score_query_reach(queries, ranks)),
    ]
    total = sum(c[3] for c in checks)
    return {
        "repo": repo.get("full_name"),
        "total": round(total, 1),
        "grade": _grade(total),
        "dimensions": [
            {"key": k, "label": lab, "weight": w, "score": s, "notes": notes}
            for k, lab, w, s, notes in checks
        ],
        "findings": _prioritize(checks),
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


def _prioritize(checks) -> list[dict]:
    """Order fixes by recoverable points, so the 5-minute wins come first."""
    out: list[dict] = []
    for key, label, weight, score, notes in checks:
        lost = weight - score
        if lost <= 0.5 or not notes:
            continue
        out.append({"dimension": label, "recoverable": round(lost, 1), "notes": notes})
    return sorted(out, key=lambda d: -d["recoverable"])

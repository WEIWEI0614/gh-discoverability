"""SkillHub search check — the registry that `find-skills` actually queries.

Measured behaviour (2026-10-17, 8 query pairs):
  * a real semantic hit  -> score roughly 0.060–0.110
  * no semantic hit      -> the list degrades to a global download ranking, scoring ~0.0500,
                            0.0492, 0.0488 … (identical ordering for two unrelated queries)

So `score >= 0.055` is the practical line between "matched you" and "you are filler".
Downloads only decide the order *inside* that filler band — an 11-download skill outranked a
1.77M-download one when the query genuinely matched it.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

ENDPOINT = "https://lightmake.site/api/v1/search"
TOP = "https://lightmake.site/api/skills/top"
UA = "gh-discoverability (+https://github.com/WEIWEI0614/gh-discoverability)"

FLOOR = 0.055
HIT_BAND = (0.060, 0.120)


def _get(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def search(query: str, limit: int = 10) -> list[dict]:
    """Ranked skill results for a query. Never raises on an empty query — returns []."""
    if not (query or "").strip():
        return []
    url = f"{ENDPOINT}?q={urllib.parse.quote(query)}&limit={limit}"
    try:
        return (_get(url).get("results") or [])[:limit]
    except (OSError, ValueError):
        return []


def diagnose(results: list[dict]) -> dict:
    """Split a result page into 'genuine hits' and 'popularity filler'."""
    if not results:
        return {"empty": True}
    hits = [r for r in results if (r.get("score") or 0) >= FLOOR]
    filler = [r for r in results if (r.get("score") or 0) < FLOOR]
    return {
        "empty": False,
        "total": len(results),
        "hits": [{"slug": r.get("slug"), "name": r.get("name"),
                  "score": round(r.get("score") or 0, 4),
                  "downloads": r.get("downloads")} for r in hits],
        "filler_count": len(filler),
        "top_score": round(results[0].get("score") or 0, 4),
        "floor_prone": len(hits) == 0,
    }


def rank_of(slug: str, query: str, limit: int = 25) -> int | None:
    for i, r in enumerate(search(query, limit)):
        if r.get("slug") == slug:
            return i + 1
    return None


def audit_skill(slug: str, queries: list[str]) -> dict:
    rows = []
    for q in queries:
        res = search(q, 12)
        rank = next((i + 1 for i, r in enumerate(res) if r.get("slug") == slug), None)
        rows.append({
            "query": q,
            "rank": rank,
            "top_score": round(res[0].get("score") or 0, 4) if res else None,
            "matched": bool(rank),
        })
    return {
        "slug": slug,
        "queries": rows,
        "hit_rate": round(sum(1 for r in rows if r["matched"]) / len(rows), 3) if rows else 0.0,
    }

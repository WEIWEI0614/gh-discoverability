"""GitHub Trending has no public API — this scrapes the HTML page and parses it.

Two brittle spots, both handled here so the rest of the codebase never touches HTML:
  1. the row container  -> <article class="Box-row">
  2. the repo link      -> the star button's ?return_to=%2Fowner%2Frepo (URL-encoded)
"""
from __future__ import annotations

import re
import statistics
import urllib.parse

from .api import get_text

BASE = "https://github.com/trending"

_ROW = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
_REPO = re.compile(r"return_to=%2F([A-Za-z0-9_.-]+)%2F([A-Za-z0-9_.-]+)")
_STARS = re.compile(r"([\d,]+)\s*stars (?:today|this week|this month)")
_DESC = re.compile(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', re.S)

BUCKETS = {
    "global": "no language filter",
    "zh": "spoken_language_code=zh",
    "en": "spoken_language_code=en",
    "python": "language=python",
    "typescript": "language=typescript",
}


def url(bucket: str = "global", since: str = "daily") -> str:
    if bucket == "global":
        return f"{BASE}?since={since}"
    if bucket in ("zh", "en"):
        return f"{BASE}?since={since}&spoken_language_code={bucket}"
    return f"{BASE}?since={since}&language={bucket}"


def fetch(bucket: str = "global", since: str = "daily") -> list[dict]:
    html = get_text(url(bucket, since))
    out: list[dict] = []
    seen: set[str] = set()
    for row in _ROW.findall(html):
        m = _REPO.search(row)
        if not m:
            continue
        name = f"{m.group(1)}/{m.group(2)}"
        if name in seen:
            continue
        seen.add(name)
        stars = _STARS.search(row)
        desc = _DESC.search(row)
        out.append({
            "repo": name,
            "stars": int(stars.group(1).replace(",", "")) if stars else None,
            "desc": re.sub(r"<[^>]+>", "", desc.group(1)).strip() if desc else "",
        })
    return out


def stats(entries: list[dict]) -> dict:
    vals = sorted((e["stars"] for e in entries if e["stars"] is not None), reverse=True)
    if not vals:
        return {"count": len(entries), "min": None, "median": None, "max": None}
    return {
        "count": len(entries),
        "min": vals[-1],
        "median": int(statistics.median(vals)),
        "max": vals[0],
    }


def measure(buckets: list[str] | None = None, since: str = "daily") -> dict:
    """Live thresholds for each bucket. These drift daily — never hardcode them."""
    buckets = buckets or ["global", "python", "zh"]
    return {b: stats(fetch(b, since)) for b in buckets}


def is_chinese_bucket_candidate(desc: str) -> bool:
    """14/21 of today's zh-bucket repos carry CJK in the description. Not sufficient, but the
    strongest single signal you control. See references/github-trending.md."""
    if not desc:
        return False
    return any("\u4e00" <= ch <= "\u9fff" for ch in desc)


def quote_path(owner_repo: str) -> str:
    return urllib.parse.quote(owner_repo, safe="/")

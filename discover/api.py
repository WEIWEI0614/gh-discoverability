"""Tiny HTTP layer: uses `gh auth token` when available, else GITHUB_TOKEN, else anonymous."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request

UA = "gh-discoverability (+https://github.com/WEIWEI0614/gh-discoverability)"
_token: str | None = None
_resolved = False


def token() -> str | None:
    """Prefer GITHUB_TOKEN; fall back to whatever `gh` already has stored."""
    global _token, _resolved
    if _resolved:
        return _token
    _resolved = True
    _token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if _token:
        return _token
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            _token = out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return _token


def _request(url: str, accept: str = "application/vnd.github+json", timeout: int = 25) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    t = token()
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b""


def get_json(url: str) -> dict:
    code, body = _request(url)
    if code != 200:
        raise RuntimeError(f"HTTP {code} for {url}: {body[:160].decode('utf-8', 'replace')}")
    return json.loads(body)


def get_text(url: str) -> str:
    code, body = _request(url, accept="text/html")
    return body.decode("utf-8", "replace") if code == 200 else ""


def repo(owner_repo: str) -> dict:
    return get_json(f"https://api.github.com/repos/{owner_repo}")


def search_count(query: str) -> int:
    """Total repositories matching a search query."""
    q = urllib.parse.quote(query)
    data = get_json(f"https://api.github.com/search/repositories?q={q}&per_page=1")
    return int(data.get("total_count") or 0)


def search_rank(query: str, owner: str, limit: int = 60) -> tuple[int | None, int, int]:
    """(1-based rank of `owner` in the first `limit` results, total_count, scanned)."""
    q = urllib.parse.quote(query)
    data = get_json(f"https://api.github.com/search/repositories?q={q}&per_page={limit}")
    items = [i.get("full_name", "") for i in data.get("items") or []]
    for i, name in enumerate(items):
        if name.split("/")[0].lower() == owner.lower():
            return i + 1, int(data.get("total_count") or 0), len(items)
    return None, int(data.get("total_count") or 0), len(items)


def readme_ratio(owner_repo: str) -> float | None:
    """Fraction of CJK characters in the default README (None if unreadable)."""
    code, body = _request(f"https://api.github.com/repos/{owner_repo}/readme",
                          accept="application/vnd.github.raw")
    if code != 200 or not body:
        return None
    text = body.decode("utf-8", "replace")
    if not text:
        return None
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk / len(text)

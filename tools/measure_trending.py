"""Standalone trending measurement — for people who want the numbers without the CLI.

    python tools/measure_trending.py --buckets global,python,zh --since weekly
    python tools/measure_trending.py --json > floors.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from discover import trending  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--buckets", default="global,python,zh")
    p.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    buckets = [b.strip() for b in a.buckets.split(",") if b.strip()]
    data = trending.measure(buckets, a.since)

    if a.json:
        print(json.dumps(data, indent=2))
        return 0

    print(f"\n  since={a.since}")
    print(f"  {'bucket':<14}{'n':>4}{'min':>8}{'median':>9}{'max':>8}")
    for b, s in data.items():
        print(f"  {b:<14}{s['count']:>4}{s['min']!s:>8}{s['median']!s:>9}{s['max']!s:>8}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

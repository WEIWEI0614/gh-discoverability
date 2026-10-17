<div align="center">

# 🔭 gh-discoverability

**Why nobody finds your repo — measured, not guessed.**
Scores your search surface, your trending-bucket odds, and your skill-registry ranking. Then
returns fixes sorted by how many points you can actually recover.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![No LLM](https://img.shields.io/badge/LLM-not%20required-success)]()
[![Deps](https://img.shields.io/badge/runtime%20deps-0-brightgreen)](pyproject.toml)

</div>

---

## The claim this tool is built to kill

There are two kinds of open-source discoverability advice: measurable, and made up.

The second kind circulates as exact formulas — `score = new_stars × 100 × 1/(1+log₂(total/1000))`,
"new stars only account for 35% of the weight", "R² = 0.92". None of it cites GitHub, and the
posts contradict each other. This tool encodes only what can be reproduced:

| Fact | Evidence |
|---|---|
| GitHub repo search indexes **`name` + `description` + `topics` only** | GitHub Docs, *Searching for repositories* |
| **Popularity affects search ordering** | GitHub Engineering, *A brief history of code search at GitHub* (2021) |
| Trending has **no API** and no published formula | there is no endpoint; the page is HTML |
| Trending floors differ **~50× between buckets** | measured: global median 898, Chinese-bucket median 16 |

## The three surfaces are not the same game

```
                       ┌─────────────────────┐
   query ─────────────►│  name / description │──► candidate set ──► popularity ──► order
                       │  / topics           │        │                              │
                       └─────────────────────┘        └── 1 repo  → rank 1
                                                        └── 11,457 → invisible at 0 stars
```

Advice that conflates these is wrong in three different directions:

- **"Add keywords to your README"** — does nothing for GitHub search. The searcher would have
  to type `in:readme`, and almost nobody does.
- **"Get more stars"** — true, useless, and downstream of everything else.
- **"Target the Chinese trending bucket"** — right instinct, but the bucket is assigned by a
  classifier you cannot fully control (7 of 21 repos in it had pure-English descriptions).

## Quick start

```bash
pip install gh-discoverability     # or: pip install -e .
```

```bash
discover trending --buckets global,python,zh      # live floors, before you plan anything
discover audit owner/repo --queries "phrase a;phrase b" --deep --html report.html
discover queries owner/repo --queries "phrase a"  # where you actually rank, right now
discover topics job-scraper skill-map beisen      # which topics are red oceans
discover skill my-skill --queries "job radar"     # skill-registry rank check
```

Sample output:

```
  WEIWEI0614/cn-job-radar  ·  76.8/100  [B]

  可搜索面      30.0/30  ██████████████████
  话题布局      15.0/20  ██████████████····
  入桶信号      15.0/20  ██████████████····
  转化面       15.0/15  ██████████████████
  查询命中       1.8/15  ██················

  按可回收分数排序的修改项：
   1. [+13.2 分] 查询命中
        · `job scraper` 前 60 名之外（候选集可能上千，0 star 进不去）
   2. [+5.0 分] 入桶信号
        · 默认 README 是纯英文 —— 只作弱信号，但补上零成本
```

## The finding that changes the plan

A zero-star repo ranks **#1** for a query with **1** candidate and is **invisible** for a query
with **11,457** — with an identical, perfectly relevant description. Measured on the same repo
on the same day:

| Query | Candidate set | Rank |
|---|---|---|
| `chinese job portal scraper` | 1 | **1** |
| `feishu hire scraper` | 1 | **1** |
| `skill gap analyzer for job descriptions` | 105 | not in top 50 |
| `skill gap in:description` | 11,457 | not in top 50 |

**Words decide whether you enter the candidate set. Stars decide where you land in it.**
So the useful question is never "what's my rank" but "what's my rank *among how many*".

## What it will not do

- **Promise you a trending spot.** The list is an outcome, not an action.
- **Tell you the trending formula.** It doesn't exist publicly. This tool measures floors and
  tells you which bucket is winnable this week.
- **Claim bucket classification is controllable.** It is probability stacking, and the docs
  say so.
- **Touch your README for search ranking.** It won't help. It matters for Google and for
  humans — a different job.

## Use it as an agent skill

`SKILL.md` is a drop-in skill for WorkBuddy / CodeBuddy / Claude-style agents:

```bash
cp -r . ~/.workbuddy/skills/gh-discoverability
```

Then ask your agent *"why does nobody find my repo"* and it will run the audit instead of
reciting folklore.

## License

MIT. The measurements are the contribution — re-measure them rather than trusting this file.

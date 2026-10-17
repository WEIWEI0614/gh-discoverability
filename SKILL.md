---
name: gh-discoverability
description: Diagnose and fix why a GitHub repository (or an agent skill published to a registry) gets no discovery — covering GitHub repository search, GitHub Trending bucketing, and skill-registry ranking. Use when the user asks "why does nobody find my repo", "how do I rank on GitHub trending", "how do I get more GitHub stars", "why is my skill not recommended", or wants a discoverability/SEO audit of an open-source project. Produces a scored audit with fixes ordered by recoverable points.
description_zh: "诊断开源项目为什么没人发现：GitHub 搜索、Trending 分桶、技能注册表排名的可复现审计"
description_en: "Diagnose why an open-source repo or agent skill gets no discovery"
---

# GitHub discoverability

Most "GitHub SEO" advice is folklore. This skill replaces it with measured behaviour, and is
explicit about the parts that are **not** controllable.

## When to use this

- "Why does nobody find my repo / my skill?"
- "How do I get on GitHub Trending?"
- "How do I rank higher in GitHub search?"
- "Why doesn't `find-skills` recommend mine?"
- Any request to audit an open-source project's discoverability.

## The three surfaces are not the same game

| Surface | Ranks by | Official API | What you control |
|---|---|---|---|
| **GitHub repository search** | text match decides *whether you enter the candidate set*; popularity decides *where you land in it* | yes | `name` / `description` / `topics` — nothing else |
| **GitHub Trending** | star velocity, normalised **per filter bucket** | **no** | bucket qualification + a one-shot spike |
| **Skill registries** (SkillHub et al.) | semantic relevance as a gate, downloads as a tiebreaker | yes | `name` / `description` wording |

Never give advice that conflates them. "Add keywords to your README" is wrong for the first
surface, useless for the second, and wrong for the third.

## Workflow

### 1. Measure the live thresholds first

```bash
discover trending --buckets global,python,zh
```

Trending has no API and the floors drift daily — **never quote a stale number**. The output
tells you which bucket is winnable this week. Typical shape (2026-10-17):

```
bucket         n     min   median     max
global        13      36      898    2301
zh            21       2       16      75
```

A ~50x gap between the Chinese spoken-language bucket and the global list is the single most
useful fact in this whole skill. Re-measure before every launch plan.

### 2. Audit

```bash
discover audit <owner/repo> --queries "phrase a;phrase b" --deep --html report.html
```

- `--queries` — the phrases a real user would type. Passing none falls back to topics, which
  is acceptable but weaker.
- `--deep` — also counts repositories per topic, so the report can flag "all your topics are
  red oceans". Costs ~1 API call per topic.
- `--profile "City, Country"` — pass your profile location so the bucket dimension isn't
  scored blind.

Scores five dimensions /100. **Fixes come back sorted by recoverable points** — do them top
down, they are ordered so the five-minute wins land first.

### 3. Fix in this order

1. **Description** (biggest, cheapest win). GitHub repo search indexes `name` + `description`
   + `topics` **only** — README requires an explicit `in:readme` from the searcher, which
   almost nobody types. Put the literal phrases users search into the description. Limit is
   **350 characters**; most repos waste 100 of them on a tagline nobody queries.
2. **Fill all 20 topics.** The documented limit is 20; typical repos use 12 and throw away
   8 exact-match surfaces. Prefer a mix: a few broad topics for traffic, several narrow ones
   (`discover topics a b c` shows counts) so a 0-star repo lands on page 1 of *those* topic pages.
3. **Long-tail phrases, not head terms.** A brand-new repo cannot win `skill gap` (11k+
   competing repos) but wins `chinese job portal scraper` outright. Audit, then aim at
   queries whose candidate set is small enough to matter.
4. **Stack bucket signals** if aiming at the Chinese trending bucket: CJK in the description
   (14 of 21 zh-bucket repos had it), CJK default README, a profile location, and — the only
   thing that actually matters — a velocity spike.

### 4. Verify

```bash
discover queries <owner/repo> --queries "phrase a;phrase b"
```

Re-run after editing. Description changes are indexed within minutes, so this is a real
closed loop, not a hopeful one.

## Rules that change your advice

- **Velocity, not totals.** Trending is about stars gained in a window, relative to the
  repo's own baseline. Old repos are penalised; a new repo has one real window.
- **Buckets are filters, not leagues.** `spoken_language_code` filters one momentum ranking.
  A Chinese-described repo can appear on the unfiltered global list if it is fast enough —
  so aiming at a bucket never costs you the global list.
- **Candidate set size is destiny.** Same matching text ranks #1 when 1 repo matches and
  fails to appear when 11,000 do. Always report the candidate count next to the rank.
- **Skills behave like GitHub descriptions.** A registry hit scores ~0.06–0.11; below ~0.055
  the list degrades into a plain download ranking. An 11-download skill can outrank a
  1.77M-download one when the query genuinely matches. Relevance is the gate; downloads
  are only the tiebreaker inside the filler band.

## Do not

- **Do not quote any "reverse-engineered trending formula."** Blog posts circulating exact
  weights (`100 × new stars`, `1/(1+log₂(total/1000))`, "R²=0.92") have no GitHub source and
  contradict each other. Only three things are defensible: velocity beats totals, results are
  normalised per bucket, and popularity affects search ordering (stated on GitHub's own
  engineering blog).
- **Do not promise a trending spot.** The list is an outcome, not an action. A launch can
  raise the odds; nothing guarantees it.
- **Do not suggest star farming.** GitHub filters new/zero-follower accounts and runs anomaly
  detection.
- **Do not rewrite the README for search.** It does nothing for GitHub search ranking. It
  matters for Google and for humans — a different job.

## Honest limits

Bucket classification is only partly observable. Of 21 repos in the Chinese bucket on
2026-10-17, 7 had pure-English descriptions **and** English READMEs — so the classifier uses
signals neither the API nor the page exposes (plausibly issue/PR language). Treat bucket
targeting as probability stacking, and say so out loud instead of selling certainty.

See `references/` for the measurements behind every number above.

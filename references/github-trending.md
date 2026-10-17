# GitHub Trending — measured, not guessed

## What is officially known

Almost nothing. GitHub launched Trending in 2013 and has never published the formula. There is
**no API**. `github.com/trending` is a server-rendered page with three window switches and
three filter axes:

```
?since=daily|weekly|monthly
&language=<programming language>
&spoken_language_code=<en|zh|…>
```

That is the entire documented surface. Everything below is measurement.

## Measured floors (2026-10-17, `discover trending`)

| Bucket | entries | min stars/period | median | max |
|---|---|---|---|---|
| global (no filter) | 13 | **36** | **898** | 2,301 |
| python | 15 | 32 | 308 | 2,301 |
| **zh spoken language** | 21 | **2** | **16** | 75 |
| zh weekly | 22 | 41 | 155 | 1,751 |

The gap is the point: the Chinese spoken-language bucket's *median* is 56× lower than the
global list's. Same momentum data, different filter.

The unfiltered global list is **not** "the English bucket" — a Chinese-described repo
(`hmjz100/LinkSwift`) appeared on it on 2026-10-17. Buckets are filters over one ranking, so
targeting a bucket never removes you from the global list.

## How the bucket is assigned — and what we could not prove

We classified all 21 repos in the Chinese bucket on 2026-10-17:

- **14 / 21** carried CJK characters in their `description`.
- **7 / 21** had pure-English descriptions: `ccfos/nightingale`, `AstrBotDevs/AstrBot`,
  `higress-group/higress`, `zizifn/edgetunnel`, `RapidAI/RapidOCR`, `zhayujie/CowAgent`,
  `oceanbase/miniob`.

Hypothesis tested and **rejected**: maybe their README decides it. Measured CJK ratio of the
default README for those 7 — six were pure English (<0.1% CJK), only `miniob` was Chinese
(34.8%).

What the 7 do share: they are established projects run by Chinese organisations with Chinese
issue/PR traffic. Conclusion: the classifier uses inputs the API does not expose. Description
CJK is the strongest *actionable* signal, not a sufficient one.

**Do not claim more than this.** Bucket targeting is probability stacking.

## Operator notes

- `discover trending --buckets global,python,zh --since daily|weekly` re-measures. Re-run it
  before writing any launch plan; floors move.
- Parsing is HTML regex, and two spots are brittle by nature: the row container
  `<article class="Box-row">` and the repo link, which appears URL-encoded inside the star
  button's `?return_to=%2Fowner%2Frepo`. Both are isolated in `discover/trending.py`.
- Entry counts are lower than the visible list because sponsored rows lack the star-button
  link. Do not read the counts as "the list size".

## What actually moves a repo onto the list

1. **Velocity relative to your own baseline.** Old repos are structurally penalised — the same
   daily gain is unremarkable for a 40k-star project. A new repo gets one window.
2. **A concentrated spike, not steady drip.** Publishing a release, a companion write-up, and
   the release note on the same day produces the shape the ranking rewards.
3. **UTC-aligned timing.** The window is UTC days. If your audience is in China (UTC+8),
   pushing between 20:00–24:00 Beijing time lands the stars inside the same UTC day and hits
   the EU afternoon / US morning overlap. Pushing at 00:00–08:00 Beijing time assigns those
   stars to the *previous* UTC day.
4. **Bucket-aware goals.** Aiming at a 900-star median is not a plan; aiming at 30–50 stars in
   a bucket whose median is 16 is.

## Debunked

Widely circulated posts give exact weights — `score = new_stars × 100 × 1/(1+log₂(total/1000))
× (forks/stars) × (merged_PR/10)`, "new stars only contribute 35%", "R² = 0.92", "Mojo gets a
1.2 language weight". None cite GitHub, and they contradict each other (one says new stars are
only 35% of the weight, another says velocity dominates). Treat them as SEO content, not data.

Defensible claims, all traceable: **velocity beats lifetime totals**, **results are normalised
per bucket**, **popularity influences GitHub search ordering** (per GitHub's own engineering
blog). Nothing more precise has been published.

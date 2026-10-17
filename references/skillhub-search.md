# Skill registries — how a skill gets recommended

`find-skills` is a **skill**, not a ranking. It queries a registry (SkillHub,
`https://lightmake.site/api/v1/search`) and installs what comes back. So "will `find-skills`
recommend mine" is really "does the registry's search match my skill".

## Endpoints

```
GET /api/v1/search?q=<query>&limit=n     # semantic search, returns results[].score
GET /api/skills/top                      # popularity board
GET /api/v1/categories
GET /api/v1/skills/<slug>
```

Search results carry: `slug`, `name`, `displayName`, `description`, `description_zh`, `score`,
`downloads`, `installs`, `stars`, `homepage`, `tags`, `category`, `namespace`.

## The score field is a two-mode scale

Measured across 8 queries on 2026-10-17:

| Query | Top result | score | downloads |
|---|---|---|---|
| `pdf` | PDF to Word Converter | 0.0860 | 4,019 |
| `天气` | 天气 | 0.1078 | 4,523 |
| `code review` | Code Review | 0.1045 | 1,754 |
| `xiaohongshu` | 小红书数据分析与市场调研 | 0.0658 | **11** |
| `<unmatched query>` | Tencent Docs | 0.0500 | 1,766,795 |
| `<unmatched query>` | Agent Browser | 0.0500 | 1,037,601 |
| `<unmatched query>` | 搜索引擎 | 0.0492 | 1,412,284 |

Two regimes:

- **≥ 0.055** — a genuine semantic match. Values observed 0.058–0.108.
- **≤ 0.0500** — no semantic match; the list degrades to a global download ranking with a
  fixed, descending tail (0.0500 → 0.0492 → 0.0488 → 0.0479 …).

Decisive test: two unrelated queries (`robotics career skill gap` and
`zzzqqq nonexistent xyz`) returned **identical results in identical order**. When nothing
matches, everyone below the relevance band sees the same popularity list.

## Consequences

1. **Downloads are not the gate.** A skill with 11 downloads scored 0.0658 and outranked a
   1.77M-download incumbent stuck at 0.0500. Relevance lifts you above the floor; downloads
   only sort you inside the floor.
2. **A new skill has a fair shot** — but only on wording. `name` + `description` must contain
   the phrases a user would type. There is no keyword-weighting trick beyond that.
3. **Chinese words belong in the description.** Registry topics/tags are effectively ASCII
   slugs; natural-language matching happens on the description text. Chinese queries work
   (`天气` scored highest of all measured queries), so bilingual descriptions are strictly
   additive.
4. **Weak matches earn nothing.** A partial match falls through to the floor — there is no
   partial credit between 0.050 and 0.058.

## Commands

```bash
discover skill <slug> --queries "job radar;resume gap;career portal"
discover skill-probe --queries "some phrase;另一个查询"
```

`skill-probe` shows whether a query matched anything at all — if `genuine hits` is 0, the
market for that phrase does not exist yet and picking a different phrase beats rewriting yours.

## Honest limit

The registry's ranking is unpublished and can change without notice. These bands were measured
on one day against one endpoint. Treat thresholds as calibration, not constants —
`discover skill-probe` re-measures the band each run.

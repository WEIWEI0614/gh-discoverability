# GitHub repository search — what actually happens

## Official facts (docs.github.com)

From **Searching for repositories**:

> "When you omit this qualifier, only the repository name, description, and topics are searched."

That is the whole search surface for a repository. `in:readme` exists, but the searcher has to
type it — treat README as out of scope for discovery.

From the **Search API** reference:

> "Unless another sort option is provided as a query parameter, results are sorted by best
> match … Multiple factors are combined to boost the most relevant item to the top."

GitHub never publishes those factors. One is known from the engineering blog
(**A brief history of code search at GitHub**, 2021-12-15), describing Blackbird:

> "the repository in which a match occurs also influences ranking. We want to show results
> from popular open-source repositories before a random match in a long-forgotten repository."

So popularity is officially confirmed as a ranking input. Exact weighting is not public.

From **Classifying your repository with topics**:

- lowercase letters, numbers and hyphens
- 50 characters or fewer
- **no more than 20 topics**

Repository `description` limit: **350 characters** (observed enforced limit).

## The two-stage model

```
query ──► text match on name/description/topics ──► candidate set
                                                         │
                                          popularity + relevance
                                                         ▼
                                                    final order
```

Consequences, all verified against live search:

| Query | Candidate set | Result |
|---|---|---|
| `chinese job portal scraper` | 1 | rank 1 |
| `feishu hire scraper` | 1 | rank 1 |
| `skill gap analyzer for job descriptions` | 105 | not in top 50 |
| `skill gap in:description` | 11,457 | not in top 50 |
| `job scraper in:description` | 3,539 | not in top 50 |

A zero-star repository wins any query whose candidate set is single digits, and is invisible in
any query whose candidate set is thousands — **with identical, perfectly relevant
descriptions**. Text gets you in; stars decide where you sit.

## Measurement notes

- `discover queries <repo> --queries "a;b"` reports `total` (candidate set) beside `rank`.
  Always read them together — a rank of "absent" means nothing without the total.
- Editing a description is indexed **within minutes**, not hours. Verified by searching a
  phrase that only existed in the new description immediately after the PATCH: it returned
  rank 1 of 1. So a failing query is a ranking problem, not an indexing problem.
- `in:description` does **not** rescue a low-popularity repo. It narrows the field but the
  ordering is unchanged.
- Hyphenated topics are their own token. A repo with topic `skill-gap` does **not** surface
  for the free-text query `skill gap`; it surfaces under `topic:skill-gap`. Topic pages
  default-sort by stars, so a 0-star repo is last on every crowded topic page.

## Practical checklist

1. Write the description last, after listing the phrases users type.
2. Front-load the highest-intent phrase; character order does not affect matching, but it is
   the only part visible in a search result row.
3. Fill all 20 topics, mixing broad (traffic) with narrow (page-1 placement).
4. Keep the repo name short and pronounceable; it is the one exact-match surface you cannot
   change later without breaking links.
5. Do not rename the repo to chase a keyword — a 40-character repo name is untrustworthy and
   still only wins a substring match.

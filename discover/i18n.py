"""Bilingual strings for reports and rule notes.

Only two languages, no framework. Keys are semantic; `t()` falls back to English so a new note
never crashes a report.
"""
from __future__ import annotations

MSG: dict[str, dict[str, str]] = {
    # ---- dimension labels ----
    "dim.search_surface": {"zh": "可搜索面", "en": "Search surface"},
    "dim.topic_layout": {"zh": "话题布局", "en": "Topic layout"},
    "dim.bucket_signal": {"zh": "入桶信号", "en": "Bucket signal"},
    "dim.conversion": {"zh": "转化面", "en": "Conversion"},
    "dim.query_reach": {"zh": "查询命中", "en": "Query reach"},

    # ---- search surface ----
    "ss.no_queries": {
        "zh": "没有可用的目标查询词 —— 先确定用户会搜什么",
        "en": "No target phrases to measure — decide what users actually type first",
    },
    "ss.missing": {
        "zh": "{n}/{m} 个目标查询词在 name/description/topics 里完全不出现",
        "en": "{n} of {m} target phrases appear in none of name/description/topics",
    },
    "ss.short_desc": {
        "zh": "description 只用了 {used}/{max} 字符，还空着 {rest} 个字符的精确匹配位",
        "en": "Description uses only {used}/{max} characters — {rest} exact-match characters left unused",
    },

    # ---- topic layout ----
    "tl.crowded": {
        "zh": "所有 topic 都是千级以上的红海话题，新仓库在话题页会被 star 排序压到底",
        "en": "Every topic is a thousand-repo red ocean — a new repo sinks to the bottom of every topic page",
    },
    "tl.unused": {
        "zh": "topics 只用了 {n}/{max} 个，白扔 {rest} 个精确匹配面",
        "en": "Only {n}/{max} topics used — {rest} exact-match surfaces thrown away",
    },
    "tl.too_long": {
        "zh": "有 topic 超过 {max} 字符上限：{list}",
        "en": "Topics over the {max}-character limit: {list}",
    },

    # ---- bucket signal ----
    "bs.no_cjk": {
        "zh": "description 无中文 —— 中文桶 21 个仓库里 14 个有中文描述，这是你能控制的最强信号",
        "en": "No CJK in the description — 14 of 21 repos in the Chinese bucket had it; it is the "
              "strongest signal you control",
    },
    "bs.cjk_not_first": {
        "zh": "中文不在 description 开头，判定时可能被前面的英文带偏",
        "en": "CJK is not at the start of the description; leading English may skew classification",
    },
    "bs.readme_en": {
        "zh": "默认 README 是纯英文（中文占比 {pct}%）—— 只作弱信号，但补上零成本",
        "en": "Default README is English ({pct}% CJK) — a weak signal, but free to fix",
    },
    "bs.no_demo": {
        "zh": "没有在线 demo —— 访客无法在 10 秒内判断它值不值得 star",
        "en": "No live demo — a visitor cannot judge in 10 seconds whether this deserves a star",
    },
    "bs.no_location": {
        "zh": "GitHub 主页 location 为空 —— 中文桶 21 个仓库里 9 个明写中国地址",
        "en": "Profile location is empty — 9 of 21 repos in the Chinese bucket list a China location",
    },

    # ---- conversion ----
    "cv.no_license": {
        "zh": "没有 LICENSE —— 企业用户和部分开发者会直接跳过",
        "en": "No LICENSE — companies and some developers skip it outright",
    },

    # ---- query reach ----
    "qr.no_top10": {
        "zh": "没有任何目标查询词进前 10 —— 先打长尾词，短词要等 star 攒起来",
        "en": "No target phrase reaches the top 10 — hunt long-tail phrases; head terms wait for stars",
    },
    "qr.absent": {
        "zh": "`{q}` 前 {limit} 名之外（候选集可能上千，0 star 进不去）",
        "en": "`{q}` outside the top {limit} (candidate set may be in the thousands; 0 stars will not enter)",
    },

    # ---- report chrome ----
    "r.title": {"zh": "可发现性审计", "en": "Discoverability audit"},
    "r.score": {"zh": "总分", "en": "Score"},
    "r.grade": {"zh": "等级", "en": "grade"},
    "r.dims": {"zh": "五个维度", "en": "Dimensions"},
    "r.fixes": {"zh": "按可回收分数排序的修改项", "en": "What to fix, by recoverable points"},
    "r.none": {"zh": "没有明显可回收项。", "en": "Nothing worth changing."},
    "r.floors": {"zh": "实时热榜门槛", "en": "Live trending floors"},
    "r.bucket": {"zh": "分桶", "en": "bucket"},
    "r.min": {"zh": "最低", "en": "min"},
    "r.median": {"zh": "中位数", "en": "median"},
    "r.max": {"zh": "最高", "en": "max"},
    "r.floors_note": {
        "zh": "GitHub 不公开热榜公式。这些数字从实时页面测出，每天都在变 —— 重跑 "
              "<code>discover trending</code> 再下结论。",
        "en": "GitHub publishes no trending formula. These numbers are measured from the live "
              "page and drift daily — re-run <code>discover trending</code>.",
    },
    "r.footer": {
        "zh": "gh-discoverability · 每条规则都对应实测，依据见 references/",
        "en": "gh-discoverability · every rule traces to a measurement, see references/",
    },
    "r.queries": {"zh": "查询词与位次", "en": "Phrases and ranks"},
    "r.query": {"zh": "查询词", "en": "phrase"},
    "r.candidates": {"zh": "候选集", "en": "candidates"},
    "r.rank": {"zh": "位次", "en": "rank"},
    "r.absent_mark": {"zh": "未进前 60", "en": "not in top 60"},
    "r.two_stage": {
        "zh": "词命中决定能否进候选集，star 数量决定在候选集里排第几。",
        "en": "Words decide whether you enter the candidate set; stars decide where you land in it.",
    },
}


def t(key: str, lang: str = "zh", **kw) -> str:
    entry = MSG.get(key, {})
    text = entry.get(lang) or entry.get("en") or key
    return text.format(**kw) if kw else text

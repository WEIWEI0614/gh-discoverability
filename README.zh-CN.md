<div align="center">

# 🔭 gh-discoverability

**为什么没人发现你的项目 —— 靠测量，不靠传说。**
给你的可搜索面、热榜入桶概率、技能注册表排名各打一个分，然后把修改项按**能拿回多少分**排序。

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![不需要 LLM](https://img.shields.io/badge/LLM-不需要-success)]()
[![零依赖](https://img.shields.io/badge/运行时依赖-0-brightgreen)](pyproject.toml)

[English](README.md) · [简体中文](README.zh-CN.md)

</div>

---

## 它要打掉的那个说法

开源项目的"曝光技巧"分两种：可测量的，和编出来的。

第二种以精确公式的形式流传——`得分 = 新增star × 100 × 1/(1+log₂(总star/1000))`、
"新增 star 只占 35% 权重"、"R² 达 0.92"。没有一条能追到 GitHub 官方，而且这些文章**互相矛盾**。
这个工具只编码能复现的东西：

| 事实 | 依据 |
|---|---|
| GitHub 仓库搜索**只索引 `name` + `description` + `topics`** | GitHub 官方文档《Searching for repositories》 |
| **热度参与搜索排序** | GitHub 工程博客《A brief history of code search at GitHub》(2021) |
| Trending **没有 API**，也没有公开公式 | 根本没有这个端点，页面是 HTML |
| 不同分桶的门槛**差约 50 倍** | 实测：全球桶中位 898，中文桶中位 16 |

## 三个入口，三套规则

```
                       ┌─────────────────────┐
   查询 ──────────────►│ name / description  │──► 候选集 ──► 热度 ──► 最终顺序
                       │ / topics            │       │                        │
                       └─────────────────────┘       └── 1 个仓库  → 第 1
                                                      └── 11457 个 → 0 star 根本进不去
```

把这三件事混为一谈的建议，会在三个方向上同时出错：

- **"在 README 里堆关键词"** —— 对 GitHub 搜索**完全无效**。搜索者得手动敲 `in:readme`，而几乎没人这么干。
- **"多攒 star"** —— 正确，但没用，因为它是所有其他事情的结果而不是原因。
- **"去冲中文热榜桶"** —— 方向对，但入桶由一个你看不全的分类器决定（桶内 21 个仓库里有 7 个是纯英文描述）。

## 快速开始

```bash
pip install gh-discoverability     # 或：pip install -e .
```

```bash
discover trending --buckets global,python,zh      # 先量当月门槛，再谈任何计划
discover audit owner/repo --queries "短语A;短语B" --deep --html report.html
discover queries owner/repo --queries "短语A"      # 你现在到底排第几
discover topics job-scraper skill-map beisen      # 哪些话题是红海
discover skill my-skill --queries "job radar"     # 技能注册表排名体检
```

样例输出：

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

## 改变打法的那个发现

同一句话、同一份完全贴切的描述：候选集只有 **1** 个仓库时你排**第 1**，候选集有 **11457** 个时你**连前 50 都进不去**。同一个仓库、同一天实测：

| 查询 | 候选集 | 位次 |
|---|---|---|
| `chinese job portal scraper` | 1 | **第 1** |
| `feishu hire scraper` | 1 | **第 1** |
| `skill gap analyzer for job descriptions` | 105 | 前 50 之外 |
| `skill gap in:description` | 11,457 | 前 50 之外 |

**词命中决定你能不能进候选集，star 数量决定你在候选集里排第几。**
所以有用的问题从来不是"我排第几"，而是"我在**多少个**里面排第几"。

## 它不做什么

- **不承诺你上热榜。** 榜是结果，不是动作。
- **不给你热榜公式。** 公开资料里没有。它只量门槛，然后告诉你这周哪个桶打得动。
- **不假装入桶资格可控。** 那是概率叠加，SKILL.md 里明写了这一点。
- **不为搜索排名去改你的 README。** 那不解决问题。README 是给 Google 和人的，是另一条战线。

## 当作 agent skill 用

`SKILL.md` 可以直接放进 WorkBuddy / CodeBuddy / Claude 类 agent：

```bash
cp -r . ~/.workbuddy/skills/gh-discoverability
```

然后问你的 agent **"为什么没人发现我的项目"**，它会跑审计，而不是背传说。

## 许可证

MIT。贡献是这些测量结果本身——请重新测，而不是信任这个文件。

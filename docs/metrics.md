---
id: DOC-METRICS
title: AI 原生研发指标
version: 0.1
status: draft
owner: orchestrator
reviewers: [human-owner]
depends_on: [DOC-06, DOC-07]
last_reviewed: 2026-10-17
---

# AI 原生研发指标

> 目的：用少量、可解释的指标判断多 agent 流程是否健康；**不做个人 KPI、不做排名、不为了数字刷分**。
>
> 数据源：`docs/backlog.md`、`docs/_review/`、`docs/runs/`、`docs/_qa/`、`docs/07`。
>
> 频率：每阶段复盘一次；先采 2 项（handoff 完整率、返工率），稳定后再加。

---

## 1. 指标定义

| ID | 指标 | 定义 | 数据源 | 目标 |
|---|---|---|---|---|
| MET-001 | Handoff 完整率 | 有完整 handoff（TASK/STATUS/CHANGED/DECISIONS/EVIDENCE/RISKS/NEXT）的任务 / 总任务 | backlog、runs | ≥95% |
| MET-002 | 返工率 | review 后需要 major/blocker 级重做的任务 / 总任务 | review | <15% |
| MET-003 | 缺陷逃逸 | QA 后/发布后发现的 P0/P1 / 阶段 | QA、release | P0/P1 = 0 |
| MET-004 | 幻觉率 | 抽检中被推翻的事实断言 / 抽检断言数 | review、抽查 | <5% |
| MET-005 | Human 推翻率 | Human 推翻 agent 决策 / Human 复核决策数 | decision memo、runs | 5–15% |
| MET-006 | 单任务成本 | token/调用/时长/工具成本 | runs | 有上限，超限即停 |
| MET-007 | 周期时间 | brief 创建 → merge 的中位时长 | backlog、runs | 按阶段设 |
| MET-008 | 评审问题密度 | blocker+major 数 / 1k 字或每任务 | review | 趋势下降 |
| MET-009 | 基线冲突数 | 与 `docs/00`/ADR 冲突的次数 | handoff、review | 0（可发现） |
| MET-010 | 文档新鲜度 | `last_reviewed` 超过 90 天的正式文档数 | docs front matter | 0 |

---

## 2. 口径与采样

- **handoff 完整率**：缺任一段即不完整；`blocked` 任务也必须有 handoff。
- **返工率**：只统计 review 后需要重写/大改的任务；minor 修复不计。
- **幻觉率**：每阶段随机抽 5% 事实断言，核对来源；无来源断言直接算失败。
- **Human 推翻率**：只统计 Human 实际复核的决策；过低（<5%）说明复核走过场，过高（>15%）说明基线/任务 brief 不清。
- **成本**：模型/工具/时长分开记录；不把 token 数当产出。
- **周期**：不含等待 Human 的时间，单独记录。

---

## 3. 当前阶段（文档）

先采：

- MET-001 handoff 完整率。
- MET-002 返工率。

观察项（不设硬目标）：

- MET-004 幻觉率（来源抽查）。
- MET-007 周期时间。
- MET-009 基线冲突数。

本次 RUN-20261017-01 的基线在 `docs/runs/` 记录；交付后填。

---

## 4. 反刷分规则

- 不把指标当个人 KPI/排名；只用于流程改进。
- 不奖励“写得多/写得快”；奖励“验收通过、返工少、来源可查”。
- 抽样由非作者执行；Human 抽检。
- 指标定义变更走 `docs/00`/ADR 流程；不偷偷改口径。
- 发现刷分（虚报 handoff、隐藏返工、伪造来源）按安全/诚信事件处理。

---

## 5. 复盘问题

1. 哪个指标变差？根因是任务太大、brief 不清、上下文不足、还是门禁缺失？
2. 哪个门没拦住问题？需要加检查还是换 reviewer？
3. 哪个模板/规范需要改？一次只改一条。
4. 成本/周期是否可接受？是否需要拆任务/换模型/加缓存？
5. 下阶段采哪些指标？不要一次上全套。

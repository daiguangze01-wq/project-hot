---
id: DOC-BACKLOG
title: 任务看板
version: 0.1
status: active
owner: orchestrator
reviewers: [human-owner]
depends_on: [DOC-00, DOC-06, DOC-07]
last_reviewed: 2026-10-17
---

# 任务看板

> 规则：无 `TASK-###` brief 不开工；完成后交 handoff、更新 `docs/07`、写 run log。
>
> 状态：planned / in_progress / review / done / blocked / future。

## 1. 文档阶段

| TASK | 标题 | Owner | 依赖 | 产出 | 验收 | 状态 |
|---|---|---|---|---|---|---|
| TASK-001 | AGENTS.md + 模板 + 目录 | Orchestrator | — | `AGENTS.md`、`_templates/*` | 新 agent 可入场 | done |
| TASK-002 | docs/00 基线 | Orchestrator | TASK-001 | `docs/00` | 数字/术语/约束完整 | done |
| TASK-003 | docs/06 + docs/07 | Orchestrator | TASK-002 | `docs/06`、`docs/07` | 流程/追踪矩阵可执行 | done |
| TASK-004 | 2.5D 竞品研究 | Researcher A | TASK-002 | `_research/competitor-2.5d.md` | ≥6 款 2.5D 样本、来源 | done |
| TASK-005 | 2.5D 美术研究 | Researcher B | TASK-002 | `_research/art-2.5d.md` | 参数/参考/风格测试 | done |
| TASK-006 | AI 协作研究 | Researcher C | TASK-002 | `_research/ai-native.md` | 角色/门禁/反模式/来源 | done |
| TASK-010 | 竞品报告 01 | C1 | TASK-004 | `docs/01` | ≥12 游戏、矩阵、20 条启示 | done |
| TASK-011 | PRD 战斗/装备 | C2/Orchestrator | TASK-002/004 | `docs/02`（直接合并） | 相机/键盘/帧数据/装备 | done |
| TASK-012 | PRD MMO/商业 | C3/Orchestrator | TASK-002 | `docs/02`（直接合并） | 副本/PvP/经济/商业化 | done |
| TASK-013 | TDD 客户端/联网 | C4/Orchestrator | TASK-002 | `docs/03`（直接合并） | 输入/2.5D/同步/测试 | done |
| TASK-014 | TDD 后端/数据/部署 | C5/Orchestrator | TASK-002 | `docs/03`（直接合并） | 数据/API/部署/成本 | done |
| TASK-015 | 美术指南 04 | C6/Orchestrator | TASK-005 | `docs/04`（直接成稿） | 剪影/参数/管线/预算 | done |
| TASK-020 | 合并 PRD 02 | Orchestrator | TASK-011/012 | `docs/02` | 无重复/数字一致 | done |
| TASK-021 | 合并 TDD 03 | Orchestrator | TASK-013/014 | `docs/03` | 架构/数据/成本一致 | done |
| TASK-030 | 一致性评审 | Reviewer A | TASK-020/021 | `_review/REV-001-consistency.md` | 数字/术语/来源/键盘 | in_progress |
| TASK-031 | 红队评审 | Reviewer B | TASK-020/021 | `_review/REV-002-red-team.md` | 产品/技术/商业/流程风险 | done（6 blocker） |
| TASK-032 | 快速一致性评审 | Quick Reviewer A | TASK-020/021 | `_review/REV-003-quick-consistency.md` | 7 blocker | done |
| TASK-033 | 快速红队评审 | Quick Reviewer B | TASK-020/021 | `_review/REV-004-quick-red-team.md` | 2 blocker/1 major | done |
| TASK-040 | 全键盘/文档 QA | QA | TASK-020/021 | `_qa/qa-report.md` | 全键盘/链接/Mermaid/字数 | done |
| TASK-041 | run log/复盘/README | Orchestrator | TASK-040 | `runs/RUN-*`、`README.md` | 可复盘/索引完整 | done（初稿，待评审关闭） |
| TASK-042 | ADR 正文 | Tech Lead | TASK-003 | `docs/decisions/ADR-*.md` | 12 条、选项/后果 | done |
| TASK-043 | docs/05 ADR 索引 | Orchestrator | TASK-042 | `docs/05` | 索引完整 | done |
| TASK-044 | AI 研发指标 | Orchestrator | TASK-003 | `docs/metrics.md` | 定义/口径/目标/反刷分 | done |
| TASK-045 | QA/评审模板 | Orchestrator | TASK-003 | `_qa/qa-checklist.md`、`_review/reviewer-brief.md`、`_templates/decision-request.md` | 可直接使用 | done |
| TASK-046 | Baseline 0.1.2 决策请求 | Orchestrator | TASK-003 | `docs/decisions/DR-001-baseline-0.1.2.md` | Human 批准/修改 | pending Human |
| TASK-047 | 多 Agent 工作保障 | Orchestrator | TASK-003 | `docs/tasks.json`、`scripts/check-agent-work.ps1`、`skills/multi-agent-delivery/SKILL.md`、`docs/handoffs/INDEX.md` | 检查器通过 | done |

## 2. 原型阶段（后续）

| TASK | 标题 | Owner | 依赖 | 产出 | 验收 | 状态 |
|---|---|---|---|---|---|---|
| TASK-050 | M0 战斗原型 | Gameplay Implementer | TASK-020/021 | 可玩原型 | 2 核心/1 图/键盘-only/连段/防御 | future |
| TASK-051 | M0 联网原型 | Netcode Implementer | TASK-021 | 2 人房间 | 100ms/2% 丢包可完成击杀 | future |
| TASK-052 | M0 美术风格测试 | Art Lead | TASK-015 | 1 角色+1 环境+3 装备+1 Boss | 10/20/30m 可读性通过 | future |
| TASK-053 | M0 后端骨架 | Backend Implementer | TASK-021 | 登录/角色/背包 | 端到端可持久化 | future |
| TASK-054 | 垂直切片评审 | Orchestrator + Human | TASK-050–053 | 决策包 | 是否进入 Alpha | future |
| TASK-060 | 2.5D 相机/可读性验证 | camera-validator | TASK-021 | `validation/camera/` | 模型级 pass | done |
| TASK-061 | 完美格挡/延迟补偿验证 | netcode-validator | TASK-021 | `validation/netcode/` | conditional；M1 fixed | done |
| TASK-062 | 键盘 rollover/组合验证 | input-validator | TASK-021 | `validation/input/` | conditional；M3 fixed；硬件 QA 待 | done |
| TASK-063 | 技术验证独立复核 | validation-reviewer | TASK-060–062 | `validation/review/` | 6B/5M/9m | done |
| TASK-064 | 技术验证汇总 | Lead | TASK-060–063 | `validation/REPORT.md` | conditional go to M0 | done |
| TASK-065 | DR-002 验证后基线修正 | Lead + Human | TASK-060–063 | `docs/decisions/DR-002-validation-baseline-fixes.md` | D1–D6 approved | done |
| TASK-066 | 3 款键盘人工 QA（B6） | QA + Human | TASK-062 | `validation/input/hardware-qa/` | 3 款×100 次 ≥99% | planned |
| TASK-070 | Web 可玩 MVP | Lead | TASK-020/021 | `mvp/` | 可双开试玩；15/15 测试；截图 | done |
| TASK-071 | MVP 独立评审 | mvp-reviewer | TASK-070 | `mvp/review/` | 0B/0M；4 minor | done |

## 3. 任务 Brief 索引

| TASK | Brief |
|---|---|
| TASK-004 | `_templates/task-brief.md` 复制后填 |
| TASK-005 | 同上 |
| TASK-006 | 同上 |
| TASK-010–015 | 见本报第 4 节摘要；handoff 在 `_drafts/TASK-010–015-handoff.md`；完整 brief 由 Orchestrator 下发（本次未单独成文件） |
| TASK-020/021/042–046 | 合并/索引/模板/DR 支持任务，按 `docs/06` §10.3 豁免独立 handoff，记录在 run log |
| TASK-020/021 | 合并 brief 由 Orchestrator 下发 |
| TASK-030/031/040 | 评审 brief 由 Orchestrator 下发 |

## 4. 撰稿任务摘要

### TASK-010 竞品报告
- 目标：≥12 款游戏、2.5D 俯视样本、矩阵、失败模式、20 条启示。
- 输入：`docs/00`、`_research/competitor-2.5d.md`。
- 输出：`docs/01`，8–12k 字。
- 验收：来源 ≥20；事实/推断分离；每条启示对应 PRD 系统。

### TASK-011 PRD 战斗/装备
- 目标：相机/全键盘/战斗/帧数据/公式/装备/Build。
- 输出：`_drafts/02a.md`，8–12k 字。
- 验收：经典布局表、1 套帧数据、1 个 Build、2.5D 高度/遮挡规则。

### TASK-012 PRD MMO/商业
- 目标：城镇/野外/副本/RAID/PvP/社交/经济/商业化/路线图/KPI。
- 输出：`_drafts/02b.md`，7–10k 字。
- 验收：内容表、经济产销、三档收入情景、风险。

### TASK-013 TDD 客户端/联网
- 目标：Unity/输入/2.5D 相机/战斗模拟/同步/反作弊/测试。
- 输出：`_drafts/03a.md`，8–12k 字。
- 验收：架构图、时序图、tick 表、键盘冲突方案、测试矩阵。

### TASK-014 TDD 后端/数据/部署
- 目标：Nakama/经济/数据模型/API/匹配/部署/成本/里程碑。
- 输出：`_drafts/03b.md`，8–12k 字。
- 验收：ER 图、API 示例、成本表、M0–M4。

### TASK-015 美术指南
- 目标：2.5D 斜俯视像素风参数/管线/预算/风格测试。
- 输出：`_drafts/04.md`，6–9k 字。
- 验收：剪影/高度/遮挡规则、资产预算、可读性测试。

## 5. 变更记录

| 日期 | 变更 | 原因 | 批准 |
|---|---|---|---|
| 2026-10-17 | 初始 backlog | 计划批准 | Human |

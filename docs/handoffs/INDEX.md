# Handoff 索引

> 规则：`docs/tasks.json` 中 `status=done` 且 `handoff_required=true` 的任务，必须有 handoff 文件；支持任务按 `docs/06` §10.3 豁免。检查器：`scripts/check-agent-work.ps1`。

## 已交付 handoff

| TASK | handoff | 内容 |
|---|---|---|
| TASK-010 | [TASK-010-handoff.md](../_drafts/TASK-010-handoff.md) | 竞品报告 01 |
| TASK-011 | [TASK-011-handoff.md](../_drafts/TASK-011-handoff.md) | PRD 战斗/装备 |
| TASK-012 | [TASK-012-handoff.md](../_drafts/TASK-012-handoff.md) | PRD MMO/商业 |
| TASK-013 | [TASK-013-handoff.md](../_drafts/TASK-013-handoff.md) | TDD 客户端/联网 |
| TASK-014 | [TASK-014-handoff.md](../_drafts/TASK-014-handoff.md) | TDD 后端/数据 |
| TASK-015 | [TASK-015-handoff.md](../_drafts/TASK-015-handoff.md) | 美术指南 04 |
| TASK-070 | [mvp/HANDOFF.md](../../mvp/HANDOFF.md) | Web 可玩 MVP |
| TASK-071 | [mvp/review/REVIEW-FOLLOWUP.md](../../mvp/review/REVIEW-FOLLOWUP.md) | MVP 独立复评 |
| TASK-080 | [client-unity/HANDOFF.md](../../client-unity/HANDOFF.md) | Unity U0 |
| TASK-081 | [client-unity/HANDOFF-AVATAR.md](../../client-unity/HANDOFF-AVATAR.md) | 纸娃娃/装备槽原型 |
| TASK-082 | [client-unity/HANDOFF-SIM.md](../../client-unity/HANDOFF-SIM.md) | Hot.Sim + U1b |
| TASK-083 | [client-unity/HANDOFF-PAPERDOLL.md](../../client-unity/HANDOFF-PAPERDOLL.md) | 2D 纸娃娃样张 |
| 整体 | [HANDOFF-20261018.md](HANDOFF-20261018.md) | 当前项目交接总览 |

## 支持任务豁免

以下任务为合并/索引/模板/评审/QA/run log 等支持任务，按 `docs/06` §10.3 不单独 handoff，记录在 run log 或评审报告：

`TASK-001`–`TASK-006`、`TASK-020`、`TASK-021`、`TASK-030`–`TASK-033`、`TASK-040`–`TASK-047`。

## 未来任务

`TASK-050`–`TASK-054` 开工后必须写 handoff 到：

- `docs/handoffs/TASK-050-handoff.md`
- `docs/handoffs/TASK-051-handoff.md`
- `docs/handoffs/TASK-052-handoff.md`
- `docs/handoffs/TASK-053-handoff.md`
- `docs/handoffs/TASK-054-handoff.md`

## 当前 blocker / 待交接

- **整体交接**：[HANDOFF-20261018.md](HANDOFF-20261018.md)。
- `TASK-046`（DR-001 items 1–13）：pending Human，handoff 豁免。
- `TASK-066`（B6 3 款键盘 QA）：blocked-human，kit 在 `validation/input/hardware-qa/`。
- `TASK-081`（真实 base_body/hair/top）、`TASK-082`（全技能试玩/Fusion）：in_progress。
- `TASK-050`–`TASK-054` M0：future；Unity/Fusion 环境未完整。
- `REV-001` M-1/M-3、完美格挡时序、赛季产能：见 `docs/07` §9。

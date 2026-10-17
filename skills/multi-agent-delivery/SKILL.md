# Skill — Multi-Agent Delivery（Project Hot）

> 适用：本项目任何多 agent 协作任务。目标不是“让 agent 更忙”，而是保证 **不重复、不冲突、可追溯、可交接**。

## 何时使用

- 任务会修改仓库文件（文档/代码/美术/配置）。
- 有 2 个以上 agent 并行，或一个 agent 分多轮执行。
- 需要交接给下一个 agent、reviewer 或 Human。

## 必读

1. `AGENTS.md`
2. `docs/00-设计基线与术语.md`
3. `docs/tasks.json`：确认任务是否存在、owner/reviewer、状态、write_scope、依赖、handoff 要求。
4. `docs/06-AI原生开发与多Agent协作规范.md` §4–§6。
5. 你的 `TASK-###` brief。

## 协议（按顺序）

### 1. Claim

- 只处理 `docs/tasks.json` 中 **owner 是你、status=planned/in_progress** 的任务。
- 开工前确认没有其他 `in_progress`/`review` 任务的 `write_scope` 与你的重叠。
- 状态变更由 **Orchestrator 单写**；agent 不直接改 `tasks.json`。需要 claim 时发消息给 Orchestrator。
- 没有任务号 → 先让 Orchestrator 建任务；不要“顺手做”。

### 2. Duplicate check

- 在 `docs/tasks.json`、`docs/backlog.md`、`docs/07` 搜索相同产物/REQ。
- 同一文件/目录同一时间只能有一个 writer。
- 发现重复：停止，提交合并/拆分建议；不要两个 agent 各写一版。

### 3. Write

- 只在 `write_scope` 内写。
- 一个文件同一时间一个 writer；跨文件任务先拆。
- baseline/ADR/`AGENTS.md` 变更：先 DR/ADR，Human 批准后再写。
- 不覆盖他人未提交/未合并的改动；冲突时停止并升级。

### 4. Self-check

- 验收标准逐条勾。
- 数字/术语以 `docs/00` 为准；关键事实有链接；不确定标「待核实」。
- 跑 `scripts/check-agent-work.ps1`（至少确认任务/写域/handoff 状态）。

### 5. Handoff

按 `AGENTS.md` §6 格式，写入：
- `docs/handoffs/TASK-###-handoff.md`（或任务指定的 handoff 路径）

必须包含：TASK / STATUS / CHANGED / DECISIONS / EVIDENCE / RISKS / NEXT。
`done` 且 `handoff_required=true` 的任务没有 handoff 文件 = 未完成。

### 6. Review

- 作者 != reviewer；reviewer 只写 `docs/_review/`。
- blocker 未关闭不得标 `done`；作者修复，Orchestrator 关闭。
- 禁止自审自批、自合并。

### 7. Traceability

每个任务至少能回答：

- 对应 REQ 是什么？
- 产物路径是什么？
- 谁写的、谁评审的？
- 用了什么来源/测试？
- handoff 在哪？
- 下一个 agent 要做什么？

记录到：`docs/tasks.json`、`docs/07`、`docs/runs/RUN-*.md`、handoff、review。

## 强制检查

```powershell
# Windows PowerShell 5.1（当前环境）
& .\scripts\check-agent-work.ps1
```

通过标准：

- `tasks=... done=... active=0 ...`
- `OK: task ownership, handoff, review, dependencies, and active write scopes are consistent.`

失败即 block：先修 tasks.json/handoff/写域，不要继续写文件。

## 反模式

- 两个 agent 同时改 `docs/02`，各写一版再合并。
- 没有 TASK 号就开始“帮忙优化”。
- `done` 但没有 handoff，或 handoff 只写“已完成”。
- reviewer 是作者自己，或 reviewer 被作者“指导结论”。
- 同一个 bug 开两个任务，最后两份报告。
- 把 `docs/tasks.json` 当摆设，实际靠聊天口头分配。

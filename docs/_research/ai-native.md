# AI 原生多 Agent 协作研究

> Research C / TASK-006。工作材料，最终沉淀到 `docs/06` 与 `AGENTS.md`。

## 结论

1. 约束写进仓库，不写进 prompt；流程靠「角色—路径—门」执行。
2. 最小闭环：TASK brief → 单写者分支 → 非作者评审 → 合并队列 → run log。
3. 不可逆、花钱、法律、玩家信任四类决策，AI 只有提案权。
4. 一个数字一个家，一个决策一个 ADR。

## AGENTS.md

- 分层：根文件路由 + 硬约束；子目录局部规则；任务 brief 再叠一层。
- 六段：读序、单一事实源、可复制命令、写权限矩阵、禁区、DoD。
- 三条禁令：不改 baseline、不编数字、不跳过 handoff。
- 规则可验证：命令要真跑得通。
- 改动走评审 + ADR；每阶段删失效条目。

## 生命周期

- brief 七要素：目标、范围、输入、输出、验收、风险、owner/reviewer。
- handoff 五段：CHANGED/DECISIONS/EVIDENCE/RISKS/NEXT；缺 handoff 视为未完成。
- 评审：只出报告不改源文件；blocker/major/minor；blocker 由 Orchestrator 关闭。
- 合并：单写者分支 → rebase → 合并队列；作者不合并。
- 一文件一 writer；冲突停手交 Orchestrator。

## 上下文/记忆

- 数字只在 baseline，决策只在 ADR，进度只在 backlog；其余链接 + 锚点。
- 单任务 ≤ 窗口 40%；单次读 ≤5 文件；子 agent 只回 1–2k token 摘要。
- 分层：run log / ADR / REQ-TASK 矩阵 / NOTES。
- 模型记忆不是事实源。

## 质量门与人类门

| 变更 | 风险 | 执行 | 评审 | 批准 |
|---|---|---|---|---|
| 文案/调研/测试补写 | 低 | AI | 独立 AI | Human 抽检 |
| 代码/配置/数值 | 中 | AI | 独立 AI + CI | AI Lead 合并 |
| 战斗数值/经济/存档 schema | 高 | AI 提案 | 双人 AI | Human |
| 付费/IP/发布/安全例外/AGENTS.md/ADR | 极高 | AI 仅提案 | 法务/安全 | Human |

人类门四条：不可逆、花钱、法律、玩家信任。

## AI 风险

| 风险 | 控制 |
|---|---|
| 幻觉 | 事实/推断/待核实；事实可点开；抽检 |
| prompt injection | 外部内容不可信；工具白名单；高危二次确认 |
| 数据泄露 | 密钥/PII 不进 prompt/日志；最小权限；出网白名单 |
| 许可/IP | 来源登记；AI 生成标注；许可扫描；只借鉴机制 |
| 模型漂移 | 钉住模型/prompt；升级跑回归 |
| 成本失控 | 单任务 token/金额/时长上限，超限即停 |
| 过度自动化 | 抽样/停止开关/关键路径签字 |

## 指标

返工率 <15%；缺陷逃逸 P0/P1；幻觉率 <5%；Human 推翻率 5–15%；单任务成本；handoff 完整率 >95%。先采两项，避免刷分。

## 分阶段

| 阶段 | 主产出 | 门 | 停止条件 |
|---|---|---|---|
| 文档 | PRD/TDD/ADR | Research + Design | 无源断言 = 0 |
| 原型 | 可玩切片 | Tech + Human 试玩 | 帧率/输入延迟达标 |
| 生产 | 系统与内容 | Code + 每日构建 | 缺陷密度达标 |
| 美术 | 风格化资产 | Art Lead + 许可 | 风格测试通过 |
| QA | 用例与回归 | Release | P0 = 0 |
| LiveOps | 活动与平衡 | Human + 回滚演练 | 回滚 <30 分钟 |

## 反模式

巨型 AGENTS.md；自审自合并；LGTM 空评审；粘贴当同步；同模型互审附和；无 handoff；无预算自主循环；把网页当指令；拿生成数字填 baseline；有自动化无回滚；把指标当 KPI 刷分。

## 来源

- https://agents.md/
- https://google.github.io/eng-practices/review/
- https://conventionalcomments.org/
- https://docs.github.com/en/pull-requests/reference/pull-request-reviews
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- https://genai.owasp.org/llm-top-10/
- https://www.nist.gov/itl/ai-risk-management-framework
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://adr.github.io/
- https://dora.dev/guides/dora-metrics/
- https://spdx.dev/

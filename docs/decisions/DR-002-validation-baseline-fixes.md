# DR-002 — 技术验证后的基线修正请求

- 状态：**approved 2026-10-18（D1–D6 全部按推荐值）**
- 日期：2026-10-18
- 提出人：Lead / Orchestrator
- 关联：`validation/REPORT.md`、`validation/review/REVIEW.md`、TASK-060/061/062/063
- 风险级别：高（相机/输入/联网基线）

## 1. 背景

三路模型级验证（相机、完美格挡/延迟补偿、键盘组合）和独立复核完成：

- 相机：**pass（模型级）**；几何/公式可复现，但 docs 有 3 处基线冲突（B1–B3）。
- 联网：**conditional**；模型可复现，但 100ms 在线窗口 + 1 tick 容差误判 5.7% > 5%，且 docs 的容差/人群口径未定义（B5，M1/M2）。
- 键盘：**conditional（硬件证据不足）**；矩阵/解析器可复现，但经典布局 C+X 防御 vs Z+X+C 必杀被抢判（B4），且没有真实键盘数据（B6）。

独立复核共 6 blocker / 5 major / 9 minor；结论是 **不能写 “validation passed”**，也不能在未决策前进入 M0。详见 `validation/review/REVIEW.md`。

## 2. 决策清单

| # | 决策 | 推荐值 | 证据 | 影响文件 |
|---|---|---|---|---|
| D1 | 相机角色高度口径 | **有效剪影高度 H_eff=1.8m（含帽/武器）**；70–90px 只对默认 size 8 / pitch 50° / 1.0× 成立（78.1px）；size9@50=69.4px、size6@50=104.1px | camera metrics.csv / REPORT §3.1 | docs/00 §3.1、docs/02 §3.1、docs/04 §4 |
| D2 | 相机 yaw | **yaw=45°**，与 pitch=50° 一起写入基线；世界 X/Y 战斗轴相对屏幕为对角 | camera REPORT §3.3/§5.1；docs/docs/_drafts 0°/45° 冲突 | docs/00 §3.1、docs/03 §3.3、ADR-002 |
| D3 | 14m 可读性 | **默认选 B**：14m 只做边缘指示器/小地图，剪影识别验收只覆盖 6/10m；若必须 14m 入屏，选 A：camera anchor ≥0.765（全身+24px）/≥0.670（脚点），后方只剩约 4.9/6.9m。20/30m 用公式 `S ≥ d·sin(pitch)`（p50 约 17/26），不写死 15/23 | camera REPORT §3.3/§5.2/§5.3 | docs/02 §3.1、docs/00 §3.1、ADR-002 |
| D4 | 经典布局 C+X 防御 vs Z+X+C 必杀 | **C+X 防御仅在 Z 未按住时成立；Z 按住时 Z+X+C 必杀优先**（候选 `z_suppresses_guard`）。同时统一 C+X 窗口为 **±50ms（3f）**，并写明“两键需同时按住、闭区间” | input REPORT §4.4/§6；REVIEW B4/M4 | docs/00 §4.2、docs/02 §3.2–§3.4、docs/03 §4.1/§4.3 |
| D5 | 完美格挡在线验收 | **在线 150ms；本地/离线 100ms；防御交互 cap 200ms；服务器容差 0.5 tick（30Hz≤16.7ms/60Hz≤8.3ms）；输入缓冲 2 帧；必须用 ClientTimeMs + defender-favoring，禁止按到达时间判**。验收人群：训练有素 σ=25ms；误判 ≤5%；100ms 在线不上线 | netcode REPORT §0/§3/§6；REVIEW B5/M2/M5 | docs/02 §4.3、docs/03 §5.4、docs/07 REQ-CBT-002/TECH-002/QA-003 |
| D6 | 真实键盘 QA | **人类执行 3 款键盘（NKRO/6KRO/薄膜）×100 次组合成功率 ≥99%**，用 `validation/input/manual_test.html`；AI 不能替代；未做前 TASK-062 只算模型级完成 | input REPORT §5/§8；REVIEW B6 | docs/_qa、docs/07 TASK-062/QA |

## 3. 选项

| 选项 | 说明 | 优点 | 缺点 |
|---|---|---|---|
| A. 全部按推荐值批准（推荐） | D1–D6 一次性写入基线 | 关闭 5 个 docs blocker；可进入 M0 | 相机/联网基线变更，需 ADR-002/008 复访 |
| B. 部分批准 | 逐项改 | 可控 | 文档仍多口径，M0 验收不可执行 |
| C. 保持现状 | 不改 docs | 不改基线 | 6 blocker 保持 open，不能进入 M0 |

## 4. 影响

- **相机**：D1–D3 属相机基线变更，按 AGENTS §9 需 ADR-002 复访 + Human；若选 14m camera lead，需同步 TDD/美术/关卡。
- **输入**：D4 属经典布局优先级变更，需 ADR-004 复访；±50ms 与 3f 输入缓冲对齐。
- **联网**：D5 的 cap 150→200、0.5 tick 容差、60Hz 排位默认属联网基线/成本变更，需 ADR-008 复访；M0 引擎实测后才能确认 Fusion 可达。
- **QA**：D6 需要 Human/QA 物理键盘时间；AI 只能提供工具与脚本。

## 5. Human 决定

- D1：**approved** —— 1.8m 有效剪影；70–90px 仅默认 size8/pitch50/1.0×。
- D2：**approved** —— yaw=45°、pitch=50°。
- D3：**approved** —— 14m 用边缘指示器/小地图；剪影验收只覆盖 6/10m；20/30m 用公式（p50 约 17/26）。
- D4：**approved** —— Z 按住时 C+X 防御让位、Z+X+C 必杀优先；C+X 统一 ±50ms（3f）。
- D5：**approved** —— 在线 150ms、本地 100ms、防御 cap 200ms、容差 0.5 tick、输入缓冲 2 帧；100ms 在线不上线。
- D6：**approved** —— 人类 QA 用 `validation/input/manual_test.html` 跑 3 款键盘 ×100 次；B6 由 QA 执行后关闭。
- 日期：2026-10-18
- 备注：批准值按推荐值；已同步 `docs/00/02/03/04/07` 与 ADR-002/004/008 复访；REVIEW B1–B5 关闭，B6 仍 open（真实键盘 QA 未执行）。

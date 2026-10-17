# Project Hot

> 2.5D 俯视角、全键盘 ZXCV、装备驱动的像素动作 MMO。原创 IP；PC/Steam 优先。

当前阶段：**文档与规范阶段**。不写游戏代码、不做可玩 Demo、不生产最终美术资产。

---

## 文档索引

| 文档 | 内容 |
|---|---|
| [AGENTS.md](AGENTS.md) | 所有 AI agent 的入口：角色、权限、流程、门禁、handoff |
| [docs/00-设计基线与术语](docs/00-设计基线与术语.md) | 单一事实源：愿景、2.5D/全键盘基线、数字、术语、决策日志 |
| [docs/01-竞品调研与机会分析](docs/01-竞品调研与机会分析.md) | 2.5D 俯视动作 MMO 竞品、矩阵、失败模式、机会 |
| [docs/02-产品设计文档](docs/02-产品设计文档.md) | PRD：相机、全键盘、战斗、装备、MMO、商业化、路线图 |
| [docs/03-技术设计文档](docs/03-技术设计文档.md) | TDD：Unity、输入、2.5D 联网、后端、数据、部署、成本、测试 |
| [docs/04-3D像素美术风格指南](docs/04-3D像素美术风格指南.md) | 斜俯视剪影、参数、管线、预算、风格测试 |
| [docs/05-关键决策记录（ADR）](docs/05-关键决策记录（ADR）.md) | 12 条架构决策索引 |
| [docs/06-AI原生开发与多Agent协作规范](docs/06-AI原生开发与多Agent协作规范.md) | 角色、生命周期、交接、评审、门禁、AI 风险、指标 |
| [docs/07-需求与决策追踪矩阵](docs/07-需求与决策追踪矩阵.md) | REQ ↔ 设计 ↔ 任务 ↔ 测试 ↔ 验收 |
| [docs/metrics.md](docs/metrics.md) | AI 原生研发指标：handoff/返工/幻觉/成本 |
| [docs/backlog.md](docs/backlog.md) | 人读任务看板 |
| [docs/tasks.json](docs/tasks.json) | 机器可读任务/owner/写域/依赖/handoff/评审 |
| [docs/handoffs/INDEX.md](docs/handoffs/INDEX.md) | handoff 索引与豁免清单 |
| [skills/multi-agent-delivery/SKILL.md](skills/multi-agent-delivery/SKILL.md) | 多 agent 防重复/防冲突/可交接 skill |
| [scripts/check-agent-work.ps1](scripts/check-agent-work.ps1) | 任务/写域/handoff/评审强制检查 |
| [validation/REPORT.md](validation/REPORT.md) | M0-lite 技术验证汇总：相机/联网/键盘，conditional go |
| [validation/review/REVIEW.md](validation/review/REVIEW.md) | 技术验证独立复核（6B/5M/9m） |
| [docs/decisions/DR-002](docs/decisions/DR-002-validation-baseline-fixes.md) | 验证后基线修正 D1–D6（pending Human） |
| [docs/_qa/qa-report.md](docs/_qa/qa-report.md) | 全键盘/文档 QA 报告 |
| [docs/_review/](docs/_review/) | 独立评审报告 |
| [docs/runs/](docs/runs/) | Agent 运行记录与复盘 |

---

## 阅读顺序

1. `AGENTS.md`
2. `docs/00-设计基线与术语.md`
3. 按角色读 `docs/01`–`docs/07`
4. `docs/tasks.json` + `docs/backlog.md` 领取任务；多 agent 任务先读 `skills/multi-agent-delivery/SKILL.md`
5. 模板：`docs/_templates/`；写完跑 `scripts/check-agent-work.ps1`

---

## 关键决策

- **2.5D 俯视角**：3D 低多边形 + 像素贴图；固定 45–55° 正交斜俯视；X/Y 平面战斗；Z 轴仅跳跃/击飞/高低差。
- **全键盘 ZXCV**：默认经典英豪布局；鼠标不参与战斗/镜头；UI 键盘可完成。
- **装备 = 招式**：武器原型 + 战斗核心 + 防具 + 符文 + 外观；不做固定职业。
- **MMO 结构**：城镇 + 频道 + 4/8 人副本 + 1v1/3v3/8 人竞技场；不做无缝大世界。
- **公平付费**：F2P + 外观/战令/创始人包；不卖属性。
- **技术**：Unity 6.3 LTS + URP；Fusion 2 Server Mode；30Hz + 预测 + 200ms 回放；Nakama/PostgreSQL/Redis/Agones。
- **AI 原生**：**1 名 Human Architect/Decision-maker + AI agent swarm + 按需外包**；技术侧 token 不设上限；不再以 12–18 FTE 为技术基线；AI 执行为主 + 独立 agent 评审 + 高风险 Human 门。
- **多 Agent 保障**：`docs/tasks.json` 单写任务/写域；一个文件一个 writer；done 必须有 handoff/评审；`scripts/check-agent-work.ps1` 强制检查重复 ID、写域冲突、依赖、handoff、review。

---

## 当前状态

- [x] AGENTS.md / 模板 / 目录
- [x] docs/00 基线
- [x] docs/01 竞品
- [x] docs/02 PRD
- [x] docs/03 TDD
- [x] docs/04 美术
- [x] docs/05 ADR（12 条）
- [x] docs/06 协作规范
- [x] docs/07 追踪矩阵
- [x] docs/metrics / backlog / QA 报告
- [x] 独立评审 REV-001–004（2/6/7/2 blockers；结构问题已修，报告在 `docs/_review/`）
- [x] Human 确认 AI-native 执行/成本模型（1 Human + AI agents + 外包；token 不设上限）
- [x] 多 Agent 保障落地：`docs/tasks.json`、handoff 索引、skill、强制检查器（当前 37 任务检查通过）
- [x] 技术验证 M0-lite：相机 pass（模型级）、联网 conditional、键盘 conditional；**不是 validation passed**
- [ ] open blockers：REVIEW B1–B6 / DR-002 D1–D6、M0 引擎/键盘实测、赛季产能、REV-001 M-1/M-3、DR-001 items 1–13
- [ ] run log 复盘完成（open blocker 关闭后）

---

## 下一步

1. Human 批准/修改 DR-002 D1–D6；批准后更新 `docs/00/02/03/04/07`，复访 ADR-002/004/008。
2. M0 引擎验证：URP 相机/78px/6·10·14m；Fusion 2 格挡矩阵（C1/C2 负对照）；3 款键盘人工 QA。
3. M0 原型：战斗、联网、美术风格测试、后端骨架。
4. 关闭 REVIEW B1–B6、DR-001 items 1–13、赛季产能后，再把 `docs/00`–`docs/07` 从 `draft` 更新为 `reviewed`。

# Project Hot

> 2.5D 俯视角、全键盘 ZXCV、装备驱动的像素动作 MMO。原创 IP；PC/Steam 优先。

当前阶段：**Unity 客户端原型 + 模块化美术管线**。`mvp/` Web 原型已可玩；Unity U0（Arena/相机/键盘/KayKit 占位动画）已构建并通过人工手感测试；模块化纸娃娃（统一基础身体 + 装备槽 + UGC 纹理）进入设计/原型（ADR-013/TASK-081）；Fusion 2 与最终美术资产尚未开始。

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
| [docs/05-关键决策记录（ADR）](docs/05-关键决策记录（ADR）.md) | 13 条架构决策索引（含 ADR-013 纸娃娃） |
| [docs/06-AI原生开发与多Agent协作规范](docs/06-AI原生开发与多Agent协作规范.md) | 角色、生命周期、交接、评审、门禁、AI 风险、指标 |
| [docs/07-需求与决策追踪矩阵](docs/07-需求与决策追踪矩阵.md) | REQ ↔ 设计 ↔ 任务 ↔ 测试 ↔ 验收 |
| [docs/08-Unity客户端与Steam发布路线](docs/08-Unity客户端与Steam发布路线.md) | 正式 Unity 6.3 + Fusion 2 + Steam 路线；Web MVP 仅原型 |
| [docs/09-角色与模块化装备系统](docs/09-角色与模块化装备系统.md) | 纸娃娃/基础模型/装备槽/共享动画/UGC 纹理架构 |
| [client-unity/README.md](client-unity/README.md) | Unity 6.3 工程/U0 构建说明（可直接打开） |
| [docs/_research/camera-relative-movement.md](docs/_research/camera-relative-movement.md) | 2.5D 固定相机移动方向调研与修复记录 |
| [docs/art/README.md](docs/art/README.md) | 美术资源管线、风格圣经、AI 提示词库、动作规格 |
| [art/generation/README.md](art/generation/README.md) | AI 美术生成请求/收件；含需要 Human 的 API 介入 |
| [docs/_research/ai-pixel-art-tools.md](docs/_research/ai-pixel-art-tools.md) | 像素 AI 工具/免费资源调研 |
| [docs/metrics.md](docs/metrics.md) | AI 原生研发指标：handoff/返工/幻觉/成本 |
| [docs/backlog.md](docs/backlog.md) | 人读任务看板 |
| [docs/tasks.json](docs/tasks.json) | 机器可读任务/owner/写域/依赖/handoff/评审 |
| [docs/handoffs/INDEX.md](docs/handoffs/INDEX.md) | handoff 索引与豁免清单 |
| [skills/multi-agent-delivery/SKILL.md](skills/multi-agent-delivery/SKILL.md) | 多 agent 防重复/防冲突/可交接 skill |
| [scripts/check-agent-work.ps1](scripts/check-agent-work.ps1) | 任务/写域/handoff/评审强制检查 |
| [mvp/README.md](mvp/README.md) | **可玩 MVP**：2.5D 键盘竞技场（Node 30Hz + SSE + Canvas） |
| [mvp/PLAYTEST.md](mvp/PLAYTEST.md) | 10 分钟双开试玩清单 |
| [validation/input/hardware-qa/README.md](validation/input/hardware-qa/README.md) | B6 3 款键盘人工 QA 包（kit ready） |
| [mvp/review/REVIEW-FOLLOWUP.md](mvp/review/REVIEW-FOLLOWUP.md) | MVP 独立复评：0 blocker / 0 major |
| [mvp/screenshots/mvp-demo.png](mvp/screenshots/mvp-demo.png) | MVP 截图 |
| [validation/REPORT.md](validation/REPORT.md) | M0-lite 技术验证汇总：相机/联网/键盘，conditional go |
| [validation/review/REVIEW.md](validation/review/REVIEW.md) | 技术验证独立复核（6B/5M/9m） |
| [docs/decisions/DR-002](docs/decisions/DR-002-validation-baseline-fixes.md) | 验证后基线修正 D1–D6（approved 2026-10-18） |
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
- **纸娃娃/模块化角色**：统一基础身体 + 共享骨架/动画 + 头发/衣服/武器/披风等独立槽；玩家只替换固定 UV 纹理，不改几何；不做“每套造型一套完整角色/动作”。
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
- [x] docs/05 ADR（13 条，含 ADR-013 纸娃娃）
- [x] docs/06 协作规范
- [x] docs/07 追踪矩阵
- [x] docs/metrics / backlog / QA 报告
- [x] 独立评审 REV-001–004（2/6/7/2 blockers；结构问题已修，报告在 `docs/_review/`）
- [x] Human 确认 AI-native 执行/成本模型（1 Human + AI agents + 外包；token 不设上限）
- [x] 多 Agent 保障落地：`docs/tasks.json`、handoff 索引、skill、强制检查器（当前 42 任务检查通过）
- [x] 技术验证 M0-lite：相机 pass（模型级）、联网 conditional、键盘 conditional；**不是 validation passed**
- [x] DR-002 D1–D6 已批准；docs/00 v0.4.0（含 ADR-013 纸娃娃）、ADR-002/004/008 已复访
- [x] Web 可玩 MVP：`mvp/`（双开多人、全键盘、服务器权威；15/15 测试）
- [x] MVP 独立评审：[REV-071](mvp/review/REVIEW.md) + [follow-up](mvp/review/REVIEW-FOLLOWUP.md)：0B/0M/4 minor
- [x] Unity U0：`Arena` 场景 + Windows 构建 + KayKit 占位角色/10 动作 + 相机相对移动/双击跑（人工手感通过）
- [ ] Unity 模块化纸娃娃（TASK-081：4 槽 + 本地 UGC 测试已通过；缺真实 base_body/hair/top；ADR-013）
- [x] U1a Hot.Sim 纯 C# 战斗核心：30Hz/4 核心/防御/必杀；`SimChecks` 18 PASS
- [x] U1b Unity 表现层接线：`CombatSimBridge` 驱动伤害/资源/HUD/木桩；PlayerMotor 只留移动/动画
- [ ] U2 Fusion 2 / U3 Steam 构建
- [ ] open blockers：B6 真实键盘 QA（TASK-066，kit ready 等人工）、M0 引擎实测、赛季产能、REV-001 M-1/M-3、DR-001 items 1–13
- [ ] run log 复盘完成（open blocker 关闭后）

---

## 下一步

1. 做 **TASK-081 模块化纸娃娃原型**：基础身体 + hair/top/weapon 3 槽 + 共享 10 动作 + 1 槽 UGC 纹理；见 [docs/09](docs/09-角色与模块化装备系统.md)。
2. 用 [request-modular-avatar-01](art/generation/request-modular-avatar-01.md) 生成 **base_body + 单件装备**，不再生成整只角色。
3. Fusion 2 双人房/Steam 构建；关闭 B6、DR-001 items 1–13、赛季产能后，把 `docs/00`–`docs/07` 从 `draft` 更新为 `reviewed`。

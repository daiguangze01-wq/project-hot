# REV-002 — 红队评审报告

> Reviewer 不得直接修改源文件；作者负责修复。
> 评审方式：只读 + 对抗性假设 + 数字复算 + 证据核对。没有运行代码/Playtest；没有看到 Human 批准记录；外部事实只核对了 Hytale 美术管线、Unity 6.3 LTS、Photon Fusion 定价三条关键来源。

## 1. 元信息

| 项 | 值 |
|---|---|
| REVIEW | REV-002（红队） |
| TASK | TASK-031 |
| 评审对象 | `AGENTS.md`、`docs/00`–`docs/07`、`ADR-001`–`ADR-012`、`docs/backlog.md`、`docs/metrics.md`、`docs/runs/RUN-20261017-01-docs.md`、`docs/_qa/qa-checklist.md`、`docs/_review/reviewer-brief.md` |
| Reviewer | Reviewer B（红队，独立于作者） |
| 日期 | 2026-10-17 |
| 结论 | **blocked**（6 blocker / 18 major / 8 minor） |
| 评审限制 | 文档阶段，无可执行原型；未做玩家测试/压测/供应商报价；未看到 Human 批准记录；未把 `_drafts` 草稿当事实源 |

> 命名说明：按任务要求输出 `REV-002-red-team.md`；但 `docs/07 §8` 目前把 REV-002 分配给 docs/01、REV-005 分配给 docs/04，评审 ID 冲突本身是 B5 的一部分。建议 Orchestrator 统一重编号（例如本报告为 REV-007）并更新矩阵。
>
> 事实抽查：Hytale 美术管线链接可打开（2025-12-22）；Unity 6.3 LTS 官方页存在；Photon Fusion 定价页可打开。未发现这三条关键来源被编造；但成本/房间上限/许可仍未形成决策级证据（B6/M7）。

## 2. 结论摘要

- 文档的结构、术语、约束意识明显高于一般 pre-production 文档；但**最关键的三个决策还没有决策级证据**：2.5D/全键盘是否保留读招、30Hz+200ms 是否支撑 100ms 完美格挡、10k CCU 是否能覆盖 12–18 人团队。
- 6 个 blocker 中，4 个是硬矛盾/不可执行，2 个是阶段门禁证据缺失。
- 18 个 major 集中在：高度/空中判定、锁定/防御锥、装备平衡与新手门槛、+10 强化与“横向成长”的冲突、PvP 时长/房间口径、键盘 UI/IME、经济账本/拍卖、容量成本、资产预算、动画/管线、GTM/法律、范围/团队、M0–M4 门禁、AI 评审独立性/指标。
- 若只能先修 5 件事：B1 可读性验收、B3 商业模型、B2 完美格挡时序、B4 输入契约、M14 范围/团队（第三杀手）。
- 结论：**不允许合并/定稿**；先修 blocker，补证据，再复评。

### 2.1 最可能杀死项目的三个风险

1. **核心玩法前提没有被可证伪地验证**（B1/B4）：2.5D 斜俯视 + 全键盘能否保留英豪的读招/防御/连段，目前只有断言和一套数学上不可执行的可读性验收。若 M0 只验“能连段/能击杀”，不验“看得清/防得住/愿意继续玩”，团队可能在 6–12 个月后才发核心不成立。
2. **单位经济在计划规模下不闭合**（B3）：1.0 目标 10k CCU，按文档自己的成本/抽成/付费假设，净收入约 $50k–$70k/月，而月成本 $250k–$420k；只有 50k CCU 情景（$875k 毛收入）能覆盖。没有 50k CCU 的获客计划/预算。
3. **范围/团队/时间不匹配**（M14）：12–18 FTE、18–24 个月，要交付 MMO 城镇/频道、4 副本/5 Boss/30 敌人/70 任务/80 外观、12 核心/8 武器/20 防具、自定义经济/拍卖/账本、匹配/MMR/赛季、反作弊、多区、LiveOps（10 周 1 副本/1 PvP 图/20 外观/1 核心）；团队表只有 1 后端、1 联网、1 QA，没有专职 DevOps/SRE/安全/数据/音频/UI/本地化/客服；社区仅 1 人兼 QA。没有缓冲。

## 3. 问题清单

### 3.1 Blocker

#### B1 — 10/20/30m 可读性验收与 7–9 正交相机在数学上不可执行

```text
SEVERITY: blocker
LOCATION: docs/00 §3.1；docs/02 §3.1；docs/04 §4/§10
ISSUE: 可读性验收距离基本超出固定正交相机的有效视口（30m 必然；20m 仅极端角落可能可见），M0/M1 的美术/可读性门禁无法稳定执行；且 PRD 与美术指南的通过阈值不一致。
EVIDENCE:
- docs/00 §3.1 定死正交尺寸 7–9；16:9 下可见半宽约 12.4–16m、半高 7–9m；45–55° 斜视下地面半深约 8.5–12.7m，屏幕对角线最远角约 15.9–20.4m。
- docs/02 §3.1 要求 10m ≥90%、20m ≥80%、30m ≥70%；30m 目标在发货相机下必然在屏幕外，20m 只在极端角落可能可见，10m 在 size 7 时也已接近/越过近边。测试无法稳定执行，或只能用另一套相机，无法验证发货配置。
- docs/04 §10 又把通过标准写成“80% 测试者 1 秒内识别自己/敌人/预警”，与 PRD 的 10m ≥90% 不一致。
- 这不是“再测一次”的问题，而是验收口径本身不可执行；M0 美术/可读性门禁因此无法判定。
FIX:
- 把可读性改为屏幕空间指标（角色/预警在 1080p 下的像素高度、对比度、轮廓可辨率），并锁定发货相机；
- 若坚持世界距离，把测试距离改到视口内（如 6/10/14m），或把正交尺寸/相机改为可覆盖 20/30m 的配置（并走 ADR-002 复访）；
- 统一 docs/00/02/03/04 的阈值（10m 90% vs 80%），写明样本量、测试协议、置信区间；
- 先做 1 周相机/可读性 spike，再进入 M0 美术量产。
STATUS: open
```

#### B2 — 100ms 完美格挡与 30Hz tick + 200ms 回放 + 2–3 帧输入缓冲的时序冲突

```text
SEVERITY: blocker
LOCATION: docs/00 §3.4/§3.5/§10；docs/03 §4.1/§4.3/§5.1/§5.4
ISSUE: 核心防御机制（完美格挡 100ms）的窗口小于网络回放/输入缓冲的时序误差；服务器只回放受击盒、不回放防御输入时，防御者按“屏幕上看到的命中”操作会被判晚；若连防御状态一起回放，则攻击者会被“命中后才按的防御”挡掉。两种都不公平。
EVIDENCE:
- 完美格挡窗口 100ms（docs/00 §3.4/§3.5：受击前 100ms，1f startup，6f active）；防御 startup 2f=33ms。
- 网络：30Hz tick（33.3ms）、60Hz 子步、客户端 60Hz 采样、输入缓冲 2–3 帧（66–100ms）、服务器命中盒回放 RTT/2+插值、上限 200ms（docs/03 §4.1/§5.1/§5.4）。
- 从攻击发生到防御输入被服务器评估的粗算：输入缓冲 66–100ms + 快照 33ms + 插值 33–66ms + RTT/2（80ms RTT 时 40ms）≈ 172–239ms，已经大于 100ms 的完美格挡窗口；若按 60Hz 输入缓冲（33–50ms），仍约 139–206ms；150ms RTT 时更差。
- 200ms 回放是 100ms 格挡窗口的 2 倍；30Hz 下 100ms 只有 3 个采样点，±50ms 的 C+X 组合窗只有 1.5 tick。
- M0 验收只写“100ms/2% 丢包可完成连段/防御/击杀”（docs/00 §10），没有“完美格挡成功率/防御者优势”指标，无法证明核心手感。
FIX:
- 定义“防御时序预算”：回放上限（建议 ≤100ms 或对防御交互单独 cap）、输入缓冲、服务器评估时刻；给防御者 50–100ms 的 guard grace 或 defender-favoring rewind，并明确攻击者补偿；
- 排位 1v1/3v3 默认 60Hz（而不是“可选”），或把完美格挡窗口按 tick 重新定义为 ≥150ms；
- M0 增加 0/50/100/150ms RTT × 0/1/2% 丢包的“完美格挡成功率/误判率/双方胜率”表；达不到就改网络方案/窗口，而不是只写“手感通过”。
STATUS: open
```

#### B3 — 10k CCU 目标下商业模型不闭合；三档情景只有 50k CCU 能覆盖成本

```text
SEVERITY: blocker
LOCATION: docs/00 §9.1/§9.2；docs/02 §11.1；docs/03 §13.3
ISSUE: 文档自己的成本/抽成/付费假设与 1.0 目标不匹配：按 10k CCU 推算的净收入远低于月成本；三档情景中只有 50k CCU 情景能覆盖成本，但 50k CCU 是 1.0 目标的 5 倍，且没有获客预算/发行计划。
EVIDENCE:
- 月成本 $250k–$420k；平台 30% + 税 3% 后净收入约 67%；盈亏平衡毛收入 $373k–$627k（docs/02 §11.1）。
- 5k CCU/50k MAU/3%/$25 = $37.5k 毛收入 → 净 $25.1k；缺口约 -$225k ~ -$395k。
- 20k/200k/4%/$30 = $240k 毛收入 → 净 $160.8k；缺口约 -$89k ~ -$259k。文档写“中档 20k 可能不足以覆盖成本上限”，实际连成本下限 $250k 也不够。
- 50k/500k/5%/$35 = $875k 毛收入 → 净 $586.3k；只有这一档有 +$166k ~ +$336k 盈余。
- 1.0 目标 10k CCU（docs/00 §9.2）介于 5k 与 20k 之间，毛收入约 $75k–$105k、净 $50k–$70k，远低于 $250k 成本下限。
- 成本口径还把“发行/税费”放进月成本，又在收入端扣平台 30%+税 3%，存在重复计算；无论是否重复，缺口都成立。
- 没有营销/获客预算，却要求 100k 愿望单/10k CCU（docs/00 §9.2）；50k 情景没有对应的买量/发行计划。
- 外部核对：Photon Fusion Premium Cloud 为 $0.50/CCU、最低 $1,000/月；10k CCU 仅 Fusion 一项约 $5k/月（[Fusion pricing](https://www.photonengine.com/fusion/pricing)）。这不是缺口的主因，但说明成本表低端偏乐观。
FIX:
- 重做 bottom-up P&L：人员（按地区）、外包、服务器、Fusion、支付/平台/税、营销、本地化、客服、法律、contingency；给出 18–24 个月现金流与 runway；
- 以 10k CCU 为 base case 反推“可持续团队规模/内容规模”，或明确“必须做到 30k–50k CCU 才成立”并给出获客预算/发行合作；
- 把三档情景改为“保守/基准/乐观”，每档给 CCU/MAU/付费率/ARPPU 的来源或 benchmark；不要用“示意”代替决策；
- 若数字不闭合，先改范围/团队/商业模式（不是回到卖属性），并在 Human 门记录。
STATUS: open
```

#### B4 — 输入契约无法表达 ZXCV 组合语法；全键盘核心不可实现/不可验收

```text
SEVERITY: blocker
LOCATION: docs/03 §4.1/§4.3；docs/00 §4.1/§4.3；docs/02 §3.2
ISSUE: InputFrame 只有 Tick/Sequence/MoveX/MoveY/Buttons/TargetId，没有 press/release 边沿、sub-tick 时间戳、combo buffer/priority；但设计需要 Z 轻按 vs 按住、C+X ±50ms、双击方向冲刺、C→C→C、Z+C/Z+X、Z+X+C、C 拾取 vs F 交互等语法。协议无法表达，服务器也无法按 60fps 帧数据校验。
EVIDENCE:
- docs/03 §4.1 结构只有 Tick/Sequence/MoveX/MoveY/Buttons/TargetId；“客户端 60Hz 采样；发送最近 3 帧冗余；服务器按 tick 执行”与 30Hz tick 冲突：按 30Hz 执行会丢失 60fps 帧数据/取消窗口；按 60Hz 子步执行则协议必须携带每帧时间戳/边沿，当前结构没有。
- 设计需要：Z 轻按=软锁定 vs 按住=特殊技修饰（docs/00 §4.1）；C+X 同时按 ±50ms（docs/03 §4.3）；双击方向冲刺；C→C→C；Z+C/Z+X；Z+X+C；C 靠近物品拾取 vs F 交互/拾取（docs/00 §4.1 重复绑定）；C+X 防御 vs X 重击、Z+X 特殊 vs Z+X+C 必杀的优先级。
- 3 键/4 键同时按（Z+X+C+方向）与常见薄膜键盘 rollover 的关系只有一句“至少 3 键”（docs/00 §4.3，无来源）；没有键位矩阵/自动回退。
FIX:
- 把输入帧升级为 60Hz、含 Pressed/Released/Timestamp/Sequence/ComboBuffer 的结构；服务器用 60Hz 子步重放，30Hz 只做快照；
- 写一张组合优先级表（C+X > X；Z+X+C > Z+X > X；Z tap vs hold 的时间窗；双击 debounce），客户端/服务器共用；
- 删除 C 的拾取绑定（只保留 F），或改为“长按 C”并写清优先级；
- 训练场内置键盘 rollover 检测 + 自动建议/一键切换 Space 防御；给出最低键盘规格/不支持列表；
- M0 验收增加“所有经典组合在 3 款键盘（全键无冲/6KRO/薄膜）上 100 次输入成功率 ≥99%”之类的可测指标。
STATUS: open
```

#### B5 — 文档阶段门禁证据缺失：done 任务无 brief/handoff、状态冲突、REV ID 冲突

```text
SEVERITY: blocker
LOCATION: docs/backlog.md §1/§3；docs/07 §5/§8；docs/runs/RUN-20261017-01-docs.md §4/§5/§6/§8/§9；AGENTS.md §6/§14；docs/06 §10.3
ISSUE: 项目自己的硬规则是“无 brief 不开工、无 handoff 视为未完成、100% 任务有 brief+handoff、独立评审”；但 done 任务没有对应 brief/handoff，backlog/07/run log 状态互相冲突，评审 ID 也没有唯一映射。这使“blocker 清零/追踪矩阵/独立评审”的声明无法被审计，阶段 DoD 不成立。
EVIDENCE:
- backlog 将 TASK-001–045 大部分标 done；`_drafts` 只有 TASK-020/021 brief；TASK-010–015 的 brief 被指向 `_drafts/TASK-*-brief.md`，不存在；没有任何 `TASK-*-handoff.md`；run log §9 却把它们列为附件。
- TASK-004/005 产出 `_research/competitor-2.5d.md`/`art-2.5d.md` 不存在；backlog 标 done，docs/07 标 pending，run log 标 running。
- TASK-003 backlog done vs docs/07 in_progress；RUN-20261017-01 仍 in_progress，§4 输出 done、§5 评审 pending、§6 成本“待统计”、§8 复盘“待填”。
- docs/07 §8 把 REV-002 分给 docs/01、REV-005 分给 docs/04；本红队报告按任务用 REV-002，ID/范围冲突。
FIX:
- 为 TASK-010–015 补 brief + handoff（可追溯作者/输入/评审/成本），或把状态改回 partial 并说明；
- 补齐 TASK-004/005 产出或改状态/产出路径；统一 backlog/07/run log 状态；
- 给本报告分配唯一 REV ID（建议 REV-007）并更新 docs/07 §8；
- 完成 RUN-20261017-01 的成本/复盘/评审记录；
- 在 Docs Gate 加“claim vs artifact”检查（每个 done 任务必须有 brief/handoff/产出文件/评审链接），CI 可自动检查。
STATUS: open
```

#### B6 — 12 条 ADR 标 accepted，但无 Human 批准记录；关键成本/上限/许可仍“待核实”

```text
SEVERITY: blocker
LOCATION: docs/decisions/ADR-001–012；docs/00 §13；docs/05 §1；docs/03 §13.3；AGENTS.md §9；docs/06 §8.2
ISSUE: 引擎/联网/数据模型/美术路线都是不可逆或高影响决策，项目规则要求 Human 批准；但 12 条 ADR 全部 accepted，没有 decision memo、批准时间、批准范围、反对意见/回滚；同时 Fusion 定价/房间上限、Unity 6.3 许可、国服版号、美术风格测试仍列为“待核实”。这是“未验证事实之上的已接受决策”，治理门不可执行。
EVIDENCE:
- ADR-007/008/009/010 状态 accepted，日期均为 2026-10-17，决策者写“Human Owner + Orchestrator”或“Tech Lead + Human”，但没有批准记录/链接。
- docs/00 §13 把 Fusion 2 最新定价/房间上限、Unity 6.3 LTS 许可与 2026 定价、目标地区版号、美术风格测试列为“待核实”；docs/03 §13.3 成本“假设，需报价核实”。
- docs/00 §13 的“已确认（Human）”没有证据链接；docs/06 §8.2 要求引擎/联网/数据模型/商业化/ADR 变更由 Human 批准。
FIX:
- 把受未核实事实影响的 ADR 标为 proposed/conditional accepted，写清“依赖的待核实项/验证 spike/失败触发/迁移预算”；
- 为每条高风险 ADR 补一页 decision memo（选项/成本/回滚/建议/批准人/日期），Human 签字；
- 在 M0 前完成 Fusion 报价+房间上限/50 人频道压测、Unity 许可确认、美术风格测试；未通过则复访 ADR；
- docs/00 §13 的“已确认”改为带链接的批准记录，否则删除“已确认”。
STATUS: open
```

### 3.2 Major

> 以下每条 `SEVERITY: major`；`STATUS: open`。

| ID | Location | Issue | Evidence | Fix | Status |
|---|---|---|---|---|---|
| M1 | docs/00 §3.2；docs/02 §4.3；docs/03 §5.2/§5.4；docs/04 §6 | 高度/空中/地形判定模型缺失：只有“地面/空中两态”与“capsule/cylinder + 高度状态”，没有高度阈值、受击盒垂直范围、空中/地面互相命中规则、重力/落地/边缘、地形高度数据；PvP 地图有高低差，但 TDD 无地形高度/nav 表示。跳跃是否躲地面攻击、空中追击 1–2 段的判定条件未定义。 | docs/00 §3.2；docs/02 §4.3；docs/03 §5.4；docs/03 §5.3 hitbox JSON 有 height 1.4/offset z 1.2，但没有状态/高度带。 | 写高度状态机（Ground/Air/Juggle/Land）+ 每状态 hurtbox 垂直范围 + 攻击高度带（low/mid/high/air）+ 地形高度采样/nav + 边界/坠落规则；给 2.5D 判定测试用例（跳躲地面、空中命中、高低差、桥/悬崖）；M0 原型验证。 | open |
| M2 | docs/00 §5；docs/02 §4.6/§5.6/§6；ADR-005 | 装备=招式的平衡/新手门槛没有可测目标：12 核心 × 8 武器 × 20 防具 × 2 符文；PvP 归一化 ±5% 但机制保留；“没有必选核心”只是口号，没有 pick/win-rate 目标、matchup 矩阵、power budget、ban/pick 或赛季调参方法；新手只有 15 分钟教程/3 场 AI/推荐 Build，没有租用/试用细节。 | docs/02 §5.6；§4.6；§10；ADR-005 follow-up 说“1.0 前做租用核心/训练场”，但 PRD 无系统设计。 | 定义 power budget、matchup 矩阵、目标 pick/win-rate 带（如 45–55%、top pick <20%）、赛季调参流程；把租用/试用 Build 写成可验收系统；M1/M2 用 telemetry + 模拟验证；新手门槛用 D1/D7 分群验证。 | open |
| M3 | docs/02 §5.4/§6；docs/00 §5.4 | +10 强化/装备评分与“横向成长/不卖属性”冲突：+0–+10 仍是垂直数值；角色有 gear_score，副本有装备评分门槛；10 套 PvE+10 套 PvP/赛季防具；传说给独特机制。PvP 归一化只覆盖 PvP，PvE 仍是数值 treadmill；“收集为了表达，不为数值碾压”与 +10/评分门槛矛盾。 | docs/02 §5.4“+0–+10”；§6“装备评分/主线/副本门槛”；docs/00 §5.4；docs/00 §1“公平长线”。 | 明确 PvE 垂直上限/软门槛；把强化改为横向（外观/机制/套装选择）或严格 cap 且不影响门槛；去掉 gear_score 硬门槛，改用机制/熟练度；做玩家感知测试，明确“不卖强度”。 | open |
| M4 | docs/00 §2/§8；docs/02 §2/§7.4/§8.4/D7；docs/03 §1.2/§13.2 | PvP 时长/房间容量口径矛盾：单局 3–5 分钟 vs 10 分钟/局；PvP 房间 8–16 vs 模式 1v1/3v3/8FFA（最大 8）且 D7 明确不做 8v8；容量模型用 16 人房，实际 8 人房会把房间数/服务器成本翻倍。 | docs/00 §2；docs/02 §8.4“10 分钟/局”；docs/03 §1.2“PvP 8–16”；docs/02 D7“3v3 + 8FFA，不做 8v8”；docs/03 §13.2“441 房=10k×60%/(16×85%)”。 | 按模式定义时长（1v1 3–5、3v3 5–8、8FFA 8–10）和房间容量（2/6/8），更新 docs/00/02/03；容量模型用实际房型重算；若保留 16 人房，补 8v8 模式/PRD 变更。 | open |
| M5 | docs/00 §4.1/§4.3；docs/02 §10；docs/03 §14.1 | 键盘-only UI/聊天/拍卖/IME/重复拾取没有设计：断言“UI 键盘可完成”，但没有焦点模型、Tab 顺序、搜索/筛选、聊天输入/IME、拍卖行大量列表的键盘操作；C 既轻击又拾取，F 也拾取；聊天输入法会触发 Z/X/C/V 战斗键；中文输入是首发 EN/CN 的硬需求，日文/KR 后置也需要 IME。 | docs/00 §4.1；docs/02 §10；docs/03 §14.1 只在测试矩阵提“输入法”。 | 写键盘 UI 规范（焦点/快捷键/搜索/分页/确认）、聊天 focus 捕获/IME 组合/发送、拍卖行键盘流程；删除 C 拾取；做 10–20 人键盘-only 可用性测试；把“全键盘”加入 QA 每轮回归。 | open |
| M6 | docs/00 §3.1；docs/04 §4/§6 | 遮挡淡出在 PvP 中泄露信息：屋顶/树冠/高墙淡出、角色轮廓/影子保留；在 PvP 中会把掩体后的敌人轮廓/影子暴露，形成不公平信息；没有按模式（PvE/PvP）区分，也没有服务器视线规则。 | docs/00 §3.1；docs/04 §4/§6。 | PvP 用“只在视线内/距离内淡出”，或只淡出本地玩家附近几何；影子/轮廓按可见性裁剪；服务器 LOS 校验；做掩体测试。 | open |
| M7 | docs/03 §13.1/§13.2/§13.3；docs/00 §8；docs/03 §6.1/§18.3；ADR-008 | 容量/成本模型自相矛盾；Fusion/房间上限未验证：预算写 16 人房 <10ms/tick，示例却用 2ms/tick 得 80 房/节点；按 10ms 只有 16 房/节点，节点数约 4.5 倍；PvP 实际 8 人房会把房间数再翻倍；Fusion 官方 $0.50/CCU，10k CCU=$5k/月，文档低端 $2.5k 无依据；50 人城镇/30 人野外用 Fusion 房间还是自定义世界服仍未决。 | docs/03 §13.1/§13.2/§13.3；[Fusion pricing](https://www.photonengine.com/fusion/pricing)；docs/03 §18.3。 | 统一 per-tick 预算与房型；用 8 人 PvP/4 人 PvE/50 人城镇分别算房间/节点；Fusion 报价按 $0.50/CCU + 流量；做 50 人频道 spike；把“自定义世界服”写成备选 ADR/成本，而不是一句 open question。 | open |
| M8 | docs/03 §7.2/§8.1/§8.2 | 经济账本/拍卖 schema 不能支撑“双录账本/防复制”：`ledger_entry` 只有 wallet_id/currency/delta，像单边流水，不是双录（缺 transaction/account/debit-credit 对）；`ref_id` 只是“幂等索引”非唯一，重复请求可能重复入账；`wallet` 乐观锁版本未在表结构；`auction` 缺 escrow/lock/buyer/settlement/tax，item 可在挂单后被交易/重复挂单；`inventory` 没有 unique(item_instance_id)，同一实例可出现在多个槽/角色；`mail` 附件领取无幂等；Nakama 账号/存储与自定义 PostgreSQL 角色/账本没有边界/同步/迁移设计，存在双事实源；1 后端（docs/02 §12）同时维护 Nakama+自定义经济/拍卖/结算+K8s/Agones 不现实。 | docs/03 §8.1 表；§8.2“ledger_entry(ref_id) 幂等索引”；§7.2“双录账本”。 | 加 `ledger_transaction` + `ledger_account` + 借贷两行、sum=0 约束、唯一 idempotency key；wallet 版本列；auction escrow/lock/结算/税流水；inventory unique(item_instance_id) + owner 一致性；mail claim idempotency；对账 job/审计测试；在 Technical Gate 前把 M8 当 blocker 处理。 | open |
| M9 | docs/03 §9.2/§11/§4.4 | API/鉴权/反作弊缺口：`POST /v1/matches/{id}/result` 出现在公开 API 示例，未标 internal-only/mTLS；`GET /v1/characters/{id}/loadout` 无对象级授权；反作弊 EAC/BattlEye 仅“1.0 前评估”，没有 launch 方案；键盘宏/自动连段/脚本没有检测；输入频率/重放/序列校验没有具体阈值。 | docs/03 §9.2；§11；§4.4。 | 把 result 改为内部服务 API（mTLS/service auth），客户端不可调用；所有角色/背包接口做 object-level authz；确定 launch 反作弊（EAC/BattlEye/自研）与隐私/兼容评估；输入异常/宏检测/回放审计；渗透测试/依赖扫描进 CI。 | open |
| M10 | docs/04 §3/§9/§10；docs/02 §8.1；ADR-010 | 资产预算 60–170 人月是 3 倍区间，且漏算 80 外观/70 任务/UI/音频/本地化；2D billboard 没有被认真比较：60–170 跨 3 倍；两个独立估算 87/174 vs 28–32/60–65 未调和；数量清单 1/8/12/20/30/5/2/4/3/1 不含 80 外观、70 任务、UI、音频、本地化、市场素材；4–6 美术+30–50% 外包在高位接近满负荷；2D billboard 只有一行“便宜/8 方向贵”，没有成本/可读性对比、没有样张；ADR-010 在测试前 accepted；外包/风格一致性只有“规范/参考/验收”一句话，没有 vendor qualification/返修上限/许可登记。 | docs/04 §9；§3；§10；docs/02 §8.1。 | 用 M0 风格测试产出单位人月，bottom-up 重估；把 80 外观/70 任务/音频/本地化纳入；给 20–30% contingency；做 2 周 3D vs 2D billboard 同角色/同装备/同动作对比（成本/可读性/遮挡/换装），再决定 ADR-010 是否 conditional。 | open |
| M11 | docs/04 §1.1/§2.2/§5.1/§5.4；docs/00 §3.5；docs/03 §3.4 | 动画时序/管线与 Hytale 参考不匹配：8–12fps 阶梯 + 2–4 帧预备 = 167–500ms，而攻击 startup 8–30f（133–500ms）；视觉预备可能长于判定，玩家会误读；“服务器用帧数据、不依赖动画事件”但没有动画→帧数据映射规则。Hytale 的管线是 cube/quad、无 rigging/weight painting、无 PBR 的 voxel-style；本项目要 3–8k tris/30–40 骨骼/模块化护甲/8 武器动画，不能直接照搬；文档一边以 Hytale 为主要参考，一边说“不是 voxel”。 | docs/04 §1.1/§5.1/§5.4/§2.2；docs/00 §3.5；[Hytale art pipeline](https://hytale.com/news/2025/12/an-introduction-to-making-models-for-hytale)。 | 定义动画帧→帧数据映射（预备/命中/后摇在 60fps 下的对应），把 2–4 帧预备压到 1–2 个阶梯帧或提高动画率；用 Blender/Blockbench 做 1 角色+1 武器+3 装备的管线 spike；把 Hytale 限定为“贴图/色板/剪影参考”，骨架/权重/动画走 Blender 管线。 | open |
| M12 | docs/00 §9.2；docs/02 §11/§12；docs/03 §13.3；ADR-012 | GTM/营销/本地化：100k 愿望单/10k CCU 没有预算与计划：目标 100k 愿望单/10k CCU/多区，但没有营销预算、Steam 页面/Playtest/展会/创作者计划时间表；成本表不含营销/本地化/客服/支付/发行；首发 EN/CN，核心受众含 JP/KR 英豪玩家却后置；国服后置使最大核心受众延迟/支付/社区分离。 | docs/00 §9.2；docs/02 §11/§12；docs/03 §13.3；ADR-012。 | 写 GTM 计划（Steam 页面/demo/playtest/愿望单漏斗/创作者/展会/买量预算），把营销/本地化/客服/支付成本纳入 P&L；明确首发语言/区域与核心受众匹配；国服单列时间线/预算/发行商。 | open |
| M13 | docs/00 §6.5/§13；docs/02 §11/§15；ADR-011/012 | UGC/国服/版号/法律/IP 没有工作流：UGC 市场 S2 只有“审核/税务/法律评估”，没有 moderation/IP/分成/税务/Steam Workshop 方案；国服没有发行商/版号时间线/预算；“原创 IP”没有商标检索/法律审阅/资产许可登记；AI 生成资产没有 Steam 披露/版权评估；产品一句话直接引用《热血英豪》名称，公开营销有商标/比较广告风险。 | docs/00 §6.5/§13；docs/02 §11/§15；ADR-011/012。 | 设 legal workstream（商标检索、IP clearance、UGC policy、AI disclosure、版号/发行商），在 Steam 页面/公开营销前完成；资产来源/许可登记；UGC 审核/分成/税务模型；公开文案只用机制描述，不用竞品名称做卖点。 | open |
| M14 | docs/00 §10；docs/02 §11.2/§12；docs/04 §9 | 范围/团队/时间与 MMO+LiveOps 不匹配：12–18 FTE、18–24 个月；团队表 4–5 程序（玩法 2/联网 1/后端 1/工具 1）、4–6 美术、2–3 策划、1–2 制作/运营、1 QA；没有专职 DevOps/SRE/安全/数据/音频/UI/本地化/客服，社区仅 1 人兼 QA；1.0 要 4 副本/5 Boss/30 敌人/70 任务/80 外观/12 核心/8 武器/20 防具 + 自定义经济/拍卖/账本 + 匹配/MMR/赛季 + 反作弊 + 多区 + 10 周赛季（1 副本/1 PvP 图/20 外观/1 核心）。没有资源负载/产能模型/缓冲。 | docs/00 §10；docs/02 §11.2/§12；docs/04 §9。 | 做 resource-loaded schedule（按角色/月）；要么加后端/DevOps/安全/QA/本地化，要么砍到 5–10 人版本；把 10 周赛季产能与美术/关卡/后端人力对齐；设 20–30% 缓冲；M1 前做产能审计。 | open |
| M15 | docs/00 §10；docs/02 §12；docs/03 §15；docs/04 §10；docs/06 §11.2 | M0–M4 退出标准不可验证/不一致：M0“手感通过”、M1“核心循环可玩”、M2“内容/联网/经济稳定”、M3“D1/D7 达标”没有阈值/样本/协议；M0 美术风格测试在 docs/04/backlog 是交付物，但 docs/00/02/03 的 M0 退出标准没有它；docs/06 §11.2 的 Human gate“是否进入垂直切片”不在路线图；M4“多区”无定义。 | docs/00 §10；docs/02 §12；docs/03 §15；docs/04 §10；docs/06 §11.2。 | 每个 M 写 SMART 退出标准（指标/阈值/样本/测试协议/负责人/失败动作），把战斗手感、可读性、键盘、网络、经济、反作弊、美术风格都纳入；M0 设 go/no-go + kill criteria；统一 docs/00/02/03/04/06 的门禁表。 | open |
| M16 | AGENTS.md §4/§7；docs/06 §3/§4.2/§5.6/§5.7；docs/runs §2 | AI 评审独立性/门禁所有权不可执行：Orchestrator 是 docs/00/06/07 作者、02/03 合并者、blocker 关闭者；同一角色既写又关；Reviewer A/B 由 Orchestrator 选择/给 brief；没有盲评/模型轮换/评审 prompt 记录；“0 自审自批”只靠声明。run log 显示 PRD/TDD 由 Orchestrator 合并，Reviewer 仍 planned。 | AGENTS.md §4/§7；docs/06 §4.2/§5.6/§5.7；run log §2。 | 设独立 Review Lead/QA 关闭 blocker；作者不能关闭自己文件的 blocker；Reviewer 由 Human/QA 选，盲评（不看作者 rationale），记录模型/prompt；baseline/ADR blocker 由 Human 关闭；不同模型/供应商轮换，降低同模型附和。 | open |
| M17 | docs/metrics.md §1/§2/§4；docs/06 §7.1/§8.2/§10；AGENTS.md §13 | AI 指标/上下文/人类门/自动化可刷分或不可执行：MET-008“评审问题密度趋势下降”奖励少报问题；MET-005“Human 推翻率 5–15%”把 Human 推翻当目标，可能鼓励随意推翻；MET-004 幻觉率抽 5%、无裁定标准；MET-001 handoff 完整率可靠模板填充；没有 seeded defect/外部审计。上下文 ≤5 文档/40% 窗口与本 review 需读 8 文档+12 ADR 冲突；run log 成本“待统计”，无 token/金额上限。Human 门 7 类高风险+2 类低风险、12 ADR 一天 accepted、无 decision memo/SLA，容易橡皮图章或瓶颈；AGENTS.md §13 只有手写 PowerShell，无 CI/链接检查/front matter schema/Mermaid render。 | docs/metrics.md §1/§2/§4；docs/06 §7.1/§8.2/§10；AGENTS.md §13。 | 用 seeded-defect recall/外部审计/逃逸 blocker 替代单纯计数；删除“Human 推翻率”硬目标；定义幻觉裁定与样本；按角色设上下文预算（reviewer 可跨文档），记录实际 token/成本；Human 门分级 + 一页 memo + SLA + 法务/安全独立审；加 CI（markdown lint/link check/front matter/Mermaid/ID 术语检查）。 | open |
| M18 | docs/00 §3.1/§3.4/§4.1；docs/02 §4.3；docs/03 §4.1/§5.2 | 锁定/防御锥/朝向语义未定义：Z 软锁定最近敌人（120° 锥）、防御正面 120° 锥，但没定义锁定后移动是 strafe 还是 face movement、防御时朝向由谁决定、背击 back vector 怎么算、120° 锥如何显示、多目标/高低差/遮挡时选谁；防御锥与锁定锥是两个锥，玩家难以同时读。 | docs/00 §3.1/§3.4/§4.1；docs/02 §4.3；docs/03 §4.1/§5.2。 | 写 facing/lock-on 状态表（面向目标/移动方向/最后输入）；锁定后 strafe 速度/动画；防御时朝向锁定目标或最后受击方向；背击用攻击者-防御者夹角；HUD/地面扇形显示；多目标优先级；训练场可视化；M0 测试背后攻击/防御转向/锁定切换可读性。 | open |

### 3.3 Minor

> 以下每条 `SEVERITY: minor`；`STATUS: open`。

| ID | Location | Issue | Evidence | Fix | Status |
|---|---|---|---|---|---|
| m1 | docs/02 §5.1 | “共 8 件”把外观算进功能槽：1 武器+1 核心+3 防具+2 符文+1 外观=8，但外观不是数值槽，容易让读者误以为有 8 个功能槽。 | docs/02 §5.1。 | 改为“7 个功能槽 + 外观覆盖层”，并明确外观不参与判定/掉落评分。 | open |
| m2 | docs/04 §4 | “若只算 1.5m 身体，size 7–9 下约 5–7%”口径不清/无法复算：按正交尺寸定义（未计相机俯角投影）约 8.3–10.7%；若计投影，需给出公式。 | docs/04 §4。 | 重算并写明“含/不含投影”的口径，或删除该句。 | open |
| m3 | docs/00 §1；docs/02 §5.2；docs/03 §5.2 | “霸体”术语/约束冲突：docs/00 写“不做霸体类机制特权”，docs/02 巨剑写“霸体技”，docs/03 命中优先级含“霸体”；术语表没有定义“霸体”与“不卖的霸体特权”的区别。 | docs/00 §1；docs/02 §5.2；docs/03 §5.2。 | 定义“通用霸体状态（有前摇/可破/可绕背）”与“不卖霸体特权”；或删除巨剑霸体技。 | open |
| m4 | docs/02 §11.1 | 净收入比例 67% vs 0.7×0.97=67.9% 的舍入不一致；盈亏平衡数字随之略差。 | docs/02 §11.1。 | 统一写“约 68%”或给出精确公式，并同步盈亏平衡。 | open |
| m5 | docs/01 front matter；docs/02 front matter；docs/05 front matter | 角色名不一致：`research-lead`/`product-lead` 不在 AGENTS.md 角色表；docs/05 owner 写 `tech-lead`，实际由 Orchestrator 维护。 | docs/01/02/05 front matter；AGENTS.md §4。 | 统一为 Researcher/Product Designer/Tech Lead/Orchestrator，或在 AGENTS.md 增加 lead 角色。 | open |
| m6 | docs/00 §11 | 术语表缺高频词：EA、ARPPU、MAU、CCU、P2W、UGC、I-frame、KRO/6KRO、霸体；文档正文大量使用。 | docs/00 §11；全文用法。 | 补术语表，或把缩写首次出现处展开。 | open |
| m7 | docs/01 §9；docs/02/03/04 §来源 | 来源缺访问日期/来源 ID；docs/01 来源列表末尾混入 Unity/Fusion 技术来源，与竞品调研无关；“待核实”没有与 ADR 关联。 | docs/01 §9；docs/02/03/04 来源。 | 建 source registry（URL/访问日期/用途/许可），把“待核实”映射到 ADR/decision memo。 | open |
| m8 | docs/05 §1；docs/00 §12 | ADR 索引与 docs/00 决策日志重复维护，存在双事实源漂移风险（docs/00 是单一事实源，docs/05 又维护一份状态/复访表）。 | docs/05 §1；docs/00 §12。 | 指定 docs/00 §12 为唯一索引，docs/05 只保留导航/关系图；或反过来，并加自动校验。 | open |

## 4. 需求/基线对照

| REQ | 覆盖 | 证据 | 缺口 |
|---|---|---|---|
| REQ-VIS-001/002/003 | 部分 | docs/00 §3.1/§3.2；docs/02 §3.1；docs/03 §3.3/§5.4；docs/04 §4/§6；ADR-001/002/003/010 | B1 可读性验收不可执行；M1 高度/地形；M6 遮挡 PvP；M10 美术预算/2D 对比 |
| REQ-CTL-001–004 | 部分 | docs/00 §4；docs/02 §3；docs/03 §4；docs/04 §7；ADR-004 | B4 输入契约；M5 键盘 UI/IME；M18 锁定/防御锥；rollover 无矩阵 |
| REQ-CBT-001–005 | 部分 | docs/00 §3.4–§3.6/§5；docs/02 §4–§5；docs/03 §5；ADR-005 | B2 完美格挡时序；M1 高度；M2 平衡/新手；M3 +10/评分；M18 防御锥/朝向 |
| REQ-MMO-001–005 | 部分 | docs/00 §6/§7；docs/02 §7–§8；docs/03 §6/§8/§10；ADR-006/009 | M4 时长/房间；M7 容量/Fusion；M8 账本/拍卖；M13 UGC/法律 |
| REQ-ART-001–003 | 部分 | docs/04 §4–§10；ADR-010 | B1；M10 预算/2D；M11 动画/管线；M6 遮挡 |
| REQ-TECH-001–006 | 部分 | docs/03 §2–§14；ADR-007/008/009 | B2；B6；M7；M8；M9；M10 |
| REQ-BIZ-001–003 | 部分 | docs/00 §9；docs/02 §11；ADR-011 | B3 可行性；M3 P2W 感知；M12 GTM；M13 法律/UGC |
| REQ-PROC-001–006 | 部分 | AGENTS.md；docs/06；docs/07；backlog；metrics；run log | B5 证据缺失；B6 批准；M16 独立性；M17 指标/上下文 |
| REQ-QA-001–004 | 未验证 | docs/07 §2.9；docs/_qa/qa-checklist.md | 没有 QA 报告/全键盘实测/网络矩阵结果；B5 |

## 5. 硬约束检查

| 硬约束 | 结果 | 证据/缺口 |
|---|---|---|
| 2.5D 俯视 | 部分 | 相机/平面/高度定义齐全（docs/00 §3），但 B1 可读性验收与 M1 高度/地形模型不成立。 |
| 全键盘 / 无鼠标依赖 | 部分 | 布局表齐全（docs/00 §4），但 B4 输入契约、M5 UI/IME、rollover 测试缺失；“至少 3 键”无来源。 |
| 装备=招式 | 概念通过 | ADR-005/PRD §5 清楚；但 M2 平衡/新手、M3 +10/评分门槛未证明。 |
| 不卖属性 | 原则通过，执行有风险 | 不卖属性/强化材料（docs/00 §9），但 +10/gear score/栏位便利付费可能被感知为 P2W-adjacent（M3）；需玩家沟通与审计。 |
| 原创 IP | 声明通过，证据不足 | 文档声明原创；但无商标检索/法律审阅/资产许可登记/AI 披露（M13）；公开文案引用《热血英豪》名称有风险。 |
| 服务器权威 | 原则通过，细节不足 | 输入-only/权威判定（docs/03 §2/§5/§11）；但 M8 账本/拍卖、M9 API/反作弊、M7 容量仍需补。 |
| 数字/术语一致 | 失败 | 具体矛盾：B1 10/20/30m vs 相机；B3 10k CCU vs 成本；B2 100ms vs 200ms；M4 3–5 vs 10 分钟、8–16 vs 8；M7 2ms vs 10ms/tick；M10 60–170 人月；m4 67% vs 68%。 |
| 来源/不确定项 | 部分 | 竞品/技术有来源，Hytale/Unity/Fusion 关键来源可打开；但 B6 的 accepted ADR 仍依赖“待核实”，m7 缺访问日期/来源 ID。 |

## 6. M0–M4 门禁逐条

| 阶段 | 文档中的退出标准 | 可验证? | 缺口 |
|---|---|---|---|
| M0 | 100ms/2% 丢包完成连段/防御/击杀；2 核心/1 图/2 人；键盘-only | 部分 | 没有完美格挡成功率、可读性、手感/乐趣阈值；美术风格测试不在 docs/00/02/03 的 M0 门禁（只在 docs/04/backlog）。 |
| M1 | 4 人副本/城镇/持久化；2k CCU 压测；核心循环可玩 | 部分 | “可玩”无定义；无经济对账/资产验收；2k CCU 是压测不是真实留存。 |
| M2 | 8 人 PvP/3 副本/2 PvP 模式/匹配/反作弊；内容/联网/经济稳定 | 部分 | “稳定”无 SLO；反作弊无定义；8 人 vs 16 人房口径冲突（M4/M7）。 |
| M3 | 内容完成/LiveOps/本地化；5k CCU；D1/D7 达标 | 部分 | Beta cohort 的 D1/D7 不等同 launch；支付/本地化/客服无验收；LiveOps 产能未证明（M14）。 |
| M4 | 1.0/多区；10k CCU；P0=0；回滚演练 | 部分 | “多区”无定义；10k CCU 是目标不是门禁；回滚演练无 RTO/RPO/指标。 |

## 7. 结论

- **Blocker 数：6**（B1–B6）。
- **是否允许合并：否。** 结论 `blocked`；文档阶段不能以“done”关闭，baseline/ADR 不能视为已批准。
- **复评要求（按优先级）：**
  1. B1：相机/可读性 spike + 屏幕空间验收 + 统一阈值；
  2. B3：bottom-up 财务模型 + 10k CCU base case + 营销/成本口径；
  3. B2：netcode 时序预算 + 完美格挡测试矩阵（0/50/100/150ms RTT）；
  4. B4：60Hz 输入帧/组合优先级/rollover 矩阵 + 训练场验证；
  5. B5/B6：补 brief/handoff/状态/唯一 REV ID + Human 批准记录/conditional ADR；
  6. M14：resource-loaded schedule/产能审计（第三杀手）。
- 只修文档措辞、不做原型/财务/证据的复评仍会 blocked。

## 8. Handoff

```text
TASK: TASK-031
STATUS: done
CHANGED: docs/_review/REV-002-red-team.md
SUMMARY: blocker=6 / major=18 / minor=8；verdict=blocked。
TOP5: 1) B1 可读性验收不可执行；2) B3 10k CCU 商业模型不闭合；3) B2 完美格挡 vs 30Hz/200ms；4) B4 输入契约不完整；5) M14 范围/团队/时间不匹配（第三杀手）。
DECISIONS: 无（只评审，不改源文件）；建议本报告使用唯一 REV ID（REV-007）并更新 docs/07 §8；建议 B1–B6 修复前不关闭文档阶段。
EVIDENCE:
- 只读评审：AGENTS.md、docs/00–07、ADR-001–012、backlog、metrics、run log、QA checklist、reviewer brief。
- 数字复算：B1 相机视口；B2 延迟预算；B3 三档净收入/盈亏平衡；B4 输入组合；B5 claim vs artifact；M7 容量/成本。
- 外部核对：Hytale 美术管线（HTTP 200，2025-12-22）、Unity 6.3 LTS、Photon Fusion 定价（500/1000/2000 CCU $125/$250/$500；Premium $0.50/CCU，min $1,000）。未做代码/Playtest/供应商报价。
RISKS:
- 6 blocker：B1 可读性验收不可执行；B2 完美格挡 vs 30Hz/200ms；B3 10k CCU 商业模型不闭合；B4 输入契约不完整；B5 阶段门禁证据缺失；B6 accepted ADR 无 Human 批准/关键事实待核实。
- 第三杀手：M14 范围/团队/时间不匹配（1 后端/1 联网/1 QA + 10 周赛季 + 多区/LiveOps）。
- 其他高风险：M1 高度/地形；M8 账本/拍卖；M9 API/反作弊；M10 资产预算/2D 对比；M13 法律/IP/UGC；M15 M0–M4 门禁；M18 锁定/防御锥。
NEXT:
- Orchestrator/作者按 B1–B6 和 M1–M18 分派修复；每个 blocker 给证据（spike/测试/财务模型/输入规格/批准记录）。
- Human 批准/否决 B6 的 ADR 状态；Reviewer 复核后更新 docs/07、backlog、run log。
```

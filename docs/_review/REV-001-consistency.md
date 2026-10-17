# REV-001 — 评审报告（一致性 / 事实 / 全键盘）

> Reviewer 不得直接修改源文件；作者负责修复。
>
> **评审快照**：2026-10-17 22:52–23:00。快照期间 `docs/00/02/03/04/07`、`docs/_drafts`、`docs/runs` 被并发改写。行号为快照读取值；修复时以章节标题定位。
>
> **已复核修复（不再计入）**：4 指令技/现代布局/顺序必杀已补（00 §4.1–4.3、02 §3.2–3.3、03 §4.1–4.3；组合判定仍见 B-1）；防具套装 2/3（02 §5.4）；美术预算按包络 33–90/65–175 并解释分项（04 §9）；可读性阈值统一到 90/80/70（04 §10）；团队补音频/外包 0–1（00 §10、02 §12）；基线版本 0.1.2 + DR-001（00 §16、decisions/DR-001）；REV 编号（07 §5/§8、_review/README）；Hytale Early Access（01 §4）；PvP 时长（00 §2、02 §8.4）；M2 副本 2（00/02/03）；TASK-004/005 研究产物、TASK-010–015 handoff。
>
> 本报告与 `REV-002`/`REV-003`/`REV-004` 有部分重叠；Orchestrator 应按 ID 合并关闭，不能重复计 blocker。

## 1. 元信息

| 项 | 值 |
|---|---|
| REVIEW | REV-001 |
| TASK | TASK-030（`docs/07` §5）；实际覆盖 docs/00–07 + ADR + 流程 |
| 评审对象 | `AGENTS.md`、`docs/00`–`docs/07`、`docs/decisions/ADR-001`–`ADR-012` + `DR-001`、`docs/backlog.md`、`docs/runs/`、`docs/_qa/qa-report.md` |
| Reviewer | 独立 Reviewer A（非作者） |
| 日期 | 2026-10-17 |
| 结论 | **blocked**（2 blocker；修复后可 pass-with-fixes） |

---

## 2. 问题清单

### Blocker

```text
SEVERITY: blocker
LOCATION: docs/03 §4.1「组合优先级（首版）」表、§4.2 注释/§4.3；docs/00 §4.1（特殊 3/4 = Z+方向+C、Z+方向+X）、§4.2（现代布局：C 技能1、X+C 技能2、方向+C 技能3、方向+X+C 技能4）；docs/02 §3.2/§3.3；对照 docs/_drafts/02a.md §3.3/§3.4/§3.5
ISSUE: 【B-1 全键盘：方向+技能组合的优先级表不能区分 1/2 与 3/4，现代布局未覆盖】
1) docs/03 §4.1 已补「组合优先级」表，但表内「Z+X / Z+C 特殊 1/2（按住 Z）」排在「Z+方向+C / Z+方向+X 特殊 3/4（方向按住）」之上；当玩家同时按住 Z 和方向再按 C/X 时，两行都匹配。若按表的先后顺序判定，特殊 1/2 永远优先，特殊 3/4 不可达；若按「方向更具体」判定，表的顺序又与实际优先级相反。文档没有 neutral/方向先按 ≤Nf/回退规则，无法判断。
2) 现代布局没有进入该优先级表：C = 技能 1，方向+C = 技能 3；X+C = 技能 2，方向+X+C = 技能 4。移动中按 C 或 X+C 会与 3/4 重叠；docs/00 §4.2、docs/02 §3.3、docs/03 §4.2 都没有「技能 1/2 要求 neutral」「方向先于 C/X ≤3f 判 3/4」的规则。
3) 起草稿 docs/_drafts/02a.md §3.3 原有组合窗口表（Z+方向+C：方向先于 C ≤3f，失败回退 Z+C 特殊 1）、§3.4 原写现代布局「方向+C 技能 3：核心启用时，默认关闭防误触」，§3.5 原写方向+C/方向+Z+X+C 的 ghosting 测试；合并稿 00/02/03 只补了按键行，没有吸收这些判定规则。
4) docs/03 §4.3 自检只覆盖 C/X/方向/V 与「方向+Z+X+C」，没有覆盖「方向+Z+C」「方向+Z+X」「方向+C」「方向+X+C」；按当前文档，全键盘验收无法判定 4 个指令技是否可稳定触发。
FIX: 修正 docs/03 §4.1 优先级表：为经典 1/2 vs 3/4、现代 1/2 vs 3/4 增加明确规则（例：方向在攻击前 ≤3f 且保持 → 3/4；否则 1/2；或技能 1/2 要求 neutral；写清先匹配哪一行、失败回退），并同步 docs/00 §4.1/§4.2、docs/02 §3.2/§3.3；把「方向+Z+C」「方向+Z+X」「方向+C」「方向+X+C」加入 docs/03 §4.3 自检与 TEST-012/013。若无法定义稳定窗口，现代技能 3/4 必须改用不与 C/X+C 重叠的键位。
STATUS: open
```

```text
SEVERITY: blocker
LOCATION: docs/04 §4「占屏口径」 vs docs/00 §3.1、docs/02 §3.1、docs/03 §3.3
ISSUE: 【B-2 占屏 8–12% 与 5–7% 口径数学不自洽】docs/04 §4 写「8–12% 按含帽子/武器的有效角色高度（约 1.8m）计算；若只算 1.5m 身体，size 7–9 下约 5–7%」。若按同一比例换算，8–12% × 1.5/1.8 = 6.7–10%，不是 5–7%；若 5–7% 正确，则 1.8m 口径应约为 6–8.4%。文档没有给出正交投影/角色包围盒公式，M0 校准无法判断该改哪一边。该数字同时被 docs/00 §3.1 与 docs/02 §3.1 引用为「8–12%（含帽子/武器 1.8m）」，属于基线级数字。
FIX: 给出测量口径（正交相机下角色 AABB/有效高度的投影公式，或实测截图法），据此修正 5–7% 或 8–12%；同步 docs/00 §3.1、docs/02 §3.1、docs/03 §3.3、docs/04 §4；M0 用同一口径校准并记录。
STATUS: open
```

### Major

```text
SEVERITY: major
LOCATION: docs/00 §4.3、docs/02 §3.4/§10、docs/03 §4.3、docs/04 §7.2；docs/07 REQ-QA-001
ISSUE: 【M-1 UI 键盘可完成只有断言，没有键位规格】四份文档都写「UI 键盘可完成/鼠标仅可选便利」，但没有 UI 焦点顺序、Tab/Shift+Tab、Enter/Esc、方向键、聊天输入、匹配弹窗的键位表；docs/03 §4.3 只有「UI 默认键盘导航」一句，docs/03 §4.2 的输入表只覆盖战斗/交互。docs/_drafts/02a.md §3.2 原有 Esc/Enter 行，合并稿丢失。QA 无法按当前文档验收「UI 无鼠标完成」。
FIX: 在 docs/02 §10 或 docs/03 §4.3 增加 UI 键盘导航规格：焦点顺序、Tab/Shift+Tab、Enter、Esc、方向键、聊天/快捷语、弹窗确认/取消；在 docs/07 REQ-QA-001 增加可测验收与 TEST-080 步骤。
STATUS: open
```

```text
SEVERITY: major
LOCATION: docs/02 §4.6「装备 PvE 数值压缩到 ±5%」、§11.1 栏位 $2.99/便利 $1.99–4.99；docs/00 §5.4「机制符文 PvP 限 1–2 条」；docs/00 §9.1
ISSUE: 【M-2 PRD 中的基线数字未回写单一事实源】docs/02 新增「PvP 装备数值压缩 ±5%」与栏位/便利具体美元价格；docs/00 §5.4/§9.1 只写「归一化」「栏位/便利付费」，没有 ±5% 与 $2.99/$1.99–4.99。反向地，docs/00 §5.4 新增「机制符文 PvP 限 1–2 条」，docs/02 §5.4 没有对应说明。商业定价与 PvP 归一化都是 Human 门事项，数字只存在于 PRD 会破坏 single source of truth；DR-001 的变更清单也没有收录 ±5%/价格/符文限制。
FIX: 把 ±5%、栏位/便利价格、机制符文 1–2 条统一收进 docs/00（或明确标为「PRD 提案，待 Human」）；docs/02 引用 00 的锚点；商业化价格变更按 AGENTS §9 走 Human，并在 DR-001/后续 ADR 登记。
STATUS: open
```

```text
SEVERITY: major
LOCATION: docs/_drafts/（TASK-010–015 handoff 已存在；TASK-020/021/042–046 handoff 缺失）、docs/backlog.md §3、docs/runs/RUN-20261017-01-docs.md §4/§9、docs/06 §10.3、AGENTS.md §6
ISSUE: 【M-3 过程证据仍不完整：brief/handoff 未覆盖 100% 任务】TASK-010–015 已有 handoff，研究产物 `_research/competitor-2.5d.md`/`art-2.5d.md` 已存在；但：
1) TASK-020/021（合并）与 TASK-042–046（ADR/索引/指标/模板/DR）没有 handoff；run log §9 仍写 `docs/_drafts/TASK-*-handoff.md`，实际只有 010–015。
2) backlog §3 明确「TASK-010–015 完整 brief 本次未单独成文件」；这与 docs/06 §10.3「100% 任务有 brief + handoff」、AGENTS §6「没有 handoff 的产出视为未完成」不一致。若合并/支持任务确实不需要独立 handoff，应在 docs/06/AGENTS 写明豁免，而不是让规则与事实冲突。
3) run log §4 仍写「输出（待填）」与旧字数（01 11.2k/02 10.8k/03 13.5k/04 6.7k；当前约 12.2k/13.3k/14.7k/6.9k）；§7 仍写「docs 仍为 draft」，§4.1 却写「docs/00–07 定稿」，自相矛盾。
FIX: 补 TASK-020/021/042–046 handoff，或修改 docs/06 §10.3/AGENTS §6 明确「哪些任务可豁免」；更新 run log 字数/「定稿」措辞；把 backlog §3 的 brief 状态写成实际状态（摘要 brief/无独立文件）。
STATUS: open
```

### Minor

```text
SEVERITY: minor
LOCATION: docs/02 §13 vs docs/00 §9.2
ISSUE: 【m-1 KPI 表缺 Steam 愿望单】docs/00 §9.2 有「Steam 愿望单 100k（首年）」，docs/02 §13 的 KPI 表没有该行。
FIX: docs/02 §13 补「Steam 愿望单 100k（首年）」，或写「KPI 见 docs/00 §9.2，本节只列运营 KPI」。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/02 §15.2 术语 vs docs/00 §11
ISSUE: 【m-2 术语「本文新增」不准确】docs/02 §15.2 写「本文新增：软锁定、高度态、完美格挡、归一化、赛季、RAID、频道、Build、战斗核心、武器原型」；其中大部分已在 docs/00 §11，真正未定义的是「高度态」「RAID」。docs/00 术语表没有这两条。
FIX: 把「高度态」「RAID」补进 docs/00 §11，或把 docs/02 §15.2 改为「引用 docs/00；新增：高度态/RAID（待入表）」。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/02 §7.5/§11.1 vs §15.1 D1–D10
ISSUE: 【m-3 待决项在正文被写成已定】§7.5 写「公会 GvG（S1 后）：定时/攻城/领地」，但 D3 把「公会战上线」列为待决；§11.1 的创始人包内容「外观/称号/30 天战令/1 栏位」与 D1「创始人包内容/价格」待决重复。
FIX: 正文改为「S1 后（待 D3 批准）」「示例内容（待 D1 批准）」，或把 D1/D3 标为已批准并写批准人/日期。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/04 §7.2/§9
ISSUE: 【m-4 美术文档漏键位/漏外观数量】§7.2 的键盘提示为「Z/X/C/V、C+X、Z+方向+C/X、Z+X+C、F、Q/Tab、+/-」，缺普通 Z+C/Z+X 特殊 1/2；§9 的 1.0 数量写「1/8/12/20/30/5/2/4/3/1」，没有 docs/00 §7 的 80 外观（外观是美术资产，预算表也未列）。
FIX: §7.2 补 Z+C/Z+X；§9 补 80 外观，或在「角色/装备/动画」人月里明确包含外观并给出数量。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/04 §4/§7.2；docs/00 §4.1；docs/02 §3.4
ISSUE: 【m-5 无鼠标光标 vs 鼠标可选便利】docs/04 §4/§7.2 写「无鼠标光标」，但 docs/00 §4.1 写「鼠标不参与战斗/镜头；UI 键盘可完成」、docs/02 §3.4 写「鼠标仅可选便利」。若 UI 完全无光标，可选鼠标便利无法成立；若鼠标可选用，UI 必须支持光标。
FIX: 统一为「UI 不依赖鼠标光标；鼠标可选时显示光标」，或删除可选鼠标；拾取明确为 F 通用、C 仅战斗上下文（或反之）。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/decisions/ADR-004/005/006/007/008/009/010/011/012 §6
ISSUE: 【m-6 ADR 来源段缺链接】ADR-007/008/009 只写「Unity 6.3 LTS 官方发布信息」「Photon Fusion 2 官方文档/定价」「Nakama 官方架构/功能文档」，没有 URL；ADR-004/005/006/010/011/012 的竞品/P2W/平台依据也没有链接。docs/01/03 虽有链接，但 ADR 单读时不可核查。
FIX: 在 ADR §6 补官方 URL 或指向 docs/01/03 的具体章节锚点；至少 ADR-007/008/009/012 的版本/定价/平台事实要有链接。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: AGENTS.md §4 vs docs/06 §4.1/§4.2
ISSUE: 【m-7 角色/写权限表不完全一致】docs/06 §4.1 给 Orchestrator 增加 `docs/runs/` 写权限，AGENTS.md §4 的可写列只写 `docs/00`、最终文档、`docs/backlog.md`；docs/06 §4.2 对 `docs/06`/`docs/07` 写「草稿」，AGENTS.md 说 Orchestrator 可写「最终文档」；QA 的 `release notes` 写在 AGENTS §4，但 06 §4.2 矩阵没有该行。
FIX: 二选一：更新 AGENTS §4 补 `docs/runs/`、`release notes` 并澄清 06/07 的 draft→merge 语义；或收紧 docs/06 与 AGENTS 一致。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/07 §3 追踪矩阵/§7 孤儿检查
ISSUE: 【m-8 章节映射与孤儿检查未收尾】REQ-CBT-004 映射到「03 §5.5/§5.6 伤害」，但 03 §5.6 是 AI；REQ-TECH-002 映射到「02 §4 网络」，02 §4 是战斗系统；REQ-ART-003 映射到「02 §12 路线图」，风格测试在 04 §10。另 §7 孤儿检查 10 项全部未勾选，TEST 目录只有范围级主题（无逐 ID 步骤），与 §3 的逐 ID 引用不完全对齐。
FIX: 改为 03 §5.5（CBT-004）、03 §6/§5 与 00 §8（TECH-002）、04 §10（ART-003）；执行 §7 孤儿检查并勾选；TEST 目录注明「范围级；逐 ID 步骤在 M0 计划展开」，或补逐 ID 验收。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/_qa/qa-report.md §1/§7；docs/runs/RUN-20261017-01-docs.md §4
ISSUE: 【m-9 QA/run log 字数与「0 blocker」口径不一致】QA 报告称字符数为 `$t.Length`，但 docs/00 ~10.6k、01 ~11.8k、02 ~12.1k、03 ~14.2k、04 ~6.7k 与当前实际（约 11.2k/12.2k/13.3k/14.7k/6.9k）不符；run log 的字数也低于当前值。QA 报告结论「无已知 blocker」与 REV-002/003/004 报出的 blocker 冲突。
FIX: 用当前 `$t.Length` 重算并注明快照时间；QA 结论改为「QA 自检无 blocker；独立评审 blocker 待回填」。
STATUS: open
```

```text
SEVERITY: minor
LOCATION: docs/00 §10 vs docs/02 §12/docs/03 §15
ISSUE: 【m-10 路线图缺 EA 里程碑】docs/00 §10 明确「EA 12–15 个月；1.0 18–24 个月」，但 docs/02 §12 与 docs/03 §15 只有 M0–M4，没有 EA 行；读者无法从 PRD/TDD 路线图看出 12–15 个月的 EA 节点。
FIX: 在 02 §12 / 03 §15 增加 EA（12–15 月）行，或把 M3 Beta 标为「含 EA 12–15 月」，并写清 EA 内容范围（1 野外/2 副本/6 核心等）。
STATUS: open
```

---

## 3. 需求/基线对照

| REQ | 是否覆盖 | 证据 | 缺口 |
|---|---|---|---|
| REQ-VIS-001 相机 | 是 | 00 §3.1；02 §3.1；03 §3.3；04 §4；ADR-002 | 占屏口径 B-2 |
| REQ-VIS-003 高度/可读性 | 是 | 02 §3.1 90/80/70；04 §10 一致；04 §6 | B-2 仅占屏；阈值已统一 |
| REQ-CTL-001 全键盘 | 部分 | 00 §4.1；02 §3.2；03 §4.2；ADR-004 | B-1 方向+技能组合冲突 |
| REQ-CTL-003 冲突/重映射 | 部分 | 00 §4.3；02 §3.4；03 §4.3 | B-1 未覆盖方向+特殊 1–4；顺序必杀已补 |
| REQ-CTL-004 现代布局 | 部分 | 00 §4.2；02 §3.3；03 §4.2 注释 | B-1 现代 C/方向+C、X+C/方向+X+C 冲突；其余已补 |
| REQ-CBT-001 装备=招式 | 是 | 00 §5.1–5.3；02 §5.1–5.3；ADR-005 | 套装 2/3 已修；4 指令技已补 |
| REQ-CBT-002 战斗规则 | 是 | 02 §4；03 §5；04 §7 | 需 B-1 组合判定补充 |
| REQ-MMO-002 PvE/PvP 模式 | 是 | 00 §6.3/§6.4；02 §7.3/§7.4/§8.4；03 §1.2 | 已修 PvP 时长；分模式时长已在 02 §8.4 |
| REQ-ART-002 资产预算 | 是 | 04 §9；00 §13 | 分项/包络已解释；80 外观见 m-4 |
| REQ-BIZ-001 不卖属性 | 部分 | 00 §5.4/§9.1；02 §4.6/§11.1；ADR-011 | ±5%/栏位/便利价格未回写 00（M-2） |
| REQ-TECH-002 30Hz/200ms | 是 | 00 §8；03 §5.1/§5.4；ADR-008 | 无 |
| REQ-PROC-004 追踪闭环 | 部分 | 07 §3/§5/§7/§8；backlog；run log | M-3 handoff/brief 不全；m-8 映射/孤儿检查 |
| REQ-QA-002 文档一致性 | 部分 | 07 §7 清单 | B-1/B-2 未清零 |

---

## 4. 硬约束检查

- [x] 2.5D 俯视（固定 45–55° 正交、X/Y 平面战斗、Z 轴仅跳跃/击飞/高低差；未发现自由镜头、自由飞行、空中自由瞄准的正向表述）
- [ ] 全键盘 / 无鼠标依赖（B-1 方向+技能组合无窗口；M-1 UI 键位未规格化；C+X/Space/重映射/顺序必杀已具备）
- [x] 装备=招式（8 武器 / 12 核心 / 4 指令技 + 必杀 + 被动 / 无固定职业；防具 2/3 件套已修正）
- [x] 不卖属性 / 不抽强度 / 无「倒闭装」（00 §9.1、02 §11.1、ADR-011；PvP 归一化；未发现售卖霸体/属性）
- [x] 原创 IP（01/04 明确只借鉴机制、不复制资产/名称）
- [x] 服务器权威（03 §4.4「客户端只发输入」、§11；00 §8）
- [ ] 数字/术语一致（B-2 占屏；M-2 ±5%/价格/符文；m-2 术语）
- [x] 来源/不确定项（01 竞品事实有链接并标「待核实」；03 成本标「假设，需报价核实」；ADR 来源段链接不足见 m-6）

---

## 5. 结论

- **Blocker 数：2**（B-1 全键盘方向+技能组合；B-2 占屏 5–7% 数学）
- **Major 数：3**（M-1 UI 键位；M-2 PRD 数字未回写 00；M-3 brief/handoff 覆盖不全）
- **Minor 数：10**（m-1–m-10）
- **是否允许合并：否（blocked）**。B-1/B-2 修完后可进入 pass-with-fixes；`docs/00` 的 0.1.2 基线还需 DR-001 的 Human 批准后才能冻结/标 reviewed。
- **复评要求：**
  1. B-1 必须用实际键盘走一遍经典/现代/低 rollover 三种场景；覆盖方向+Z+C、方向+Z+X、方向+C、方向+X+C，并补 TEST-012/013。
  2. B-2 给出投影/实测公式，同步 00/02/03/04；M0 用同一口径校准。
  3. M-1–M-3 可与下一轮修订合并复评；M-3 未闭合前不要把任务标 done，或先在 docs/06/AGENTS 写明豁免。
  4. Orchestrator 需把 REV-002/003/004 的 blocker 与本报告去重，形成一张 closure 矩阵；不要因编号/重复而漏关。
  5. 复评时重新核对行号；快照期间 docs 被并发改写，以章节标题定位。

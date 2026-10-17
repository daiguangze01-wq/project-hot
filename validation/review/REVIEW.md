# REVIEW: TASK-063 技术验证独立复核（TASK-060 / TASK-061 / TASK-062）

> 本文件是独立复核报告；Reviewer 未修改任何作者文件，仅写 `validation/review/`。
> 评审对象：`validation/camera/`（TASK-060）、`validation/netcode/`（TASK-061）、`validation/input/`（TASK-062）。
> 证据等级：复核者独立重跑 + 独立公式重算；**不包含 Unity/Fusion 实测、不包含真实键盘测试**。
> 建议 REV 编号由 Lead 分配（`docs/_review/` 已用到 REV-004；本报告未占用新编号，避免与 TASK-064 冲突）。

| 项 | 值 |
|---|---|
| REVIEW | TASK-063 / `validation/review/REVIEW.md` |
| TASK | TASK-063（复核 TASK-060/061/062） |
| Reviewer | validation-reviewer（独立于三位作者） |
| 日期 | 2026-10-18 |
| 复核结论 | **camera: pass（模型级）；netcode: conditional；input: conditional（硬件证据不足）** |
| Blocker | **6**（5 个 docs/design 决策 + 1 个证据缺口） |
| Major | **5** |
| Minor | **9** |
| 是否允许直接合并/标记三 stream 完成 | **否**。三个 stream 的“模型证据”可接受，但下列 blocker 未闭环前**不能**把 TASK-060/061/062 标记为决策级完成；TASK-064 汇总必须带条件与限制。 |

---

## 0. 结论先行

| Stream | 判定 | 一句话理由 | 对 M0 是否决策级 |
|---|---|---|---|
| **TASK-060 相机** | **pass（模型级）** | 正交投影/可见地面/70–90px/6·10·14m/zoom 的公式、数字、图全部独立复算/重跑一致；报告已正确标注“模型级、非引擎/playtest”。但 docs 基线存在 3 处必须先解决的冲突（1.5m vs 1.8m、yaw 未定义、14m 验收不可达）。 | **几何/公式：是**（可据此改文档/定代理相机参数）；**可读性/playtest：否**。 |
| **TASK-061 网络** | **conditional** | 模型可复现（9216 配置逐字节一致）、假设 A1–A16 明确、10/10 自检通过；但 §3.10/Q1 的若干引用数字与交付的 `sensitivity.csv`/`summary_tables.md` 不一致（最大 1.3pp），且 headline 的“150ms 够”只对“理想预判者 A4 + 零时钟误差 A5 + 对称 A6”成立，σ=50 休闲人群 RTT80 误判 8.5% > 5%。 | **M0 测试计划/约束排序：是**（修 M1/M2 后）；**公平性/上线：否**。 |
| **TASK-062 键盘** | **conditional（硬件证据不足）** | 计数矩阵/解析器/时序用例/fuzz 可复现，`manual_test.html` 页面自检 28/28 已由 reviewer 独立复现；但**没有任何真实键盘数据**（docs/03 §4.1 要求 3 款键盘 ×100 次 ≥99%），且“顺序必杀干净条件（X 抬起后 3f）”与脚本实际条件（X 按下后 3f 且 X 已松开）不符。 | **解析器行为/键数矩阵：部分**（修 M3 后）；**硬件支持：否**。 |

**一句话给 Lead**：三份模型本身做得扎实、数字绝大多数可复现；但**不能写成“validation passed”**。必须先把 docs/design 的 6 个 blocker 变成决策/文档修改，并把 TASK-061 的 §3.10 数字与 TASK-062 的顺序必杀条件修正后，才能进入 M0。

---

## 1. 复核方法与本轮独立证据

### 1.1 环境（与作者一致）

```text
python 3.12.14
numpy 2.3.5
pandas 3.0.1
Pillow 12.3.0
PY = C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
```

### 1.2 重跑方式与退出码

| # | 脚本 | 重跑方式（reviewer） | 退出码 | stdout/日志 |
|---|---|---|---|---|
| R1 | `validation/camera/run.py` | `python run.py --out-dir validation/review/rerun/camera`（不覆盖作者目录） | **0** | 自检全过、`REPORT FACTS`、`DONE`；日志 `validation/review/rerun/camera.log` |
| R2 | `validation/netcode/run.py` | `python run.py --outdir validation/review/rerun/netcode` | **0** | 9216 configs / 92.16M trials，`sanity failures: none`，约 8.8s；日志 `.../netcode.log` |
| R3 | `validation/input/run.py` | 复制 `run.py` 到 `validation/review/rerun/input/` 后运行（该脚本写死 `OUT_DIR=脚本目录`，只有复制才能不覆盖作者文件） | **0** | `combo_matrix 45 行`、`timing_cases 37 例 PASS=27 EDGE=10 FAIL=0`、`fuzz 500 序列 deterministic_fail=0`、`RESULT: PASS`；日志 `.../input.log` |
| R4 | reviewer 独立核验脚本 | `python validation/review/verify_numbers.py` | **0** | **462 checks / 0 failures**；日志 `.../verify.log` |
| R5 | `manual_test.html` 页面自检 | 注入 `manual_test_selftest.js` 到临时副本，用 headless Chrome `--dump-dom` 复跑 | **0** | `SELFTEST_JSON:{"ok":true,"checks":28,"failures":[]}` —— 作者“28/28”属实（**仅页面逻辑**） |

> 说明：netcode 的 `summary_tables.md` 含运行耗时秒数，重跑时该行不同（作者 8.8s / 本次 7.2s），其余内容一致；因此**唯一不能逐字节复现的文件是 `summary_tables.md`**，但该文件不在作者报告声明的哈希列表中。其余**全部产物逐字节一致**（见 1.3）。
> 所有临时产物（rerun CSV/PNG/SVG、Chrome profile）已清理；保留 `validation/review/rerun/*.log`、`EVIDENCE.txt`、`verify_numbers.py` 作为复核证据。

### 1.3 SHA-256：交付产物 vs 独立重跑（逐字节一致性）

| 文件 | 交付 SHA-256 | 重跑 | 一致 |
|---|---|---|---|
| `camera/metrics.csv` | `156a168d9547f0b46fe6f9d7d771965723a3d3a3214e0f1c730239b296f5f992` | 同 | ✅ |
| `camera/render_size7.png` | `ba172c2c70dafebea317256efae064aa7e835d7b4175f42ea7ec11ff51dc69f3` | 同 | ✅ |
| `camera/render_size8.png` | `b2d88c285a805d54e203ad8eac3e19366a6ad5527535a260faf516cdb4101d08` | 同 | ✅ |
| `camera/render_size9.png` | `920f834b5c5ecaecb602c0afffb092707b0871affd242d11c8d677f4dd21671d` | 同 | ✅ |
| `netcode/results.csv` | `92C90D0995065514137D1A29F9F12E512B2319E008752E9C5C33C2392CF0E743` | 同 | ✅ |
| `netcode/sensitivity.csv` | `116B7D19E32D22E117979B41607A6463FE874CDC898D9399FAC9D681D6D56E49` | 同 | ✅ |
| `netcode/sanity_checks.csv` | `A662B535684DA1DA905B27A7BF3AFE6A36180185458DAC2C16C36179B4465119` | 同 | ✅ |
| `netcode/guard_success.svg` | `616102BAAA6037303EAE4A881D4B426688D81CCA0DF5C46A8108940367B85B6F` | 同 | ✅ |
| `netcode/summary_tables.md` | `9C4C3A35…D47E4C` | `423CAA76…A3367` | ⚠️ 仅 1 行（runtime 秒数）不同 |
| `input/combo_matrix.csv` | `6913A97748290A03BC2FC754CB92B8B012AE33393FAF4AEA3ABB5FC9533F75FB` | 同 | ✅ |
| `input/context_matrix.csv` | `67FAB58EA8DB9795529BE5890F279AF392797353BD31A503154B571624352F60` | 同 | ✅ |
| `input/timing_cases.csv` | `86C7F96D6A54CFDE53E20EE22F8844F90052DF33C00962585EAFD30FAC25395E` | 同 | ✅ |

补充：camera 交付报告中的 4 个哈希与本次复核计算完全一致；netcode 报告 §8.2 的 3 个哈希与交付文件一致；input 报告未列哈希，但三 CSV 重跑逐字节一致。

### 1.4 Reviewer 独立核验脚本覆盖范围（`validation/review/verify_numbers.py`，462 项断言全过）

- **Camera**：用**独立重写**的投影公式复算 15 行的 scale/角色 px/半宽/半深/半对角/世界轴可见距离/各距离脚点 y 与 in-view 标志（CSV 3 位小数内一致，max diff < 5e-4）；复算全身可见距离、zoom 所需 size、camera anchor、1.5m 口径反例、70–90 带宽计数、覆盖统计。
- **Netcode**：复算主配置 success/false-positive 表（§3.1/§3.3）、人因/网络 p95 分离（§3.2）、cap150 vs cap200（§3.4）、defender-favoring on/off（§3.5）、buffer×loss（§3.8）、interp 0/33（§3.9）、追溯率/可见预警（§3.11）；核对 10/10 sanity 与 sensitivity 场景；内部一致性（success = in-window×delivered + FP）。
- **Input**：复算 45 行 combo 矩阵与 24 行 context 矩阵的计数/risk/verdict、37 例时序用例结果、关键用例 actual、`manual_test.html` 页面自检 JSON；另**用与作者不同的调用方式**对 `ComboResolver` 做对抗性复测（见 M3）。
- **Docs 对照**：逐条 grep/read 核对 docs/00、02、03、04、07 与作者引用的原文、行号（见 §4、§5）。

### 1.5 复核边界（reviewer 没做的事）

- 未运行 Unity/URP、Photon Fusion；无法验证引擎实现、真实渲染、真实命中盒/回放。
- 未做真实键盘/人类 playtest；`manual_test.html` 只复跑其**页面逻辑自检**（合成 KeyboardEvent）。
- 未在另一台机器/另一个 Python 版本复验；单机单环境（作者同为 Win + Python 3.12.14）。
- 未审作者的历史运行/旧版本（仓库只有最终产物，无中间版本）。

---

## 2. 逐 stream 判定与决策级说明

### 2.1 TASK-060 相机：**pass（模型级）**，几何上决策级

- **通过依据**：投影公式、可见地面闭式解、角色 px、6/10/14m 入屏、20/30m zoom 全部由 `metrics.csv` 复算一致；三张 PNG 与作者声明一致（已抽查 `render_size8.png`：6m 角色、10m 裁头 55px、14m 出屏 184px、inset、1:1 剪出条均在图上）；`run.py` 内置 assert 通过；重跑产物逐字节一致。
- **决策级**：对“几何是否可行 / 相机参数怎么定 / docs 哪里需要改”**是**决策级证据（在 H_eff=1.8m、yaw=45° 假设下）；对 docs/02 的 90/85/80% 可读性、真实美术剪影、遮挡/后处理**不是**决策级证据（作者也已声明）。
- **不能通过的原因不在模型**，而在 docs 基线：见 B1（1.5m vs 1.8m）、B2（yaw 缺失）、B3（14m 验收不可达）。模型报告已正确指出并给建议，但 Lead 未决策前不能把“相机基线验证通过”写进 TASK-064。

### 2.2 TASK-061 网络：**conditional**，仅对 M0 测试计划决策级

- **通过的部分**：离散事件模型与报告 §2.1 一一对应；A1–A16 假设明确（§2.3）；9,216 配置/92.16M trials 可逐字节复现；10/10 自检通过；核心数字（5.7% 误判、cap 影响、60Hz 量化减半）从 CSV 可复算。
- **conditional 的原因**：(a) M1 引用数字与交付数据不一致（§3.10、Q1）；(b) M2 headline 的“够/通过”建立在理想预判者/零时钟误差等乐观假设上，σ=50 会失败；(c) B5 的“误判/容差/人群”在 docs 未定义，M0 验收目前不可执行。
- **决策级**：对“M0 要测什么、先测哪个假设、哪种判定方式结构性不可行”**是**；对“150ms 参数公平、可上线、60Hz 排位是否值得”**否**。

### 2.3 TASK-062 键盘：**conditional（硬件证据不足）**，解析器模型部分决策级

- **通过的部分**：45/24 行矩阵、15 组合 × 3 键盘、37 例时序、fuzz 500 全部可复现；`manual_test.html` 存在且页面逻辑自检 28/28 由 reviewer 独立复现；2KRO 不可同按清单、C16/C17/C24 规范张力在脚本/CSV 中可复现。
- **conditional 的原因**：(a) docs/03 §4.1 的 M0 键盘验收（3 款键盘 ×100 次 ≥99%）**没有执行**，交付只有工具和协议（B6）；(b) 顺序必杀“干净条件”的表述与脚本实际条件不符（M3）；(c) 经典布局防御 vs 必杀优先级需 docs 决策（B4）。
- **决策级**：对“键数矩阵 / 解析器行为 / 回退建议（模型级）”**部分**；对“真实键盘在 2KRO/6KRO 上可稳定触发”**否**。

---

## 3. 问题清单（AGENTS.md §7 格式；STATUS 全部 open，作者/Lead 修复后复评）

### 3.1 Blocker（6）

```text
SEVERITY: blocker
ID: B1
LOCATION: docs/00 §3.1（L80–L81）；docs/03 §3.3（L126）
ISSUE: 同一相机基线自相矛盾：docs/00 §3.1 相机表 L80 写“正交尺寸 7–9（以角色 1.5m 为基准；M0 可校准 6–8）”，
       紧邻 L81 又写“70–90px（约 6.5–8.3%；有效高度 1.8m、size 7–9、pitch 50°）”。
       模型证明：70–90px 只在 H_eff=1.8m 口径成立（size8@p50=78.1px；若按 1.5m 只有 65.1px，size9=57.9px）；
       且 size 9@p50=69.4px，已低于 70；size 6@p50=104.1px（camera REPORT §3.1/§4 已列）。
       证据：validation/camera/metrics.csv 列 char_px_H_eff_1.8m / char_px_body_1.5m；reviewer 独立复算（verify_numbers.py）。
FIX: 改 docs/00 §3.1 L80 为“以角色有效剪影高度 1.8m（含帽/武器）为基准”；L81 与 docs/02 §3.1 L91、
     docs/04 §4 L108/L116 统一标注“70–90px 仅对默认 size 8 / pitch 50° / 1.0× 成立；size9@50=69.4px”，
     删除或重定义“M0 可校准 6–8”（6=104px，与 70–90 冲突）。属 docs/00 基线变更 → 需 ADR-002 复访 + Human 门。
STATUS: open
```

```text
SEVERITY: blocker
ID: B2
LOCATION: docs/00 §3.1（L78、L331）；docs/02 §3.1（L88–97）；docs/03 §3.3（L124–129）；docs/04 §4；ADR-002
ISSUE: 已发布基线 docs/00–04 与 ADR-002 均**未定义 yaw**（grep “yaw/偏航” 在 docs/00–04 无命中）；
       但相机实现必须有 yaw。camera REPORT 按 TASK-060 brief 取 yaw=45° 并证明“14m 沿世界轴可见性依赖 yaw”；
       docs/_drafts 内部还互相冲突：_drafts/02a L101/L967、_drafts/03a L226 写 yaw 0°，
       _drafts/04 L108 写偏航默认 45°。M0 若按 yaw=0 实现，14m 正前方仍必然出屏（camera REPORT §3.3/§4）。
FIX: 由 Tech Lead/Human 决策并写入 docs/00 §3.1 与 docs/03 §3.3：yaw=45°（推荐，理由是让世界 X/Y 战斗轴
     成为屏幕对角、14m 沿战斗轴可贴边）+ pitch=50°；同时清理 _drafts 的 0° 方案或标注 superseded。
     这是相机实现的前置决策，未定前 TASK-060 不能算“基线验证通过”。
STATUS: open
```

```text
SEVERITY: blocker
ID: B3
LOCATION: docs/02 §3.1 可读性验收（L99–L106）；docs/00 §3.1（L181 范围/§3.4 锁定）；ADR-002 §5 复访触发
ISSUE: docs/02 §3.1 要求 14m“轮廓/方向/危险 ≥80%”，20/30m 用固定 zoom size 15/23。
       camera 模型（默认居中相机）证明：14m 正前方 0/9 参数组合可见（默认 8/50 超出可见地面 3.56m，
       size9/p45 也差 54px）；仅 14m 沿世界轴 6/9 贴边裁头；10m 默认脚点 y=23px、头顶裁 55px；
       20/30m size15/23 仅在 p45 脚点口径成立（p50 下 20m 脚点 y=-11.6px、30m 仅贴边 0.4px；p55 两者出屏）。
       这不是脚本错误，而是“验收前提在居中相机下不成立”。
FIX: 三选一并写入 docs/02 §3.1 与 ADR-002 复访：(A) 引入 camera lead/anchor（默认 8/50：14m 全身+24px
     需 anchor≥0.765、脚点≥0.670，代价后方仅剩 4.91/6.89m）；(B) 把 14m 验收改为“边缘指示器/小地图”，
     仅对 6/10m 做剪影识别；(C) 14m 场景限定屏幕对角方向。20/30m 把固定 size 15/23 改为公式：
     脚点 S≥d·sin(pitch)（p50: 15.32/22.98），全身+24px S≥(d·sin p+1.8·cos p)·1080/1032（p50: 17.24/25.26），
     建议 p50 取 17/26（或保留 15/23 但注明“pitch45–50、仅脚点贴边”）。
STATUS: open
```

```text
SEVERITY: blocker
ID: B4
LOCATION: docs/00 §4.2 方向组合判定（L210）；docs/03 §4.1 组合优先级表（L162–L167）
ISSUE: 文档字面优先级“C+X 防御 > Z+X+C 必杀”使经典布局（默认布局）在近同时三键时必杀被防御抢判：
       input timing_cases C16（Z 按住、X→C 20ms）actual=GUARD；C17 显示干净必杀只剩 X→C∈(40,50]ms 窄带；
       若 X 仍按住时按 C，模型 100% 判 GUARD（reviewer 对抗复测：`X still held -> SOFT_LOCK>GUARD`）；
       C24 候选策略（z_suppresses_guard）才判 ULTIMATE。这直接影响默认布局核心操作手感与“必杀可用”的 M0 验收。
FIX: Human/Tech Lead 决策并改 docs/00 §4.2 / docs/03 §4.1：
      推荐“Z 按住时 C+X 防御让位给 Z+X+C 必杀”（即 C24）；或明确“经典布局必杀仅支持顺序输入/需先松开 X”，
      并把该限制写进 docs/02 §3.2 与 M0 输入验收。属基线变更 → 需 ADR + Human 门。
STATUS: open
```

```text
SEVERITY: blocker
ID: B5
LOCATION: docs/02 §4.3（L203–L205）；docs/03 §5.4（L265–L266）；docs/07 REQ-CBT-002（L61）/REQ-QA-003（L120）/REQ-TECH-002（L89）
ISSUE: M0 的“完美格挡成功率 ≥70%、误判 ≤5%”在 docs 里没有可执行定义：
       ① “1 tick 容差”未说明是 ±1 tick 还是总量 +1 tick（模型按 ±1 tick，更宽松；30Hz 下影响 FP 5.7% vs 4.4–4.9%）；
       ② “误判”未定义人群/输入分布/窗口单双边：同一实现 σ=25 时 FP 0.5–5.7%，σ=50 时 8.5%（RTT80/150ms/1tick），
          同一实现可“通过”也可“不通过”（netcode REPORT §7.3 已指出）；
       ③ docs/00 §11（L401）写“受击前 100ms 内防御”（单边）vs §3.4/02 §4.3 的 100/150ms 窗口（可能居中），口径冲突。
       不先定义，M0 验收不可复现、可被玩法/参数选择“通过”。
FIX: 在 docs/02 §4.3、docs/03 §5.4、docs/07 REQ-CBT-002 写死：
      (a) 容差=±0.5 tick（30Hz ≤16.7ms；60Hz ≤8.3ms），禁用“1 full tick”作为验收口径；
      (b) 误判定义=真实输入时刻（含客户端采样量化）不在窗口内却被服务器判完美；窗口=以真实命中为中心 ±W/2；
      (c) 测试人群与输入分布=训练型 bot（σ≈25ms）为主验收 + 5–10 人真人 cohort 对照；休闲 σ=50 单列且不用于通过 5% 线；
      (d) 单边/双边口径二选一并全文统一（建议居中双边）。
STATUS: open
```

```text
SEVERITY: blocker
ID: B6
LOCATION: validation/input/REPORT.md §5/§8.3；docs/03 §4.1 全键盘验收（L178）；docs/07 REQ-CTL-003（L53）
ISSUE: docs/03 要求“3 款键盘（全键无冲/6KRO/薄膜）各 100 次组合输入，成功率 ≥99%”，但 TASK-062
       没有任何真实键盘数据：报告 §7 明确“本任务未做、也不能做物理键盘测试”，manual_test.html 只是工具；
       reviewer 只能复现其页面逻辑（28/28），不能替代硬件。2KRO 计数模型只是保守估计，真实 ghosting/固件/OS 未验。
       因此“键盘组合可行”目前只是模型结论，不能作为 M0 键盘验收通过依据。
FIX: QA/Human 按 validation/input/REPORT.md §8.3 在 NKRO / 标称 6KRO / 薄膜（笔记本）各 1 把键盘上跑
     manual_test.html，填 K01–K15 + S1–S3 报告并回填；若与计数模型不符，以实测为准并更新 REPORT 风险表述。
     在实测完成前，TASK-062 只能标“模型级完成”，TASK-064 必须把硬件测试列为 M0 必做项。
STATUS: open
```

### 3.2 Major（5）

```text
SEVERITY: major
ID: M1
LOCATION: validation/netcode/REPORT.md §0.1 Q1、§3.10；对照 validation/netcode/sensitivity.csv、summary_tables.md
ISSUE: 报告宣称“所有报告数字来自脚本输出/切片”“summary_tables.md 数字一致”（§8.3），但 §3.10 多行与交付数据不符：
       · arrival-time 60Hz RTT80/100：报告 20.1%/5.3%，实际 20.99%/6.06%（差 +0.89/+0.76pp）；
       · window_200/cap_150 30Hz RTT80/100：报告 94.7%/82.0%，实际 95.41%/82.45%（+0.71/+0.45pp）；
       · chord40 30Hz/100ms FP：报告“18.5–21.1%”，实际 19.7–22.2%；Q1 又写“17–21%”（与 §3.10 自相矛盾）；
       · arrival-time 30Hz RTT50/80/100：报告 89.0/54.8/27.1，实际 88.66/54.94/27.30（±0.34pp）。
       方向性结论不变（甚至更强：chord 对 100ms 窗口更致命），但报告的“可追溯性”声明不成立，属决策证据的质量缺陷。
FIX: 用 run.py 从 sensitivity.csv/summary_tables.md 重新生成 §3.10 全表（保留 2 位小数），并把 Q1 的 chord 数字改为
     “19.7–22.2%（40ms 场景，30Hz/100ms）”；在 REPRO/§8 加一条“报告表格由脚本自动生成/校验”的自检，防止再漂移。
STATUS: open
```

```text
SEVERITY: major
ID: M2
LOCATION: validation/netcode/REPORT.md §0.1 Q1/Q2、§0.2、§3.3；validation/REPORT.md（TASK-064，待 Lead 写）
ISSUE: headline 把“150ms + 1 tick 够”和“30Hz+150ms+cap200 通过 ≥70%/≤5%”写得像已证明公平，但其成立依赖：
       A3 对称 RTT、A4“理想预判者”（按压中心=感知命中）、A5 零时钟误差（报告自称“最乐观假设”）、
       A6 输入缓冲对称、A7 冗余 B+1（Fusion 实际固定 3 帧）、cap=200 + defender-favoring + 1 tick grace。
       报告 §3.3 自己已列 σ=50 时 RTT80 误判 8.5% FAIL，§3.11 又说“看到再格挡结构性不可能”。
       若 TASK-064 引用时省略这些前提，会形成“验证通过=公平性已验证”的假阳性。
FIX: 在 §0.1 Q2 答案首句加限定：“在 A3/A4/A5/A6/A7 全部成立、σ=25 训练型预判者的模型上限下”；§0.2 的
     “在线窗口 150ms（维持）”改为“模型建议，M0 实测前不构成基线变更”；TASK-064 必须写明“不是玩家公平性证据”，
     并把 A1（真实 Fusion + 真人 cohort）列为 M0 强制项。
STATUS: open
```

```text
SEVERITY: major
ID: M3
LOCATION: validation/input/REPORT.md §0.3、§3.1、§4.6、§4.2 C18 note；validation/input/run.py C18
ISSUE: 报告称顺序必杀的干净解析条件是“X 抬起后 3f（50ms）内按 C”。但脚本实际条件是：
       (a) C 必须在 X **按下**后 3f（50ms）内按下（X 按下的重击在 X_down+50ms 提交，超时即先提交），
       (b) C 按下前 X 必须已松开（否则 C+X 字面防御会抢判 GUARD）。
       reviewer 用 ComboResolver 对抗复测（verify_numbers.py 已固化）：
       · C18 原用例（X down 50 / up 60 / C 90）→ SOFT_LOCK>ULTIMATE（复现）；
       · X up 60、C 110（=X 抬起后正好 3f）→ SOFT_LOCK>HEAVY_ATTACK>ULTIMATE（**按报告条件却失败**）；
       · X down 50、仍按住时 C 90 → SOFT_LOCK>GUARD（防御抢判）；
       · X down 50 / up 55 / C 100（=X 按下后 3f）→ SOFT_LOCK>ULTIMATE（真正的干净边界）。
       结论方向不变（顺序输入仍脆弱、仍需引擎意图缓冲），但报告把可行条件写错，会误导 TDD 输入系统实现与 2KRO 回退承诺。
FIX: 修正 §0.3、§3.1、§4.2 C18 note、§4.6：把条件写成“C 在 X 按下后 ≤3f 按下，且 C 前 X 已松开（否则判防御）；
     而引擎若要有 250ms 顺序输入承诺，必须引入意图缓冲/取消（不能靠当前 3f 攻击缓冲）”。
     新增反例用例 C18b（X up 60、C 110）与 C18c（X 按住时 C）进 timing_cases.csv，结果标 EDGE/FAIL 语义说明。
STATUS: open
```

```text
SEVERITY: major
ID: M4
LOCATION: docs/03 §4.1（L166）vs §4.3（L202）
ISSUE: C+X 窗口一处写“±40ms”、一处写“±50ms”，会改变判定：input C09（41.7ms）按 40ms 判 LIGHT+HEAVY、
       C25 按 50ms 判 GUARD。input REPORT 已把该冲突列为 docs 修正 #1，但 docs 仍未统一；
       同时它与 B4 的优先级问题耦合（窗口越宽，防御抢判必杀越严重）。
FIX: 在 B4 决策后统一 docs/03 §4.1 与 §4.3 为一个值（建议 ±50ms 与 3f 缓冲对齐；若保留 ±40 则 §4.3 改 40），
     并写明“两键需同时按住、闭区间”；更新 docs/07 REQ-CTL-003 验收。
STATUS: open
```

```text
SEVERITY: major
ID: M5
LOCATION: docs/02 §4.3（L204）、docs/03 §5.4（L265）、docs/07 REQ-TECH-002（L89）
ISSUE: 模型建议把防御交互 cap 从 150ms 提到 200ms（cap150：RTT100 82.4%、RTT150 仅 18.4%；cap200：99.7%/81.7%），
       并把 60Hz 排位从“可选”升级为“推荐默认”。但这两项属于联网基线/服务器成本决策（ADR-008/Human），
       报告只给模型证据、未评估成本；且 M0 的 RTT80/100 验收用 cap150 仍能过 70% 线（95.2/82.4%），
       所以“是否必须改 200”取决于排位 RTT 上限与 60Hz 决策，而不是模型能单方决定。
FIX: 作为 ADR 决策请求交 Human/Tech Lead：①排位是否支持 RTT≤150ms？是→防御 cap 200ms（改 docs/02/03/07，
     Human 门）；否→保持 cap150，但 TASK-064 写明 RTT150 场景成功率仅 18.4%。②60Hz 排位默认需 M0 A/B +
     服务器成本评估后再定，暂不改 docs。
STATUS: open
```

### 3.3 Minor（9）

```text
SEVERITY: minor
ID: m1
LOCATION: validation/camera/REPORT.md §0 表第 1 行
ISSUE: 称“若允许 ±1px 容差则 6 个组合通过”，实际为 **7/9**（size8/p55=69.7、size9/p50=69.4 均进入 69–91 带）。
证据：metrics.csv band_delta_px 复算（verify_numbers.py 已打印 7/9）。
FIX: 改为“7/9”，或明确 ±1px 只放宽下限/上限的定义。
STATUS: open
```

```text
SEVERITY: minor
ID: m2
LOCATION: validation/camera/REPORT.md §3.3 解读、§4 表（docs/02 14m 行附近）
ISSUE: “只有 size 9 能全身看到 10m”不成立于 size9/p55：全身可见距离 9.73m < 10m（头顶仍裁 12.9px），
       实际只有 size9/p45（10.93）与 p50（10.24）；size 9/p55 仅脚点可见（y=49px）。
FIX: 改为“只有 size 9 且在 pitch≤50° 时 10m 可全身可见”。
STATUS: open
```

```text
SEVERITY: minor
ID: m3
LOCATION: validation/camera/REPORT.md §0 结论表第 3 行、§3.4 解读、§4 docs 对照行
ISSUE: ①“docs 的 size 15/23 在 pitch≤50° 时勉强成立”对 20m 不成立：p50 下 20m 脚点 y=-11.6px（出屏）；
       ②§4 写“yaw=45° 世界 X/Y 轴可见 12.9–18.0m”，混用了 p50 size7(12.92) 与 p45 size9(17.99)；
       ③§4 “缩放全域 55.5–107.2px”只在 p50 口径成立（p55 size9 0.8×=49.5，p45 size7 1.2×=117.8）。
FIX: 分 pitch 表述：20m 仅 p45 脚点成立；30m p45–50 脚点贴边；世界轴按 p50 报 12.92–16.62m（或列全表）；
      缩放口径注明“p50/size7–9”。
STATUS: open
```

```text
SEVERITY: minor
ID: m4
LOCATION: validation/netcode/REPORT.md §0.2 输入缓冲行
ISSUE: “0 帧不可接受”不是模型结论：2% 丢包 B0 成功率 98.0%（>70% 验收线），模型只说“损失 ~2pp/无冗余余量”；
       这是鲁棒性/余量建议，不是验收失败。
FIX: 改为“0 帧不建议（2% 丢包损失 ~2pp 且无冗余余量）；1 帧已恢复 99.9%；建议 2 帧留抖动余量”。
STATUS: open
```

```text
SEVERITY: minor
ID: m5
LOCATION: validation/netcode/REPORT.md §3.2 末段
ISSUE: “p95 总量 ~55ms，其中人因 ~49ms”把 p95 当可加分量；p95(|x+y|) ≠ p95(|x|)+p95(|y|)，
       且报告自定义 p95_network_error 已减掉 e_h，本身不是独立噪声。
FIX: 改为“p95 总量 55ms；人因分量 p95 49ms、网络/量化分量 p95 26ms（非可加分解）”，或给分位数分解方法。
STATUS: open
```

```text
SEVERITY: minor
ID: m6
LOCATION: validation/netcode/run.py emit_summary / validation/netcode/summary_tables.md；REPORT §8.3
ISSUE: summary_tables.md 含运行秒数 → 不能逐字节复现；且 §8.3 说“报告表格取自该文件、数字一致”被 M1 证伪。
FIX: 生成 summary 时去掉/固定 runtime（或用固定占位），并把 §8.3 改为“表格由 run.py 生成，报告数字以 sensitivity.csv 为准”。
STATUS: open
```

```text
SEVERITY: minor
ID: m7
LOCATION: validation/input/REPORT.md §0 第 5 条
ISSUE: “人类三键近同时按时 X/C 间隔通常就在 10–40ms”无来源；§7 自己把“玩家 3 键同按时序分布”列为待核实。
       该句是 B4 论证的核心前提（若真实间隔>40ms，防御抢判概率降低）。
FIX: 标注“模型假设/待核实”，并建议 M0 instrumentation 采集真实 X→C 间隔分布后回填。
STATUS: open
```

```text
SEVERITY: minor
ID: m8
LOCATION: validation/input/REPORT.md §4.2；run.py run_timing_cases()
ISSUE: PASS/EDGE 不是独立于作者预期的判定：PASS=actual==手写 expected 且 edge=False；EDGE 是作者标记；
       FAIL=0 只说明解析器符合作者对 docs 的解读，不等于已证明“符合 docs”。报告应避免让读者把“0 FAIL”理解为规范一致性验证。
FIX: 在 §4.2 加一句“expected 为人工按 docs 解读编写，FAIL=0 表示解析器与该解读一致，不替代 docs 原文审查”；
      并把 C16/C25 这类规范张力标 EDGE 的理由说明白。
STATUS: open
```

```text
SEVERITY: minor
ID: m9
LOCATION: validation/input/REPORT.md §4.3
ISSUE: “60Hz 采样下 50–66.7ms 之间不存在整帧间隔，实际离散到 16.7ms 一档”是现实假设，但解析器用的是理想连续时间戳，
       并未对 keydown 做 60Hz 量化；C09/C13/C14 的 41.7/50/66.7ms 是理想值。
FIX: 在 §4.3/§7 注明“本模型不含输入采样量化；真实 60Hz 采样会把边界折叠为 16.7ms 档，需 M0 instrumentation 复测”。
STATUS: open
```

---

## 4. Claim audit（逐条核对高风险 claim；只认脚本/CSV/公式）

### 4.1 Camera（TASK-060）

| # | 作者 claim（位置） | 独立核对 | 结论 |
|---|---|---|---|
| C-1 | 投影公式 `u=dot(p,right), v=dot(p,up), screen=center+u*scale, center-v*scale, scale=1080/(2S)`（REPORT §2.1，run.py 头注释） | 重写同一公式复算 15 行 scale/char_px/half_width/half_depth/half_diag/feet_y，与 CSV 差 <5e-4；run.py 内 assert 通过 | ✅ 成立 |
| C-2 | 可见地面公式 `half_width=W·S/H`、`half_depth=S/sin(pitch)`、`half_diag=hypot`、`world_axis=min(half_w,half_d)/cos45°`（§2.2） | 逐行复算：size8/p50 = 14.222 / 10.443 / 17.645 / 14.769m；与 CSV 一致 | ✅ 成立 |
| C-3 | 70–90px：默认 size8/p50=78.1（7.23%）；size9=69.4 严格 fail；H_eff=1.8 → 5/9 组合通过；按 1.5m size8=65.1（§0/§3.1/§4） | 复算：89.3/78.1/69.4；1.5m 口径 74.4/65.1/57.9；within_70_90=5/9 | ✅ 成立（±1px 计数 7/9 见 m1） |
| C-4 | 14m 正前方 0/9 不可见；默认 8/50 超出可见地面 3.56m；size9/p45 最远差 54px；14m 世界轴 6/9 贴边裁头（§0/§3.3） | 复算 d14_forward_feet_y 全部 <0；3.557m；世界轴 6/9（y=0/28/53/68/85/120px，均贴边/裁头） | ✅ 成立 |
| C-5 | docs 1.5m vs 1.8m 冲突（§4；docs/00 §3.1 L80–81） | docs 原文核对：L80“1.5m 基准”，L81/§3.4 L459/02 §3.1 L91/04 §4 L108/116 用 1.8m；模型 1.5m 下 65.1px 不达 70 | ✅ 冲突成立（B1） |
| C-6 | docs 未写 yaw（§4；yaw 属于待补）（camera REPORT §4 行“yaw 缺失”） | grep docs/00–04 无 yaw/偏航；ADR-002 也无；_drafts 有 0°/45° 冲突；brief 指定 45° | ✅ 成立（B2） |
| C-7 | 20/30m 必须 zoom-out；docs size15/23 只在脚点口径/特定 pitch 勉强成立；按公式需 20m→15.32/17.24、30m→22.98/25.26（§3.4/§5.3） | 复算 size15/p50 20m y=-11.55px、size23/p50 30m y=0.44px；need_size 公式 15.32/17.24/22.98/25.26 一致 | ✅ 成立（措辞问题见 m3） |
| C-8 | 6/10/14m 屏幕尺寸与距离无关（正交），docs/02 的 90/85/80% 不能由像素尺寸解释（§0 末） | 正交下 char px 常数（78.1 across d）；文档阈值确为 playtest 指标 | ✅ 成立 |
| C-9 | 合成图内容：6m 可见/10m 裁头/14m 出屏、1:1 剪出条、inset、SYNTHETIC 标注（§2.3/§3.5） | 抽查 render_size8.png：图上 6m 角色、10m“head 55px above top edge”、14m“OFF-VIEWPORT 184px”、inset、剪出条均存在 | ✅ 成立 |
| C-10 | 确定性：两次运行 metrics.csv / PNG 字节一致（§7） | reviewer 独立输出目录重跑：4 文件 SHA-256 全部一致 | ✅ 成立 |

### 4.2 Netcode（TASK-061）

| # | 作者 claim（位置） | 独立核对 | 结论 |
|---|---|---|---|
| N-1 | sanity checks 10/10 PASS（§3.12） | `sanity_checks.csv` 10 行 passed=1；S1=1.0000, S2=0, S3=0.0084, S4=0.9997, S5=0.6393, S6 fp30=0.0583>fp60=0.0494, S7=0.0203, S8=0.9998/0.9969/0.1819, S9=0.0230, S10=2.00；重跑一致 | ✅ 成立 |
| N-2 | 100ms/30Hz 误判 5.7% > 5%（Q1/§3.1/§3.3） | 主配置（B2/jitter10/loss2%/cap200/DF on/interp33/σ25）行：30Hz W100 RTT80/100 = 99.7/99.4% success，FP=**5.7/5.7%**；RTT0 FP 5.6%；60Hz 5.4/5.1% | ✅ 成立（口径依赖 B5） |
| N-3 | 150ms/30Hz 在 RTT80/100 成功（Q2/§3.3） | 同配置：success=**100.0%/99.7%**，FP=0.5%/0.2%；60Hz=99.9%/99.5%，FP 0.4/0.1% | ✅ 成立（仅 σ25/理想预判者，见 M2） |
| N-4 | cap150 vs cap200：cap 是 RTT≥120ms 第一约束（§3.4） | 30Hz W150：RTT100 82.4%→99.7%，RTT150 18.4%→81.7%；W100：95.2/82.6 vs 99.7/99.4；60Hz W100 91.6/74.0 vs 99.1/99.0 | ✅ 成立（cap 语义映射见 §7.2 #3，报告已标） |
| N-5 | 60Hz 收益：纯网络/量化 p95 25.8→12.9ms（σ=0），误判 5.7→5.4 / 0.5→0.4（§3.6/§3.7/S10） | 复算 σ=0 RTT80 150ms：p95_network 25.8 vs 12.9，ratio=2.00；W100 FP 5.7→5.4；W150 0.5→0.4 | ✅ 成立（成本未评估，M5） |
| N-6 | 假设 A1–A16 明确（§2.3） | REPORT 有 A1–A16 逐条表；simulate() docstring/代码与 A1/A2/A4/A6/A10 等一致 | ✅ 成立（A3/A4/A5/A6/A7 乐观，M2） |
| N-7 | 到达时间判定结构性失败、必须用 ClientTimeMs（§3.10/S3） | arrival_ts 场景：30Hz/150ms RTT50/80/100=88.7/54.9/27.3%，60Hz 80/100=21.0/6.1%；sanity S3 RTT150=0.84% | ✅ 方向成立，但引用的 20.1/5.3 与 89.0/54.8/27.1 与交付数据不符（M1） |
| N-8 | chord 延迟 0–40ms 对 100ms 窗口“致命”：成功率 97.0–99.2%、误判 18.5–21.1%（§3.10；Q1 写 17–21%） | 交付 sensitivity 的 chord_delay_40ms（U(0,40)）30Hz/100ms：success 99.2/99.0/97.0%，FP **21.4/22.2/19.7%**；150ms：FP 4.3/4.1/2.1%、success 99.9/99.4/97.0% | ⚠️ 方向成立，**引用数字错误**（M1；实际 FP 更高、更支持结论） |
| N-9 | window 放大到 200ms+cap150 不能替代 cap（§3.10） | sensitivity window_200_cap_150：RTT80/100/150 = 95.4/82.5/17.8% | ✅ 方向成立（报告数字 94.7/82.0/17.9 略漂，M1） |
| N-10 | 输入缓冲 2 帧、B0 不可接受（§0.2/§3.8） | B0 loss2%=98.0%、B1=99.9%、B2/B3=100%；B0 仍 >70% 验收线 | ⚠️ 数据成立，结论“不可接受”超出模型（m4） |
| N-11 | 误判对人群敏感；σ50 在 150ms/1tick RTT80 误判 8.5%（§3.7/§7.3） | 复算 30Hz/150ms RTT80 σ50：success 94.5%、FP 8.5%；60Hz 6.8% | ✅ 成立（B5 的核心证据） |
| N-12 | 追溯撤销率 RTT≥80ms ≈100%，输入比真实命中晚 121–192ms（§3.11） | 复算 retro=100.0/99.7/81.7%（RTT80/100/150），mean_arrival=121.6/141.5/191.9ms | ✅ 成立（攻击方观感未量化，报告已声明） |
| N-13 | 有无“超出模型”的结果？ | 发现 3 处：Q3“60Hz 排位推荐默认”（成本未测）、§0.2“0 帧不可接受”、headline 近乎“150ms 够=公平通过”；其余推荐均带模型/待核实标注 | ⚠️ 见 M2/M5/m4；不构成 blocker，但 TASK-064 必须改写口径 |

### 4.3 Input（TASK-062）

| # | 作者 claim（位置） | 独立核对 | 结论 |
|---|---|---|---|
| I-1 | combo 矩阵：15 组合×3 键盘=45 行；NKRO 15/15；6KRO 15/15（none=10/low=5）；2KRO 10/15 正交、9/15 斜向（low=10/high=5）（§2.1/§2.2） | 逐行统计 CSV：全部一致；主矩阵最大键数正交 4/斜向 5 | ✅ 成立 |
| I-2 | 2KRO 不可同按：Z+X+C、方向+Z+C、方向+Z+X、方向+Z+X+C、方向+X+C；方向+C 正交可/斜向不可（§0/§2.2） | CSV 过滤 `within_limit=False` 的 2KRO 5 行完全一致；Direction+C cardinal within=True、diagonal=False | ✅ 成立 |
| I-3 | context 24 行：NKRO 8/8、6KRO 8/8、2KRO 2/8；6 键极限（V+斜向+Z+X+C）用满 6KRO（§2.3） | 复算一致；context 最大同时键=6；6KRO 该行 risk=medium | ✅ 成立 |
| I-4 | 3f 方向窗口：方向领先 50ms 仍判方向版、66.7ms 回退基础版、已按住 >3f 回退；C13/C14/C12/C10 与 M02/M03（§4.3） | 逐例核对 actual/expected：C10=SPECIAL_3、C13=SPECIAL_3、C14=SPECIAL_1、C12=SPECIAL_1、M02=SKILL_3、M03=SKILL_1；3f 常量=50.0ms | ✅ 成立（连续时间模型，见 m9） |
| I-5 | C+X 防御 vs Z+X+C 必杀规范张力：C16 GUARD；C17 干净必杀仅 (40,50]ms；C24 候选策略 ULTIMATE；±50 时 C25 GUARD（§4.4） | CSV 逐行一致；reviewer 额外对抗复测证实：X 按住时 C 按下→GUARD；X 松开且 C≤X_down+50ms→ULTIMATE | ✅ 成立（B4 的实证）；顺序条件表述错误见 M3 |
| I-6 | docs/03 §4.1 ±40ms vs §4.3 ±50ms 冲突（§0 第 5 条、§6 #1） | docs/03 L166“±40ms”、L202“±50ms”原文确认；C09/C25 证明确会改变判定 | ✅ 冲突成立（M4） |
| I-7 | manual_test.html 自检 28 项全过；**只是页面逻辑，不是硬件证据**（§0 第 7/§8.2） | reviewer 用 headless Chrome 独立复现：`{"ok":true,"checks":28,"failures":[]}`；报告无硬件数据 | ✅ 成立（但硬件证据=0，B6） |
| I-8 | 顺序必杀干净条件“X 抬起后 3f 内按 C”（§0.3/§3.1/§4.6/C18 note） | 独立复测否证：X up 60→C 110（抬起后 50ms）仍先提交 HEAVY；真正边界是 X_down+50ms 且 X 已松开；X 按住时按 C 判 GUARD | ❌ **不成立（M3）** |
| I-9 | 2KRO 顺序回退“可解析”= C18/C20；引擎只需 2–3 帧缓冲？（§3.1/§4.6） | C18/C20 确实可解析（EDGE），但 C19 证明 >3f 中间动作已提交；报告结论“需引擎意图缓冲/取消”正确 | ✅ 结论正确，条件错（M3） |
| I-10 | fuzz：500 序列 seed 20261017，deterministic_fail=0、unknown=0、non_monotonic=0（§4.7） | 重跑 stdout 同数值（soft_lock=396, guard=397, ultimate=1）；代码使用固定 seed | ✅ 成立 |
| I-11 | 2KRO 下“只有 1–2 键组合可同按（15 个中的 10 个）” | 2KRO within 恰好 10 行（6 单键+4 双键） | ✅ 成立 |
| I-12 | 人工硬件测试未执行（§7/§8.3） | 报告明确承认；仓库无真实键盘数据；docs/03 §4.1 要求 3 款键盘×100 次 ≥99% | ✅ 作者未虚报，但验收缺口=B6 |

---

## 5. Docs 修正建议（exact files/sections/values；Reviewer 不修改 docs，交 Lead/Human）

> 以下编号与 §3 blocker/major 对应；`docs/00` 与 ADR 属 Human 门（AGENTS §9），`docs/02/03/07` 由 Lead/Tech Lead 处理。

| # | 文件/位置 | 现状 | 建议改为 | 依据 | 严重度 |
|---|---|---|---|---|---|
| D1 | `docs/00` §3.1 L80 | 正交尺寸 7–9（**以角色 1.5m 为基准**；M0 可校准 6–8） | “正交尺寸 7–9（以角色**有效剪影高度 1.8m（含帽/武器）**为基准；M0 校准范围为 7–9；6 对应 104px，不满足 70–90px，需重定目标）” | camera 78.1 vs 65.1px；size6=104.1px | B1 |
| D2 | `docs/00` §3.1 L81；`docs/02` §3.1 L91；`docs/04` §4 L108/L116 | “70–90px（约 6.5–8.3%；有效高度 1.8m、size7–9、pitch50°）” + “取整 70–90px” | 保留 70–90px 作为**默认相机目标**，但加限定：“size8@p50=78.1px 达标；size9@p50=69.4px（低于下限 0.6px）；pitch45–55×size7–9 的 9 组合中严格 5/9 达标（±1px 容差下 7/9）；45° 时 size7=98.2px、55° 时 size8/9<70px” | camera §3.1/§0；±1px 计数 7/9 | B1/m1 |
| D3 | `docs/00` §3.1 L78（视角行）；`docs/03` §3.3 L126；`docs/02` §3.1 L88 | 仅写“固定 45–55° 斜俯视/正交”，未定义 yaw | 写死 **pitch=50°（45–55° 为风格测试范围）、yaw=45°**；说明“世界 X/Y 战斗轴为屏幕对角（14m 沿轴可贴边）”；_drafts 中 yaw 0° 方案标 superseded/删除 | camera §3.3/§4；docs/00–04 grep 无 yaw | B2 |
| D4 | `docs/02` §3.1 L99–L106 | 6/10/14m ≥90/85/80%；20/30m zoom-out size15/23 ≥70% | 14m 改为“边缘指示器/小地图 + 方向信息；居中相机下 14m 正前方不可见（0/9 参数），沿世界轴仅 6/9 贴边裁头”；或选 camera lead（8/50：脚点 anchor≥0.670、全身+24px≥0.765，后方剩 6.89/4.91m）；10m 注明默认裁头（size9 可全身）；20/30m 改为公式 `S≥d·sin p`（p50:15.32/22.98）与 `S≥(d·sin p+1.8cos p)·1080/1032`（p50:17.24/25.26），建议 p50 取 17/26 | camera §3.4/§5.2/§5.3 | B3 |
| D5 | `docs/02` §3.1 L90；`docs/03` §3.3 L126；`docs/00` §3.1 L80 | “M0 可校准 6–8” | 删除，或改为“M0 只允许 7–9 内校准；6 会使角色 104px，需同时改 70–90 目标”；若坚持 6–8，则 70–90px 目标需重定 | camera §3.1/§4 | B1 |
| D6 | `docs/03` §4.1 L166 vs §4.3 L202 | C+X 一处 ±40ms、一处 ±50ms | 统一为一个值（推荐 **±50ms**，与 3f=50ms 对齐；若按 B4 保留防御优先则需评估抢判必杀更严重），写明“两键同时按住、闭区间”；同步更新 C09/C25 预期与 docs/07 REQ-CTL-003 | input C09/C25；M4 | M4 |
| D7 | `docs/00` §4.2 L210；`docs/03` §4.1 L162–L167 | 优先级“C+X 防御 > Z+X+C 必杀” | 改为“**Z 按住时 Z+X+C 必杀 > C+X 防御**”（C24 候选策略），或明确“经典布局必杀仅支持先松 X 的顺序输入”并把限制写入 docs/02 §3.2；需 ADR+Human | input C16/C17/C24；B4 | B4 |
| D8 | `docs/02` §4.3 L203–L205；`docs/03` §5.4 L265–L266；`docs/07` REQ-CBT-002 L61 / REQ-QA-003 L120 | “150ms（9f）+ 1 tick 容差”“误判 ≤5%”无定义 | 定义：(a) 容差=±0.5 tick（30Hz≤16.7ms；60Hz≤8.3ms）；(b) 误判=真实输入不在窗口内却被判完美，窗口以真实命中为中心；(c) 人群=训练型 bot（σ≈25）+真人 cohort，σ=50 单列不用于 5% 通过线；(d) 单/双边口径统一（建议居中双边） | netcode §3.7/§7.2/§7.3；B5 | B5 |
| D9 | `docs/02` §4.3 L204；`docs/03` §5.4 L265；`docs/07` REQ-TECH-002 L89 | 防御交互 cap 150ms（REQ-TECH-002 写死） | 决策请求：若排位支持 RTT≤150ms → cap 改 **200ms**（model: RTT150 18.4%→81.7%，RTT100 82.4%→99.7%）；若排位锁 RTT≤100ms → 可留 150ms（82.4% 过 70% 但余量小）；此变更需 ADR/ Human | netcode §3.4；M5 | M5 |
| D10 | `docs/03` §5.1 L218–L223；docs/00 §8 L332–L333 | 排位 60Hz“可选” | 维持“可选”，待 M0 A/B + 服务器成本评估后再决定是否默认；TASK-064 写明“模型支持公平性收益，但成本未评估” | netcode §3.6/§4.4；M5 | M5 |
| D11 | `docs/03` §4.1 L178 | “3 款键盘 ×100 次组合输入，成功率 ≥99%”无协议 | 引用 `validation/input/manual_test.html`（+`manual_test_selftest.js` 仅页面逻辑）作为人工测试工具；定义“组合成功=组合解析结果符合预期且无丢键”；硬件实测未完成前该验收不得勾选 | input §8.3；B6 | B6 |
| D12 | `docs/00` §4.3 L217 | “常见薄膜键盘至少 3 键同时按可完成防御+方向” | 改为“常见薄膜多数键区可 3 键，但**不保证**（保守 2KRO 模型）；低 rollover 档默认 Space 防御，并在自检失败时提示改键” | input §6 #4/§5 | minor |
| D13 | `docs/00` §11 L401 | “完美格挡：受击前 100ms 内防御”（单边） | 与 §3.4/02 §4.3 统一为“以命中为中心 ±W/2；本地 100ms/在线 150ms”，或全文改单边并重跑模型 | netcode §7.2 #1；B5 | B5 |
| D14 | `docs/07` REQ-VIS-003 L45 / REQ-CBT-002 L61 | 验收仍写 6/10/14m ≥90/85/80%、成功率≥70%/误判≤5% | 按 D4/D8 更新可执行口径；REQ-VIS-003 的 14m 项需与相机决策同步（边缘指示器/lead） | camera/netcode | B3/B5 |

---

## 6. M0 还缺什么：强制引擎/QA 测试 vs 可接受的模型级证据

### 6.1 必须由 M0 引擎/QA 实测（模型不能替代）

| Stream | 测试 | 验收/对账 |
|---|---|---|
| Camera | URP `orthographicSize=8` 语义实测；1.8m 剪影包围盒是否 78px@1080p；6/10/14m 目标 feet y 与 metrics.csv 对齐（±2px）；yaw=45° 的相机绕 Y 实现；anchor/边缘指示器落地；16:10/21:9；真实美术/遮挡/后处理后 6/10/14m **真人 1 秒识别率 90/85/80%** | 几何 ±2px；可读性为 playtest 指标（不可由合成图通过） |
| Netcode | Fusion 2 Server Mode 30/60Hz；C1/C2 负对照（到达时间判定、无 defender-favoring）先过；A1/A2/A3/B1/B2 决策格（REPORT §6.2）；A5 时钟同步 p95≤16.7ms；A6 输入缓冲语义；C5 C+X chord p95≤16.7ms；5–10 人真人 cohort + 攻击方“被回放格挡”观感问卷；与 results.csv 对账（偏差>10pp 先查 A3/A5/A6） | 成功率 ≥70%、FP ≤5%（人群/容差按 D8 定义）；p95 网络/量化 30Hz≤33ms/60Hz≤17ms；追溯撤销率记录；与模型对账 |
| Input | docs/03 §4.1：NKRO/6KRO/薄膜 3 款键盘 ×100 次组合 ≥99%；低 rollover 顺序输入模式（意图缓冲/取消）实现后复测 2KRO Z→X→C / Z→方向→C/X；OS 粘滞键/筛选键/IME/浏览器焦点；X→C 间隔分布 instrumentation | 成功率 ≥99%；顺序输入成功率/中间动作计数；硬件 ghosting 以实测为准（模型仅保守估计） |

### 6.2 可以作为模型级证据接受（写进 TASK-064 结论，但必须标注模型级）

- **Camera**：正交投影/可见地面/角色 px/6·10·14m 入屏/zoom 尺寸/camera anchor 的**几何数学**；H_eff=1.8m 假设下的 70–90px；20/30m 必须 zoom-out 的结论；yaw 对 14m 可见性的方向性结论。
- **Netcode**：**约束排序**——必须用输入时间戳（到达时间判定结构性失败）；cap 是 RTT≥120ms 的第一约束；1 tick 容差对 100ms 窗口过宽（5.7%>5%）；60Hz 量化误差减半；追溯撤销率≈100% 是 lag-comp 固有代价。这些方向性结论在合理假设扰动下稳健，可用于 M0 测试设计。
- **Input**：键数计数矩阵（NKRO/6KRO/2KRO 模型）；2KRO 不可同按清单；3f 窗口/优先级解析器行为；`manual_test.html` 页面逻辑（28/28）；回退建议（顺序输入/改键/Space）作为**待硬件确认**的建议。

### 6.3 不得当作证据/不得写入“passed”的项

- 任何“可读性 90/85/80% 已验证”“6/10/14m 可读性通过”——未做 playtest，且 14m 居中相机几何不成立。
- 任何“Fusion 实测成功率/公平性已验证”“150ms 参数可上线”——模型理想预判者/零时钟误差，σ=50 已失败。
- 任何“2KRO/6KRO 真实硬件可用”——无真实键盘数据；6KRO 厂商标称差异未测。
- 任何“15/23 zoom 已验证”——p50 下 20m 出屏、30m 贴边；应改公式。

---

## 7. 需求/基线对照与硬约束检查

| REQ | 覆盖 | 证据 | 缺口 |
|---|---|---|---|
| REQ-VIS-001（相机参数/70–90px） | 部分 | camera metrics/渲染 | 1.5 vs 1.8m、yaw、size9=69.4（B1/B2） |
| REQ-VIS-003（6/10/14m ≥90/85/80%） | 部分 | camera §3.3 | 14m 几何不可达、阈值是 playtest（B3） |
| REQ-CTL-001（全键盘/无鼠标） | 模型级覆盖 | input 矩阵 | 硬件未测（B6） |
| REQ-CTL-003（重映射/C+X/顺序输入/3f） | 部分 | input parser/timing | 优先级冲突、顺序条件错误、硬件（B4/M3/B6） |
| REQ-CBT-002（完美格挡 ≥70%/≤5%） | 仅模型 | netcode results | 误判/人群/容差未定义（B5）；无引擎/真人 |
| REQ-TECH-002（30Hz+200ms 回放+防御 cap150） | 模型级 | netcode §3.4 | cap 150→200 决策（M5） |
| REQ-QA-001/003（全键盘 QA/网络矩阵） | 计划级 | input/netcode 报告 | QA 执行未发生 |

硬约束检查：2.5D 俯视/全键盘/装备=招式/不卖属性/原创 IP/服务器权威——三份验证不涉及违反项；数字/术语一致性存在上列 docs 冲突；来源/不确定项标注总体良好（netcode A1–A16、camera 限制、input 待核实），个别引文无来源（m7）与数字漂移（M1）。

---

## 8. 最终结论（给 Lead / TASK-064）

- **Blocker 数：6**（B1–B6）。其中 B1/B2/B3/B4/B5 是 **docs/design 决策**（Lead/Human），B6 是 **QA 证据缺口**；作者不能自行修 docs（写域）。
- **Major 数：5**（M1–M5）。M1/M3 是作者产物必须修正的**事实性错误**；M2/M4/M5 是 Lead/TASK-064 必须携带的决策请求。
- **Minor 数：9**（m1–m9）。
- **是否允许把 TASK-060/061/062 标记“done（验证通过）”：否。**
  - TASK-060：可接受为 **camera 几何模型 pass**；**baseline 验证**需 B1–B3 决策后才可关闭。
  - TASK-061：需先修 M1/M2，且 B5 的验收定义落地；在此之前只能标“模型完成，M0 决策待定”。
  - TASK-062：需先修 M3，且 B4/B6 落地；在此之前只能标“模型完成，硬件未验”。
  - 若 Lead 仅按 `docs/tasks.json` 的 acceptance 关闭“交付物齐备”（脚本/报告/矩阵/HTML 均齐），可以把三 stream 标为
    **done（model-level, with open blockers）**，但**必须**在 TASK-064 保留上述 blocker、且不得写“验证通过/decision-grade passed”，
    也不得据此进入 M0 集成；B1–B6 闭环前“技术验证通过”这一结论不成立。
- **TASK-064（REPORT.md）撰写要求**：必须逐 stream 标“模型级/非引擎/非玩家实测”，引用本报告 §3/§4 的 blocker/major；不得写“validation passed”；把 §6.1 的 M0 必测矩阵列为进入 M0 的前置任务；把 §5 的 docs 修正建议连同决策请求（ADR-002 复访、ADR-008/Human 门）提交 Human。
- **复评要求**：作者修完 M1/M3/minor 后，reviewer 复跑 `verify_numbers.py` + 三个 `run.py`（确认哈希/数字一致）；B1–B6 闭环需 docs 修改 PR/ADR/Human 批准 + QA 硬件与引擎实测证据。

---

## 9. 附录：复核证据文件与未修改声明

- `validation/review/REVIEW.md`（本文件）
- `validation/review/verify_numbers.py`（reviewer 独立核验脚本；462 checks，0 failures）
- `validation/review/rerun/camera.log`、`netcode.log`、`input.log`、`verify.log`
- `validation/review/rerun/EVIDENCE.txt`（env、命令、退出码、SHA-256 对照、页面自检 JSON、差异表）
- Reviewer 未修改 `validation/camera/`、`validation/netcode/`、`validation/input/`、`docs/`、`AGENTS.md`、`docs/tasks.json`、`validation/README.md`、`validation/REPORT.md`；
  临时重跑数据与 Chrome profile 已清理。`git status` 中仅 `docs/tasks.json` 为 Lead 先前修改、`validation/` 未跟踪（复核期间未新增作者目录变更）。

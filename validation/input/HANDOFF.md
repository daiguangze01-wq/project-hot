TASK: TASK-062 键盘 rollover/组合技术验证

STATUS: done

CHANGED:
- validation/input/run.py（新建；矩阵 + 组合解析器 + 37 个合成时序用例 + 固定种子模糊回放；确定性；退出码 0/1）
- validation/input/combo_matrix.csv（新建；15 组合 × NKRO/6KRO/2KRO = 45 行）
- validation/input/context_matrix.csv（新建；8 个移动/跳跃/斜向/修饰键上下文 × 3 模型 = 24 行）
- validation/input/timing_cases.csv（新建；37 例：PASS=27 / EDGE=10 / FAIL=0）
- validation/input/manual_test.html（新建；file:// 单文件人工测试页：实时按键/同时键数/会话最大/最近组合、K01–K15 组合测试、S1–S3 顺序输入、键盘信息与报告导出；无外部依赖）
- validation/input/manual_test_selftest.js（新建；可选的页面逻辑自检注入脚本，供复核复现“页面 28 项检查通过”）
- validation/input/REPORT.md（新建；结论先行 + 矩阵 + 解析器结果 + 硬件不可保证项 + docs 修正建议；2026-10-18 按 TASK-063 M3 修正「顺序必杀干净条件」并补 X 按住/「松开后 3f」反例，仅改 §0/§3.1/§4.2/§4.6/§8.2）
- validation/input/HANDOFF.md（本文件）
未修改 docs/、AGENTS.md、docs/tasks.json、validation/README.md、validation/REPORT.md；写域仅 validation/input/。

DECISIONS:
1. 键盘模型按任务书取保守计数模型：NKRO 不限 / 6KRO ≤6 非修饰键 / 2KRO ≤2 非修饰键；Shift 等修饰键不计入上限（假设，REPORT §7 标待核实）；方向按 1 键计，斜向另 +1 键单列。
2. 风险标签语义：none / low（计数在上限内但硬件差异未建模）/ medium（用满上限无余量）/ high（超限必须回退）；verdict：ok / ok_space_optional / ok_cardinal_only / sequential_required / sequential_or_remap / not_a_command。
3. 组合解析器建模 docs/03 §4.4 的 2–3 帧输入缓冲（取 3f=50ms）：攻击类动作延迟 3f 提交，更高优先级组合在缓冲内可取消低优先级动作；C+X 防御要求两键同时按住（避免顺序输入误判）。
4. 经典布局默认按 docs 字面优先级 `C+X 防御 > Z+X+C 必杀`（literal）；另实现候选策略 `z_suppresses_guard`（Z 按住时防御让位）并用 C16/C24 对比复现——需 docs/00 §4.2 基线决策，本 stream 未改 docs。
5. C+X 窗口默认取 docs/03 §4.1 的 ±40ms，并单独用 C25 验证 ±50ms 变体（§4.3 写法冲突）；结论建议统一为一个值。
6. 顺序输入仅在 docs 明确承诺的两条路径实现：必杀 `Z→X→C`（≤250ms）与特殊 3/4 `Z→方向→C/X`（≤250ms）；不实现顺序特殊 1/2（避免 Z tap 软锁 + 普攻被误判）。
7. 人工硬件测试不在本任务执行（AI 无法做物理键盘测试）；交付 manual_test.html 供 2–3 把键盘人工填充，REPORT §8.3 给了协议。

EVIDENCE:
- 复现命令：`cd validation/input; & "C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" run.py` → 最后一行 `RESULT: PASS`。
- run.py 输出要点：
  - combo_matrix: 45 行 = 15 组合 × 3 模型；主矩阵最大同时非修饰键 正交 4 / 斜向 5。
  - NKRO 15/15（risk none=15）；6KRO 15/15（none=10, low=5）；2KRO 10/15 正交、9/15 斜向（low=10, high=5）。
  - 2KRO 不可同按：Z+X+C、方向+Z+C、方向+Z+X、方向+Z+X+C、方向+X+C；方向+C 正交可、斜向不可。
  - context_matrix: 24 行；NKRO 8/8、6KRO 8/8、2KRO 2/8；6 键极限上下文（V+斜向+Z+X+C）在 6KRO 用满上限、0 余量。
  - timing_cases: 37 例；PASS=27 EDGE=10 FAIL=0（EDGE 清单见 REPORT §4.2）。
  - fuzz: 500 序列 seed=20261017；deterministic_fail=0、unknown_action=0、non_monotonic=0。
- 确定性：run.py 连续两次运行，combo_matrix.csv / timing_cases.csv SHA-256 完全一致。
- TASK-063 M3 修正证据（用同一 `ComboResolver` 按同一脚本逻辑逐点探测，未新增 timing_cases 行、未改 run.py/CSV）：
  - 精确条件：顺序必杀「干净」= `C↓−X↓ ≤ 3f(50ms)` 且不满足「X 仍按住 且 C−X ≤40ms」；与「X 何时松开」无关。
  - X 按住反例：Z↓0, X↓50 按住, C↓70（C−X=20）→ `GUARD`；C↓90（C−X=40 边界）→ `GUARD`。
  - X 按住窄带：C↓95（C−X=45）、C↓100（C−X=50）→ `ULTIMATE`（干净，仅当 literal ±40ms 窗口）；C↓101（C−X=51）→ `SPECIAL_2>ULTIMATE`（dirty）。
  - 「松开后 3f」反例：Z↓0, Z↑30, X↓50, X↑60, C↓110（C 距 X 松开 50ms，但 C−X=60ms）→ `SOFT_LOCK>HEAVY_ATTACK>ULTIMATE`（dirty）；C18（C↓90）→ `SOFT_LOCK>ULTIMATE`（干净）。
  - M3 修正后重跑 run.py：输出不变（37 例 / PASS=27 EDGE=10 FAIL=0 / RESULT: PASS），C18/C19 的 expected/actual 与 timing_cases.csv 一致。
- manual_test.html 页面逻辑自检（headless Chrome，合成 KeyboardEvent，非硬件证据）：28 项检查全部通过（`SELFTEST_JSON:{"ok":true,"checks":28,"failures":[]}`）；复现步骤见 manual_test_selftest.js 文件头。
- 未修改受保护文件（`docs/`、`AGENTS.md`、`docs/tasks.json`、`validation/README.md`、`validation/REPORT.md`）。`git status` 中 docs/ 下的改动来自 Lead/其他 agent（非本任务）；`validation/` 为未跟踪目录（含其他 stream 产物）；本任务只新增/修改 `validation/input/` 下文件。

RISKS:
- blocker（需决策，非脚本问题）：docs 字面优先级「C+X 防御 > Z+X+C 必杀」会让经典布局近同时必杀被防御抢判（C16）；X 仍按住时干净必杀仅存在于 X→C ∈ (40,50]ms 窄带（C17/C25），且 ±50ms 窗口写法下窗口为空。候选修正 C24（Z 按住时防御让位）需 docs/00 §4.2 基线变更 + Human 门。
- major：docs/03 §4.1 ±40ms 与 §4.3 ±50ms 窗口冲突，需统一；2–3 帧输入缓冲（33–50ms）不足以支撑 250ms 顺序输入（C19 中间普攻先提交），TDD 需补「低 rollover 顺序输入模式」的缓冲/取消语义，否则 2KRO 顺序必杀不可靠。
- major：现代技能 4（方向+X+C）的顺序回退与 3f 方向新鲜窗口冲突，2KRO 建议改键而非顺序输入。
- 风险未闭环：真实键盘 ghosting/固件/OS/连接方式未测（AI 不能测物理键盘）；2KRO 结论为计数保守模型，个别键位可能碰巧能按 3 键，不能视为稳定；6KRO 厂商标称差异、修饰键是否占 rollover 均标「待核实」。
- 遗留（待 Lead 决定，本次按指示未动）：`run.py` 生成文本仍含旧措辞「X 抬起后 3f 内按 C」——`combo_matrix.csv` K10 2KRO 的 note、`timing_cases.csv` C18 title/note（生成源在 run.py `note_for()` 与 C18 的 title/note）。数据/判定本身正确（C18 干净、C19 dirty），但措辞与新 REPORT §4.6 精确条件不一致；若 Lead 批准，可后续小改 run.py 并重生成 CSV 统一措辞，不影响本次 M3 修复范围。
- 人工硬件测试（2–3 把键盘）未执行，需 Human/QA 按 manual_test.html 补齐后回填 TASK-064。

NEXT:
1. validation-reviewer（TASK-063）：独立重跑 `run.py`（核对上述数字/退出码），审阅 combo_matrix.csv 列语义与 REPORT 论证；可复现 manual_test.html 页面自检（按 manual_test_selftest.js 头注释）；重点复核 blocker 级规范张力（C16/C24）与 §6 的 docs 修正建议是否成立。
2. lead（TASK-064）：把 REPORT §6 的 8 条 docs 修正建议转入汇总/决策请求；其中 #2（防御 vs 必杀优先级）与 #3（顺序输入缓冲语义）需 Human/Tech Lead 决策后才能进 M0 输入系统实现；#1 窗口统一为文档小修。
3. QA/Human：按 REPORT §8.3 在 NKRO / 6KRO / 2KRO 各 1 把真实键盘上跑 manual_test.html，回填实测报告；若 2KRO 硬件实测与计数模型不一致，以实测为准并更新 REPORT 风险表述。
4. 后续 M0 输入系统实现时，以 `run.py: ComboResolver` 为行为基线（3f 窗口、Z tap/hold、顺序输入、优先级），但需先落 docs 决策 #2/#3。

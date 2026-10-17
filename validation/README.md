# 技术验证（M0-lite）

> **结果（2026-10-18）**：三路验证完成，结论 **conditional go to M0**，不是 validation passed。汇总见 [`REPORT.md`](REPORT.md)；独立复核见 [`review/REVIEW.md`](review/REVIEW.md)；基线修正 [`DR-002`](../docs/decisions/DR-002-validation-baseline-fixes.md) 已获 Human 批准（D1–D6）。B6 真实键盘 QA 仍 open。

> 目的：在 **不引入 Unity/Fusion** 的前提下，用可复现的模型/渲染先验证 2.5D 相机可读性、完美格挡时序、键盘组合可行性。
> 这不是最终游戏原型，而是“决策级证据”：通过 → 进入引擎集成；不通过 → 调整基线后再集成。
> 所有结论必须能由 `validation/` 下的脚本/数据复现。

## 非目标

- 不做 Unity 场景、不做 Fusion 联网、不做最终美术。
- 不验证服务器成本、后端吞吐、反作弊、内容量。
- 不把合成图/模拟结果当成玩家 playtest 结论。

## 目录

```text
validation/
  README.md                 # 本文件（Lead 维护）
  camera/                   # TASK-060：2.5D 相机/可读性
  netcode/                  # TASK-061：完美格挡/延迟补偿
  input/                    # TASK-062：键盘 rollover/组合
  review/                   # TASK-063：独立复核
  REPORT.md                 # TASK-064：Lead 汇总
```

## 通用要求

- Python：`C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`
- 可用：numpy 2.3.5、pandas 3.0.1、Pillow 12.3.0；**不要 pip install**。
- 随机种子固定（如 20261017），结果可复现。
- 每个 stream 至少交付：
  1. `run.py`（可重复执行）
  2. `REPORT.md`（结论先行、假设、方法、结果、限制、建议）
  3. `HANDOFF.md`（按 AGENTS.md §6 格式）
  4. 数据/图（CSV/SVG/PNG）
- 只写自己的 `validation/<area>/`；不改 `docs/`、`AGENTS.md`、`docs/tasks.json`、`validation/README.md`、`validation/REPORT.md`。
- 关键数字必须来自脚本输出；报告中标注“模型/合成，不是引擎/玩家实测”。

## TASK-060：2.5D 相机/可读性

**要回答**：固定 45–55° 正交、pitch 50°、yaw 45°、size 7–9、H=1.8m 时，角色是否 70–90px @1080p？6/10/14m 战斗是否在视口内？20/30m 是否必须 zoom-out？

**方法**：
- 实现正交投影：`u=dot(p,right), v=dot(p,up)`，`screen=center+u*scale, center-v*scale`，`scale=1080/(2*S)`。
- 计算角色屏高 `H*cos(pitch)*scale`，对比 70–90px；计算可见地面多边形/视口半宽半深。
- 渲染合成图：地面 1m 网格、6/10/14m 标记、3 个简化角色（帽/肩/武器/影子）、高度条；size 7/8/9 各一张（至少 size 8）。
- 输出 `metrics.csv`：size、pitch、角色 px、可见半宽/半深、6/10/14/20/30m 是否在视口。
- 结论：70–90px 是否成立；6/10/14m 是否可测；20/30m 是否只能 zoom-out；建议 size 默认值。

## TASK-061：完美格挡/延迟补偿

**要回答**：100ms 完美格挡在 30Hz tick + 200ms 回放 + 2–3 帧输入缓冲下是否公平？150ms 在线窗口 + 1 tick 容差是否够？是否必须 60Hz 排位？

**方法**：
- 离散事件模拟：30/60Hz tick、60Hz 输入、输入缓冲 0–3 帧、RTT 0/50/80/100/150/200ms、jitter 0/10ms、loss 0/2%、格挡窗口 100/150ms、回放 cap 150/200ms、defender-favoring on/off。
- 定义攻击时间线（轻击 8f startup/3f active）和防御输入时间戳；服务器用输入时间戳 + 回放判定。
- 每个配置 Monte Carlo ≥10k 次；输出 `results.csv`：成功率、误判率、平均伤害、p95 误差。
- 输出 `guard_success.svg`（成功率 vs RTT，分 30/60Hz、100/150ms）。
- 结论：推荐窗口/tick/回放 cap；M0 引擎验证的最小测试矩阵。

## TASK-062：键盘 rollover/组合

**要回答**：C+X、Z+X+C、方向+Z+C、方向+X+C 在 NKRO/6KRO/2KRO 上是否可稳定触发？软件层优先级/回退是否足够？

**方法**：
- 键盘模型：NKRO（不限）、6KRO（最多 6 非修饰键）、2KRO（最多 2 非修饰键；超出丢键）。
- 组合清单：单键、C+X、Z+C、Z+X、Z+X+C、方向+C、方向+Z+C、方向+Z+X、方向+Z+X+C、方向+X+C。
- 输出 `combo_matrix.csv`：组合 × 键盘 → 可同时按键数/是否超限/建议回退。
- 实现组合解析器：3f 方向窗口、C+X 防御优先、Z+X+C 必杀优先；输出测试用例结果。
- 生成 `manual_test.html`：浏览器键盘检测页，显示当前按下的键/同时按键数/最后组合；用户可在真实键盘上跑。
- 结论：哪些组合需要顺序输入/Space/改键；不能保证所有硬件。

## TASK-063：独立复核

- Reviewer 读三份报告 + 脚本，重跑至少一次；核对公式/数字/结论。
- 输出 `validation/review/REVIEW.md`：blocker/major/minor、能否作为决策证据、需要补什么。
- 不修改作者文件；作者修复后 reviewer 复核。

## TASK-064：汇总

Lead 写 `validation/REPORT.md`：
- 三个 stream 的结论/证据/限制；
- 对 docs/00/02/03 的修正建议；
- M0 引擎集成的最小任务清单；
- 是否建议进入 M0。

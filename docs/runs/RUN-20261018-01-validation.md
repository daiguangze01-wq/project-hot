# RUN-20261018-01 — M0-lite 技术验证

- 日期：2026-10-18
- 阶段：文档/验证阶段（无 Unity/Fusion 实现）
- 执行模型：Lead + 3 个独立验证 teammate + 1 个独立 reviewer
- 结论：**conditional go to M0，不是 validation passed**

## 1. 目标

在进入 Unity/Fusion M0 前，用模型/合成验证三件高风险假设：

1. 2.5D 正交相机能否同时满足 70–90px、6/10/14m 战斗可见性；
2. 完美格挡在 30Hz/200ms 回放/2–3 帧缓冲下是否公平；
3. 全键盘 ZXCV 组合在 NKRO/6KRO/2KRO 上是否可触发。

## 2. Agent 与分工

| Agent | TASK | 写域 | 产物 |
|---|---|---|---|
| camera-validator | TASK-060 | `validation/camera/` | run.py、metrics.csv、3 PNG、REPORT、HANDOFF |
| netcode-validator | TASK-061 | `validation/netcode/` | run.py、results.csv（9216 配置）、sensitivity、SVG、REPORT、HANDOFF |
| input-validator | TASK-062 | `validation/input/` | run.py、3 CSV、manual_test.html、REPORT、HANDOFF |
| validation-reviewer | TASK-063 | `validation/review/` | REVIEW.md、verify_numbers.py、rerun 日志 |
| Lead | TASK-064 | `validation/REPORT.md` | 汇总 + DR-002 |

## 3. 结果

| Stream | 判定 | 关键数字 |
|---|---|---|
| 相机 | pass（模型级） | size8/p50=78.1px；14m 正前方 0/9 可见；size15/p50 20m 出屏 |
| 联网 | conditional | 100ms/30Hz 误判 5.7% >5%；150ms/30Hz RTT80/100 成功 100/99.7%、误判 0.5/0.2%；cap150→200 是 RTT≥120ms 第一约束 |
| 键盘 | conditional（硬件不足） | NKRO/6KRO 15/15；2KRO 10/15；C+X 防御抢判 Z+X+C 必杀 |

## 4. 独立复核

- 6 blocker / 5 major / 9 minor；不能写 validation passed。
- 三路脚本全部 exit 0；camera/netcode/input 主要数据文件 SHA-256 逐字节一致；verify_numbers.py 462 checks 0 failures；manual_test.html 页面逻辑 28/28（非硬件）。
- 作者已修 M1（netcode 引用数字）与 M3（input 顺序必杀条件）；数据未变。

## 5. 未关闭

- B1 1.5m vs 1.8m；B2 yaw 未定义；B3 14m/zoom；B4 C+X vs 必杀；B5 容差/人群定义；B6 真实键盘 QA。
- 决策请求：`docs/decisions/DR-002-validation-baseline-fixes.md`（D1–D6，pending Human）。
- **M0 前置**：URP 相机对账、Fusion 格挡矩阵、3 款键盘 QA；未完成前不冻结 1.0 基线。

## 6. 产物

- `validation/REPORT.md`（汇总）
- `validation/camera/`、`validation/netcode/`、`validation/input/`
- `validation/review/REVIEW.md`
- `docs/decisions/DR-002-validation-baseline-fixes.md`
- `docs/07` §10、`docs/tasks.json` TASK-060–065、`docs/backlog.md`

## 7. 复盘

- 模型级验证成本低、发现了两类真问题（相机 14m 不可见、C+X 抢判必杀），比直接进 Unity 更早暴露。
- 仍需 M0 引擎/真实键盘证据；模型不能替代 Fusion/URP/playtest。
- 独立复核是必要的：作者报告中的 M1 数字漂移与 M3 条件错误均由 reviewer 发现。

# B6 — 3 款键盘人工 QA（TASK-066）

> AI 无法替代物理键盘测试；本目录把 B6 变成一份**可直接执行、可回填**的 QA 包。
> 工具：`validation/input/manual_test.html`（离线 file:// 可用；页面逻辑自检 28/28，不等于硬件证据）。

## 目标

在 **3 类键盘**上验证 ZXCV 组合是否可被真实硬件稳定上报：

1. NKRO / 全键无冲键盘
2. 标称 6KRO 键盘（或游戏键盘）
3. 办公薄膜 / 笔记本键盘（保守 2KRO 档）

每款键盘对 `manual_test.html` 的 **K01–K15 + S1–S3** 每项做 **100 次**，记录成功次数；目标：

- NKRO / 6KRO：支持组合成功率 **≥99%**；
- 2KRO/薄膜：允许部分组合失败，但必须记录实际失败项与替代路径（Space 防御/顺序输入/改键）；
- 任何键盘：不得出现“按了完全没反应且页面无记录”的静默丢键。

## 环境

- Windows 本机，关闭粘滞键/筛选键/切换键；关闭输入法组合（或切英文）。
- 浏览器：Chrome/Edge 最新稳定版；`file://` 打开 `../manual_test.html`。
- 关闭其他占用键盘的软件（远程桌面、虚拟机、宏工具、浏览器快捷键）。
- 每款键盘重新插拔/重新打开页面，填写键盘型号。

## 步骤

1. 打开 `validation/input/manual_test.html`。
2. 在“键盘信息”填：测试人、日期、键盘型号、连接方式（USB/PS2/蓝牙）、标称 NKRO/6KRO/2KRO。
3. 逐项执行 K01–K15、S1–S3；每项 100 次。页面会记录当前按下的键与最大同时键数。
4. 每项结束记录：尝试次数、成功次数、失败表现（丢哪个键/串键/OS 吞键）。
5. 点“生成报告”→“下载报告 .txt”，保存为 `report-<keyboard>-<date>.txt`。
6. 把 3 份报告与填写好的 `REPORT-TEMPLATE.md` 放回本目录。
7. 运行 `check-kit.ps1` 做完整性检查（只检查文件/字段是否齐全，不替代人工结论）。

## 通过/失败判定

| 结果 | 条件 |
|---|---|
| PASS | 3 款键盘完成；NKRO/6KRO 支持组合 ≥99%；2KRO 失败项已记录且有可执行替代 |
| CONDITIONAL | 2KRO 失败项多，但 Space/顺序/改键可覆盖；需 Human 决定最低键盘规格 |
| FAIL | NKRO/6KRO 也出现 ≥2% 丢键，或任何键盘静默丢键无法解释 |

## 交付

- `report-nkro-*.txt`
- `report-6kro-*.txt`
- `report-membrane-*.txt`
- `REPORT-TEMPLATE.md` 填好
- 结论写回 `validation/input/HANDOFF.md` 的 B6 段，并更新 `docs/07` TASK-066。

# TASK-061 Handoff — 完美格挡/延迟补偿技术验证

```text
TASK: TASK-061
STATUS: done

CHANGED:
  validation/netcode/run.py             # 新增：确定性离散事件 Monte Carlo 模型（stdlib+numpy）
  validation/netcode/results.csv        # 新增：9,216 配置 × 10,000 trials 全矩阵（35 列）
  validation/netcode/sensitivity.csv    # 新增：78 行敏感性场景（半/零容差、chord、到达时间判、60Hz 子步等）
  validation/netcode/sanity_checks.csv  # 新增：10 项模型自检（全部 PASS）
  validation/netcode/guard_success.svg  # 新增：成功率 + 误判率 vs RTT（4 曲线 + 95% CI）
  validation/netcode/summary_tables.md  # 新增：脚本自动生成的 T1–T17 汇总表（REPORT 数字来源）
  validation/netcode/REPORT.md          # 新增：结论先行报告 + M0 Unity/Fusion 最小测试矩阵
  validation/netcode/HANDOFF.md         # 新增：本文件
  # 未修改 docs/、AGENTS.md、docs/tasks.json、validation/README.md、validation/REPORT.md

DECISIONS:
  1. 模型口径（全部写入 REPORT §2.1/§2.3，run.py 文档字符串同步）：
     - 轻击命中偏移 = (8 + 3/2)×16.667 = 158.333ms；服务器在下一 tick 判定（delta~U(0,1 tick)）。
     - 防御者按“感知命中（one-way+interp）+ N(0,σ)”出手；σ∈{0,25,50}（0=perfect-timing 对照）。
     - 判定策略两种：ON = 客户端时间戳 + 视图延迟补偿 + cap 内追溯 + 1 tick 容差（主矩阵）；
       OFF = 严格实时（无时间戳补偿/无追溯/无容差），作为负对照。
     - 网络：对称 RTT、抖动 ±10ms、丢包 0/2%（冗余 B+1 份）、插值 0/33ms；输入缓冲为服务器侧对称
       缓冲（只影响抖动/冗余，不改变相对时序——A6，M0 需复核 Fusion 实现）。
  2. 矩阵在 TASK-061 必选维度之外增加 interp(0/33) 与 human_sigma(0/25/50) 两轴，合计 9,216 配置；
     必选列全部保留，报告按需切片（主配置见 REPORT §3）。
  3. 指标定义：success = 服务器判完美比例；success_given_in_window = 纯网络/实现交付率；
     false_positive = 服务器判完美但真实时序不在窗口内；p95_timing_error_ms = 服务器观测 |guard−hit|。
     “人因误差”与“网络/量化误差”通过 σ 轴与 p95 分量列分离（REPORT §3.2）。
  4. 参数推荐（模型级，非已批准基线）：
     - 在线窗口维持 150ms；100ms 仅本地/离线（100ms+1 tick 容差 → 误判 5.7% > 5%）。
     - 防御交互 cap 建议 200ms（cap150 在 RTT150 仅 18.4%，cap200 为 81.7%）。
     - 服务器容差建议 0.5 tick（30Hz ≤16.7ms；60Hz ≤8.3ms），不按 1 full tick。
     - 输入缓冲 2 帧（B0 在 2% 丢包下损失 ~2pp；B1 已恢复；B2 留抖动余量）。
     - 60Hz 排位：非 M0 成功率必要条件，但公平/精度收益明确（量化误差减半、误判更低），推荐排位默认。
  5. 误判口径/窗口单双边/defense cap 150 vs 200 等 docs 歧义只写成“待核实 + 建议”，未改 docs。

EVIDENCE:
  - 复现：`C:\Users\dai\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe validation\netcode\run.py`
    Python 3.12.14 / numpy 2.3.5；seed=20261017；10,000 trials/config；全矩阵 92.16M trials，约 7s。
  - 确定性：连续两次运行，results.csv SHA256 相同 =
    92C90D0995065514137D1A29F9F12E512B2319E008752E9C5C33C2392CF0E743
    sensitivity.csv SHA256 = 116B7D19E32D22E117979B41607A6463FE874CDC898D9399FAC9D681D6D56E49
    guard_success.svg SHA256 = 616102BAAA6037303EAE4A881D4B426688D81CCA0DF5C46A8108940367B85B6F
  - 自检 sanity_checks.csv 10/10 PASS：离线完美时序 100%；RTT200+无 lag comp 0%；到达时间判 RTT150 0.84%；
    defender-favoring 增益 +99.97pp；cap200 对 cap150 增益 +63.93pp；60Hz 误判更低；2% 丢包损失 2.03pp；
    RTT 单调；冗余恢复 +2.30pp；30Hz/60Hz 量化误差比 2.00×。
  - SVG：XML 可解析；用 Edge headless 渲染 1000×730 检查过布局（无重叠）。
  - 关键结论数字（主配置 cap200/ON/B2/jitter10/loss2%/interp33/σ25）：
    30Hz/150ms：RTT 0/50/80/100/150/200 成功率 100/100/100/99.7/81.7/18.4%，
      误判 0.5/0.4/0.5/0.2/0.0/0.0%；cap150 时 RTT100/150 成功率 82.4%/18.4%。
    30Hz/100ms：成功率 99.7/99.7/99.7/99.4/82.1/17.4%，误判 5.6/5.9/5.7/5.7/0.7/0.9%。
    60Hz/150ms：成功率 100/100/99.9/99.5/74.1/10.8%，误判 0.4/0.4/0.4/0.1/0.1/0.1%。
    按到达时间判（RTT80/100）：54.9%/27.3%（30Hz）→ 必须用输入时间戳。
  - 所有报告数字来自 results.csv/sensitivity.csv 的切片；summary_tables.md 为 run.py 自动生成；
    数据文件是唯一事实源（REPORT §3/§8.3 已写明“正文与数据文件不一致时以数据文件为准”）。

RISKS:
  - 这是合成模型，不是 Fusion/Unity 实测：A3 对称 RTT、A5 时钟/tick 映射零误差、A6 输入缓冲对称性
    都是乐观假设；若 Fusion 实现不符，成功率/误判会偏离模型（REPORT §7.1、§6.4 给对账方法）。
  - “误判 ≤5%”对测试人群/输入分布敏感：σ25 误判 0.5%，σ50 为 8.5%（30Hz/150ms/1 tick，RTT80）。
    M0 前必须定义测试人群与窗口单/双边口径（REPORT §7.2/§7.3）。
  - 防御交互 cap 150→200ms 与 60Hz 排位默认都属于联网基线/成本决策 → 需 ADR + Human 门（AGENTS.md §9）；
    本任务只给模型证据与建议。
  - 追溯撤销率在 RTT≥80ms 接近 100%（攻击方先看到命中后被撤销）——观感公平未量化，需 M0 实测/UX 设计。
  - 主矩阵未建模 C+X chord 延迟（敏感性 0–40ms 显示 100ms 窗口误判升到 16.9–22.2%）、位置命中盒 rewind、
    多段连招、服务器成本、反作弊/宏；“看到起手再反应”在 RTT0 已只有 158ms 可见预警（预判机制）。
  - 若 reviewer 认为窗口应为单边“受击前 100ms”而非居中，误判/成功率数字需重算（模型口径已明确标注）。

NEXT:
  1. validation-reviewer（TASK-063）：独立重跑 run.py（核对 seed/哈希/自检）→ 抽检 REPORT 表格与
     summary_tables.md/results.csv 一致性 → 复核 A3/A5/A6 假设与结论强度 → 输出 REV（blocker/major/minor），
     不改作者文件。
  2. Lead（TASK-064）：将本报告结论/证据/限制并入 validation/REPORT.md；决定是否向 Human 提交
     docs/02 §4.3（防御 cap 150→200）、docs/03 §5.4（容差 0.5 tick）、docs/00 §8（60Hz 排位）修订建议。
  3. M0 实现/QA：按 REPORT §6.2 最小矩阵在 Unity/Fusion 实测（A/B/C 阶段），用 results.csv 对账；
     先跑 C1/C2 负对照确认实现正确性，再跑 A1/A3/B1/B2 决策格。
  4. TASK-062（input-validator）：C+X chord 延迟是 TASK-061 的关键外部输入；若 chord p95 >16.7ms，
     按 REPORT §7.3/§6.5 重估在线窗口策略。

NOTES:
  - 共享任务 task-2 已完成（status=completed, revision 3）。
  - 仅写 validation/netcode/；临时 SVG 渲染检查图/临时脚本已删除；仓库其他文件未动。
  - 2026-10-18 按 REVIEW TASK-063 M1 修正 REPORT/HANDOFF 中敏感性引用数字（到达时间判定、窗口 200ms/cap150、
    chord 延迟、预压补偿、半 tick 容差等），使之与 sensitivity.csv/summary_tables.md 完全一致；数据文件与哈希未变
    （results 92C90D09…、sensitivity 116B7D19…、svg 616102BA…），结论方向不变。REPORT §3/§8.3 已写明
    “正文与数据文件不一致时以数据文件为准”。
```

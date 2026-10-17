# ADR-008 — 联网采用 Fusion 2 Server Mode + 30Hz 基线

- 状态：accepted
- 日期：2026-10-17
- 决策者：Tech Lead + Human
- 关联 REQ：REQ-TECH-001/002/006
- 影响范围：联网、战斗、服务器、成本、反作弊

## 1. 背景

2.5D 近战需要低延迟、服务器权威、客户端预测、命中盒回放；执行模型为 1 Human Architect + AI agents + 外包，token 不设上限，需要快速验证，不想从零写 netcode。

## 2. 选项

| 方案 | 优点 | 缺点 | 风险 |
|---|---|---|---|
| Fusion 2 Server Mode | tick/预测/AOI/Linux headless；快速；成熟 | CCU 订阅/锁定；需第三方托管 | 中 |
| Quantum 3 | 确定性 rollback；适合 1v1/2v2 | 16 人 3D 房成本高；学习曲线 | 中高 |
| FishNet/Mirror | 开源/自托管；无 CCU 费 | 预测/延迟补偿需自建 | 中高 |
| 自研 C# | 完全控制 | 6–12 个月追平；风险高 | 高 |

## 3. 决策

选择 **Fusion 2 Server Mode**，30Hz 基线。

- 客户端 60fps；输入缓冲；客户端预测 + 服务器校正。
- 命中盒回放 ≤200ms；同区 RTT 目标 <80ms。
- 30Hz 基线；排位 1v1/3v3 **推荐 60Hz**（成本/M0 A/B 后再定是否默认）。
- 保留 FishNet/自研迁移触发条件；不首版自研。

**2026-10-18 复访（DR-002 批准）**：

- 完美格挡：本地/离线 100ms；在线 **150ms**；**100ms 在线不上线**（模型误判 5.7% >5%）。
- 防御交互回放 cap **200ms**；容差 **0.5 tick**（30Hz≤16.7ms/60Hz≤8.3ms）；输入缓冲 2 帧。
- 判定必须用 `ClientTimeMs` + defender-favoring；禁止按到达时间判（RTT100 仅 27.3%/6.1%）。
- 60Hz 收益明确（量化 p95 25.8→12.9ms、误判更低），但服务器成本未评估。
- M0 先跑 C1/C2 负对照，再跑 A/B/C 决策格；与 `validation/netcode/results.csv` 对账。
- 依据：`validation/netcode/REPORT.md`、`validation/review/REVIEW.md` B5/M2/M5、`docs/decisions/DR-002-validation-baseline-fixes.md`。

## 4. 后果

### 正面
- 快速验证 2.5D 近战手感/联网；成熟 CSP/AOI。
- 服务器权威/反作弊基础好；可扩 MMO 房间。
- 与 Unity/C# 同栈。

### 负面/代价
- Photon CCU 订阅/托管成本；规模大时可能不划算。
- 供应商锁定；迁移需抽象网络层。
- 30Hz 对极限连段/帧数据可能有影响。

### 跟进
- M0 在 100ms/2% 丢包验收。
- 抽象输入/状态/命中接口，保留迁移 FishNet 的可能。
- 监控 CCU 成本/房间上限；设定迁移触发。

## 5. 复访触发

- 30Hz 手感不达标/排位需要 60Hz。
- Photon 成本超过自建。
- 房间上限/AOI 不满足 MMO。
- 供应商条款/地区合规问题。

## 6. 来源

- Photon Fusion 2 官方文档/定价。
- `docs/03` 联网/测试章节。

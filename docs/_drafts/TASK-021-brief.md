# TASK-021 — 合并 TDD（docs/03）

- Owner：TDD Lead
- Reviewer：Reviewer B（独立）
- 风险：中
- 依赖：TASK-013（03a）、TASK-014（03b）
- 输入：`docs/_drafts/03a.md`、`docs/_drafts/03b.md`、`docs/00`、`docs/05`、`docs/07`
- 输出：`docs/03-技术设计文档.md`，15–20k 中文字符

## 目标

把 03a（客户端/输入/战斗/联网）与 03b（后端/数据/API/部署/成本）合并成一份可指导原型的 TDD，统一架构图/术语/数字，补齐接口与里程碑。

## 必须保留

- Unity 6.3 LTS + URP；Fusion 2 Server Mode；30Hz；60fps 客户端；预测/校正/200ms 回放。
- 2.5D 固定正交相机；X/Y + 高度状态；全键盘输入/键位重映射/C+X 冲突/rollover。
- 共享 C# 战斗核心；数据驱动招式；地面 capsule/cylinder；服务器权威。
- Nakama + PostgreSQL/Redis/Kafka + Agones/K8s；数据模型/API/经济账本。
- 部署/可观测性/反作弊/测试矩阵/M0–M4/成本模型。
- 与 PRD 的数字/术语一致；ADR 引用。

## 合并规则

- 以 `docs/00` 为唯一数字来源；冲突标出。
- 03a 与 03b 的架构图不要重复；保留一张总图 + 分图。
- 统一章节编号；加 front matter；结论先行；表格/时序图。
- 不新增未批准决策；缺内容标「待补/待决」。
- 关键选型附官方文档；定价标「以官方报价为准」。
- 输出中文，Markdown + Mermaid。

## 验收

- [ ] 15–20k 字
- [ ] 总架构图 + 联网时序 + 数据 ER + API 示例 + 成本表 + 测试矩阵 + M0–M4
- [ ] 全键盘/键位冲突方案
- [ ] 2.5D 高度/判定方案
- [ ] 与 00/02 数字一致
- [ ] front matter/链接/无占位符
- [ ] handoff 提交

## 交接

完成后返回 handoff（AGENTS.md 格式），写清合并来源、删除的重复内容、发现的冲突、未决问题。

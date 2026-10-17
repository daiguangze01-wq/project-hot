# TASK-014 Handoff — TDD 后端/数据

```text
TASK: TASK-014
STATUS: done
CHANGED: docs/_drafts/03b.md; final merged into docs/03-技术设计文档.md by Orchestrator
DECISIONS: Nakama（会话/社交/排行/匹配候选）+ Go（角色/资产/经济/拍卖/邮件）+ Fusion（战斗/签名结果）；PG16/Redis7/Kafka/Agones/K8s；match_record 避保留字；platform_id 不写死 steam_id；wallet 首版 per-character、可扩展 owner_type/owner_id
EVIDENCE: 3 个 Mermaid、13 张表 + 支撑表、6 个 API 示例、12 条官方来源；成本模型 1k/10k/50k ≈ $3.9k/$30.9k/$139.5k，最终 docs/03 用区间并标模型
RISKS: Fusion 企业/自托管条款、云报价、EU 数据驻留待核实；D1–D7 待决；独立评审未回填
NEXT: D1–D7 走 ADR-013/decision request；Reviewer 复核 schema/成本
```

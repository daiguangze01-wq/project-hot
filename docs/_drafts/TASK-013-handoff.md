# TASK-013 Handoff — TDD 客户端/联网

```text
TASK: TASK-013
STATUS: done
CHANGED: docs/_drafts/03a.md; final merged into docs/03-技术设计文档.md by Orchestrator
DECISIONS: Unity 6.3 LTS + URP；30Hz 网络 tick + 60Hz 战斗子步；Fusion 2 Server Mode；预测/校正/200ms 回放；2.5D 地面 capsule/cylinder + 高度状态；全键盘输入/键位重映射/C+X 冲突
EVIDENCE: 客户端架构/输入/战斗/联网/性能/测试/M0 章节；4 个 Mermaid；12 条官方来源；与 docs/00 数字一致
RISKS: 30Hz 手感、C+X ghosting、2.5D 高度判定、出网成本；Fusion 锁定/迁移触发
NEXT: M0 原型在 100ms/2% 丢包验收；Reviewer 复核客户端/联网
```

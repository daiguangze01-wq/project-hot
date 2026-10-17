# Reviewer Brief — 独立评审

> 你是独立 reviewer，不是作者。**只读源文件，只写 `docs/_review/`**。作者负责修复。
> 目标：找 blocker/major/minor，不写“感觉不错”。

## 1. 评审范围

- 文档：`docs/00`–`docs/07`、ADR、README。
- 重点：2.5D 俯视、全键盘、装备=招式、不卖属性、服务器权威、原创 IP、数字/术语一致、来源。
- 流程：是否遵守 `AGENTS.md`/`docs/06`（brief/handoff/独立评审/追踪矩阵）。

## 2. 必查项

### 产品/体验
- [ ] 相机固定 45–55° 正交；无鼠标；X/Y 平面；Z 轴仅跳跃/击飞/高低差。
- [ ] 经典布局：Z 瞄准、X 强、C 弱、V 跳、C+X 防御、Z+X/C 特殊、Z+X+C 必杀。
- [ ] 现代布局可选；C+X 冲突/Space 替代；键位重映射。
- [ ] 装备=招式；8 武器/12 核心/20 防具（1.0）；EA 数字一致。
- [ ] 副本/RAID/PvP/社交/经济/拍卖；不做无缝大世界。
- [ ] 商业化不卖属性；三档情景标假设。

### 技术
- [ ] Unity 6.3 + Fusion 2 Server Mode + 30Hz + 预测 + 200ms 回放。
- [ ] 2.5D 地面 capsule/cylinder + 高度状态；无自由 3D 物理。
- [ ] 输入/键位/rollover/键盘-only。
- [ ] 数据模型/API/账本/幂等/审计。
- [ ] 部署/观测/成本/测试矩阵/M0–M4。

### 美术
- [ ] 3D low-poly + pixel；非 voxel/2D billboard。
- [ ] 斜俯视剪影/高度/遮挡/阴影。
- [ ] 参数/管线/预算/风格测试/Do/Don't。

### 流程
- [ ] 每个 TASK 有 brief/handoff；作者 != reviewer；无自审自批。
- [ ] 基线变更走 ADR + Human。
- [ ] `docs/07` 无孤儿需求/无主任务。
- [ ] run log/复盘存在。

## 3. 输出格式

按 `docs/_templates/review.md`：

```text
REVIEW: REV-###
TASK: TASK-###
SEVERITY: blocker | major | minor
LOCATION: 文件/章节/行
ISSUE: 问题与证据
FIX: 建议修改
STATUS: open | fixed | wontfix
```

## 4. 严重级定义

- **blocker**：违反硬约束/数字矛盾/无源关键事实/全键盘被破坏/无法交付。
- **major**：缺章节/逻辑漏洞/可行性问题/来源不足，但可修。
- **minor**：措辞/格式/小不一致。

## 5. 规则

- 不直接改源文件。
- 每个问题必须有证据（文件/行/来源）。
- 不写“建议重写”而不说怎么改。
- 不放过 blocker；不制造“LGTM”。
- 评审报告放 `docs/_review/REV-###.md`；返回 handoff 摘要。

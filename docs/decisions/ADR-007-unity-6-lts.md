# ADR-007 — 引擎选择 Unity 6.3 LTS + URP

- 状态：accepted
- 日期：2026-10-17
- 决策者：Tech Lead + Human
- 关联 REQ：REQ-TECH-001/005
- 影响范围：客户端、工具、招聘、授权、性能

## 1. 背景

需要 2.5D 俯视、3D 低多边形+像素贴图、全键盘、服务器权威联网、PC 优先、未来主机/移动可能。执行模型：1 Human Architect + AI agents + 按需外包；技术 token 不设上限。

## 2. 选项

| 引擎 | 优点 | 缺点 | 风险 |
|---|---|---|---|
| Unity 6.3 LTS + URP | C# 迭代快；Fusion/Quantum/FishNet 生态；2.5D/像素适配；PC/主机/移动一套工程 | 授权/服务成本；URP 需自定义 shader | 中 |
| Unreal 5 | 画面/动画/GAS 强 | 重、C++/蓝图、像素风需后处理、包体大 | 中高 |
| Godot 4 | MIT、轻、2D 像素强 | 3D 动作/联网/主机生态弱 | 中 |
| 自研/Web | 控制力强 | 成本/风险极高 | 高 |

## 3. 决策

选择 **Unity 6.3 LTS + URP**。

- C# 客户端 + 共享战斗核心；Fusion 2 Server Mode。
- URP + 自定义像素/描边/色板 shader；Addressables/UI Toolkit/Input System。
- 不在首版引入 DOTS/ECS 重架构；先跑通玩法/联网。

## 4. 后果

### 正面
- 迭代快、生态成熟、招聘容易；与 Fusion/Nakama 集成好。
- 2.5D 正交相机/像素渲染/UI 工具链成熟。
- PC/主机/移动扩展路径清晰。

### 负面/代价
- Unity 许可/定价需持续评估；URP 自定义渲染有技术成本。
- 与 UE 的 3A 画面差距；但本项目不需要写实。

### 跟进
- 评估 Unity 6.3 LTS 许可/2026 定价。
- 像素/描边/色板 shader 做技术原型。
- 监控 Unity 版本支持周期。

## 5. 复访触发

- Unity 许可/定价不可接受。
- 性能/渲染无法满足 2.5D 像素目标。
- 团队引擎能力/招聘市场变化。
- 主机认证要求。

## 6. 来源

- Unity 6.3 LTS 官方发布信息。
- Fusion 2 / Nakama / Agones 官方文档。
- `docs/03` 技术选型章节。

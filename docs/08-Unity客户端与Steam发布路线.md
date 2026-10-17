# Unity 客户端与 Steam 发布路线

> 结论：`mvp/` 的 Web 版本是**验证原型**，不是最终交付形态。正式客户端按 ADR-007/012 用 **Unity 6.3 LTS + URP + Photon Fusion 2**，Windows x64 优先，通过 Steam 发行。
>
> 当前环境未安装 Unity/.NET，因此本文件是**迁移与工程路线**，不是已编译验证的客户端。

## 1. 为什么 Web MVP 不是最终客户端

Web MVP 的价值是快速验证：

- 2.5D 俯视 + 全键盘 ZXCV 的操作形态；
- 服务器权威的命中/防御/必杀/重生；
- 4 个数据驱动核心的招式差异；
- 多人房间/PvP 的最小闭环。

它不能作为 Steam 客户端，因为：

- Canvas 渲染不是 URP/3D 低模+像素贴图管线；
- HTTP/SSE 不是 Fusion 2 的预测/校正/回放；
- 没有 Steamworks、成就/云存档/好友/大厅；
- 没有 Unity 的构建、打包、Steam Deck/Proton 验证；
- Web 版本的 30Hz/输入时序不能替代 M0 引擎验证。

## 2. 推荐引擎与版本

| 项 | 选择 | 说明 |
|---|---|---|
| 引擎 | **Unity 6.3 LTS** | ADR-007；LTS 适合 18–24 个月周期 |
| 渲染 | URP | 低模+像素贴图、正交相机、描边/色板 shader |
| 输入 | Input System 1.14+ | 全键盘、重映射、C+X 组合、rollover 自检 |
| 联网 | **Photon Fusion 2 Server Mode** | 服务器权威、预测/校正、命中盒回放；ADR-008 |
| UI | UI Toolkit | 键盘导航/HUD/设置 |
| 构建 | Windows x64 IL2CPP | Steam 首版；Linux/Steam Deck 后评估 |
| 后端 | Nakama + PostgreSQL/Redis + Agones | 账号/社交/匹配/经济；M1 后接入 |
| 发行 | Steamworks | AppID、depot、Playtest、成就/云存档 |

> 如果你更想用 Unreal/Godot，需要改 ADR-007 并重估动画/网络/资产管线；当前默认 Unity。

## 3. 工程结构（目标）

```text
client-unity/
  Assets/
    Hot/
      Sim/                 # 纯 C# 共享核心，无 UnityEngine 依赖
        CoreModels.cs
        MoveTable.cs
        CombatSim.cs
        CoresData.cs
      Client/
        Input/KeyboardInput.cs
        Camera/OrthoCameraRig.cs
        Render/CharacterView.cs
        UI/HudController.cs
        Bootstrap/GameBootstrap.cs
      Net/
        FusionBootstrap.cs
        NetworkInput.cs
        ServerCombat.cs
      Data/
        cores.json         # 与 mvp/cores.json 同源
    Scenes/
      Arena.unity
  Packages/manifest.json
  ProjectSettings/
```

原则：

- `Hot.Sim` 不引用 `UnityEngine`，客户端预测与 Linux headless 服务器共用。
- 渲染/输入/UI 只在 `Hot.Client`；网络只在 `Hot.Net`。
- 招式/核心数据从 JSON/ScriptableObject 读，不把数值写死在 MonoBehaviour。
- 服务器权威：客户端只发 `InputFrame`，命中/伤害/资源由服务器算。

## 4. 从 Web MVP 迁移

| Web MVP | Unity 目标 | 说明 |
|---|---|---|
| `mvp/sim.js` | `Hot.Sim/CombatSim.cs` | 逐条移植移动/攻击/防御/完美格挡/冷却/重生；用 C# 单元测试对齐 |
| `mvp/cores.json` | `Hot/Data/cores.json` + `CoresData.cs` | 4 核心先迁，后续扩到 12；用 JSON 或 ScriptableObject |
| `mvp/public/game.js` 投影/绘制 | URP 正交相机 + 3D 低模/像素贴图 | pitch50/yaw45/size8；6/10m 可读；14m 边缘指示 |
| `mvp/public/game.js` 键盘组合 | Input System + `KeyboardInput.cs` | 70ms 组合缓冲改为 60Hz InputFrame/时间戳；服务器解析 |
| `mvp/server.js` HTTP+SSE | Fusion 2 Server Mode | 30Hz tick + 60Hz 子步；200ms 回放；session token 由 Fusion 连接身份替代 |
| `mvp/public` HUD | UI Toolkit | 键盘导航/HUD/计分/技能冷却 |
| `mvp/test` | NUnit/Unity Test Framework | 同一批规则用例迁移 |

## 5. 里程碑

| 阶段 | 时间 | 交付 | 验收 |
|---|---|---|---|
| U0 工程/输入/相机 | 1–2 周 | Unity 工程、URP 正交相机、键盘 Input、1 张训练场 | size8/pitch50/yaw45；1.8m≈78px；6/10m 可见；全键盘无鼠标 |
| U1 本地战斗 | 2–4 周 | `Hot.Sim` 移植、4 核心、木桩、HUD | 与 Web MVP 规则一致；连段/防御/必杀/重生 |
| U2 Fusion 2 联网 | 4–8 周 | 2 人房、服务器权威、预测/校正、200ms 回放 | 100ms/2% 丢包；150ms 格挡矩阵；C1/C2 负对照 |
| U3 Steam 构建 | 8–12 周 | Windows IL2CPP、Steamworks、Playtest | Steam Playtest 可安装/启动/退出；无 P0 |
| U4 垂直切片 | 12–16 周 | 1 城镇/1 野外/2 副本/2 PvP/EA 内容 | 2k CCU 压测；D1/D7 初测 |

> 时间以内容/美术/合规门禁为准；不是工程人力估算（AI-native 执行模型）。

## 6. Steam 发布清单

- Steamworks 合作伙伴账号 + AppID（$100 Steam Direct，需 Human/公司主体）。
- Windows x64 IL2CPP 构建；Steamworks SDK 初始化；App ID 注入。
- Depot/分支：`dev`、`playtest`、`public`；`steamcmd` 上传脚本。
- Steam Playtest（先小规模）→ 商店页 → 愿望单 → EA。
- 成就/云存档/好友/排行榜（按需）；Steam Deck/Proton 验证后置。
- 隐私政策/EULA/年龄分级/区域合规；国服版号另计。
- 反作弊：服务器权威 + EAC/BattlEye 评估（1.0 前）。

## 7. 当前环境缺什么

| 项 | 状态 | 需要 |
|---|---|---|
| Unity 6.3 LTS | **未安装** | Unity Hub + Editor + Windows Build Support |
| .NET SDK | 未安装 | 可选；用于纯 C# `Hot.Sim` 单测 |
| Fusion 2 | 未安装 | Photon 账号 + Fusion 2 SDK |
| Steamworks | 未配置 | 合作伙伴账号/AppID |
| 3 款键盘 | 未测 | B6 QA 包 |

## 8. 下一步

1. Human 安装 Unity 6.3 LTS（Windows Build Support）+ 创建 URP 工程。
2. 申请/导入 Fusion 2；创建 2 人测试房。
3. Lead 按 U0–U2 移植 `Hot.Sim`/输入/相机/联网；每个阶段独立测试。
4. Steamworks 账号/AppID 由 Human 准备，U3 接入。

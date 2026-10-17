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

## 2. 费用与许可（2026-10 核对）

| 项 | 结论 | 依据 |
|---|---|---|
| Unity 能否上 Steam | **能**。Unity 构建 Windows x64，Steamworks 只接收可执行构建；引擎不限 | Steamworks 文档；Unity 构建 |
| Unity Personal | **免费**，且可用于商业游戏/Steam 销售；但仅当过去 12 个月 **Total Finances（总收入 + 融资）< $200,000** | [Unity 许可选择](https://support.unity.com/hc/en-us/articles/28114350573460-Which-Unity-Editor-license-should-I-use-purchase)、[Unity Personal 商用](https://support.unity.com/hc/en-us/articles/205253119-Can-I-make-a-commercial-game-with-Unity-Free-Personal-Edition) |
| Unity Pro | **超过 $200K 必须升级 Pro**（按订阅付费）；注意是营收 **+ 融资**，不是利润 | 同上 |
| Runtime Fee | **没有**（2024 已取消） | [Unity 取消 Runtime Fee](https://unity.com/blog/unity-is-canceling-the-runtime-fee) |
| Splash | Unity 6 Personal **可关闭/自定义** Made with Unity 启动画面 | [Unity 支持](https://support.unity.com/hc/en-us/articles/212165803-How-do-I-remove-the-Splash-Screen-from-my-build) |
| Steam Direct | **$100/款应用**；达到 $1,000 adjusted gross revenue 后可返还 | [Steam Direct Fee](https://partner.steamgames.com/doc/gettingstarted/appfee) |
| Steam 分成 | 标准 **30%**；达到阈值后 25%/20%（以 Steamworks 当前条款为准） | Steamworks |
| Unity 6.3 LTS | 已发布，按 Hub 最新 6000.3.x LTS 安装 | [Unity 6.3 LTS](https://unity.com/blog/unity-6-3-lts-is-now-available) |

> 关键提醒：**$200K 是“收入 + 融资”总额**。如果拿了一轮超过 $200K 的投资，即使还没收入，也要升级 Unity Pro。个人/小团队无融资、收入低于 $200K 时，Unity Personal 免费且可商用。

## 2.1 推荐引擎与版本

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
| U0 工程/输入/相机 | 1–2 周 | Unity 工程、URP 正交相机、键盘 Input、1 张训练场 | size8/pitch50/yaw45；1.8m≈78px；6/10m 可见；全键盘无鼠标；**camera-relative 屏向移动**（[调研](_research/camera-relative-movement.md)） |
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
| Unity Hub | **已安装 3.22.3**（MSIX，per-user） | 已启动；等待 Unity 账号登录 |
| Unity Editor | **已安装 6.3 LTS 6000.3.26f1**，`D:\Unity\Hub\Editor\6000.3.26f1\Editor\Unity.exe` | 已通过 Hub CLI 安装；`Unity.exe -version` 验证 6000.3.26f1 |
| Windows Build Support (IL2CPP) | **已安装**（`windowsstandalonesupport\Variations\win64_player_*_il2cpp`） | 已随 Editor 模块安装 |
| Unity 账号/Personal License | **已登录/已激活 Personal** | Licensing Client resolved Unity Personal（无限期） |
| 工程/U0 | **已创建** `client-unity/ProjectHot`；Arena 场景 + Windows 构建成功 | 见 `client-unity/HANDOFF.md` |
| .NET SDK / Visual Studio | 未安装 | U0 Mono 构建不需要；IL2CPP/IDE 构建前再装 VS Community |
| Fusion 2 | 未安装 | Photon 账号已有；需要创建 App/导入 SDK |
| Steamworks | 未配置 | 合作伙伴账号/AppID |
| 3 款键盘 | 未测 | B6 QA 包 |

## 8. 下一步

1. Human 打开 `client-unity/ProjectHot`，Arena 场景 Play；或直接运行 `Builds/U0/ProjectHot.exe`，目视验收相机/输入/木桩。
2. U1：把 `mvp/sim.js` 规则移植到 `Assets/Hot/Sim`（纯 C#），接 4 核心/连招/防御/必杀。
3. U2：创建 Photon Fusion App，导入 Fusion 2 SDK；2 人服务器权威房。
4. U3：IL2CPP + Steamworks/Playtest；届时安装 Visual Studio C++ 工作负载。
5. Steamworks 账号/AppID 由 Human 准备。

# client-unity — Unity 6.3 LTS 客户端（U0）

> **这是一个可打开的 Unity 工程**：`client-unity/ProjectHot/`。
> Editor：Unity **6.3 LTS 6000.3.26f1**；URP 17.0.1；Input System 1.20.1。
> 当前阶段：**U0 相机/输入/训练场**，Fusion 2 与 Steam 构建尚未接入。

## 打开

1. Unity Hub → Add → 选择 `client-unity/ProjectHot/ProjectSettings/ProjectVersion.txt` 所在目录。
2. 打开场景：`Assets/Scenes/Arena.unity`。
3. 点 Play。

或直接运行已构建的 U0：

```text
client-unity/ProjectHot/Builds/U0/ProjectHot.exe
```

## 操作（U0）

- WASD / 方向键：移动
- V：跳跃
- C / X：轻/重击（打木桩）
- Space 或 C+X：防御（U0 只有状态显示）
- 无鼠标战斗/镜头；固定正交相机 pitch=50、yaw=45、size=8。

## 工程结构

```text
Assets/
  Hot/
    Client/          # 相机/输入/移动/木桩/HUD（U0）
    Editor/          # Arena 场景生成、U0 Windows 构建
    Data/cores.json  # 4 核心数据（从 MVP 复制，U1 接入）
  Scenes/
    Arena.unity      # U0 训练场
  Settings/          # URP 模板设置
Packages/manifest.json
ProjectSettings/
```

## 重新生成/构建

```powershell
# 生成 Arena 场景
Unity.exe -batchmode -quit -projectPath client-unity\ProjectHot `
  -executeMethod Hot.Editor.ArenaBootstrap.CreateArena `
  -logFile client-unity\bootstrap.log

# 构建 Windows U0
Unity.exe -batchmode -quit -projectPath client-unity\ProjectHot `
  -executeMethod Hot.Editor.BuildU0.Build `
  -logFile client-unity\build-u0.log
```

## 状态/限制

- U0 场景与 Windows 构建**已通过 batchmode 构建成功**；Play 画面/手感需要 Human 目视验收。
- U0 是本地原型：没有服务器权威、没有 Fusion、没有连招/技能/防御判定。
- 正式 U1 把 `mvp/sim.js` 规则移植到 `Assets/Hot/Sim/`，U2 接入 Fusion 2，U3 接 Steamworks。
- `Library/`、`Builds/`、`Temp/` 等生成物已在 `.gitignore`。

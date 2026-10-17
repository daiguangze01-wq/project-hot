# client-unity — Unity 6.3 LTS 客户端（ staging）

> 这不是一个可直接打开的 Unity 工程，而是**迁移 staging 目录**：
> 当前环境未安装 Unity，无法生成/验证 `.unity` 场景、ProjectSettings 和包版本。
> 安装 Unity 后，按下面步骤创建工程，再把 `Assets/` 复制进去。

## 1. 安装

1. 安装 **Unity Hub**。
2. 安装 **Unity 6.3 LTS**（Hub 中最新的 6000.3.x LTS），勾选：
   - Windows Build Support (IL2CPP)
   - Microsoft Visual Studio / Rider（任选）
3. 创建新工程：模板 **Universal 3D (URP)**，名称 `ProjectHot`。
4. 安装包：
   - Input System
   - UI Toolkit（Unity 6 内置）
   - Cinemachine（仅 UI/展示，不用于战斗镜头）
   - Photon **Fusion 2**（从 Photon 官网导入）

## 2. 复制 staging

把本目录的：

```text
Assets/Data/cores.json
```

复制到 Unity 工程的 `Assets/Hot/Data/cores.json`。

后续 `Assets/Hot/Sim/`、`Client/`、`Net/` 的 C# 文件由 Lead 在 Unity 工程内生成/移植，避免在没有编译器的情况下交付不可验证的 `.cs`。

## 3. 工程约定

- `Assets/Hot/Sim/`：纯 C#，不引用 `UnityEngine`；客户端预测与 Linux headless 共用。
- `Assets/Hot/Client/`：Input System、URP 正交相机、角色视图、UI Toolkit。
- `Assets/Hot/Net/`：Fusion 2 Server Mode 的 NetworkBehaviour/输入/服务器战斗。
- `Assets/Scenes/Arena.unity`：训练场，先 1 张图、2 个玩家、木桩。
- 数据：`Assets/Hot/Data/cores.json`（与 `mvp/cores.json` 同源）。
- 服务器权威：客户端只发 `InputFrame`；命中/伤害/资源由服务器算。

## 4. 第一个场景验收（U0）

- `Camera.orthographic = true; orthographicSize = 8;` pitch=50°、yaw=45°。
- 1.8m 角色包围盒在 1080p 下约 78px；6/10m 可见；14m 用边缘指示。
- WASD/方向 + Z/X/C/V + Space/C+X 全键盘；无鼠标。
- 1 张训练场 + 木桩；无网络。

## 5. 之后

- U1：移植 `mvp/sim.js` 规则到 `Hot.Sim`；4 核心；本地战斗。
- U2：Fusion 2 2 人房；100ms/2% 丢包；150ms 格挡矩阵。
- U3：Windows IL2CPP + Steamworks/Playtest。

## 6. 当前状态

- Unity：**未安装**（本机检查无 Unity Hub/Editor）。
- 因此本目录只有 staging 数据；不能声称“Unity 客户端已完成”。
- 安装完成后，Lead 可在该工程内按 `docs/08-Unity客户端与Steam发布路线.md` 执行。

# 角色与动作资产规格 v0.1

## 1. 角色

| 项 | 3D 路线（基线） | 2D sprite 路线（样张） |
|---|---|---|
| 身高 | 1.8m；低模 2.6m 根节点缩放到 1.8m | 96×96 帧内约 78px 高 |
| 朝向 | 角色可 360° 转向；相机固定 | 先 4 向（S/E/N/W），再评估 8 向 |
| 换装 | 武器/头/身/披风分槽 | 换色/换武器图层；复杂度高 |
| 贴图 | 256×256 或 128×128 像素 atlas，无烘焙光 | 每帧调色板 ≤32 色 |
| 轮廓 | 1px 深色描边（shader/贴图） | 1px 深色描边 |
| Pivot | 脚底中心 | 脚底中心 `(48, 8)` |

## 2. 动作模块（必须）

| ID | 动作 | 2D 帧数 | 3D 占位 clip（KayKit） | 循环 |
|---|---|---|---|---|
| `idle` | 待机 | 4 | `Idle` | 是 |
| `walk` | 行走 | 8 | `Walking_A` | 是 |
| `run` | 奔跑 | 8 | `Running_A` | 是 |
| `light_attack` | 轻攻击 | 5 | `1H_Melee_Attack_Slice_Diagonal` | 否 |
| `heavy_attack` | 重攻击 | 7 | `1H_Melee_Attack_Chop` | 否 |
| `run_light_attack` | 奔跑+轻攻击 | 5 | `RunLightAttack`（当前映射同一轻击 clip） | 否 |
| `run_heavy_attack` | 奔跑+重攻击 | 7 | `RunHeavyAttack`（当前映射同一重击 clip） | 否 |
| `jump` | 跳跃 | 5 | `Jump_Full_Short` | 否 |
| `jump_attack` | 跳跃攻击 | 6 | `JumpAttack`（当前映射突刺 clip） | 否 |
| `guard` | 防御 | 3 | `Blocking` | 是 |

> 3D 路线的“奔跑+轻/重”当前是**状态名 + 同一攻击 clip**（保留移动），等正式动画/upper-body mask 再拆分；这不影响 U1 的输入/时序验证。
> 2D 路线的帧数可按 6/8 帧扩展，但必须保持同一 canvas、pivot、色板。

## 3. 命名与导出

```text
角色概念： art/characters/hot_blade_01/character_ref.png
2D 帧：    art/characters/hot_blade_01/sheets/hot_blade_01_<dir>_<anim>_<frame>.png
spritesheet：art/characters/hot_blade_01/sheets/hot_blade_01_<dir>_<anim>.png
3D 资产：   art/characters/hot_blade_01/model/body.fbx
贴图：      art/characters/hot_blade_01/textures/body_atlas_256.png
```

- 帧号从 `00` 开始；dir = `S/E/N/W`（先 4 向）。
- 导出：PNG、RGBA、无抗锯齿；spritesheet 每行一个方向，每列一帧。
- 记录 `manifest.json`：tool/model/prompt/seed/license/date/author/review。

## 4. Unity 导入

| 设置 | 值 |
|---|---|
| Sprite Mode | Multiple（2D） |
| Pixels Per Unit | 96（与 1.8m≈96px 对齐） |
| Filter Mode | Point (no filter) |
| Compression | None |
| Pivot | Custom (0.5, 0.08) |
| Animation | 按帧序列生成 clip；30/60Hz 采样 |
| 3D Model | Humanoid/Generic；Animator 状态见 `CharacterAnimationDriver` |

## 5. 当前 U0 占位

- 角色：KayKit Knight（CC0），缩放到约 1.8m；材质 `KnightMat`。
- 动画状态：`Idle/Walk/Run/LightAttack/HeavyAttack/RunLightAttack/RunHeavyAttack/Jump/JumpAttack/Guard`。
- 输入：Shift 跑；C 轻；X 重；Space/C+X 防御；V 跳。
- 截图：`client-unity/screenshots/u0-knight.png`。
- **不是最终美术**；只验证动作状态机/相机/输入/时序。

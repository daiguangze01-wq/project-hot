# 2.5D 固定相机下的移动方向调研

- 日期：2026-10-18
- 触发：U0 中按 D/右，画面看起来往右上；根因是 **世界坐标 X/Z 输入**与 **yaw45 相机画面**不一致。
- 结论：键盘移动应使用 **camera-relative（屏幕方向）输入**，不是世界 X/Z；相机跟随玩家时仍保持固定 yaw，输入方向随相机投影。

## 常见做法

| 方案 | 代表 | 做法 | 对本项目 |
|---|---|---|---|
| 相机相对（camera-relative） | Hades、Lost Ark 等 3D 俯视/等距动作 | 把输入 `(x,y)` 投影到相机的 **right/forward 在地面的投影**，归一化后移动 | **采用** |
| 输入绕相机 yaw 旋转 | 大量 Unity/Unreal 等距教程 | `Quaternion.Euler(0, cameraYaw, 0) * new Vector3(input.x,0,input.y)` | 固定 yaw 时与上一种等价；更简单但只支持 yaw |
| 点击移动（screen-to-ground） | Diablo/POE 类 | 鼠标屏幕点 raycast 到地面，角色向落点走 | 不适用：本项目鼠标不参与战斗/镜头，键盘-only |
| 角色相对（tank controls） | 部分第三人称/恐怖游戏 | 左右转角色、前后走 | 不符合 ZXCV 读招/等距操作 |
| 固定世界轴 | 某些 2D/斜 45° 游戏 | 直接 `x=world X, y=world Z` | **失败**：yaw45 下 D 会显示为右上，正是本次 bug |

参考：
- [Stack Overflow — Camera Relative Movement](https://stackoverflow.com/questions/37637954/camera-relative-movement)
- [GameDev SE — Unity move with WASD in the way the camera is facing](https://gamedev.stackexchange.com/questions/182853/unity-move-with-wasd-in-the-way-the-camera-is-facing)
- [GameDev SE — Adjusting movement vector for isometric input](https://gamedev.stackexchange.com/questions/214534/adjusting-movement-vector-for-converting-to-input-vector-in-an-isometric-game)
- [Unity Discussions — Hades-like isometric movement](https://discussions.unity.com/t/hades-like-isometric-movement/882050)
- Lost Ark 类俯视动作游戏同样以相机方向为移动基准；其相机是固定俯视/等距，而不是自由轨道。

## 本项目实现

`Assets/Hot/Client/PlayerMotor.cs`：

```csharp
Vector3 right = Vector3.ProjectOnPlane(cameraTransform.right, Vector3.up).normalized;
Vector3 forward = Vector3.ProjectOnPlane(cameraTransform.forward, Vector3.up).normalized;
Vector3 dir = right * input.x + forward * input.y;
```

- W/S/A/D = 屏幕上下左右；斜向按相机投影后归一化，速度不因 pitch 变慢。
- 角色朝向 = 实际移动方向；攻击使用角色 forward，因此“屏幕方向→朝向→攻击”一致。
- `OrthoCameraRig` 已跟随 player 的 X/Z；最终形态可继续跟随，但 yaw 固定（不做自由轨道）。
- 若未来相机可旋转，同一套 camera-relative 逻辑自动适配，无需改输入映射。

## 验收

`Hot.Editor.U0Checks`（Unity batchmode）结果：

```text
PASS D -> screen-right (world +X,-Z) -> (0.707, 0.000, -0.707)
PASS W -> screen-up (world +X,+Z) -> (0.707, 0.000, 0.707)
PASS S -> opposite of W -> (-0.707, 0.000, -0.707)
PASS D/W perpendicular
U0 CAMERA-RELATIVE CHECK PASS
```

Human 目视仍待：D 应显示为屏幕正右，W 为正上，斜向为屏幕斜向。

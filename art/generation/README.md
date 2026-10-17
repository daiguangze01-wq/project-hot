# AI 美术生成请求 / 收件

> 目的：让外部 AI（PixelLab / Retro Diffusion / GPT Image / 其他）按**同一风格圣经**产出可评估的角色与动作资产。
> 当前没有 API key / 本地模型；需要 Human 介入（见文末）。

## 重要：不要生成整只角色

ADR-013 已改向 **统一基础模型 + 模块化装备（头发/衣服/武器/披风…）**。
- 不再生成“整套角色 + 整套动作”（旧请求已 superseded）。
- 先生成 `base_body`、`hair`、`top`、`weapon` 等**独立件**，以及 3D 概念/UV 模板；动画由共享骨架提供。
- 需要 3D mesh 时，AI 只出概念/贴图，mesh 要 Blender/人工清理/绑定。
- 详细架构见 [docs/09-角色与模块化装备系统](../../docs/09-角色与模块化装备系统.md)。

## 推荐顺序

1. **PixelLab**（角色 + 动画，首选）
   - 输入 `character_ref`，生成 4/8 向、idle/walk/run/attack/jump。
   - 导出 PNG spritesheet 或逐帧 PNG。
2. **Retro Diffusion (RD Animation)**（spritesheet，备选）
   - 直接按 walk/run 等格式出风格一致的 sheet；适合做 walk/run 对照。
3. **GPT Image / Midjourney**（概念/风格板，不作为动画帧）
   - 出 1 张角色概念/色板；用来确定 `character_ref`，再交给 1/2 做动画。
4. **Meshy / Tripo**（仅 3D 备选）
   - 若坚持 3D 低模：AI 图生 3D 后仍需手工 rig/动画；战斗动作不要直接依赖 AI 生成。

## 生成顺序（不要一次全做）

```text
① character_ref（正面/3/4，透明或纯色背景）
② idle + walk（验证比例/脚底/pivot/色板）
③ run + light + heavy
④ run_light + run_heavy + jump + jump_attack
```

## 收件格式

```text
art/generated/inbox/hot_blade_01/
  character_ref.png
  sheets/hot_blade_01_S_idle.png
  sheets/hot_blade_01_S_walk.png
  ...
  manifest.json
```

`manifest.json` 至少包含：工具/模型、prompt、negative、seed、参考图、日期、许可/条款链接、人工修改。

## 最小人工介入（三选一）

### A. 给 API key（推荐 PixelLab）

- 注册：<https://www.pixellab.ai/>
- 在账号/API 页面创建 key。
- **不要发到聊天里**。在本机设置环境变量：
  ```powershell
  # 只对当前用户；值不要写进仓库
  [Environment]::SetEnvironmentVariable('PIXELLAB_API_KEY','<your-key>','User')
  ```
- 告诉我“已设置”，我读取环境变量（只读取，不打印）并调用。

### B. 给 Replicate token（Retro Diffusion）

- 注册：<https://replicate.com/>
- 创建 `REPLICATE_API_TOKEN`，同样设置到用户环境变量。
- 我用 `retro-diffusion/rd-animation` 生成 spritesheet。

### C. 你网页生成，我收件

- 用 PixelLab/Retro Diffusion 网页按 [request-hot-blade-01.md](request-hot-blade-01.md) 生成。
- 导出 PNG 放到 `art/generated/inbox/hot_blade_01/`。
- 我负责切帧、调色、Unity 导入、动画控制器和可读性检查。

## 不做什么

- 不把带水印/来源不明/许可不清的图放进游戏。
- 不直接模仿竞品角色/商标。
- 不在没有 Human 确认的情况下把 AI 图当最终资产。

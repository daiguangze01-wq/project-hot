# Project Hot — 像素风 Style Bible v0.1

> 与 `docs/04-3D像素美术风格指南` 对齐；本文件只管**可执行的视觉 token 与 prompt**。

## 1. 视觉支柱

1. **2.5D 斜俯视**：正交、pitch 50°、yaw 45°、size 8；不自由旋转。
2. **低模 + 像素贴图**：轮廓干净、色块大、细节靠色板而非噪点。
3. **读招优先**：攻击起手/命中/收招在 78px 身高下可辨；VFX 不遮角色。
4. **原创英豪气质**：轻快、街头、装备感；不复制竞品角色/UI。
5. **统一色板**：深蓝竞技场 + 青色友方 + 暖金强调 + 红色危险。

## 2. 色板（sRGB）

| 用途 | Hex |
|---|---|
| 背景/阴影 | `#0B1020`、`#151C2E` |
| 地面 | `#1B263B`、`#2A3B55` |
| 友方/玩家 | `#63D6FF`、`#2E9FD8` |
| 危险/敌方 | `#FF6B6B`、`#C0392B` |
| 强调/UI | `#F2C14E`、`#FFE6A7` |
| 皮肤 | `#F2C6A0`、`#C98E6B` |
| 武器/金属 | `#DCE6F2`、`#8A99AD` |
| 草地/自然 | `#61E28F`、`#2F8F5B` |

- 每个角色 **≤32 色**（含 4 档明度）；UI 可 16 色。
- 禁止大面积渐变/噪点；用 2–3 档色块表现体积。

## 3. 比例与尺寸

| 项 | 值 |
|---|---|
| 角色身高 | 1.8m（默认 size8 下约 78px） |
| 2D sprite | 96×96 / 帧；脚底 pivot；透明背景 |
| 3D 贴图 atlas | 256×256 或 128×128；无烘焙光照 |
| 轮廓 | 1px 深色描边；不要抗锯齿 |
| 可读距离 | 6m/10m 可辨；14m 用边缘指示 |

## 4. 动画原则

- 轻击 4–6 帧、重击 6–8 帧；**起手 1–2 帧必须可读**。
- 跑+轻/重是“移动中攻击”的变体：重心前倾、攻击后保持移动惯性。
- 跳跃：起跳/滞空/落地三段；跳跃攻击在滞空帧出手。
- 所有动作循环点对齐；脚底不滑动（sprite 对齐 pivot，3D 用 root motion 关闭 + 速度匹配）。
- 帧率：idle 8fps、walk 12fps、run 16fps、攻击 16fps、跳跃 12fps；游戏内按 30/60Hz 采样。

## 5. 全局 Prompt 前缀

```text
2.5D isometric action game, fixed 3/4 top-down orthographic camera (pitch 50, yaw 45),
low-poly silhouette with crisp pixel-art texture, 1.8m heroic proportions, 96x96 sprite,
limited 32-color palette (dark navy #0B1020, cyan #63D6FF, warm gold #F2C14E, danger red #FF6B6B),
1px dark outline, clean color blocks, readable at 78px tall, transparent background,
game-ready, consistent scale and pivot at feet, no anti-aliasing, no blur, no text, no watermark
```

## 6. 全局负面词

```text
photorealistic, 3D render, smooth gradient, anti-aliasing, blurry, motion blur,
noisy dithering, excessive details, inconsistent palette, inconsistent proportions,
extra limbs, extra fingers, broken weapon, weapon clipping, floating feet,
text, logo, watermark, UI frame, perspective distortion, fisheye, free camera,
copying existing game character, trademark, franchise IP
```

## 7. 统一约束

- 同一角色所有动作使用**同一 seed/参考图/色板**；先生成 `character_ref`，再以图生图/风格参考生成动作。
- 每次生成记录：tool、model、prompt、negative、seed、reference、date、license。
- 任何“像某竞品”的结果直接废弃，不进入 Review。

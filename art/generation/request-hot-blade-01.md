# Generation Request — hot_blade_01（已 superseded）

> **已由 [request-modular-avatar-01.md](request-modular-avatar-01.md) 取代。**
> 本请求生成的是“整只角色 + 整套动作”，与 ADR-013 的“统一基础模型 + 模块化装备”冲突；
> 仅保留作为“风格/比例参考”的历史样例，不再用于生产。

> 目标：1 个原创剑客的像素风角色样张 + 动作模块；先做 **4 向**，通过后再扩 8 向。
> 所有 prompt 的全局风格/负面词来自 [docs/art/style-bible.md](../../docs/art/style-bible.md) 与 [docs/art/prompt-bank.json](../../docs/art/prompt-bank.json)。

## 角色 brief

- 原创敏捷剑客，短青黑发，旧海军蓝短外套，皮革护腕，细长英雄比例，右手单剑。
- 气质：街头决斗者，轻快、干净，不是重甲骑士。
- 色板：深蓝 `#0B1020`、地面 `#1B263B`、青色 `#63D6FF`、暖金 `#F2C14E`、危险红 `#FF6B6B`、肤色 `#F2C6A0`、钢色 `#DCE6F2`。
- 轮廓：1px 深色描边；96×96/帧；脚底 pivot；透明背景。
- 禁止：写实、3D 渲染感、抗锯齿、渐变、文字/水印、竞品角色。

## 全局前缀

```text
2.5D isometric action game, fixed 3/4 top-down orthographic camera (pitch 50, yaw 45),
low-poly silhouette with crisp pixel-art texture, 1.8m heroic proportions, 96x96 sprite,
limited 32-color palette (dark navy #0B1020, cyan #63D6FF, warm gold #F2C14E, danger red #FF6B6B),
1px dark outline, clean color blocks, readable at 78px tall, transparent background,
game-ready, consistent scale and pivot at feet, no anti-aliasing, no blur, no text, no watermark
```

## 角色 ref prompt

```text
original agile sword fighter, short cyan-black hair, worn navy short coat, leather bracers,
slim heroic build, one sword on right hand, confident street-duelist stance, front three-quarter view,
full body, transparent background, same palette as style, clean 1px outline, no text, no watermark
```

## 动作（先 4 向 S/E/N/W）

| 动作 | 帧数 | fps | 循环 | 说明 |
|---|---|---|---|---|
| idle | 4 | 8 | 是 | 呼吸/肩部微动，剑低垂 |
| walk | 8 | 12 | 是 | 脚接触/通过位，手臂反摆 |
| run | 8 | 16 | 是 | 前倾、大步、外套下摆 |
| light_attack | 5 | 16 | 否 | 1 帧起手，斜斩，青色小拖尾 |
| heavy_attack | 7 | 14 | 否 | 明显蓄力、上步、金色命中火花、长收招 |
| run_light_attack | 5 | 16 | 否 | 保持前冲惯性，短横斩 |
| run_heavy_attack | 7 | 14 | 否 | 前冲突进斩，外套/剑拖尾 |
| jump | 5 | 12 | 否 | 下蹲/起跳/上升/顶点/落地 |
| jump_attack | 6 | 14 | 否 | 跃起、举剑、空中斜斩、落地 |
| guard | 3 | 10 | 是 | 剑横挡，重心后坐 |

## 动作 prompt 模板

```text
{global_prefix}
{character_ref} exact same character, same outfit/palette/proportions,
{action}, {frames} frames, {loop_or_once}, {direction} view,
sprite sheet, evenly spaced frames, transparent background, no text, no watermark
```

示例 `run`：

```text
... exact same character ...
run cycle, 8 frames, screen-left to screen-right, forward lean, long stride,
coat tails trailing, sword trailing behind, seamless loop,
sprite sheet one row, transparent background, no text, no watermark
```

## 交付验收

- [ ] 角色比例/服装/武器在 10 个动作中一致；脚底同一基线。
- [ ] 96×96 帧，透明背景，无抗锯齿，≤32 色。
- [ ] 4 向命名 `hot_blade_01_<dir>_<anim>_<frame>.png`。
- [ ] 提供 `manifest.json`：工具/模型/prompt/seed/许可。
- [ ] 人工在 Unity 78px 身高下可读；无多余肢体/武器穿模。

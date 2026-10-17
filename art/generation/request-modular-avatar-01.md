# Generation Request — Modular Avatar 01

> 取代旧的 `request-hot-blade-01`。目标不是“一个完整角色”，而是**一套共享基础身体 + 可拆装备件**。
> 架构依据：[ADR-013](../decisions/ADR-013-modular-avatar-and-ugc-textures.md)、[docs/09](../09-角色与模块化装备系统.md)。

## 0. 总原则

- **所有角色共用**：基础身体 mesh、骨架、10 个动作。
- **每个外观件独立**：`hair / top / bottom / shoes / cape / weapon_main / weapon_offhand`。
- 动作不随装备重新生成；换装只换 mesh/material。
- AI 产出：概念图、2D layer、贴图/花纹/UGC 模板；3D mesh 仍需 Blender/人工清理/绑定。
- 禁止：整只角色 + 整套动作、把不同衣服烘焙进同一张身体贴图。

## 1. 先做 Phase 0（不要一次全做）

### 1.1 Base body turnaround（给 3D 建模/绑定用）

```text
neutral base body mannequin for a 2.5D action game, slim heroic 1.8m proportions,
featureless face, neutral A-pose, plain undergarment only, no hair, no coat,
front three-quarter + side + back turnaround, orthographic, transparent background,
clean 1px dark outline, limited 32-color palette, no text, no watermark
```

交付：`base_body_turnaround.png`（三视图/3/4 视图），标注身高比例/关节点。

验收：
- 比例与 KayKit 占位/`docs/04` 的 2.5–3 头身方向一致（可先按 1.8m/约 78px 目标）。
- 肩/肘/膝/髋/踝位置清楚，后续能对齐骨架。
- 无衣服/头发干扰。

### 1.2 单件概念（每件单独一张，透明背景）

按顺序：

1. `hair_01`：短青黑发，前/侧/后。
2. `top_01`：旧海军蓝短外套 + 皮护腕，前/侧/后，**无身体**。
3. `bottom_01`：深色长裤 + 皮带，前/侧/后，**无身体**。
4. `shoes_01`：深色皮靴，侧/3/4。
5. `cape_01`：短披风，后/侧。
6. `weapon_sword_01`：细剑，3/4 + 侧，**无手**。

统一用 [modular-avatar-prompts.json](../../docs/art/modular-avatar-prompts.json) 的全局风格/负面词。

### 1.3 UV 模板（必须从 mesh 导出，不要让 AI 猜）

- 由 3D 建模/Blender 导出每件装备的 UV layout。
- 生成 `*_uv_template.png`：色块标 UV 岛、无光照、无文字。
- 玩家/ AI 只画颜色/花纹，不改变 UV/几何。

## 2. 2D 纸娃娃样张（可选，先不要量产）

如果要做 MapleStory/英豪式 2D 层叠：

- 先 1 个基础身体 + 1 头发 + 1 上衣 × 4 向 × idle/walk；
- 所有 layer 同 96×96 canvas、脚底 pivot、同帧号；
- 确认能叠加后再扩动作；不要先做 10 动作 × 8 向。

## 3. 3D 模块化样张

- 1 个基础身体（可换装）+ 1 头发 mesh + 1 上衣 skinned mesh + 1 剑 socket；
- 共享 KayKit/正式骨架的 10 个动作；
- 验收：换装不破坏动作、遮挡/穿插可控、同一贴图模板可被 UGC 替换。

## 4. 交付格式

```text
art/generated/inbox/modular_avatar_01/
  base_body/base_body_turnaround.png
  items/hair_01/{front,side,back}.png
  items/top_01/{front,side,back}.png
  items/weapon_sword_01/{three_quarter,side}.png
  uv/top_01_uv_template.png
  manifest.json
```

`manifest.json`：工具/模型/prompt/seed/参考图/许可/人工修改。

## 5. 当前不要做的事

- 不要再生成“完整角色 8 向 idle / 10 动作”作为生产资产；之前的 PixelLab 输出只做风格参考。
- 不要把衣服/头发画进 base body 贴图。
- 不要用 AI 生成 UV 模板；UV 必须来自真实 mesh。
- 不要在没有基础身体/骨架前批量做装备。

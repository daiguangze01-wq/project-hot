# 美术资源管线 / Art Pipeline

> 目标：统一 2.5D 像素风角色/动作/提示词；**AI 生成是提案，不是自动入包**。
> 当前 U0 用 CC0 KayKit 低模占位；最终风格在 M0 用 1 个角色样张决策。

## 文件

| 文件 | 内容 |
|---|---|
| [style-bible.md](style-bible.md) | 全局风格、色板、比例、相机、轮廓、负面词 |
| [prompt-bank.json](prompt-bank.json) | 机器可读的提示词（角色/9 组动作/贴图/负面） |
| [asset-spec.md](asset-spec.md) | 帧数、方向、尺寸、命名、导出、Unity 导入 |
| [LICENSES.md](LICENSES.md) | 第三方资产/AI 生成许可记录 |
| [generation/README.md](../../art/generation/README.md) | AI 生成请求/收件流程、需要 Human 的介入 |
| [generation/request-modular-avatar-01.md](../../art/generation/request-modular-avatar-01.md) | **当前有效**：统一基础身体 + 可拆头发/衣服/武器请求 |
| [modular-avatar-prompts.json](modular-avatar-prompts.json) | 模块化装备/基础身体/UV 模板提示词 |
| [../09-角色与模块化装备系统](../09-角色与模块化装备系统.md) | 纸娃娃/装备槽/共享动画/UGC 架构 |
| [_research/ai-pixel-art-tools.md](../_research/ai-pixel-art-tools.md) | 工具/免费资源调研与建议 |

## 两条资产路线

### A. 3D 低模 + 像素贴图（基线，推荐）

- 与 ADR-007 / `docs/04` 一致；角色可自由转向、换武器/防具。
- 动画来自 rig/clip（当前 KayKit CC0 占位）；AI 负责概念、色板、贴图、UI。
- 最终资产要求：低模面数、像素贴图 atlas、无烘焙光照、可换色/换装。

### B. 2D 像素 sprite/billboard（风格测试）

- 用 PixelLab / Retro Diffusion 出 spritesheet；在 Unity 中 billboard 显示。
- 优点：像素味最直接、AI 可批量；缺点：8 向动作/换装/武器挂点会膨胀。
- 只建议先做 **1 角色 × 4 向 × 9 动作** 的样张，与 A 对比后再决定。

## 流程

```text
风格圣经 → prompt（本目录） → 外部 AI 生成
        → Aseprite 清理/调色板/对齐脚底
        → 命名/导出 → Unity 导入（见 asset-spec）
        → 独立美术/可读性评审 → 入包或退回
```

## 规则

- **禁止**直接模仿竞品角色、服装、UI、名称；提示词只描述原创设计。
- AI 资产必须记录：工具/模型版本、prompt、seed/参考图、许可、人工修改。
- 任何生成图都要过 Aseprite：去抗锯齿、限色、对齐 pivot、检查多余肢体/武器穿模。
- 最终商业条款以工具官方为准；免费资源必须核对每个包的许可，不能默认 CC0。
- 当前 KayKit Knight 为 **CC0 占位**，不是最终角色；见 `LICENSES`/`client-unity/HANDOFF.md`。

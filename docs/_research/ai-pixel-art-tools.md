# 像素/2.5D 美术资源获取调研

- 日期：2026-10-18
- 目标：给 U1 角色形象 + 9 组动作找到可落地的资源路径；同时统一 AI 生成提示词。
- 结论：**先用 CC0 低模动画跑通玩法，再用专用像素工具做风格测试；GPT 只做概念/提示词，不作为批量帧生成主力。**

## 1. 两条路线

| 路线 | 适合 | 优点 | 风险 |
|---|---|---|---|
| A. 3D 低模 + 像素贴图（基线） | 2.5D 斜俯视、8 向自由转向、装备换装 | 与 `docs/04`/ADR-007 一致；动画复用/重定向成熟 | 需要 rig/动画师；AI 直接生成 3D 动画不成熟 |
| B. 2D 像素 sprite/billboard | 快速视觉风格测试、独立游戏感 | AI 像素工具可出 spritesheet；成本低 | 8 向动作量爆炸；与 3D 低模/装备换装管线冲突 |
| C. 混合（建议） | 现在到 M0 | A 跑玩法/时序；B 只做 1 个角色 8 向风格样张，M0 后决策 | 需要明确“样张不是最终资产” |

## 2. AI 工具对比

| 工具 | 能力 | 对项目适用性 | 备注/来源 |
|---|---|---|---|
| **PixelLab** | 专用像素画；文生动画、骨骼动画；4/8 向；style reference；Aseprite 插件 | **首选 2D 像素候选**；适合角色/动画/8 向 | 官方 FAQ 有“能否商用/上 Steam”条目；订阅/API，需核对条款：[pixellab.ai](https://www.pixellab.ai/)、[FAQ](https://www.pixellab.ai/docs/faq) |
| **Retro Diffusion (RD Animation)** | 专门生成**风格一致的像素 spritesheet**；低帧率；调色板约束；walk/idle 等格式 | **首选 spritesheet 候选**；适合 walk/run/attack 帧序列 | Replicate 可试跑/API：[RD Animation](https://replicate.com/retro-diffusion/rd-animation) |
| **Scenario** | 游戏资产生成/风格训练/批量一致性 | 适合后期 UI/图标/概念批量；需核对套餐 | [scenario.com](https://www.scenario.com/) |
| **ChatGPT / GPT Image** | 概念图、角色设定、prompt 迭代、拆动作描述 | **适合前期概念/提示词/评审**；不适合精确逐帧 spritesheet | 帧间一致性/精确网格弱；适合当 art director 助手 |
| **Midjourney** | 风格板、气氛图、角色概念 | 适合 moodboard；不适合动画帧 | 商用条款随订阅，需核对 |
| **Stable Diffusion / Flux + ComfyUI** | 可训练 LoRA/IP-Adapter/ControlNet；可复现 | 一致性最强，但工程量大；模型许可证要逐个核对 | 仅建议在确定 2D 路线后投入 |
| **Aseprite / LibreSprite** | 像素清理、调色板、洋葱皮、导出 sheet | **任何 AI 输出都必须过 Aseprite 清理** | Aseprite 付费一次性；LibreSprite 免费 |
| **Meshy / Tripo / Rodin** | 图生 3D 模型 | 可做道具/场景占位；角色战斗动画不成熟 | 不用于最终动作模组 |

> GPT 的定位：**概念设定 + 提示词管理 + 质量检查**，不是直接产出可用的 9 组动作 spritesheet。

## 3. 免费/公开资源（可立即用）

| 资源 | 内容 | 许可 | 用途 |
|---|---|---|---|
| **KayKit Character Pack: Adventurers** | 4 个低模角色，**75 个动画**（idle/walk/run/1H/2H attack/jump/block/hit 等），FBX/GLTF | **CC0**，可商用、免署名 | **U0/U1 占位动画（已接入 Knight）**：[GitHub](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0) |
| **Kenney Mini Characters** | 3D 低模小人，含动画 | **CC0** | 备用角色/群演：[Kenney](https://kenney.nl/assets/mini-characters) |
| **Quaternius** | 低模角色/动画库 | 逐个包核对 QAL 许可 | 备用；不要默认当 CC0 |
| **Mixamo** | 人形动画（idle/walk/run/attack/jump） | Adobe 账号；Mixamo 许可允许游戏使用，需核对 | 3D 动画补充；风格需重定向 |
| **OpenGameArt / itch.io** | 像素角色/动作 | **逐包核对**（CC0/CC-BY/CC-BY-SA/GPL） | 只选明确可商用的包，记录来源 |

## 4. 对项目的建议

1. **现在**：KayKit Knight 已作为 U0 占位角色（CC0），先验证 9 组动作的**状态机/时序/手感**；不把它当最终美术。
2. **风格样张**：用 PixelLab 或 Retro Diffusion 生成 **1 个角色、4 向、9 组动作**的像素 sheet；先在 Unity 里以 billboard 方式对比可读性。
3. **M0 决策**：
   - 如果 3D 低模 + 像素贴图胜出：AI 只做概念/贴图/调色板；动画用 rig/外包/Mixamo。
   - 如果 2D 像素胜出：再扩到 8 向，并改渲染/碰撞管线；prompt bank 已准备好。
4. **所有 AI 资产**：记录工具、模型版本、prompt、seed、许可、人工修改；过 Aseprite 清理；禁止模仿竞品角色/商标。

## 5. 参考

- [PixelLab FAQ（商用/Steam）](https://www.pixellab.ai/docs/faq)
- [Retro Diffusion RD Animation（spritesheet）](https://replicate.com/retro-diffusion/rd-animation)
- [KayKit Adventurers（CC0，75 animations）](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0)
- [Kenney Mini Characters（CC0）](https://kenney.nl/assets/mini-characters)
- [Aseprite](https://www.aseprite.org/)

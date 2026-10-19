# TASK-083 Handoff — 2D 纸娃娃样张

```text
TASK: TASK-083
STATUS: partial

CHANGED:
  docs/decisions/ADR-014-2d-paperdoll-style-sample.md
  docs/10-2D纸娃娃样张计划.md
  art/generated/inbox/modular_avatar_01/base_body.png
  art/generated/inbox/modular_avatar_01/items/hair_01.png
  art/generated/inbox/modular_avatar_01/items/top_01.png
  art/generated/inbox/modular_avatar_01/items/weapon_sword_01.png

DECISIONS:
  - Human 选择先做 2D 纸娃娃样张；ADR-014 仅授权样张，暂不取代 ADR-010。
  - 主场景仍保留 KayKit 3D 作对照；2D 样张独立场景/路径。
  - 复用：相机/输入/移动/Hot.Sim/HUD/联网方案；重做：角色渲染、2D 装配、层动画、UGC 2D 语义。
  - PixelLab API 已验证可用（2026-10-20，64x64 生成成功）。

EVIDENCE:
  - PixelLab API: base_body/top/sword 可用；hair 仍带脸/头，不能直接作为 layer。
  - 当前没有 2D 场景/装配代码；样张未完成。

RISKS:
  - 4/8 向 x 动作 x 层资产量；层对齐/遮挡/武器挂点。
  - 2D UGC 纹理语义需重新定义。
  - 若最终切 2D，需新 ADR 取代 ADR-010，并更新 00/02/03/04/07/08/09。
  - 现有 3D 角色/装配代码会在最终切 2D 后废弃（玩法/联网核心不受影响）。

NEXT:
  1. 清理 hair（去脸/头）、生成 4 向 base/hair/top（先 front/back）。
  2. 新建 PaperdollSample 场景 + PaperdollAvatar/FrameAnimator。
  3. 4 向 idle/walk 拼装、78px 可读性、换装/UGC 测试。
  4. Human 评审后再决定 2D vs 3D。
```

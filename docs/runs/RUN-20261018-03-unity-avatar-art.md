# RUN-20261018-03 — Unity U0 收尾、模块化纸娃娃转向、文档同步

- 日期：2026-10-18
- 目标：在 PixelLab API 无法充值的情况下，完成可做的工程部分，并把“统一基础模型 + 模块化装备/UGC 纹理”决策落到所有相关文档。
- 结论：U0 完成；ADR-013 纸娃娃决策 accepted；模块化装备槽/UGC 原型通过；真实 base_body/hair/top 资产仍缺（等待 AI/3D 资产）。

## 1. 触发

- Human 指出：AI 生成的整只角色/整套动作不符合“统一模型 + 头发/衣服等独立外观”的方向；参考冒险岛/热血英豪/热斗传说。
- PixelLab API 余额 $0，Human 暂时无法充值；先做不依赖 AI 的工程/文档。

## 2. 决策

- [ADR-013](../decisions/ADR-013-modular-avatar-and-ugc-textures.md) accepted：
  - 统一基础身体 + 共享骨架 + 共享 10 动画；
  - 槽位：hair/face/head_accessory/top/bottom/shoes/gloves/cape/weapon_main/offhand；
  - 固定 UV 的 UGC 纹理替换，不改几何；
  - 禁止“每套造型重新生成整套角色/动作”。
- 旧的全角色生成请求 [request-hot-blade-01](../../art/generation/request-hot-blade-01.md) superseded。
- 新请求 [request-modular-avatar-01](../../art/generation/request-modular-avatar-01.md)：base_body + 单件装备 + UV 模板。

## 3. 工程

- Unity U0（TASK-080）完成：Arena 场景、相机相对移动、双击跑、KayKit 占位角色/10 动作、Windows 构建、人工手感测试。
- TASK-081 模块化装备槽原型：
  - `AvatarSlot` / `AvatarEquipmentController` / `UgcTextureLoader` / `AvatarDebugInput` / `AvatarChecks`。
  - 4 槽：HeadAccessory / Cape / WeaponMain / WeaponOffhand。
  - UGC：`StreamingAssets/ugc/test_pattern.png` 128×128 → body 材质贴图覆盖。
  - `AvatarChecks` PASS；Windows build exit 0。
- 限制：KayKit 衣服/身体烘焙，不能真正换 hair/top/bottom；需要真实 base body + 装备件。

## 4. 文档同步

- 更新：`docs/00` v0.4.0（§5.1/§12/修订记录）、`docs/02` v0.2.1（§5.1.1）、`docs/03` v0.2.1（§3.4.1）、`docs/04`（纸娃娃注记）、`docs/05`（ADR-013 索引）、`docs/07`（REQ-ART-004/TEST-043/TASK-080/081）、`docs/08`、`docs/09`、`docs/art/*`、`art/generation/*`、`AGENTS.md`、`README.md`、`docs/backlog.md`、`docs/tasks.json`。
- 旧 `request-hot-blade-01` 标记 superseded；`prompt-bank.json` 保留为风格参考，生产改用 `modular-avatar-prompts.json`。

## 4.1 Bug fix：C 连点重复伤害

- 症状：快速按 C，动画只展示一次，但伤害结算多次。
- 根因：`StartAttack` 在攻击锁内仍执行 damage；`CharacterAnimationDriver` 的 state 字符串未变化，不会重播动画。
- 修复：
  - `StartAttack` 开头 `if (attacking) return;`；active/recovery 内输入不再结算。
  - 攻击间隔/伤害/范围来自 `WeaponProfile`（空手 0.32s、1H 0.45s、2H 0.58s），不再全局常量。
  - 数字键 5 循环战斗武器 profile，HUD 显示当前武器/冷却。
- 证据：`CombatChecks` PASS（两次 StartAttack 只计 1 次；空手/1H/2H 冷却递增）。

## 5. 证据

- `Hot.Editor.AvatarChecks`: PASS（UGC 128×128；4 槽；切换 head/weapon/offhand）。
- `Hot.Editor.CombatChecks`: PASS（unarmed 0.32s / 1H 0.45s / 2H 0.58s；两次 StartAttack 只计 1 次）。
- U0 build: `Builds/U0/ProjectHot.exe` exit 0。
- 截图：`client-unity/screenshots/u0-knight.png`、`u0-avatar-slots.png`、`u0-combat-profile.png`。
- PixelLab 输出（48×48、8 向 idle）只作风格参考；不是模块化资产。

## 6. 下一步

1. 选/做真实基础身体 + 骨架（CC0/Blender/外包）；共享现有 10 动作。
2. 生成/制作 hair_01、top_01、bottom_01、shoes_01、weapon_sword_01 单件。
3. 把 slot 绑定迁到 `AvatarItemDefinition` ScriptableObject。
4. UGC 加服务端 hash/审核；Steam Workshop 后置。
5. PixelLab 充值后再用 API 生成 base_body/单件装备；不再生成整只角色。

# TASK-081 Handoff — 模块化角色/装备槽原型

```text
TASK: TASK-081
STATUS: partial

CHANGED:
  client-unity/ProjectHot/Assets/Hot/Client/AvatarSlot.cs
  client-unity/ProjectHot/Assets/Hot/Client/AvatarEquipmentController.cs
  client-unity/ProjectHot/Assets/Hot/Client/UgcTextureLoader.cs
  client-unity/ProjectHot/Assets/Hot/Client/AvatarDebugInput.cs
  client-unity/ProjectHot/Assets/Hot/Editor/AvatarChecks.cs
  client-unity/ProjectHot/Assets/Hot/Editor/ArenaBootstrap.cs
  client-unity/ProjectHot/Assets/StreamingAssets/ugc/test_pattern.png
  client-unity/screenshots/u0-avatar-slots.png
  docs/09-角色与模块化装备系统.md (reference)
  docs/decisions/ADR-013-modular-avatar-and-ugc-textures.md

DECISIONS:
  - ADR-013: shared base body/skeleton/animations + modular slots + fixed-UV UGC textures.
  - U0 placeholder uses KayKit parts as slot items: HeadAccessory, Cape, WeaponMain, WeaponOffhand.
  - Hair/Top/Bottom/Shoes slots are defined in enum/data but not yet populated (need modular base/equipment assets).
  - UGC prototype loads a local 128x128 PNG from StreamingAssets and replaces the body material texture; no server/moderation yet.
  - Combat core remains separate from appearance (ADR-005).

EVIDENCE:
  - Unity build exit 0: Builds/U0/ProjectHot.exe.
  - Hot.Editor.AvatarChecks: PASS
    * UGC 128x128 load
    * slots=4 HeadAccessory/Cape/WeaponMain/WeaponOffhand
    * head toggled off, weapon 2H, offhand Badge after cycle
  - Screenshot: client-unity/screenshots/u0-avatar-slots.png

RISKS:
  - KayKit body/clothes are baked; hair/top/bottom real modular items are not present yet.
  - No real base body/skeleton selected; U0 uses KayKit skeleton as placeholder.
  - UGC is local-only; no validation beyond size/format, no moderation/storage/server hash.
  - No equipment data assets/ScriptableObjects yet; slot bindings are built in ArenaBootstrap.

NEXT:
  1. Select/author a base body + skeleton (CC0/Blender/outsource); no new animations.
  2. Add hair_01/top_01 real modular items and populate slots.
  3. Move slot catalog to AvatarItemDefinition ScriptableObjects.
  4. Add UGC upload/server hash + moderation design; Steam Workshop later.
```

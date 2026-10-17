# TASK-080 Handoff — Unity 6.3 U0

```text
TASK: TASK-080
STATUS: done

CHANGED:
  client-unity/ProjectHot/Assets/Hot/Client/OrthoCameraRig.cs
  client-unity/ProjectHot/Assets/Hot/Client/PlayerMotor.cs   # camera-relative input
  client-unity/ProjectHot/Assets/Hot/Client/TargetDummy.cs
  client-unity/ProjectHot/Assets/Hot/Client/HotHud.cs
  client-unity/ProjectHot/Assets/Hot/Editor/ArenaBootstrap.cs
  client-unity/ProjectHot/Assets/Hot/Editor/BuildU0.cs
  client-unity/ProjectHot/Assets/Hot/Editor/U0Checks.cs
  client-unity/ProjectHot/Assets/Hot/Editor/KayKitAnimationBuilder.cs
  client-unity/ProjectHot/Assets/Hot/Editor/InspectKayKit.cs
  client-unity/ProjectHot/Assets/Hot/Client/CharacterAnimationDriver.cs
  client-unity/ProjectHot/Assets/Hot/Art/KayKit/Knight.fbx
  client-unity/ProjectHot/Assets/Hot/Art/KayKit/knight_texture.png
  client-unity/ProjectHot/Assets/Hot/Art/KayKit/KnightMat.mat
  client-unity/ProjectHot/Assets/Hot/Art/KayKit/KnightAnimator.controller
  client-unity/screenshots/u0-knight.png
  docs/art/README.md
  docs/art/style-bible.md
  docs/art/prompt-bank.json
  docs/art/asset-spec.md
  docs/_research/ai-pixel-art-tools.md
  client-unity/ProjectHot/Assets/Hot/Data/cores.json
  client-unity/ProjectHot/Assets/Scenes/Arena.unity
  client-unity/ProjectHot/Packages/manifest.json
  client-unity/README.md
  client-unity/HANDOFF.md
  .gitignore

DECISIONS:
  - Unity 6.3 LTS 6000.3.26f1 + URP 17.0.1; project created from official 3D cross-platform URP template.
  - Input System 1.12.0 from the 6.3.12 template fails on 6.3.26 (BuildTarget.ReservedCFE removed); upgraded to 1.20.1.
  - U0 uses a fixed ortho camera rig (pitch50/yaw45/size8), local-only PlayerMotor, training dummy, IMGUI HUD.
  - Movement is camera-relative (screen right/up), not world X/Z. Research: docs/_research/camera-relative-movement.md.
  - U0 character is KayKit Knight (CC0) with 10 animation states: Idle/Walk/Run/Light/Heavy/RunLight/RunHeavy/Jump/JumpAttack/Guard. It is a placeholder, not final art.
  - Run = Shift; attacks lock a short state; CharacterAnimationDriver maps to Animator states.
  - AI prompt bank centralized in docs/art/prompt-bank.json + style-bible.md; AI tool/free-asset research in docs/_research/ai-pixel-art-tools.md.
  - BuildU0 uses Mono Windows x64 for U0; IL2CPP remains for U3 Steam build.
  - Fusion 2 / server authority NOT in U0; local prototype only.

EVIDENCE:
  - Unity.exe -version: 6000.3.26f1.
  - `ArenaBootstrap.CreateArena`: exit 0; Assets/Scenes/Arena.unity (158 KB).
  - `BuildU0.Build`: exit 0; Builds/U0/ProjectHot.exe; build report size 100,416,748 bytes.
  - Player log: D3D12, NVIDIA RTX 5080, Input System initialized; no script exceptions in build log.
  - `Hot.Editor.U0Checks`: PASS D=screen-right/W=screen-up/S=opposite/D-W perpendicular; exit 0.
  - KayKit build: 10 Animator states, 76 clips imported; U0 build exit 0.
  - Visual capture `client-unity/screenshots/u0-knight.png`: Knight visible, dummy/HUD render; captured via `-capture`/ScreenCapture.
  - Human playtest: "大部分功能都没问题"; camera-relative movement and double-tap run accepted; animation timing/readability still needs iterative polish.
  - `client-unity/screenshots/u0-avatar-slots.png`: modular slot HUD + UGC test overlay.
  - `Hot.Editor.AvatarChecks`: PASS UGC 128x128 + 4 slots + head/weapon/offhand switching.

RISKS:
  - U0 is a local movement/attack dummy prototype, not the authoritative simulator or Fusion netcode.
  - Input System upgraded package; need verify keyboard-only 2KRO/6KRO in-engine later (B6).
  - URP 17.0.1 from template; may upgrade with 6.3 packages.
  - No Fusion 2 SDK, no Steamworks, no IL2CPP/Steam build yet.
  - Builds/Library generated, ignored by git.

NEXT:
  1. TASK-081: modular avatar base body/equipment slots + UGC texture (see client-unity/HANDOFF-AVATAR.md).
  2. U1: port mvp/sim.js rules to Assets/Hot/Sim (pure C#), 4 cores, HUD.
  3. U2: import Fusion 2, 2-player authoritative room.
  4. U3: IL2CPP + Steamworks/Playtest.
```

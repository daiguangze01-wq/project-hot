# TASK-080 Handoff — Unity 6.3 U0

```text
TASK: TASK-080
STATUS: partial

CHANGED:
  client-unity/ProjectHot/Assets/Hot/Client/OrthoCameraRig.cs
  client-unity/ProjectHot/Assets/Hot/Client/PlayerMotor.cs
  client-unity/ProjectHot/Assets/Hot/Client/TargetDummy.cs
  client-unity/ProjectHot/Assets/Hot/Client/HotHud.cs
  client-unity/ProjectHot/Assets/Hot/Editor/ArenaBootstrap.cs
  client-unity/ProjectHot/Assets/Hot/Editor/BuildU0.cs
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
  - BuildU0 uses Mono Windows x64 for U0; IL2CPP remains for U3 Steam build.
  - Fusion 2 / server authority NOT in U0; local prototype only.

EVIDENCE:
  - Unity.exe -version: 6000.3.26f1.
  - `ArenaBootstrap.CreateArena`: exit 0; Assets/Scenes/Arena.unity (158 KB).
  - `BuildU0.Build`: exit 0; Builds/U0/ProjectHot.exe; build report size 100,416,748 bytes.
  - Player log: D3D12, NVIDIA RTX 5080, Input System initialized; no script exceptions in build log.
  - Not visually verified: automation session could not bring the player window/desktop capture to foreground; needs Human Play/visual QA.

RISKS:
  - U0 is a local movement/attack dummy prototype, not the authoritative simulator or Fusion netcode.
  - Input System upgraded package; need verify keyboard-only 2KRO/6KRO in-engine later (B6).
  - URP 17.0.1 from template; may upgrade with 6.3 packages.
  - No Fusion 2 SDK, no Steamworks, no IL2CPP/Steam build yet.
  - Builds/Library generated, ignored by git.

NEXT:
  1. Human opens client-unity/ProjectHot in Unity 6.3.26f1, opens Assets/Scenes/Arena.unity, Play; or runs Builds/U0/ProjectHot.exe; confirm camera/input/dummy.
  2. U1: port mvp/sim.js rules to Assets/Hot/Sim (pure C#), 4 cores, HUD.
  3. U2: import Fusion 2, 2-player authoritative room.
  4. U3: IL2CPP + Steamworks/Playtest.
```

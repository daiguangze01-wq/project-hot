# TASK-082 Handoff — U1 Hot.Sim 纯 C# 战斗核心

```text
TASK: TASK-082
STATUS: partial

CHANGED:
  client-unity/ProjectHot/Assets/Hot/Sim/SimTypes.cs
  client-unity/ProjectHot/Assets/Hot/Sim/CombatSim.cs
  client-unity/ProjectHot/Assets/Hot/Editor/SimChecks.cs
  client-unity/ProjectHot/Assets/Hot/Client/CombatSimBridge.cs
  client-unity/ProjectHot/Assets/Hot/Client/PlayerMotor.cs (externalCombat/guard hooks)
  client-unity/ProjectHot/Assets/Hot/Client/TargetDummy.cs (sim sync)
  client-unity/ProjectHot/Assets/Hot/Client/HotHud.cs (sim resources)
  client-unity/screenshots/u0-sim-bridge.png

DECISIONS:
  - Hot.Sim is pure C# + System.Numerics, no UnityEngine; server/client can share it.
  - 30Hz tick; X/Y ground combat; 4 cores (Blade/Fist/Spear/Staff) with move-table modifiers.
  - One action at a time; damage at startup; cooldown/MP/ult validated in TryAction.
  - Guard/perfect guard (0.16s) and guard break implemented; light combo damage +8 per hit.
  - U1b `CombatSimBridge` now owns attacks/guard/damage/cooldowns/MP/ult;
    PlayerMotor owns locomotion/animation only (externalCombat=true).
  - Camera-relative movement stays in PlayerMotor; sim position is copied each frame.
  - U1b input: C/X, Z+C/Z+X/Z+dir+C/Z+dir+X, Z+X+C; Space guard; 6 cycles core.
  - Local U0 dummy view mirrors sim HP/alive.

EVIDENCE:
  - Hot.Editor.SimChecks: 18 PASS
    movement, light damage 30, attack gating, guard 20%, perfect guard 0,
    blade/fist skill1 70/60, spear ranged, staff AoE/melee, ult resource/cost/damage,
    death + respawn.
  - Unity build exit 0 after bridge; screenshot `u0-sim-bridge.png` shows core/HP/MP/guard/ult HUD.
  - Core checks remain 18 PASS.

RISKS:
  - PlayerMotor still owns locomotion/animation; sim does not own movement yet, so movement prediction/authority is split for U1b.
  - Hit detection is 1 target dummy + other players; no wall/height/vertical hits.
  - Knockback/guard formulas are simplified vs final docs; server validation not wired.
  - No network serialization; Fusion 2 integration later.

NEXT:
  1. Unity bridge: feed camera-relative input/held/actions into CombatSim, sync player/dummy view.
  2. Replace PlayerMotor local damage/cooldowns with CombatSim results; keep animation driver.
  3. Add 4-core selection UI; HUD from sim state.
  4. U2 Fusion 2: run same CombatSim on server; input frames.
```

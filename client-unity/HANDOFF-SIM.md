# TASK-082 Handoff — U1 Hot.Sim 纯 C# 战斗核心

```text
TASK: TASK-082
STATUS: partial

CHANGED:
  client-unity/ProjectHot/Assets/Hot/Sim/SimTypes.cs
  client-unity/ProjectHot/Assets/Hot/Sim/CombatSim.cs
  client-unity/ProjectHot/Assets/Hot/Editor/SimChecks.cs

DECISIONS:
  - Hot.Sim is pure C# + System.Numerics, no UnityEngine; server/client can share it.
  - 30Hz tick; X/Y ground combat; 4 cores (Blade/Fist/Spear/Staff) with move-table modifiers.
  - One action at a time; damage at startup; cooldown/MP/ult validated in TryAction.
  - Guard/perfect guard (0.16s) and guard break implemented; light combo damage +8 per hit.
  - Local Unity bridge is NOT wired yet; PlayerMotor still uses its own U0 attack logic.

EVIDENCE:
  - Hot.Editor.SimChecks: 18 PASS
    movement, light damage 30, attack gating, guard 20%, perfect guard 0,
    blade/fist skill1 70/60, spear ranged, staff AoE/melee, ult resource/cost/damage,
    death + respawn.
  - No Unity build needed for this core (pure C# checks under Editor).

RISKS:
  - Not integrated with Unity transform/animator/HUD/dummy; next task must replace U0 damage path.
  - Hit detection is 1 target dummy + other players; no wall/height/vertical hits.
  - Knockback/guard formulas are simplified vs final docs; server validation not wired.
  - No network serialization; Fusion 2 integration later.

NEXT:
  1. Unity bridge: feed camera-relative input/held/actions into CombatSim, sync player/dummy view.
  2. Replace PlayerMotor local damage/cooldowns with CombatSim results; keep animation driver.
  3. Add 4-core selection UI; HUD from sim state.
  4. U2 Fusion 2: run same CombatSim on server; input frames.
```

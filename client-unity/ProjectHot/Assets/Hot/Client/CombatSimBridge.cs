using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using Hot.Sim;
using Vec2 = System.Numerics.Vector2;

namespace Hot.Client
{
    /// <summary>
    /// U1b bridge: keyboard/camera presentation -> Hot.Sim authoritative combat.
    /// PlayerMotor still owns locomotion/animation; Hot.Sim owns attacks, guard,
    /// damage, cooldowns, MP and ult. Fusion will replace the input transport later.
    /// </summary>
    public class CombatSimBridge : MonoBehaviour
    {
        public PlayerMotor motor;
        public TargetDummy dummyView;
        public CoreId core = CoreId.Blade;

        private CombatSim sim;
        private PlayerState player;
        private RunningAction lastAction;
        private float accumulator;
        private string status = "";
        private ActionId lastTried = ActionId.Light;
        private const float GuardChordWindow = 0.18f;
        private float cPressAt = -10f;
        private float xPressAt = -10f;

        public string CoreName => CoreDef.All[player != null ? player.Core : core].Name;
        public float Hp => player != null ? player.Hp : 0;
        public float Mp => player != null ? player.Mp : 0;
        public float Guard => player != null ? player.Guard : 0;
        public float Ult => player != null ? player.Ult : 0;

        private void Start()
        {
            sim = new CombatSim();
            player = sim.AddPlayer("Player", core);
            if (motor != null) motor.externalCombat = true;
        }

        private void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || sim == null || motor == null) return;

            SyncSimToPresentation();
            UpdateCoreSelection(kb);

            if (kb.cKey.wasPressedThisFrame) cPressAt = Time.unscaledTime;
            if (kb.xKey.wasPressedThisFrame) xPressAt = Time.unscaledTime;

            bool cHeld = kb.cKey.isPressed;
            bool xHeld = kb.xKey.isPressed;
            bool zHeld = kb.zKey.isPressed;
            bool bothAttack = cHeld && xHeld;
            // Forgiving C+X guard: accept a chord within 180ms, including the
            // case where the first attack already started its startup frames.
            bool chord = bothAttack && !zHeld && Mathf.Abs(cPressAt - xPressAt) <= GuardChordWindow;
            bool guardHeld = kb.spaceKey.isPressed || bothAttack;
            if (chord)
            {
                bool accepted = sim.TryGuard(player);
                if (accepted)
                {
                    motor.CancelExternalAttack();
                    status = "C+X guard";
                }
            }
            motor.SetExternalGuard(guardHeld);

            var actions = new List<ActionId>();
            if (!chord && kb.cKey.wasPressedThisFrame && !bothAttack)
            {
                if (zHeld && xHeld) actions.Add(ActionId.Ultimate);
                else if (zHeld && HasDirection(kb)) actions.Add(ActionId.Skill3);
                else if (zHeld) actions.Add(ActionId.Skill1);
                else actions.Add(ActionId.Light);
            }
            if (!chord && kb.xKey.wasPressedThisFrame && !bothAttack)
            {
                if (zHeld && cHeld) actions.Add(ActionId.Ultimate);
                else if (zHeld && HasDirection(kb)) actions.Add(ActionId.Skill4);
                else if (zHeld) actions.Add(ActionId.Skill2);
                else actions.Add(ActionId.Heavy);
            }

            if (actions.Count > 0) lastTried = actions[0];
            sim.ApplyInput(player.Id, new SimInput
            {
                Move = Vec2.Zero, // locomotion stays in PlayerMotor for U1b
                Guard = guardHeld,
                Actions = actions
            });

            accumulator += Time.deltaTime;
            while (accumulator >= 1f / CombatSim.TickRate)
            {
                sim.Tick(1f / CombatSim.TickRate);
                accumulator -= 1f / CombatSim.TickRate;
                SyncSimActionToAnimation();
            }

            SyncPresentationToSim();
        }

        private void SyncSimToPresentation()
        {
            var pos = motor.transform.position;
            player.Position = new Vec2(pos.x, pos.z);
            player.Facing = Mathf.Atan2(motor.transform.forward.z, motor.transform.forward.x);
            player.Height = motor.Height;

            if (dummyView != null)
            {
                var dp = dummyView.transform.position;
                sim.Dummy.X = dp.x;
                sim.Dummy.Y = dp.z;
            }
        }

        private void SyncPresentationToSim()
        {
            if (dummyView != null)
                dummyView.SyncFromSim(sim.Dummy.Hp, sim.Dummy.Alive);
        }

        private void SyncSimActionToAnimation()
        {
            var action = player.Action;
            if (action != null && action != lastAction)
            {
                lastAction = action;
                bool heavy = action.Id != ActionId.Light && action.Id != ActionId.Skill1 && action.Id != ActionId.Skill3;
                motor.PlayExternalAttack(heavy, action.Move.Duration);
            }
            else if (action == null)
            {
                lastAction = null;
            }
        }

        private void UpdateCoreSelection(Keyboard kb)
        {
            if (!kb.digit6Key.wasPressedThisFrame) return;
            int next = ((int)player.Core + 1) % 4;
            player.Core = (CoreId)next;
            core = player.Core;
            status = "core: " + CoreName;
        }

        private static bool HasDirection(Keyboard kb)
        {
            return kb.wKey.isPressed || kb.aKey.isPressed || kb.sKey.isPressed || kb.dKey.isPressed ||
                   kb.upArrowKey.isPressed || kb.downArrowKey.isPressed ||
                   kb.leftArrowKey.isPressed || kb.rightArrowKey.isPressed;
        }

        private void OnGUI()
        {
            if (player == null) return;
            var style = new GUIStyle(GUI.skin.label) { fontSize = 12 };
            GUILayout.BeginArea(new Rect(18, 420, 760, 92), GUI.skin.box);
            GUILayout.Label("HOT.SIM  core=" + CoreName + "  HP=" + Hp.ToString("0") +
                            "  MP=" + Mp.ToString("0") + "  GUARD=" + Guard.ToString("0") +
                            "  ULT=" + Ult.ToString("0"), style);
            GUILayout.Label("C light / X heavy / Z+C skill1 / Z+X skill2 / Z+dir+C skill3 / Z+dir+X skill4 / Z+X+C ult", style);
            GUILayout.Label("Space / C+X (180ms chord) guard · 6 core · V jump · SIM owns damage/cooldown", style);
            if (!string.IsNullOrEmpty(status)) GUILayout.Label(status, style);
            GUILayout.EndArea();
        }
    }
}

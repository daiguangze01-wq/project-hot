using System;
using Vec2 = System.Numerics.Vector2;
using UnityEditor;
using UnityEngine;
using Hot.Sim;

namespace Hot.Editor
{
    public static class SimChecks
    {
        private static bool pass = true;

        public static void Run()
        {
            Movement();
            LightAttackAndGating();
            GuardAndPerfect();
            Cores();
            Ultimate();
            DeathRespawn();

            Debug.Log(pass ? "SIM_CHECK PASS" : "SIM_CHECK FAIL");
            EditorApplication.Exit(pass ? 0 : 1);
        }

        private static void Movement()
        {
            var sim = new CombatSim();
            var p = sim.AddPlayer("A", CoreId.Blade);
            var start = p.Position.Y;
            sim.ApplyInput(p.Id, new SimInput { Move = new Vec2(0, 1) });
            for (int i = 0; i < 30; i++) sim.Tick();
            Check("movement", p.Position.Y > start + 1f, p.Position.Y.ToString("F2"));
        }

        private static void LightAttackAndGating()
        {
            var sim = new CombatSim();
            var p = sim.AddPlayer("A", CoreId.Blade);
            p.Position = new Vec2(0, -1);
            p.Facing = MathF.PI / 2f;
            float before = sim.Dummy.Hp;
            sim.TryAction(p, ActionId.Light, Vec2.Zero);
            bool blocked = !sim.TryAction(p, ActionId.Light, Vec2.Zero);
            sim.Tick(0.2f);
            Check("light damage", sim.Dummy.Hp < before, sim.Dummy.Hp.ToString("F0"));
            Check("attack gating", blocked, "second attack blocked");

            for (int i = 0; i < 20; i++) sim.Tick();
            var after = sim.GetMove(p, ActionId.Light);
            Check("move table", after != null && after.Damage == 30f, "light damage 30");
        }

        private static void GuardAndPerfect()
        {
            var sim = new CombatSim();
            var a = sim.AddPlayer("A", CoreId.Blade);
            var b = sim.AddPlayer("B", CoreId.Blade);
            a.Position = new Vec2(0, -1);
            b.Position = new Vec2(0, 0);
            a.Facing = MathF.PI / 2f;

            b.Guarding = true;
            b.GuardStart = 0f;
            sim.TryAction(a, ActionId.Light, Vec2.Zero);
            sim.Tick(0.2f);
            Check("guard reduces", b.Hp == 500f - 6f, b.Hp.ToString("F1"));

            a.Action = null;
            b.Hp = 500f;
            b.Guarding = true;
            b.GuardStart = sim.Time;
            sim.TryAction(a, ActionId.Light, Vec2.Zero);
            sim.Tick(0.13f);
            Check("perfect guard", b.Hp == 500f, b.Hp.ToString("F1"));
        }

        private static void Cores()
        {
            var sim = new CombatSim();
            var blade = sim.AddPlayer("Blade", CoreId.Blade);
            var fist = sim.AddPlayer("Fist", CoreId.Fist);
            var spear = sim.AddPlayer("Spear", CoreId.Spear);
            var staff = sim.AddPlayer("Staff", CoreId.Staff);
            Check("blade core", sim.GetMove(blade, ActionId.Skill1).Damage == 70f, "70");
            Check("fist core", sim.GetMove(fist, ActionId.Skill1).Damage == 60f, "60");
            Check("spear ranged", sim.GetMove(spear, ActionId.Skill2).Ranged == true, "ranged");
            Check("staff aoe", sim.GetMove(staff, ActionId.Skill2).Aoe == true, "aoe");
            Check("staff melee", sim.GetMove(staff, ActionId.Skill2).Ranged == false, "melee");
        }

        private static void Ultimate()
        {
            var sim = new CombatSim();
            var p = sim.AddPlayer("A", CoreId.Blade);
            p.Position = new Vec2(0, -1);
            p.Facing = MathF.PI / 2f;
            Check("ult requires resource", !sim.TryAction(p, ActionId.Ultimate, Vec2.Zero), "blocked");
            p.Ult = 100;
            Check("ult starts", sim.TryAction(p, ActionId.Ultimate, Vec2.Zero), "started");
            Check("ult spends resource", p.Ult == 0f, p.Ult.ToString("F0"));
            float before = sim.Dummy.Hp;
            for (int i = 0; i < 20; i++) sim.Tick();
            Check("ult damage", sim.Dummy.Hp < before, sim.Dummy.Hp.ToString("F0"));
        }

        private static void DeathRespawn()
        {
            var sim = new CombatSim();
            var a = sim.AddPlayer("A", CoreId.Blade);
            var b = sim.AddPlayer("B", CoreId.Blade);
            a.Position = new Vec2(0, -1);
            b.Position = new Vec2(0, 0);
            b.Hp = 5f;
            a.Facing = MathF.PI / 2f;
            sim.TryAction(a, ActionId.Heavy, Vec2.Zero);
            sim.Tick(0.3f);
            Check("death", !b.Alive, b.Alive.ToString());
            for (int i = 0; i < 100; i++) sim.Tick();
            Check("respawn", b.Alive, b.Alive.ToString());
        }

        private static void Check(string name, bool ok, string detail)
        {
            if (!ok) pass = false;
            Debug.Log((ok ? "PASS " : "FAIL ") + name + " :: " + detail);
        }
    }
}


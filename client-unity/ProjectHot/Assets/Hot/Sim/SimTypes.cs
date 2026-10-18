using System;
using System.Collections.Generic;
using System.Numerics;

namespace Hot.Sim
{
    public enum CoreId { Blade, Fist, Spear, Staff }

    public enum ActionId
    {
        Light, Heavy, Skill1, Skill2, Skill3, Skill4, Ultimate
    }

    public enum CombatEventKind { Damage, PerfectGuard, GuardBreak, Death, Spawn, DummyDown }

    public sealed class MoveDef
    {
        public float Startup;
        public float Active;
        public float Recovery;
        public float Damage;
        public float Range;
        public float Width;
        public float Arc;          // degrees
        public float Knockback;
        public float Mp;
        public float Cooldown;
        public float ComboWindow;
        public float UltCost;
        public float Dash;
        public bool? Ranged;
        public bool? Aoe;

        public float Duration => Startup + Active + Recovery;
    }

    public sealed class CoreDef
    {
        public CoreId Id;
        public string Name;
        public Dictionary<ActionId, MoveDef> Mods = new Dictionary<ActionId, MoveDef>();

        public static readonly Dictionary<CoreId, CoreDef> All = Build();

        private static Dictionary<CoreId, CoreDef> Build()
        {
            return new Dictionary<CoreId, CoreDef>
            {
                { CoreId.Blade, new CoreDef { Id = CoreId.Blade, Name = "剑豪", Mods = MakeMods(
                    (ActionId.Skill1, new MoveDef { Damage = 70, Range = 2.8f, Mp = 20, Cooldown = 4 }),
                    (ActionId.Skill2, new MoveDef { Damage = 60, Range = 7f, Width = 1.4f, Mp = 30, Cooldown = 6, Ranged = true }),
                    (ActionId.Skill3, new MoveDef { Damage = 85, Range = 3f, Arc = 160, Mp = 25, Cooldown = 7 }),
                    (ActionId.Skill4, new MoveDef { Damage = 120, Range = 3.4f, Arc = 360, Aoe = true, Mp = 35, Cooldown = 9 }),
                    (ActionId.Ultimate, new MoveDef { Damage = 220, Range = 4.8f })
                ) } },
                { CoreId.Fist, new CoreDef { Id = CoreId.Fist, Name = "拳师", Mods = MakeMods(
                    (ActionId.Light, new MoveDef { Damage = 26, Range = 2f }),
                    (ActionId.Heavy, new MoveDef { Damage = 85, Range = 2.5f, Startup = 0.24f, Recovery = 0.28f }),
                    (ActionId.Skill1, new MoveDef { Damage = 60, Range = 2.3f, Mp = 15, Cooldown = 3 }),
                    (ActionId.Skill2, new MoveDef { Damage = 75, Range = 3f, Arc = 180, Mp = 25, Cooldown = 5, Ranged = false, Width = 0 }),
                    (ActionId.Skill3, new MoveDef { Damage = 95, Range = 2.6f, Arc = 200, Mp = 20, Cooldown = 6 }),
                    (ActionId.Skill4, new MoveDef { Damage = 100, Range = 3.8f, Arc = 360, Aoe = true, Mp = 30, Cooldown = 8 }),
                    (ActionId.Ultimate, new MoveDef { Damage = 240, Range = 4.2f })
                ) } },
                { CoreId.Spear, new CoreDef { Id = CoreId.Spear, Name = "枪兵", Mods = MakeMods(
                    (ActionId.Light, new MoveDef { Damage = 28, Range = 2.8f }),
                    (ActionId.Heavy, new MoveDef { Damage = 75, Range = 3.2f, Knockback = 2.6f }),
                    (ActionId.Skill1, new MoveDef { Damage = 65, Range = 3.6f, Mp = 20, Cooldown = 4 }),
                    (ActionId.Skill2, new MoveDef { Damage = 70, Range = 8f, Width = 0.9f, Mp = 30, Cooldown = 6, Ranged = true }),
                    (ActionId.Skill3, new MoveDef { Damage = 80, Range = 3.2f, Arc = 200, Mp = 25, Cooldown = 7 }),
                    (ActionId.Skill4, new MoveDef { Damage = 110, Range = 4f, Arc = 360, Aoe = true, Mp = 35, Cooldown = 9 }),
                    (ActionId.Ultimate, new MoveDef { Damage = 210, Range = 5.2f })
                ) } },
                { CoreId.Staff, new CoreDef { Id = CoreId.Staff, Name = "术士", Mods = MakeMods(
                    (ActionId.Light, new MoveDef { Damage = 24, Range = 2.2f }),
                    (ActionId.Heavy, new MoveDef { Damage = 65, Range = 2.8f }),
                    (ActionId.Skill1, new MoveDef { Damage = 55, Range = 8f, Width = 1.2f, Mp = 20, Cooldown = 4, Ranged = true }),
                    (ActionId.Skill2, new MoveDef { Damage = 80, Range = 3f, Arc = 360, Aoe = true, Mp = 30, Cooldown = 6, Ranged = false }),
                    (ActionId.Skill3, new MoveDef { Damage = 75, Range = 7f, Width = 1.4f, Mp = 25, Cooldown = 7, Ranged = true }),
                    (ActionId.Skill4, new MoveDef { Damage = 100, Range = 4.2f, Arc = 360, Aoe = true, Mp = 35, Cooldown = 9 }),
                    (ActionId.Ultimate, new MoveDef { Damage = 230, Range = 5f, Arc = 360, Aoe = true })
                ) } }
            };
        }

        private static Dictionary<ActionId, MoveDef> MakeMods(params (ActionId id, MoveDef move)[] entries)
        {
            var d = new Dictionary<ActionId, MoveDef>();
            foreach (var e in entries) d[e.id] = e.move;
            return d;
        }
    }

    public sealed class SimInput
    {
        public Vector2 Move;
        public bool Guard;
        public bool Jump;
        public List<ActionId> Actions = new List<ActionId>();
    }

    public sealed class RunningAction
    {
        public ActionId Id;
        public MoveDef Move;
        public float Elapsed;
        public bool Hit;
        public int Combo;
    }

    public sealed class PlayerState
    {
        public string Id;
        public string Name;
        public CoreId Core;
        public Vector2 Position;
        public Vector2 MoveInput;
        public float Height;
        public float VerticalVelocity;
        public float Facing;
        public float Hp = 500f;
        public float Mp = 100f;
        public float Guard = 300f;
        public float Ult;
        public bool Guarding;
        public float GuardStart = -99f;
        public RunningAction Action;
        public int Combo;
        public float ComboUntil;
        public Dictionary<ActionId, float> Cooldowns = new Dictionary<ActionId, float>();
        public int Kills;
        public int Deaths;
        public bool Alive = true;
        public float RespawnAt;
    }

    public sealed class DummyState
    {
        public float X;
        public float Y;
        public float Hp = 5000f;
        public float MaxHp = 5000f;
        public bool Alive = true;
        public float RespawnAt;
    }

    public sealed class CombatEvent
    {
        public CombatEventKind Kind;
        public float X;
        public float Y;
        public float Value;
        public string Target;
    }

    public static class SimMath
    {
        public static float Clamp(float v, float lo, float hi) => MathF.Max(lo, MathF.Min(hi, v));

        public static float AngleDiff(float a, float b)
        {
            float d = a - b;
            while (d > MathF.PI) d -= MathF.PI * 2f;
            while (d < -MathF.PI) d += MathF.PI * 2f;
            return d;
        }

        public static Vector2 NormalizeOrZero(Vector2 v)
        {
            float len = v.Length();
            return len > 0.0001f ? v / len : Vector2.Zero;
        }
    }
}

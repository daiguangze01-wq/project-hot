using System;
using System.Collections.Generic;
using System.Numerics;

namespace Hot.Sim
{
    /// <summary>
    /// Pure C# authoritative combat core (U1). No UnityEngine dependency.
    /// The Unity client sends SimInput; this core owns damage/cooldowns/guard.
    /// </summary>
    public sealed class CombatSim
    {
        public const int TickRate = 30;
        public const float ArenaHalf = 8f;
        public const float PlayerRadius = 0.42f;
        public const float Speed = 5.2f;
        public const float GuardSpeed = 1.5f;
        public const float JumpVelocity = 5f;
        public const float Gravity = 16f;
        private const float PerfectGuardWindow = 0.16f;

        public float Time { get; private set; }
        public int TickCount { get; private set; }
        public readonly Dictionary<string, PlayerState> Players = new Dictionary<string, PlayerState>();
        public DummyState Dummy = new DummyState();
        public readonly List<CombatEvent> Events = new List<CombatEvent>();

        private readonly Dictionary<ActionId, MoveDef> baseMoves = BuildBaseMoves();
        private int nextId = 1;
        private int spawned;

        public PlayerState AddPlayer(string name, CoreId core)
        {
            var p = new PlayerState { Id = "p" + nextId++, Name = name, Core = core };
            spawned++;
            p.Position = spawned % 2 == 1 ? new Vector2(0f, -3f) : new Vector2(0f, 3f);
            p.Facing = spawned % 2 == 1 ? MathF.PI / 2f : -MathF.PI / 2f;
            Players[p.Id] = p;
            Push(CombatEventKind.Spawn, p.Position.X, p.Position.Y, 0f, p.Id);
            return p;
        }

        public MoveDef GetMove(PlayerState p, ActionId id)
        {
            if (!baseMoves.TryGetValue(id, out var b)) return null;
            var core = CoreDef.All[p.Core];
            if (!core.Mods.TryGetValue(id, out var mod)) return b;

            return new MoveDef
            {
                Startup = mod.Startup > 0 ? mod.Startup : b.Startup,
                Active = mod.Active > 0 ? mod.Active : b.Active,
                Recovery = mod.Recovery > 0 ? mod.Recovery : b.Recovery,
                Damage = mod.Damage > 0 ? mod.Damage : b.Damage,
                Range = mod.Range > 0 ? mod.Range : b.Range,
                Width = mod.Width > 0 ? mod.Width : b.Width,
                Arc = mod.Arc > 0 ? mod.Arc : b.Arc,
                Knockback = mod.Knockback > 0 ? mod.Knockback : b.Knockback,
                Mp = mod.Mp > 0 ? mod.Mp : b.Mp,
                Cooldown = mod.Cooldown > 0 ? mod.Cooldown : b.Cooldown,
                ComboWindow = mod.ComboWindow > 0 ? mod.ComboWindow : b.ComboWindow,
                UltCost = mod.UltCost > 0 ? mod.UltCost : b.UltCost,
                Ranged = mod.Ranged ?? b.Ranged,
                Aoe = mod.Aoe ?? b.Aoe,
                Dash = mod.Dash > 0 ? mod.Dash : b.Dash
            };
        }

        public bool ApplyInput(string id, SimInput input)
        {
            if (!Players.TryGetValue(id, out var p) || input == null) return false;
            if (!p.Alive) return true;
            p.MoveInput = SimMath.NormalizeOrZero(input.Move);

            if (input.Guard && !p.Guarding && p.Action == null)
            {
                p.Guarding = true;
                p.GuardStart = Time;
            }
            else if (!input.Guard)
            {
                p.Guarding = false;
            }

            if (input.Jump && p.Height <= 0.001f && p.VerticalVelocity <= 0f)
            {
                p.VerticalVelocity = JumpVelocity;
                p.Guarding = false;
            }

            if (input.Actions != null)
            {
                foreach (var action in input.Actions)
                {
                    if (TryAction(p, action, input.Move)) break;
                }
            }
            return true;
        }

        public bool TryAction(PlayerState p, ActionId id, Vector2 inputDirection)
        {
            if (!p.Alive || p.Action != null) return false;
            var m = GetMove(p, id);
            if (m == null) return false;
            if (m.UltCost > 0 && p.Ult < m.UltCost) return false;
            if (m.Mp > 0 && p.Mp < m.Mp) return false;
            if (p.Cooldowns.TryGetValue(id, out var cd) && Time < cd) return false;

            var dir = SimMath.NormalizeOrZero(inputDirection);
            if (dir != Vector2.Zero) p.Facing = MathF.Atan2(dir.Y, dir.X);

            if (m.Mp > 0) p.Mp -= m.Mp;
            if (m.UltCost > 0) p.Ult -= m.UltCost;
            if (m.Cooldown > 0) p.Cooldowns[id] = Time + m.Cooldown;

            int combo = 1;
            if (id == ActionId.Light)
            {
                if (Time <= p.ComboUntil) combo = Math.Min(3, p.Combo + 1);
                p.Combo = combo;
                p.ComboUntil = Time + (m.ComboWindow > 0 ? m.ComboWindow : 0.75f);
            }

            if (m.Dash > 0)
            {
                p.Position += new Vector2(MathF.Cos(p.Facing), MathF.Sin(p.Facing)) * m.Dash;
                p.Position = ClampPosition(p.Position);
            }

            p.Action = new RunningAction { Id = id, Move = m, Combo = combo };
            p.Guarding = false;
            Push(CombatEventKind.Spawn, p.Position.X, p.Position.Y, 0f, p.Id); // action flash placeholder
            return true;
        }

        public void Tick(float dt = 1f / TickRate)
        {
            Time += dt;
            TickCount++;
            foreach (var p in Players.Values) TickPlayer(p, dt);
            TickDummy();
            SeparateBodies();
        }

        private void TickPlayer(PlayerState p, float dt)
        {
            if (!p.Alive)
            {
                if (Time >= p.RespawnAt) Respawn(p);
                return;
            }

            var expired = new List<ActionId>();
            foreach (var pair in p.Cooldowns)
                if (pair.Value <= Time) expired.Add(pair.Key);
            foreach (var key in expired) p.Cooldowns.Remove(key);

            if (p.Action != null)
            {
                p.Action.Elapsed += dt;
                if (!p.Action.Hit && p.Action.Elapsed >= p.Action.Move.Startup)
                {
                    p.Action.Hit = true;
                    ResolveHit(p, p.Action.Move, p.Action.Id, p.Action.Combo);
                }
                if (p.Action.Elapsed >= p.Action.Move.Duration) p.Action = null;
            }

            var dir = p.MoveInput;
            float speed = p.Guarding ? GuardSpeed : Speed;
            if (p.Action != null) speed *= 0.18f;
            if (dir != Vector2.Zero)
            {
                p.Position += dir * (speed * dt);
                p.Position = ClampPosition(p.Position);
                if (p.Action == null) p.Facing = MathF.Atan2(dir.Y, dir.X);
            }

            if (p.Height > 0 || p.VerticalVelocity != 0)
            {
                p.VerticalVelocity -= Gravity * dt;
                p.Height += p.VerticalVelocity * dt;
                if (p.Height <= 0)
                {
                    p.Height = 0;
                    p.VerticalVelocity = 0;
                }
            }

            if (p.Guard <= 0)
            {
                p.Guarding = false;
                p.Guard = 0;
            }
        }

        private void TickDummy()
        {
            if (!Dummy.Alive && Time >= Dummy.RespawnAt)
            {
                Dummy.Alive = true;
                Dummy.Hp = Dummy.MaxHp;
                Push(CombatEventKind.Spawn, Dummy.X, Dummy.Y, 0f, "dummy");
            }
        }

        private void ResolveHit(PlayerState attacker, MoveDef m, ActionId id, int combo)
        {
            foreach (var target in Players.Values)
            {
                if (target.Id == attacker.Id || !target.Alive) continue;
                if (IsInHitArea(attacker, target.Position, m)) ApplyDamage(attacker, target, m, id, combo);
            }

            if (Dummy.Alive)
            {
                var pos = new Vector2(Dummy.X, Dummy.Y);
                if (IsInHitArea(attacker, pos, m, 0.6f))
                {
                    Dummy.Hp = MathF.Max(0, Dummy.Hp - MathF.Round(m.Damage + (id == ActionId.Light ? (combo - 1) * 8 : 0)));
                    Push(CombatEventKind.Damage, pos.X, pos.Y, m.Damage, "dummy");
                    if (Dummy.Hp <= 0)
                    {
                        Dummy.Alive = false;
                        Dummy.RespawnAt = Time + 2f;
                        Push(CombatEventKind.DummyDown, pos.X, pos.Y, 0f, "dummy");
                    }
                }
            }
        }

        private bool IsInHitArea(PlayerState attacker, Vector2 target, MoveDef m, float extraRadius = PlayerRadius)
        {
            var delta = target - attacker.Position;
            float dist = delta.Length();
            if (dist > m.Range + extraRadius) return false;

            if (m.Ranged == true)
            {
                float dot = delta.X * MathF.Cos(attacker.Facing) + delta.Y * MathF.Sin(attacker.Facing);
                float perp = MathF.Abs(-delta.X * MathF.Sin(attacker.Facing) + delta.Y * MathF.Cos(attacker.Facing));
                return dot > 0 && dot <= m.Range && perp <= m.Width;
            }
            if (m.Aoe == true) return true;

            float angle = MathF.Atan2(delta.Y, delta.X);
            return MathF.Abs(SimMath.AngleDiff(angle, attacker.Facing)) <= (m.Arc * MathF.PI / 180f) / 2f;
        }

        private void ApplyDamage(PlayerState attacker, PlayerState target, MoveDef m, ActionId id, int combo)
        {
            float raw = m.Damage + (id == ActionId.Light ? (combo - 1) * 8 : 0);
            bool perfect = false;
            if (target.Guarding)
            {
                if (Time - target.GuardStart <= PerfectGuardWindow)
                {
                    perfect = true;
                    raw = 0;
                    target.Guard = MathF.Min(300f, target.Guard + 20f);
                    Push(CombatEventKind.PerfectGuard, target.Position.X, target.Position.Y, 0f, target.Id);
                }
                else
                {
                    raw *= 0.2f;
                    target.Guard = MathF.Max(0f, target.Guard - raw * 0.55f);
                    if (target.Guard <= 0)
                    {
                        target.Guarding = false;
                        target.Guard = 0;
                        target.Combo = 0;
                        Push(CombatEventKind.GuardBreak, target.Position.X, target.Position.Y, 0f, target.Id);
                    }
                }
            }

            int damage = (int)MathF.Round(raw);
            if (damage > 0)
            {
                target.Hp = MathF.Max(0f, target.Hp - damage);
                target.Ult = MathF.Min(100f, target.Ult + damage * 0.08f);
                attacker.Ult = MathF.Min(100f, attacker.Ult + damage * 0.12f);
                Push(CombatEventKind.Damage, target.Position.X, target.Position.Y, damage, target.Id);
                if (m.Knockback > 0)
                {
                    var push = SimMath.NormalizeOrZero(target.Position - attacker.Position) * m.Knockback * 0.18f;
                    target.Position = ClampPosition(target.Position + push);
                }
            }

            if (target.Hp <= 0 && target.Alive)
            {
                target.Alive = false;
                target.Action = null;
                target.Guarding = false;
                target.RespawnAt = Time + 3f;
                target.Deaths++;
                attacker.Kills++;
                Push(CombatEventKind.Death, target.Position.X, target.Position.Y, 0f, target.Id);
            }
        }

        private void Respawn(PlayerState p)
        {
            p.Alive = true;
            p.Hp = 500f;
            p.Mp = 100f;
            p.Guard = 300f;
            p.Ult = 0;
            p.Height = 0;
            p.VerticalVelocity = 0;
            p.Action = null;
            p.Guarding = false;
            p.Combo = 0;
            p.Cooldowns.Clear();
            p.Position = p.Id == "p1" ? new Vector2(0f, -3f) : new Vector2(0f, 3f);
            Push(CombatEventKind.Spawn, p.Position.X, p.Position.Y, 0f, p.Id);
        }

        private void SeparateBodies()
        {
            var list = new List<(Vector2 pos, float r, Action<Vector2> set)>();
            foreach (var p in Players.Values)
                if (p.Alive) list.Add((p.Position, PlayerRadius, v => p.Position = v));
            if (Dummy.Alive) list.Add((new Vector2(Dummy.X, Dummy.Y), 0.6f, v => { Dummy.X = v.X; Dummy.Y = v.Y; }));

            for (int i = 0; i < list.Count; i++)
            {
                for (int j = i + 1; j < list.Count; j++)
                {
                    var a = list[i];
                    var b = list[j];
                    var d = b.pos - a.pos;
                    float dist = d.Length();
                    float min = a.r + b.r;
                    if (dist >= min || dist < 0.0001f) continue;
                    var n = d / dist;
                    float push = (min - dist) * 0.5f;
                    a.set(ClampPosition(a.pos - n * push));
                    b.set(ClampPosition(b.pos + n * push));
                }
            }
        }

        private static Vector2 ClampPosition(Vector2 pos)
        {
            return new Vector2(
                SimMath.Clamp(pos.X, -ArenaHalf + PlayerRadius, ArenaHalf - PlayerRadius),
                SimMath.Clamp(pos.Y, -ArenaHalf + PlayerRadius, ArenaHalf - PlayerRadius));
        }

        private void Push(CombatEventKind kind, float x, float y, float value, string target)
        {
            Events.Add(new CombatEvent { Kind = kind, X = x, Y = y, Value = value, Target = target });
            if (Events.Count > 64) Events.RemoveAt(0);
        }

        private static Dictionary<ActionId, MoveDef> BuildBaseMoves()
        {
            return new Dictionary<ActionId, MoveDef>
            {
                { ActionId.Light, new MoveDef { Startup = .12f, Active = .06f, Recovery = .16f, Damage = 30, Range = 2.2f, Arc = 120, Knockback = 1f, ComboWindow = .75f } },
                { ActionId.Heavy, new MoveDef { Startup = .26f, Active = .08f, Recovery = .30f, Damage = 80, Range = 2.7f, Arc = 100, Knockback = 2.4f } },
                { ActionId.Skill1, new MoveDef { Startup = .20f, Active = .08f, Recovery = .22f, Damage = 70, Range = 2.8f, Arc = 130, Mp = 20, Cooldown = 4, Knockback = 1.8f, Dash = 2f } },
                { ActionId.Skill2, new MoveDef { Startup = .30f, Active = .10f, Recovery = .26f, Damage = 60, Range = 7f, Width = 1.4f, Mp = 30, Cooldown = 6, Knockback = 1.2f, Ranged = true } },
                { ActionId.Skill3, new MoveDef { Startup = .22f, Active = .08f, Recovery = .24f, Damage = 85, Range = 3f, Arc = 160, Mp = 25, Cooldown = 7, Knockback = 2f } },
                { ActionId.Skill4, new MoveDef { Startup = .30f, Active = .12f, Recovery = .30f, Damage = 120, Range = 3.4f, Arc = 360, Mp = 35, Cooldown = 9, Knockback = 2.8f, Aoe = true } },
                { ActionId.Ultimate, new MoveDef { Startup = .42f, Active = .16f, Recovery = .45f, Damage = 220, Range = 4.8f, Arc = 360, Cooldown = 20, Knockback = 3f, Aoe = true, UltCost = 100 } }
            };
        }
    }
}

'use strict';

/**
 * Project Hot — MVP authoritative simulation.
 * Pure Node module: no DOM, no network. 30Hz tick is driven by server.js.
 * Rules follow docs/00 v0.3.0 (2.5D ground combat, keyboard-only actions).
 */

const TICK_RATE = 30;
const ARENA_HALF = 8;
const PLAYER_RADIUS = 0.42;
const SPEED = 5.2;
const GUARD_SPEED = 1.5;
const JUMP_V = 5.0;
const GRAVITY = 16;

const MOVES = {
  light: {
    startup: 0.12, active: 0.06, recovery: 0.16, damage: 30, range: 2.2, arc: 120,
    mp: 0, cooldown: 0, knockback: 1.0, comboWindow: 0.75
  },
  heavy: {
    startup: 0.26, active: 0.08, recovery: 0.30, damage: 80, range: 2.7, arc: 100,
    mp: 0, cooldown: 0, knockback: 2.4
  },
  skill1: {
    startup: 0.20, active: 0.08, recovery: 0.22, damage: 70, range: 2.8, arc: 130,
    mp: 20, cooldown: 4, knockback: 1.8, dash: 2.0
  },
  skill2: {
    startup: 0.30, active: 0.10, recovery: 0.26, damage: 60, range: 7.0, width: 1.4,
    mp: 30, cooldown: 6, knockback: 1.2, ranged: true
  },
  skill3: {
    startup: 0.22, active: 0.08, recovery: 0.24, damage: 85, range: 3.0, arc: 160,
    mp: 25, cooldown: 7, knockback: 2.0
  },
  skill4: {
    startup: 0.30, active: 0.12, recovery: 0.30, damage: 120, range: 3.4, arc: 360,
    mp: 35, cooldown: 9, knockback: 2.8, aoe: true
  },
  ultimate: {
    startup: 0.42, active: 0.16, recovery: 0.45, damage: 220, range: 4.8, arc: 360,
    mp: 0, cooldown: 20, knockback: 3.0, aoe: true, ult: 100
  }
};

const CORES = {
  blade: {
    name: '剑豪',
    mods: {
      light: { damage: 30 },
      heavy: { damage: 80 },
      skill1: { damage: 70, range: 2.8, mp: 20, cooldown: 4 },
      skill2: { damage: 60, range: 7.0, width: 1.4, mp: 30, cooldown: 6, ranged: true },
      skill3: { damage: 85, range: 3.0, mp: 25, cooldown: 7, arc: 160 },
      skill4: { damage: 120, range: 3.4, mp: 35, cooldown: 9, arc: 360, aoe: true },
      ultimate: { damage: 220, range: 4.8 }
    }
  },
  fist: {
    name: '拳师',
    mods: {
      light: { damage: 26, range: 2.0 },
      heavy: { damage: 85, range: 2.5, startup: 0.24, recovery: 0.28 },
      skill1: { damage: 60, range: 2.3, mp: 15, cooldown: 3, dash: 1.6 },
      skill2: { damage: 75, range: 3.0, arc: 180, mp: 25, cooldown: 5, ranged: false, width: 0 },
      skill3: { damage: 95, range: 2.6, mp: 20, cooldown: 6, arc: 200 },
      skill4: { damage: 100, range: 3.8, mp: 30, cooldown: 8, arc: 360, aoe: true },
      ultimate: { damage: 240, range: 4.2 }
    }
  }
};

const PLAYER_COLORS = ['#63d6ff', '#ffb84d', '#a78bfa', '#61e28f'];
const SPAWNS = [
  { x: 0, y: 4.8 }, { x: 0, y: -4.8 },
  { x: -4.8, y: 0 }, { x: 4.8, y: 0 }
];

function makeId(prefix, n) {
  return prefix + n;
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function len(x, y) {
  return Math.hypot(x, y);
}

function angleDiff(a, b) {
  let d = a - b;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return d;
}

function createPlayer(id, name, color, spawn) {
  return {
    id,
    name: Array.from(String(name || 'Player')).slice(0, 18).join(''),
    color,
    x: spawn.x,
    y: spawn.y,
    z: 0,
    vx: 0,
    vy: 0,
    vz: 0,
    facing: spawn.y > 0 ? -Math.PI / 2 : Math.PI / 2,
    hp: 500,
    maxHp: 500,
    mp: 100,
    maxMp: 100,
    guard: 300,
    maxGuard: 300,
    ult: 0,
    maxUlt: 100,
    action: null,
    core: 'blade',
    coreName: '剑豪',
    guarding: false,
    guardStart: -99,
    combo: 0,
    comboUntil: 0,
    cooldowns: {},
    kills: 0,
    deaths: 0,
    alive: true,
    respawnAt: 0,
    held: { up: false, down: false, left: false, right: false, guard: false },
    seq: 0,
    lastSeen: 0,
    colorIndex: 0
  };
}

function createDummy() {
  return {
    id: 'dummy',
    name: '训练木桩',
    x: 0,
    y: 0,
    z: 0,
    facing: 0,
    hp: 5000,
    maxHp: 5000,
    alive: true,
    respawnAt: 0,
    color: '#8b98b8'
  };
}

class Sim {
  constructor(opts = {}) {
    this.time = 0;
    this.tickCount = 0;
    this.players = new Map();
    this.nextPlayer = 1;
    this.dummy = createDummy();
    this.fx = [];
    this.events = [];
    this.opts = opts;
  }

  addPlayer(name, core) {
    const n = this.nextPlayer++;
    const spawn = SPAWNS[(n - 1) % SPAWNS.length];
    const color = PLAYER_COLORS[(n - 1) % PLAYER_COLORS.length];
    const chosen = (typeof core === 'string' && Object.prototype.hasOwnProperty.call(CORES, core))
      ? core
      : (n % 2 === 1 ? 'blade' : 'fist');
    const p = createPlayer('p' + n, name, color, spawn);
    p.colorIndex = (n - 1) % PLAYER_COLORS.length;
    p.core = chosen;
    p.coreName = CORES[chosen].name;
    this.players.set(p.id, p);
    this.pushFx({ type: 'spawn', x: p.x, y: p.y, z: 0, color, ttl: 0.7 });
    return p;
  }

  removePlayer(id) {
    const existed = this.players.delete(id);
    // Keep ids/spawns stable for a fresh room, so a reload gets p1 again.
    if (existed && this.players.size === 0) this.nextPlayer = 1;
  }

  getPlayer(id) {
    return this.players.get(id);
  }

  applyInput(id, payload) {
    const p = this.players.get(id);
    if (!p) return false;
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return false;

    const seq = payload.seq;
    if (!Number.isInteger(seq) || seq <= 0) return false;
    if (seq <= p.seq || seq > p.seq + 3000) return false;

    const h = payload.held;
    if (h !== undefined && (typeof h !== 'object' || h === null || Array.isArray(h))) return false;
    if (payload.actions !== undefined && (!Array.isArray(payload.actions) || payload.actions.length > 8)) return false;

    p.seq = seq;
    p.lastSeen = this.time;

    // Full snapshot semantics: omitted keys mean "not held", so a partial
    // client update can never leave a movement key stuck.
    for (const k of ['up', 'down', 'left', 'right', 'guard']) {
      p.held[k] = !!(h && h[k]);
    }

    if (p.alive) {
      if (p.held.guard && !p.guarding && !p.action) {
        p.guarding = true;
        p.guardStart = this.time;
      } else if (!p.held.guard) {
        p.guarding = false;
      }
      if (Array.isArray(payload.actions)) {
        const seen = new Set();
        for (const action of payload.actions) {
          if (typeof action !== 'string' || seen.has(action)) continue;
          seen.add(action);
          this.tryAction(p, action);
        }
      }
    }
    return true;
  }

  getMove(p, type) {
    if (typeof type !== 'string' || !Object.prototype.hasOwnProperty.call(MOVES, type)) return null;
    const core = CORES[p.core] || CORES.blade;
    return { ...MOVES[type], ...(core.mods[type] || {}) };
  }

  tryAction(p, type) {
    if (!p.alive || p.action) return false;

    // V jump is an input verb, not a frame-data move.
    if (type === 'jump') {
      if (p.z > 0.001 || p.vz !== 0) return false;
      p.vz = JUMP_V;
      p.guarding = false;
      this.pushFx({ type: 'spawn', x: p.x, y: p.y, z: 0.2, color: p.color, ttl: 0.35 });
      return true;
    }

    const m = this.getMove(p, type);
    if (!m) return false;
    if (m.ult && p.ult < m.ult) return false;
    if (m.mp && p.mp < m.mp) return false;
    if (this.time < (p.cooldowns[type] || 0)) return false;

    // Direction held at activation chooses facing for directional skills.
    const dir = this.heldDirection(p);
    if (dir) p.facing = Math.atan2(dir.y, dir.x);

    if (m.mp) p.mp -= m.mp;
    if (m.ult) p.ult -= m.ult;
    if (m.cooldown) p.cooldowns[type] = this.time + m.cooldown;

    let combo = 1;
    if (type === 'light') {
      if (this.time <= p.comboUntil) combo = Math.min(3, p.combo + 1);
      p.combo = combo;
      p.comboUntil = this.time + m.comboWindow;
    }

    if (m.dash) {
      p.x = clamp(p.x + Math.cos(p.facing) * m.dash, -ARENA_HALF + PLAYER_RADIUS, ARENA_HALF - PLAYER_RADIUS);
      p.y = clamp(p.y + Math.sin(p.facing) * m.dash, -ARENA_HALF + PLAYER_RADIUS, ARENA_HALF - PLAYER_RADIUS);
    }

    p.action = { type, t: 0, hit: false, combo, duration: m.startup + m.active + m.recovery, move: m };
    p.guarding = false;
    this.pushFx({ type: 'action', action: type, x: p.x, y: p.y, z: p.z, color: p.color, ttl: 0.22 });
    return true;
  }

  heldDirection(p) {
    const dx = (p.held.right ? 1 : 0) - (p.held.left ? 1 : 0);
    const dy = (p.held.down ? 1 : 0) - (p.held.up ? 1 : 0);
    if (!dx && !dy) return null;
    const n = Math.hypot(dx, dy) || 1;
    return { x: dx / n, y: dy / n };
  }

  tick(dt = 1 / TICK_RATE) {
    this.time += dt;
    this.tickCount++;

    for (const p of this.players.values()) this.tickPlayer(p, dt);
    this.tickDummy(dt);

    // Separate players/dummy (simple circle separation).
    const bodies = [...this.players.values()].filter((p) => p.alive).map((p) => ({ p, r: PLAYER_RADIUS }));
    if (this.dummy.alive) bodies.push({ p: this.dummy, r: 0.6 });
    for (let i = 0; i < bodies.length; i++) {
      for (let j = i + 1; j < bodies.length; j++) {
        const a = bodies[i];
        const b = bodies[j];
        const dx = b.p.x - a.p.x;
        const dy = b.p.y - a.p.y;
        const d = Math.hypot(dx, dy) || 0.0001;
        const min = a.r + b.r;
        if (d < min) {
          const push = (min - d) / 2;
          const nx = dx / d;
          const ny = dy / d;
          a.p.x = clamp(a.p.x - nx * push, -ARENA_HALF + a.r, ARENA_HALF - a.r);
          a.p.y = clamp(a.p.y - ny * push, -ARENA_HALF + a.r, ARENA_HALF - a.r);
          b.p.x = clamp(b.p.x + nx * push, -ARENA_HALF + b.r, ARENA_HALF - b.r);
          b.p.y = clamp(b.p.y + ny * push, -ARENA_HALF + b.r, ARENA_HALF - b.r);
        }
      }
    }

    // FX lifetimes
    for (const f of this.fx) f.ttl -= dt;
    this.fx = this.fx.filter((f) => f.ttl > 0);
    for (const e of this.events) e.ttl -= dt;
    this.events = this.events.filter((e) => e.ttl > 0);
  }

  tickPlayer(p, dt) {
    if (!p.alive) {
      if (this.time >= p.respawnAt) this.respawn(p);
      return;
    }

    for (const type of Object.keys(p.cooldowns)) {
      if (p.cooldowns[type] <= this.time) delete p.cooldowns[type];
    }

    if (p.action) {
      const m = p.action.move || this.getMove(p, p.action.type);
      p.action.t += dt;
      if (!p.action.hit && p.action.t >= m.startup) {
        p.action.hit = true;
        this.resolveHit(p, m, p.action.type, p.action.combo);
      }
      if (p.action.t >= p.action.duration) p.action = null;
    }

    // Movement
    const dir = this.heldDirection(p);
    let speed = SPEED;
    if (p.guarding) speed = GUARD_SPEED;
    if (p.action) speed *= 0.18;
    if (dir) {
      p.x = clamp(p.x + dir.x * speed * dt, -ARENA_HALF + PLAYER_RADIUS, ARENA_HALF - PLAYER_RADIUS);
      p.y = clamp(p.y + dir.y * speed * dt, -ARENA_HALF + PLAYER_RADIUS, ARENA_HALF - PLAYER_RADIUS);
      // Once committed, an attack keeps its facing (no mid-startup turn).
      if (!p.action) p.facing = Math.atan2(dir.y, dir.x);
      if (p.guarding && p.action) p.guarding = false;
    }

    // Jump / gravity
    if (p.z > 0 || p.vz !== 0) {
      p.vz -= GRAVITY * dt;
      p.z += p.vz * dt;
      if (p.z <= 0) {
        p.z = 0;
        p.vz = 0;
      }
    }

    // Guard break recovery
    if (p.guard <= 0) {
      p.guarding = false;
      p.guard = 0;
    }
  }

  tickDummy(dt) {
    const d = this.dummy;
    if (!d.alive) {
      if (this.time >= d.respawnAt) {
        d.alive = true;
        d.hp = d.maxHp;
        this.pushEvent({ type: 'dummyRespawn' });
      }
    }
  }

  resolveHit(p, m, type, combo) {
    const targets = [];
    for (const other of this.players.values()) {
      if (other.id !== p.id && other.alive) targets.push(other);
    }
    if (this.dummy.alive) targets.push(this.dummy);

    for (const t of targets) {
      const dx = t.x - p.x;
      const dy = t.y - p.y;
      const dist = Math.hypot(dx, dy);
      if (dist > m.range + (t === this.dummy ? 0.6 : PLAYER_RADIUS)) continue;

      if (m.ranged) {
        const dot = dx * Math.cos(p.facing) + dy * Math.sin(p.facing);
        const perp = Math.abs(-dx * Math.sin(p.facing) + dy * Math.cos(p.facing));
        if (dot <= 0 || dot > m.range || perp > m.width) continue;
      } else if (!m.aoe) {
        const ang = Math.atan2(dy, dx);
        if (Math.abs(angleDiff(ang, p.facing)) > (m.arc * Math.PI / 180) / 2) continue;
      }

      let dmg = m.damage;
      if (type === 'light') dmg += (combo - 1) * 8;
      this.applyDamage(p, t, dmg, type, m);
    }
  }

  applyDamage(attacker, target, raw, type, move) {
    if (target === this.dummy) {
      this.dummy.hp = Math.max(0, this.dummy.hp - Math.round(raw));
      this.pushFx({ type: 'damage', x: target.x, y: target.y, z: 1.2, value: Math.round(raw), color: '#ffd166', ttl: 0.8 });
      if (this.dummy.hp <= 0) {
        this.dummy.alive = false;
        this.dummy.respawnAt = this.time + 2;
        this.pushEvent({ type: 'dummyDown' });
      }
      if (attacker && attacker.ult !== undefined) attacker.ult = Math.min(attacker.maxUlt, attacker.ult + raw * 0.12);
      return;
    }

    let dmg = raw;
    let perfect = false;
    if (target.guarding) {
      if (this.time - target.guardStart <= 0.16) {
        perfect = true;
        dmg = 0;
        target.guard = Math.min(target.maxGuard, target.guard + 20);
        this.pushFx({ type: 'perfect', x: target.x, y: target.y, z: 1.5, color: '#63d6ff', ttl: 0.7 });
      } else {
        dmg = raw * 0.2;
        target.guard = Math.max(0, target.guard - raw * 0.55);
        if (target.guard <= 0) {
          target.guarding = false;
          target.guard = 0;
          target.combo = 0;
          this.pushFx({ type: 'guardBreak', x: target.x, y: target.y, z: 1.2, color: '#ff6b6b', ttl: 0.8 });
        }
      }
    }

    dmg = Math.round(dmg);
    if (dmg > 0) {
      target.hp = Math.max(0, target.hp - dmg);
      target.ult = Math.min(target.maxUlt, target.ult + dmg * 0.08);
      if (attacker && attacker.ult !== undefined) attacker.ult = Math.min(attacker.maxUlt, attacker.ult + dmg * 0.12);
      this.pushFx({ type: 'damage', x: target.x, y: target.y, z: 1.2, value: dmg, color: perfect ? '#63d6ff' : '#ffd166', ttl: 0.8 });
      // Simple knockback
      if (move && move.knockback) {
        const dx = target.x - attacker.x;
        const dy = target.y - attacker.y;
        const d = Math.hypot(dx, dy) || 1;
        target.x = clamp(target.x + (dx / d) * move.knockback * 0.18, -ARENA_HALF + PLAYER_RADIUS, ARENA_HALF - PLAYER_RADIUS);
        target.y = clamp(target.y + (dy / d) * move.knockback * 0.18, -ARENA_HALF + PLAYER_RADIUS, ARENA_HALF - PLAYER_RADIUS);
      }
    }

    if (target.hp <= 0 && target.alive) {
      target.alive = false;
      target.action = null;
      target.guarding = false;
      target.respawnAt = this.time + 3;
      target.deaths++;
      if (attacker && attacker.id !== target.id) attacker.kills++;
      this.pushEvent({ type: 'ko', x: target.x, y: target.y, name: target.name, by: attacker ? attacker.name : '' });
      this.pushFx({ type: 'ko', x: target.x, y: target.y, z: 1.0, color: '#ff6b6b', ttl: 1.2 });
    }
  }

  respawn(p) {
    const spawn = SPAWNS[p.colorIndex % SPAWNS.length];
    p.alive = true;
    p.hp = p.maxHp;
    p.mp = p.maxMp;
    p.guard = p.maxGuard;
    p.ult = 0;
    p.x = spawn.x;
    p.y = spawn.y;
    p.z = 0;
    p.vz = 0;
    p.action = null;
    p.guarding = false;
    p.combo = 0;
    p.cooldowns = {};
    this.pushFx({ type: 'spawn', x: p.x, y: p.y, z: 0, color: p.color, ttl: 0.7 });
  }

  pushFx(f) {
    this.fx.push({ ...f, id: this.tickCount + ':' + this.fx.length });
  }

  pushEvent(e) {
    this.events.push({ ...e, ttl: 1.0 });
  }

  getState() {
    return {
      time: Number(this.time.toFixed(3)),
      tick: this.tickCount,
      arena: ARENA_HALF,
      players: [...this.players.values()].map((p) => ({
        id: p.id,
        name: p.name,
        color: p.color,
        core: p.core,
        coreName: p.coreName,
        x: +p.x.toFixed(3),
        y: +p.y.toFixed(3),
        z: +p.z.toFixed(3),
        facing: +p.facing.toFixed(3),
        hp: Math.round(p.hp),
        maxHp: p.maxHp,
        mp: Math.round(p.mp),
        maxMp: p.maxMp,
        guard: Math.round(p.guard),
        maxGuard: p.maxGuard,
        ult: Math.round(p.ult),
        maxUlt: p.maxUlt,
        action: p.action ? { type: p.action.type, t: +p.action.t.toFixed(3), duration: p.action.duration } : null,
        guarding: p.guarding,
        alive: p.alive,
        kills: p.kills,
        deaths: p.deaths,
        respawnIn: p.alive ? 0 : Math.max(0, +(p.respawnAt - this.time).toFixed(1)),
        cooldowns: Object.fromEntries(Object.entries(p.cooldowns).map(([k, v]) => [k, Math.max(0, +(v - this.time).toFixed(1))]))
      })),
      dummy: {
        x: this.dummy.x, y: this.dummy.y, hp: Math.round(this.dummy.hp), maxHp: this.dummy.maxHp,
        alive: this.dummy.alive, name: this.dummy.name
      },
      fx: this.fx.map((f) => ({ ...f, ttl: +f.ttl.toFixed(2) })),
      events: this.events.map((e) => ({ ...e, ttl: +e.ttl.toFixed(2) }))
    };
  }
}

module.exports = {
  Sim, MOVES, CORES, TICK_RATE, ARENA_HALF, PLAYER_RADIUS, SPEED, createPlayer, createDummy
};

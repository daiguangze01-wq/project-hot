(() => {
  'use strict';

  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;

  const W = 1280;
  const H = 720;
  const ARENA = 8;
  const SCALE = 38;
  const CX = W / 2;
  const CY = 348;
  const PITCH = 50 * Math.PI / 180;
  const YAW = Math.PI / 4;
  const CP = Math.cos(PITCH), SP = Math.sin(PITCH);
  const CYAW = Math.cos(YAW), SYAW = Math.sin(YAW);

  const qs = new URLSearchParams(location.search);
  const demo = qs.get('demo') === '1';
  const requestedCore = qs.get('core') || '';
  const truncate = (s) => Array.from(String(s)).slice(0, 18).join('');
  const playerName = truncate(qs.get('name') || ('Player-' + Math.floor(Math.random() * 900 + 100)));

  function project(x, y, z = 0) {
    const rx = x * CYAW - y * SYAW;
    const ry = x * SYAW + y * CYAW;
    return {
      x: CX + rx * SCALE,
      y: CY + ry * SP * SCALE - z * CP * SCALE
    };
  }

  const el = {
    pname: document.getElementById('pname'),
    pstate: document.getElementById('pstate'),
    hpFill: document.getElementById('hpFill'),
    hpText: document.getElementById('hpText'),
    mpFill: document.getElementById('mpFill'),
    mpText: document.getElementById('mpText'),
    guardFill: document.getElementById('guardFill'),
    guardText: document.getElementById('guardText'),
    ultFill: document.getElementById('ultFill'),
    ultText: document.getElementById('ultText'),
    skills: document.getElementById('skills'),
    scoreList: document.getElementById('scoreList'),
    dummyHp: document.getElementById('dummyHp'),
    toast: document.getElementById('toast'),
    conn: document.getElementById('conn')
  };

  const my = { id: null, name: playerName, color: '#63d6ff', token: null, coreName: '' };
  let snapshots = [];
  let lastRecv = 0;
  let seq = 0;
  let reqInFlight = false;

  const keys = { up: false, down: false, left: false, right: false, z: false, x: false, c: false, v: false, space: false };
  let guardHeld = false;
  let subGuard = false;
  let pendingActions = [];
  let comboTimer = null;
  let ultimateLatch = false;
  const comboPressed = { z: false, x: false, c: false };
  let lastEventKey = '';
  let toastUntil = 0;

  const SKILLS = [
    { id: 'light', label: 'C', name: '轻击', cd: 0 },
    { id: 'heavy', label: 'X', name: '重击', cd: 0 },
    { id: 'skill1', label: 'Z+C', name: '技能1', cd: 4 },
    { id: 'skill2', label: 'Z+X', name: '技能2', cd: 6 },
    { id: 'skill3', label: 'Z→C', name: '技能3', cd: 7 },
    { id: 'skill4', label: 'Z→X', name: '技能4', cd: 9 },
    { id: 'ultimate', label: 'ULT', name: '必杀', cd: 20 }
  ];
  const skillEls = new Map();
  for (const s of SKILLS) {
    const d = document.createElement('div');
    d.className = 'skill';
    d.innerHTML = `<b>${s.label}</b>${s.name}<span class="cd" style="display:none"></span>`;
    el.skills.appendChild(d);
    skillEls.set(s.id, d);
  }

  function hasDir() {
    return keys.up || keys.down || keys.left || keys.right;
  }

  function scheduleCombo() {
    if (comboTimer) clearTimeout(comboTimer);
    comboTimer = setTimeout(resolveCombo, 70);
  }

  function resolveCombo() {
    comboTimer = null;
    const z = keys.z || comboPressed.z;
    const x = keys.x || comboPressed.x;
    const c = keys.c || comboPressed.c;
    comboPressed.z = comboPressed.x = comboPressed.c = false;
    if (z && x && c) {
      if (!ultimateLatch) {
        pendingActions.push('ultimate');
        ultimateLatch = true;
      }
      return;
    }
    if (z && c) {
      pendingActions.push(hasDir() ? 'skill3' : 'skill1');
      return;
    }
    if (z && x) {
      pendingActions.push(hasDir() ? 'skill4' : 'skill2');
      return;
    }
    if (c && x) {
      guardHeld = true;
      return;
    }
    if (c) {
      pendingActions.push('light');
      return;
    }
    if (x) {
      pendingActions.push('heavy');
      return;
    }
  }

  function updateGuardHeld() {
    guardHeld = keys.space || subGuard || (keys.c && keys.x && !keys.z);
    if (!keys.c || !keys.x) subGuard = false;
  }

  function keyName(e) {
    const k = e.code;
    if (k === 'ArrowUp' || k === 'KeyW') return 'up';
    if (k === 'ArrowDown' || k === 'KeyS') return 'down';
    if (k === 'ArrowLeft' || k === 'KeyA') return 'left';
    if (k === 'ArrowRight' || k === 'KeyD') return 'right';
    if (k === 'KeyZ') return 'z';
    if (k === 'KeyX') return 'x';
    if (k === 'KeyC') return 'c';
    if (k === 'KeyV') return 'v';
    if (k === 'Space') return 'space';
    return null;
  }

  function onKeyDown(e) {
    const k = keyName(e);
    if (!k) return;
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    e.preventDefault();
    if (e.repeat) return;
    keys[k] = true;
    if (k === 'v') {
      pendingActions.push('jump');
    } else if (k === 'z' || k === 'x' || k === 'c') {
      comboPressed[k] = true;
      if (k === 'c' && keys.x) subGuard = true;
      scheduleCombo();
    }
    if (k === 'space') {
      guardHeld = true;
    }
    updateGuardHeld();
  }

  function onKeyUp(e) {
    const k = keyName(e);
    if (!k) return;
    e.preventDefault();
    keys[k] = false;
    if (k === 'z' || k === 'x' || k === 'c') {
      ultimateLatch = false;
      if (!(keys.z && keys.x && keys.c)) ultimateLatch = false;
    }
    if (k === 'space') guardHeld = false;
    updateGuardHeld();
  }

  window.addEventListener('keydown', onKeyDown);
  window.addEventListener('keyup', onKeyUp);
  window.addEventListener('blur', () => {
    for (const k of Object.keys(keys)) keys[k] = false;
    guardHeld = false;
    subGuard = false;
    updateGuardHeld();
  });

  function heldPayload() {
    updateGuardHeld();
    return {
      up: keys.up,
      down: keys.down,
      left: keys.left,
      right: keys.right,
      guard: !!(guardHeld || keys.space)
    };
  }

  async function sendInput() {
    if (!my.id || !my.token || reqInFlight) return;
    reqInFlight = true;
    const actions = pendingActions.splice(0, 8);
    try {
      const res = await fetch('/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ playerId: my.id, token: my.token, seq: ++seq, held: heldPayload(), actions })
      });
      if (!res.ok && res.status !== 409) {
        el.conn.textContent = 'input error ' + res.status;
      }
    } catch (_) {
      // transient; SSE reconnect handles display
    } finally {
      reqInFlight = false;
    }
  }
  setInterval(sendInput, 33);

  function connect() {
    const q = 'name=' + encodeURIComponent(playerName) + (requestedCore ? '&core=' + encodeURIComponent(requestedCore) : '');
    const es = new EventSource('/events?' + q);
    es.addEventListener('welcome', (ev) => {
      try {
        const data = JSON.parse(ev.data);
        my.id = data.id;
        my.name = data.name;
        my.color = data.color;
        my.token = data.token;
        my.coreName = data.coreName || '';
        el.pname.textContent = data.name + (my.coreName ? ' · ' + my.coreName : '');
        el.pname.style.color = data.color;
        el.conn.textContent = 'connected · ' + data.id;
      } catch (_) {}
    });
    es.addEventListener('state', (ev) => {
      try {
        const s = JSON.parse(ev.data);
        snapshots.push(s);
        if (snapshots.length > 3) snapshots.shift();
        lastRecv = performance.now();
        if (demo) startDemo(s);
        if (my.id && !el.conn.textContent.startsWith('connected')) {
          el.conn.textContent = 'connected · ' + my.id;
        }
      } catch (_) {}
    });
    es.onerror = () => {
      el.conn.textContent = 'reconnecting…';
    };
  }

  function lerp(a, b, t) { return a + (b - a) * t; }

  function interpolatedState() {
    if (!snapshots.length) return null;
    const cur = snapshots[snapshots.length - 1];
    if (snapshots.length < 2) return cur;
    const prev = snapshots[snapshots.length - 2];
    const t = Math.max(0, Math.min(1, (performance.now() - lastRecv) / 50));
    const players = cur.players.map((p) => {
      const q = prev.players.find((x) => x.id === p.id);
      if (!q) return p;
      return {
        ...p,
        x: lerp(q.x, p.x, t),
        y: lerp(q.y, p.y, t),
        z: lerp(q.z, p.z, t),
        facing: p.facing,
        hp: p.hp,
        mp: p.mp,
        guard: p.guard,
        ult: p.ult
      };
    });
    return { ...cur, players };
  }

  // ---------- Rendering ----------
  function drawBackground() {
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#0c1320');
    g.addColorStop(0.55, '#0a0f19');
    g.addColorStop(1, '#05070c');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // distant glow
    const rg = ctx.createRadialGradient(CX, CY - 40, 40, CX, CY - 40, 560);
    rg.addColorStop(0, 'rgba(62,110,180,.18)');
    rg.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = rg;
    ctx.fillRect(0, 0, W, H);
  }

  function drawFloor() {
    const corners = [
      project(-ARENA, -ARENA, 0), project(ARENA, -ARENA, 0),
      project(ARENA, ARENA, 0), project(-ARENA, ARENA, 0)
    ];
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    for (let i = 1; i < 4; i++) ctx.lineTo(corners[i].x, corners[i].y);
    ctx.closePath();
    ctx.fillStyle = '#111a2a';
    ctx.fill();
    ctx.strokeStyle = 'rgba(99,214,255,.32)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // grid
    for (let i = -ARENA; i <= ARENA; i++) {
      const a = project(i, -ARENA, 0);
      const b = project(i, ARENA, 0);
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = i % 2 === 0 ? 'rgba(100,150,220,.15)' : 'rgba(100,150,220,.07)';
      ctx.lineWidth = 1;
      ctx.stroke();

      const c = project(-ARENA, i, 0);
      const d = project(ARENA, i, 0);
      ctx.beginPath();
      ctx.moveTo(c.x, c.y);
      ctx.lineTo(d.x, d.y);
      ctx.strokeStyle = i % 2 === 0 ? 'rgba(100,150,220,.15)' : 'rgba(100,150,220,.07)';
      ctx.stroke();
    }

    // center rings
    for (let r = 2; r <= 6; r += 2) {
      ctx.beginPath();
      for (let a = 0; a <= 64; a++) {
        const th = (a / 64) * Math.PI * 2;
        const p = project(Math.cos(th) * r, Math.sin(th) * r, 0);
        if (a === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
      }
      ctx.strokeStyle = 'rgba(99,214,255,.10)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // corner pylons
    for (const [x, y] of [[-ARENA, -ARENA], [ARENA, -ARENA], [ARENA, ARENA], [-ARENA, ARENA]]) {
      drawPylon(x, y);
    }
  }

  function drawPylon(x, y) {
    const base = project(x, y, 0);
    const top = project(x, y, 1.4);
    ctx.fillStyle = '#1a2538';
    ctx.strokeStyle = 'rgba(99,214,255,.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(base.x - 9, base.y);
    ctx.lineTo(base.x + 9, base.y);
    ctx.lineTo(top.x + 6, top.y);
    ctx.lineTo(top.x - 6, top.y);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#63d6ff';
    ctx.fillRect(top.x - 2, top.y - 2, 4, 4);
  }

  function drawShadow(x, y, z) {
    const g = project(x, y, 0);
    const a = Math.max(0.12, 0.48 - z * 0.16);
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(g.x, g.y, 22, 9, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawHealthBar(p) {
    const top = project(p.x, p.y, p.z);
    const y = top.y - 66;
    const w = 54;
    ctx.fillStyle = 'rgba(0,0,0,.55)';
    ctx.fillRect(top.x - w / 2 - 1, y - 1, w + 2, 6);
    const frac = Math.max(0, p.hp / p.maxHp);
    ctx.fillStyle = p.id === my.id ? '#63d6ff' : '#ff5c7a';
    ctx.fillRect(top.x - w / 2, y, w * frac, 4);
    ctx.font = '10px Consolas, monospace';
    ctx.textAlign = 'center';
    ctx.fillStyle = p.id === my.id ? '#bfefff' : '#c9d5ea';
    ctx.fillText(p.name, top.x, y - 6);
  }

  function drawCharacter(p, isLocal) {
    const g = project(p.x, p.y, 0);
    const b = project(p.x, p.y, p.z);
    drawShadow(p.x, p.y, p.z);

    if (!p.alive) {
      ctx.save();
      ctx.globalAlpha = 0.45;
      ctx.fillStyle = '#6f7f9a';
      ctx.beginPath();
      ctx.arc(g.x, g.y - 10, 10, Math.PI, 0);
      ctx.fill();
      ctx.fillStyle = '#cfd9ea';
      ctx.font = '10px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.fillText('RESPAWN ' + (p.respawnIn || 0) + 's', g.x, g.y - 28);
      ctx.restore();
      return;
    }

    // local ring
    if (isLocal) {
      ctx.save();
      ctx.strokeStyle = 'rgba(99,214,255,.65)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.ellipse(g.x, g.y, 27, 11, 0, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    const color = p.color || '#63d6ff';
    const dark = shade(color, -0.45);
    const light = shade(color, 0.35);
    const baseY = b.y - 8;

    // facing direction in screen space
    const f = project(p.x + Math.cos(p.facing), p.y + Math.sin(p.facing), 0);
    let dx = f.x - g.x, dy = f.y - g.y;
    const dl = Math.hypot(dx, dy) || 1;
    dx /= dl; dy /= dl;

    // legs
    ctx.strokeStyle = dark;
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(b.x - 6, baseY - 10);
    ctx.lineTo(b.x - 7, baseY + 4);
    ctx.moveTo(b.x + 6, baseY - 10);
    ctx.lineTo(b.x + 7, baseY + 4);
    ctx.stroke();

    // torso
    ctx.fillStyle = color;
    roundRect(b.x - 10, baseY - 30, 20, 22, 3);
    ctx.fill();
    ctx.fillStyle = light;
    ctx.fillRect(b.x - 8, baseY - 28, 6, 3);

    // shoulder / hat
    ctx.fillStyle = light;
    ctx.beginPath();
    ctx.moveTo(b.x - 15, baseY - 24);
    ctx.lineTo(b.x - 4, baseY - 32);
    ctx.lineTo(b.x + 5, baseY - 25);
    ctx.closePath();
    ctx.fill();

    // head
    ctx.fillStyle = '#f0d3b4';
    ctx.beginPath();
    ctx.arc(b.x, baseY - 38, 7, 0, Math.PI * 2);
    ctx.fill();

    // hat brim
    ctx.fillStyle = dark;
    ctx.beginPath();
    ctx.moveTo(b.x - 13, baseY - 44);
    ctx.lineTo(b.x + 13, baseY - 44);
    ctx.lineTo(b.x + 7, baseY - 48);
    ctx.lineTo(b.x - 7, baseY - 48);
    ctx.closePath();
    ctx.fill();

    // weapon
    ctx.strokeStyle = '#e9f2ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(b.x + dx * 8, baseY - 24 + dy * 4);
    ctx.lineTo(b.x + dx * 30, baseY - 32 + dy * 10);
    ctx.stroke();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(b.x + dx * 8, baseY - 24 + dy * 4);
    ctx.lineTo(b.x + dx * 28, baseY - 31 + dy * 9);
    ctx.stroke();

    // guard shield
    if (p.guarding) {
      ctx.save();
      ctx.strokeStyle = 'rgba(242,193,78,.85)';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(b.x + dx * 13, baseY - 26 + dy * 6, 22, -0.9, 0.9);
      ctx.stroke();
      ctx.restore();
    }

    // attack arc / hit flash
    if (p.action) {
      const t = p.action.t / Math.max(0.001, p.action.duration);
      const a = p.action.type;
      const col = a === 'ultimate' ? '#c4a5ff' : a === 'heavy' ? '#ffb84d' : a === 'skill2' ? '#ff7b7b' : '#63d6ff';
      ctx.save();
      ctx.globalAlpha = 0.35 + 0.45 * Math.sin(Math.min(1, t) * Math.PI);
      ctx.strokeStyle = col;
      ctx.lineWidth = a === 'ultimate' ? 6 : 3;
      ctx.beginPath();
      const rad = a === 'ultimate' ? 45 : a === 'skill4' ? 38 : 30;
      ctx.arc(b.x, baseY - 20, rad, p.facing - 0.7, p.facing + 0.7);
      ctx.stroke();
      ctx.restore();
    }

    drawHealthBar(p);
  }

  function drawDummy(d) {
    const g = project(d.x, d.y, 0);
    drawShadow(d.x, d.y, 0);
    if (!d.alive) {
      ctx.save();
      ctx.globalAlpha = 0.35;
      ctx.fillStyle = '#8794ad';
      ctx.fillRect(g.x - 9, g.y - 18, 18, 20);
      ctx.restore();
      return;
    }
    // post
    ctx.strokeStyle = '#5b4a35';
    ctx.lineWidth = 7;
    ctx.beginPath();
    ctx.moveTo(g.x, g.y + 4);
    ctx.lineTo(g.x, g.y - 46);
    ctx.stroke();
    // straw body
    ctx.fillStyle = '#b99a62';
    roundRect(g.x - 16, g.y - 58, 32, 30, 8);
    ctx.fill();
    ctx.fillStyle = '#d9bd82';
    ctx.beginPath();
    ctx.arc(g.x, g.y - 64, 11, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#8d744b';
    ctx.fillRect(g.x - 3, g.y - 70, 6, 2);
    ctx.fillRect(g.x - 10, g.y - 45, 20, 3);
    // hp bar
    const w = 74;
    ctx.fillStyle = 'rgba(0,0,0,.6)';
    ctx.fillRect(g.x - w / 2 - 1, g.y - 112, w + 2, 6);
    ctx.fillStyle = '#f2c14e';
    ctx.fillRect(g.x - w / 2, g.y - 111, w * Math.max(0, d.hp / d.maxHp), 4);
    ctx.fillStyle = '#d8c7a0';
    ctx.font = '10px Consolas, monospace';
    ctx.textAlign = 'center';
    ctx.fillText('木桩 ' + Math.max(0, Math.round(d.hp)), g.x, g.y - 118);
  }

  function drawFx(fx) {
    const p = project(fx.x, fx.y, fx.z || 0);
    const life = Math.max(0, Math.min(1, fx.ttl / 0.8));
    ctx.save();
    ctx.globalAlpha = life;
    if (fx.type === 'damage') {
      ctx.fillStyle = fx.color || '#ffd166';
      ctx.font = 'bold 18px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.fillText('-' + fx.value, p.x, p.y - (1 - life) * 26);
    } else if (fx.type === 'perfect') {
      ctx.strokeStyle = '#63d6ff';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 20 + (1 - life) * 24, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = '#bfefff';
      ctx.font = 'bold 12px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.fillText('PERFECT', p.x, p.y - 34);
    } else if (fx.type === 'guardBreak') {
      ctx.strokeStyle = '#ff6b6b';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 26 + (1 - life) * 20, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = '#ffb3b3';
      ctx.font = 'bold 12px Consolas, monospace';
      ctx.textAlign = 'center';
      ctx.fillText('GUARD BREAK', p.x, p.y - 34);
    } else if (fx.type === 'ko') {
      ctx.strokeStyle = '#ff6b6b';
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 30 + (1 - life) * 40, 0, Math.PI * 2);
      ctx.stroke();
    } else if (fx.type === 'spawn') {
      ctx.strokeStyle = fx.color || '#63d6ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 12 + (1 - life) * 26, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function shade(hex, amt) {
    const h = hex.replace('#', '');
    const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
    let r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    r = Math.max(0, Math.min(255, Math.round(r + 255 * amt)));
    g = Math.max(0, Math.min(255, Math.round(g + 255 * amt)));
    b = Math.max(0, Math.min(255, Math.round(b + 255 * amt)));
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawWorld(s) {
    drawBackground();
    drawFloor();
    if (!s) return;
    const objs = [];
    for (const p of s.players) objs.push({ kind: 'player', p, depth: p.x + p.y });
    if (s.dummy) objs.push({ kind: 'dummy', p: s.dummy, depth: s.dummy.x + s.dummy.y });
    objs.sort((a, b) => a.depth - b.depth);
    for (const o of objs) {
      if (o.kind === 'player') drawCharacter(o.p, o.p.id === my.id);
      else drawDummy(o.p);
    }
    for (const fx of s.fx || []) drawFx(fx);
  }

  function updateHud(s) {
    if (!s) return;
    const me = s.players.find((p) => p.id === my.id);
    if (!me) {
      el.pname.textContent = 'DISCONNECTED';
      el.pstate.textContent = 'reconnecting…';
      return;
    }
    el.pname.textContent = me.name + (me.coreName ? ' · ' + me.coreName : '');
    el.pname.style.color = me.color;
    el.pstate.textContent = !me.alive ? 'DOWN · ' + me.respawnIn + 's' : me.guarding ? 'GUARD' : me.action ? me.action.type.toUpperCase() : 'READY';
    setBar(el.hpFill, el.hpText, me.hp, me.maxHp);
    setBar(el.mpFill, el.mpText, me.mp, me.maxMp);
    setBar(el.guardFill, el.guardText, me.guard, me.maxGuard);
    setBar(el.ultFill, el.ultText, me.ult, me.maxUlt);
    for (const sdef of SKILLS) {
      const node = skillEls.get(sdef.id);
      if (!node) continue;
      const cd = (me.cooldowns && me.cooldowns[sdef.id]) || 0;
      const cdNode = node.querySelector('.cd');
      node.classList.toggle('cool', cd > 0 || (sdef.id === 'ultimate' && me.ult < 100));
      if (cd > 0) {
        cdNode.style.display = 'flex';
        cdNode.textContent = cd.toFixed(1);
      } else if (sdef.id === 'ultimate' && me.ult < 100) {
        cdNode.style.display = 'flex';
        cdNode.textContent = Math.floor(me.ult) + '%';
      } else {
        cdNode.style.display = 'none';
      }
    }
    const list = [...s.players].sort((a, b) => (b.kills - a.kills) || (a.deaths - b.deaths));
    el.scoreList.innerHTML = list.map((p) => (
      `<div class="scoreItem"><span><i class="dot" style="background:${p.color}"></i>${escapeHtml(p.name)}</span><span>${p.kills} / ${p.deaths}</span></div>`
    )).join('');
    el.dummyHp.textContent = Math.max(0, s.dummy.hp);
    if (s.events && s.events.length) {
      const ev = s.events[s.events.length - 1];
      const key = s.tick + ':' + ev.type + ':' + (ev.name || '');
      if (key !== lastEventKey) {
        lastEventKey = key;
        if (ev.type === 'ko') showToast((ev.by ? ev.by + ' KO ' : 'KO ') + (ev.name || ''), '#ff7d91');
        else if (ev.type === 'perfect') showToast('PERFECT GUARD', '#63d6ff');
        else if (ev.type === 'dummyDown') showToast('木桩重置', '#f2c14e');
      }
    }
  }

  function setBar(fill, text, v, max) {
    const pct = Math.max(0, Math.min(100, (v / max) * 100));
    fill.style.width = pct + '%';
    text.textContent = Math.round(v);
  }

  let toastTimer = null;
  function showToast(text, color) {
    el.toast.textContent = text;
    el.toast.style.color = color;
    el.toast.style.opacity = '1';
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.toast.style.opacity = '0'; }, 1100);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function loop() {
    const s = interpolatedState();
    drawWorld(s);
    updateHud(s);
    requestAnimationFrame(loop);
  }

  // Demo mode for screenshots / smoke test: approach dummy and attack.
  let demoStarted = false;
  function startDemo(s) {
    if (!demo || demoStarted) return;
    const me = s.players.find((p) => p.id === my.id);
    if (!me) return;
    demoStarted = true;
    if (me.y > 0.2) keys.up = true;
    else if (me.y < -0.2) keys.down = true;
    if (me.x > 0.2) keys.left = true;
    else if (me.x < -0.2) keys.right = true;
    setTimeout(() => { keys.up = keys.down = keys.left = keys.right = false; }, 400);
    setTimeout(() => pendingActions.push('light'), 760);
    setTimeout(() => pendingActions.push('light'), 1500);
    setTimeout(() => pendingActions.push('skill1'), 2500);
    setTimeout(() => pendingActions.push('skill2'), 4000);
  }

  connect();
  requestAnimationFrame(loop);
})();

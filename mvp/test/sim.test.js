'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { Sim, MOVES, ARENA_HALF, PLAYER_RADIUS } = require('../sim');

function step(sim, seconds) {
  const n = Math.ceil(seconds * 30);
  for (let i = 0; i < n; i++) sim.tick(1 / 30);
}

test('add/remove player and clamp movement', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  assert.equal(sim.players.size, 1);
  p.x = 0;
  p.y = 0;
  sim.applyInput(p.id, { seq: 1, held: { right: true, up: false, down: false, left: false }, actions: [] });
  step(sim, 1);
  assert.ok(p.x > 0);
  assert.ok(p.x <= ARENA_HALF - PLAYER_RADIUS + 1e-6);
  sim.removePlayer(p.id);
  assert.equal(sim.players.size, 0);
});

test('light attack damages the training dummy', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  p.x = 0;
  p.y = 2.2;
  p.facing = -Math.PI / 2;
  const before = sim.dummy.hp;
  assert.equal(sim.tryAction(p, 'light'), true);
  step(sim, 0.4);
  assert.ok(sim.dummy.hp < before, 'dummy hp should drop');
});

test('guard reduces damage and recent guard can perfect-block', () => {
  const sim = new Sim();
  const a = sim.addPlayer('A');
  const b = sim.addPlayer('B');
  a.x = -2; a.y = 0;
  b.x = 0; b.y = 0;

  // Guard started now: within perfect window.
  b.guarding = true;
  b.guardStart = sim.time;
  const hp0 = b.hp;
  sim.applyDamage(a, b, 100, 'heavy', MOVES.heavy);
  assert.equal(b.hp, hp0, 'perfect guard should block all damage');
  assert.ok(b.guard > b.maxGuard - 1);

  // Guard started long ago: normal guard reduces to 20%.
  b.guarding = true;
  b.guardStart = sim.time - 2;
  const hp1 = b.hp;
  sim.applyDamage(a, b, 100, 'heavy', MOVES.heavy);
  assert.equal(b.hp, hp1 - 20);
});

test('MP, cooldown and ultimate resource are enforced', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  p.ult = 0;
  assert.equal(sim.tryAction(p, 'ultimate'), false);
  p.ult = 100;
  assert.equal(sim.tryAction(p, 'ultimate'), true);
  assert.equal(p.ult, 0);
  p.action = null;
  p.mp = 0;
  assert.equal(sim.tryAction(p, 'skill1'), false);
});

test('death and respawn restore resources', () => {
  const sim = new Sim();
  const a = sim.addPlayer('A');
  const b = sim.addPlayer('B');
  b.hp = 1;
  sim.applyDamage(a, b, 100, 'light', MOVES.light);
  assert.equal(b.alive, false);
  assert.equal(b.deaths, 1);
  sim.time = b.respawnAt + 0.01;
  sim.tick(1 / 30);
  assert.equal(b.alive, true);
  assert.equal(b.hp, b.maxHp);
  assert.equal(b.mp, b.maxMp);
});

test('stale/oversized/non-finite sequences are rejected', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  assert.equal(sim.applyInput(p.id, { seq: 2, held: {}, actions: [] }), true);
  assert.equal(sim.applyInput(p.id, { seq: 2, held: {}, actions: [] }), false);
  assert.equal(sim.applyInput(p.id, { seq: 1e15, held: {}, actions: [] }), false);
  assert.equal(sim.applyInput(p.id, { seq: '3', held: {}, actions: [] }), false);
  assert.equal(sim.applyInput(p.id, { seq: Infinity, held: {}, actions: [] }), false);
  assert.equal(sim.applyInput('missing', { seq: 3, held: {}, actions: [] }), false);
});

test('malformed held/action values do not throw or create moves', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  assert.equal(sim.applyInput(p.id, { seq: 1, held: 5, actions: [] }), false);
  assert.equal(sim.applyInput(p.id, { seq: 2, held: 'up', actions: [] }), false);
  for (const type of ['constructor', 'toString', '__proto__', '', 42]) {
    assert.equal(sim.tryAction(p, type), false, 'bad action ' + type);
  }
  assert.equal(p.action, null);
});

test('V jump lifts the player and lands', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  assert.equal(sim.tryAction(p, 'jump'), true);
  assert.ok(p.vz > 0);
  step(sim, 0.2);
  assert.ok(p.z > 0, 'player is airborne');
  step(sim, 1.2);
  assert.equal(p.z, 0, 'player lands');
});

test('cores change the moveset and reject prototype keys', () => {
  const sim = new Sim();
  const blade = sim.addPlayer('Blade', 'blade');
  const fist = sim.addPlayer('Fist', 'fist');
  assert.equal(blade.core, 'blade');
  assert.equal(fist.core, 'fist');
  assert.notEqual(sim.getMove(blade, 'skill1').damage, sim.getMove(fist, 'skill1').damage);
  assert.equal(sim.getState().players[0].coreName, '剑豪');

  const ghost = sim.addPlayer('Ghost', '__proto__');
  assert.equal(ghost.core, 'blade', 'prototype key falls back to blade');

  const emoji = sim.addPlayer('😀'.repeat(25), 'blade');
  assert.equal(Array.from(emoji.name).length, 18, 'name truncates by code point');
});

test('held is a full snapshot (omitted keys released)', () => {
  const sim = new Sim();
  const p = sim.addPlayer('A');
  sim.applyInput(p.id, { seq: 1, held: { right: true }, actions: [] });
  step(sim, 0.2);
  assert.equal(p.held.right, true);
  sim.applyInput(p.id, { seq: 2, held: {}, actions: [] });
  assert.equal(p.held.right, false);
  assert.equal(p.held.guard, false);
});

test('state snapshot exposes players and dummy', () => {
  const sim = new Sim();
  sim.addPlayer('A');
  const s = sim.getState();
  assert.equal(s.players.length, 1);
  assert.ok(s.dummy);
  assert.equal(s.players[0].maxHp, 500);
  assert.equal(s.players[0].maxGuard, 300);
});

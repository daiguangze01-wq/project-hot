'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('../server');

async function start() {
  const app = createApp();
  await new Promise((resolve) => app.server.listen(0, '127.0.0.1', resolve));
  const port = app.server.address().port;
  return { app, base: `http://127.0.0.1:${port}` };
}

async function joinSSE(base, name) {
  const ac = new AbortController();
  const res = await fetch(base + '/events?name=' + encodeURIComponent(name), { signal: ac.signal });
  assert.equal(res.status, 200);
  const reader = res.body.getReader();
  let buf = '';
  let id = null, token = null;
  const deadline = Date.now() + 3000;
  while (Date.now() < deadline && !token) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += Buffer.from(value).toString('utf8');
    const m = buf.match(/event: welcome\ndata: (\{[^\n]+\})/);
    if (m) {
      const w = JSON.parse(m[1]);
      id = w.id;
      token = w.token;
    }
  }
  assert.ok(id && token, 'SSE welcome includes id and token');
  return { id, token, ac, reader };
}

test('health and static client', async () => {
  const { app, base } = await start();
  try {
    const health = await fetch(base + '/health');
    assert.equal(health.status, 200);
    const h = await health.json();
    assert.equal(h.ok, true);
    assert.equal(h.players, 0);

    const page = await fetch(base + '/');
    assert.equal(page.status, 200);
    const html = await page.text();
    assert.match(html, /Project Hot/i);
    assert.match(html, /game\.js/);
  } finally {
    app.close();
  }
});

test('SSE join + input round-trip', async () => {
  const { app, base } = await start();
  const ac = new AbortController();
  try {
    const res = await fetch(base + '/events?name=Tester', { signal: ac.signal });
    assert.equal(res.status, 200);
    const reader = res.body.getReader();
    let buf = '';
    let id = null;
    let token = null;
    const deadline = Date.now() + 3000;
    while (Date.now() < deadline && !token) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += Buffer.from(value).toString('utf8');
      const m = buf.match(/event: welcome\ndata: (\{[^\n]+\})/);
      if (m) {
        const w = JSON.parse(m[1]);
        id = w.id;
        token = w.token;
      }
    }
    assert.ok(id, 'welcome event with player id');
    assert.ok(token, 'welcome event with session token');
    assert.equal(app.sim.players.size, 1);

    const input = await fetch(base + '/input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: id, token, seq: 1, held: { right: true }, actions: ['light'] })
    });
    assert.equal(input.status, 204);

    const health = await fetch(base + '/health');
    const h = await health.json();
    assert.equal(h.players, 1);

    ac.abort();
    try { await reader.cancel(); } catch (_) {}
  } finally {
    ac.abort();
    app.close();
  }
});

test('two SSE clients see each other', async () => {
  const { app, base } = await start();
  const a = await joinSSE(base, 'Alpha');
  const b = await joinSSE(base, 'Beta');
  try {
    let buf = '';
    let seen = null;
    const deadline = Date.now() + 3000;
    while (Date.now() < deadline && !seen) {
      const { value, done } = await a.reader.read();
      if (done) break;
      buf += Buffer.from(value).toString('utf8');
      const states = [...buf.matchAll(/event: state\ndata: (\{[^\n]+\})/g)];
      for (const m of states) {
        const s = JSON.parse(m[1]);
        if (s.players.length === 2) { seen = s; break; }
      }
    }
    assert.ok(seen, 'both players appear in broadcast state');
    assert.deepEqual(seen.players.map((p) => p.name).sort(), ['Alpha', 'Beta']);
  } finally {
    try { a.ac.abort(); } catch (_) {}
    try { b.ac.abort(); } catch (_) {}
    try { await a.reader.cancel(); } catch (_) {}
    try { await b.reader.cancel(); } catch (_) {}
    app.close();
  }
});

test('rejects malformed input without killing the server', async () => {
  const { app, base } = await start();
  const conn = await joinSSE(base, 'ShapeProbe');
  try {
    const badBodies = [
      'null',
      '{not json',
      JSON.stringify({ playerId: conn.id, token: conn.token, seq: 2, held: 5 }),
      JSON.stringify({ playerId: conn.id, token: conn.token, seq: 2, held: 'up' }),
      JSON.stringify({ playerId: conn.id, token: conn.token, seq: 2, actions: 'light' })
    ];
    for (const body of badBodies) {
      const r = await fetch(base + '/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body
      });
      assert.equal(r.status, 400, 'bad body should be 400: ' + body);
    }

    const missingToken = await fetch(base + '/input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: conn.id, seq: 2, held: {}, actions: [] })
    });
    assert.equal(missingToken.status, 401);

    const mismatch = await fetch(base + '/input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: 'p999', token: conn.token, seq: 2, held: {}, actions: [] })
    });
    assert.equal(mismatch.status, 403);

    const health = await fetch(base + '/health');
    assert.equal(health.status, 200);
    const h = await health.json();
    assert.equal(h.ok, true);
    assert.equal(h.players, 1, 'server survives malformed input');

    const good = await fetch(base + '/input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playerId: conn.id, token: conn.token, seq: 2, held: { right: true }, actions: [] })
    });
    assert.equal(good.status, 204);
  } finally {
    try { conn.ac.abort(); } catch (_) {}
    try { await conn.reader.cancel(); } catch (_) {}
    app.close();
  }
});

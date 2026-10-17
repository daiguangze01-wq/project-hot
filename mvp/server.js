'use strict';

/**
 * Project Hot MVP — zero-dependency HTTP + SSE server.
 * - GET /              : playable client
 * - GET /events?name=  : SSE state stream (joins a player)
 * - POST /input        : { playerId, seq, held, actions }
 * - GET /health        : smoke-test summary
 *
 * Production plan uses Unity + Fusion 2; this MVP validates the 2.5D keyboard
 * combat loop and server-authoritative state with a simple transport.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { URL } = require('url');
const { Sim, TICK_RATE } = require('./sim');

const PUBLIC_DIR = path.join(__dirname, 'public');
const MAX_PLAYERS = 4;

function sendJson(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'Content-Length': Buffer.byteLength(body)
  });
  res.end(body);
}

function contentTypes(file) {
  if (file.endsWith('.html')) return 'text/html; charset=utf-8';
  if (file.endsWith('.js')) return 'text/javascript; charset=utf-8';
  if (file.endsWith('.css')) return 'text/css; charset=utf-8';
  if (file.endsWith('.png')) return 'image/png';
  if (file.endsWith('.svg')) return 'image/svg+xml';
  return 'application/octet-stream';
}

function createApp(opts = {}) {
  const publicDir = opts.publicDir || PUBLIC_DIR;
  const intervalMs = opts.intervalMs || 10;
  const sim = new Sim();
  const clients = new Map(); // playerId -> { res, name, token }
  const sessions = new Map(); // token -> playerId (input identity binding)
  let closed = false;
  let startedAt = Date.now();

  const server = http.createServer((req, res) => {
    // keep malformed HTTP from taking down the room
    req.on('error', () => {});
    res.on('error', () => {});
    const u = new URL(req.url, 'http://localhost');

    if (req.method === 'GET' && u.pathname === '/health') {
      return sendJson(res, 200, {
        ok: true,
        tick: sim.tickCount,
        players: sim.players.size,
        clients: clients.size,
        uptimeSec: Math.round((Date.now() - startedAt) / 1000)
      });
    }

    if (req.method === 'GET' && u.pathname === '/events') {
      return handleEvents(req, res, u);
    }

    if (req.method === 'POST' && u.pathname === '/input') {
      return handleInput(req, res);
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      return sendJson(res, 405, { error: 'method_not_allowed' });
    }

    return serveStatic(req, res, u);
  });

  function handleEvents(req, res, u) {
    if (sim.players.size >= MAX_PLAYERS) {
      res.writeHead(503, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Room is full (max 4 players).');
      return;
    }

    const rawName = (u.searchParams.get('name') || 'Player').trim();
    const name = Array.from(rawName).slice(0, 18).join('') || 'Player';
    const core = u.searchParams.get('core') || undefined;
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-store, no-transform',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no'
    });
    res.write('retry: 3000\n\n');

    const p = sim.addPlayer(name, core);
    const token = crypto.randomBytes(18).toString('hex');
    clients.set(p.id, { res, name, token });
    sessions.set(token, p.id);
    res.write(`event: welcome\ndata: ${JSON.stringify({ id: p.id, name: p.name, color: p.color, core: p.core, coreName: p.coreName, token })}\n\n`);
    res.write(`event: state\ndata: ${JSON.stringify(sim.getState())}\n\n`);

    const heartbeat = setInterval(() => {
      try { res.write(': ping\n\n'); } catch (_) { /* close below */ }
    }, 15000);
    if (heartbeat.unref) heartbeat.unref();

    const cleanup = () => {
      clearInterval(heartbeat);
      if (clients.has(p.id)) {
        const c = clients.get(p.id);
        clients.delete(p.id);
        if (c && c.token) sessions.delete(c.token);
        sim.removePlayer(p.id);
      }
    };
    req.on('close', cleanup);
    req.on('error', cleanup);
    res.on('close', cleanup);
  }

  function handleInput(req, res) {
    let raw = '';
    let tooLarge = false;
    req.on('data', (chunk) => {
      if (tooLarge) return;
      raw += chunk;
      if (raw.length > 8192) {
        tooLarge = true;
        sendJson(res, 413, { error: 'payload_too_large' });
        req.destroy();
      }
    });
    req.on('end', () => {
      if (tooLarge) return;
      try {
        const ct = String(req.headers['content-type'] || '');
        if (!ct.includes('application/json')) {
          return sendJson(res, 400, { error: 'content_type_must_be_json' });
        }

        let payload;
        try {
          payload = JSON.parse(raw || '{}');
        } catch (_) {
          return sendJson(res, 400, { error: 'invalid_json' });
        }
        if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
          return sendJson(res, 400, { error: 'payload_must_be_object' });
        }
        if (typeof payload.token !== 'string' || !sessions.has(payload.token)) {
          return sendJson(res, 401, { error: 'invalid_session' });
        }
        const boundId = sessions.get(payload.token);
        if (payload.playerId !== boundId) {
          return sendJson(res, 403, { error: 'player_session_mismatch' });
        }
        if (payload.held !== undefined && (typeof payload.held !== 'object' || payload.held === null || Array.isArray(payload.held))) {
          return sendJson(res, 400, { error: 'held_must_be_object' });
        }
        if (payload.actions !== undefined && !Array.isArray(payload.actions)) {
          return sendJson(res, 400, { error: 'actions_must_be_array' });
        }
        if (payload.actions && payload.actions.length > 8) {
          return sendJson(res, 400, { error: 'too_many_actions' });
        }

        const ok = sim.applyInput(boundId, payload);
        if (!ok) return sendJson(res, 409, { error: 'stale_or_invalid_seq' });
        res.writeHead(204, { 'Cache-Control': 'no-store' });
        res.end();
      } catch (err) {
        console.error('input handler error:', err && err.message);
        if (!res.headersSent) sendJson(res, 500, { error: 'internal_error' });
      }
    });
    req.on('error', () => {});
  }

  function serveStatic(req, res, u) {
    let rel = u.pathname === '/' ? '/index.html' : u.pathname;
    // Basic traversal protection: resolve under publicDir only.
    const file = path.resolve(publicDir, '.' + rel);
    if (!file.startsWith(publicDir + path.sep) && file !== path.join(publicDir, 'index.html')) {
      return sendJson(res, 403, { error: 'forbidden' });
    }
    fs.readFile(file, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('Not found');
        return;
      }
      res.writeHead(200, {
        'Content-Type': contentTypes(file),
        'Cache-Control': 'no-store',
        'Content-Length': data.length
      });
      if (req.method === 'HEAD') res.end();
      else res.end(data);
    });
  }

  // Fixed-step accumulator: Windows setInterval is coarse (~21Hz at 33ms),
  // so drive 30Hz sim steps from monotonic elapsed time instead.
  let lastTick = process.hrtime.bigint();
  let accumulator = 0;
  const interval = setInterval(() => {
    if (closed) return;
    const now = process.hrtime.bigint();
    let elapsed = Number(now - lastTick) / 1e9;
    lastTick = now;
    if (!Number.isFinite(elapsed) || elapsed < 0) elapsed = 0;
    if (elapsed > 0.25) elapsed = 0.25;
    accumulator += elapsed;

    let steps = 0;
    while (accumulator >= 1 / TICK_RATE && steps < 5) {
      sim.tick(1 / TICK_RATE);
      accumulator -= 1 / TICK_RATE;
      steps++;
    }
    if (steps === 0 || clients.size === 0) return;

    const data = JSON.stringify(sim.getState());
    for (const [id, c] of clients) {
      try {
        c.res.write(`event: state\ndata: ${data}\n\n`);
      } catch (_) {
        const c = clients.get(id);
        if (c && c.token) sessions.delete(c.token);
        clients.delete(id);
        sim.removePlayer(id);
      }
    }
  }, intervalMs);
  if (interval.unref) interval.unref();

  function close() {
    if (closed) return;
    closed = true;
    clearInterval(interval);
    for (const c of clients.values()) {
      try { c.res.end(); } catch (_) {}
    }
    clients.clear();
    sessions.clear();
    server.close();
  }

  return { server, sim, clients, close };
}

if (require.main === module) {
  const port = Number(process.env.PORT || 3000);
  const host = process.env.HOST || '127.0.0.1';
  const { server } = createApp();
  server.listen(port, host, () => {
    console.log(`Project Hot MVP running at http://${host}:${port}`);
    console.log('Open two tabs to test multiplayer. Keyboard only: WASD/arrows, Z X C V, Space.');
  });
  const shutdown = () => {
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(0), 500).unref();
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

module.exports = { createApp };

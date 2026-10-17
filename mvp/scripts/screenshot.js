'use strict';

/**
 * CDP screenshot helper (no Puppeteer).
 * Usage: node mvp/scripts/screenshot.js <url> <out.png> [width] [height] [waitMs]
 */
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const url = process.argv[2] || 'http://127.0.0.1:3000/?demo=1';
const out = path.resolve(process.argv[3] || 'mvp/screenshots/mvp-demo.png');
const width = Number(process.argv[4] || 1280);
const height = Number(process.argv[5] || 720);
const waitMs = Number(process.argv[6] || 6000);
const port = 9223;
const profile = path.resolve('mvp/.chrome-cdp-profile');
const chrome = process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

fs.mkdirSync(path.dirname(out), { recursive: true });
fs.mkdirSync(profile, { recursive: true });

const child = spawn(chrome, [
  '--headless=new',
  '--no-sandbox',
  '--disable-gpu',
  '--disable-dev-shm-usage',
  '--hide-scrollbars',
  `--window-size=${width},${height}`,
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`,
  'about:blank'
], { stdio: 'ignore', detached: false });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getJson(p) {
  const res = await fetch(`http://127.0.0.1:${port}${p}`);
  return res.json();
}

async function main() {
  let targets;
  for (let i = 0; i < 100; i++) {
    try {
      targets = await getJson('/json');
      if (targets && targets.length) break;
    } catch (_) {}
    await sleep(100);
  }
  if (!targets || !targets.length) throw new Error('CDP target not ready');
  const target = targets.find((t) => t.type === 'page') || targets[0];
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  let nextId = 1;
  ws.addEventListener('message', (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch (_) { return; }
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(JSON.stringify(msg.error)));
      else resolve(msg.result);
    }
  });
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true });
    ws.addEventListener('error', reject, { once: true });
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url });
  await sleep(waitMs);
  const shot = await send('Page.captureScreenshot', { format: 'png', fromSurface: true, captureBeyondViewport: false });
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log(`screenshot: ${out} (${fs.statSync(out).size} bytes)`);
  try { await send('Browser.close'); } catch (_) {}
  ws.close();
}

main().catch((err) => {
  console.error('screenshot failed:', err.message);
  process.exitCode = 1;
}).finally(async () => {
  await sleep(300);
  try { execFileSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore' }); } catch (_) {}
});

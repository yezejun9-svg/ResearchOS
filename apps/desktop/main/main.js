// ResearchOS Desktop main (W13-01 increment on the W02-03 thin shell).
//
// It still does not start a second business scheduler: it discovers the existing Go control host, starts it
// when it is genuinely unreachable, and exposes the four native clients through the channels declared in
// main/lib/ipc.js. The registration and the routing are pure functions of injected collaborators, so
// tests/ui/check drives them without an Electron runtime; what only a real session can prove stays disclosed.
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const childProcess = require('node:child_process');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const host = require('./lib/host.js');
const ipc = require('./lib/ipc.js');

const ROOT = path.resolve(__dirname, '..', '..');
const DISCOVERY = path.resolve(ROOT, '..', '..', '.local', 'v24_host.json');
const PRINCIPAL = path.resolve(ROOT, '..', '..', '.local', 'v24_principal.json');
const SMOKE = process.env.ROS_DESKTOP_SMOKE === '1';

const deps = {
  fsImpl: fs,
  httpImpl: http,
  spawnImpl: (cmd, args) => childProcess.spawn(cmd, args, { detached: true, stdio: 'ignore' }),
  discoveryFile: DISCOVERY,
  principalFile: PRINCIPAL,
  coreArgv: process.env.RESEARCHOS_CONTROL_EXE ? [process.env.RESEARCHOS_CONTROL_EXE, '--serve'] : ['researchos-control-unavailable'],
  sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
  transport: (verb, url, payload, headers) => request(verb, url, payload, headers),
};

function request(verb, url, payload, headers) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const body = payload && Object.keys(payload).length ? JSON.stringify(payload) : null;
    const req = http.request({
      hostname: u.hostname, port: u.port, path: u.pathname, method: verb, agent: false, timeout: 8000,
      headers: Object.assign({ 'content-type': 'application/json' }, headers || {},
        body ? { 'content-length': Buffer.byteLength(body) } : {}),
    }, (res) => {
      let text = '';
      res.on('data', (c) => { text += c; });
      res.on('end', () => {
        if (res.statusCode >= 400) return resolve({ status: 'ERROR', http_status: res.statusCode, error: 'HTTP_' + res.statusCode, body: text.slice(0, 400) });
        try { resolve(JSON.parse(text || '{}')); } catch { resolve({ status: 'ERROR', error: 'MALFORMED_HOST_REPLY' }); }
      });
    });
    req.on('error', (e) => resolve({ status: 'ERROR', error: String(e.code || e.message || e) }));
    req.on('timeout', () => { req.destroy(); resolve({ status: 'ERROR', error: 'TIMEOUT' }); });
    if (body) req.write(body);
    req.end();
  });
}

ipc.register(ipcMain, deps);

// The directory picker answers from the native dialog, so the first-run path never sends the user to a
// terminal to type a path.
ipcMain.handle('ros:workspacePickDirectory', async (event, body) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  const picked = await dialog.showOpenDialog(win, { properties: ['openDirectory', 'createDirectory'], title: 'Choose the ResearchOS workspace' });
  if (picked.canceled || !picked.filePaths.length) return { ok: false, reason: 'PICKER_CANCELLED' };
  return ipc.callCore(deps, 'workspace', 'register', Object.assign({}, body || {}, { path: picked.filePaths[0] }));
});

async function boot() {
  const started = await host.ensureCore(deps);
  const win = new BrowserWindow({
    width: 1180, height: 760, title: 'ResearchOS', show: !SMOKE,
    webPreferences: { preload: path.join(ROOT, 'preload', 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  win.loadFile(path.join(__dirname, 'workbench.html'));
  const report = {
    event: 'ready_to_show', host_health: started.health, host_launched_by_shell: started.launched,
    spawns: started.spawns, host_url: started.discovery ? started.discovery.url : null,
    channels: ipc.BRIDGE.length, electron: process.versions.electron, protocol: 'researchos-client/2', pid: process.pid,
  };
  console.log('ROS_DESKTOP_REPORT ' + JSON.stringify(report));
  if (SMOKE) setTimeout(() => app.exit(0), 300);
}

app.whenReady().then(boot).catch((e) => {
  console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'boot_failed', error: String(e && e.message || e) }));
  app.exit(2);
});

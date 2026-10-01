// ResearchOS Desktop thin main (W02-03). Uses the upstream-pinned Electron runtime
// (version locked in package.json, same major as third_party/mu/desktop). It does NOT
// start a second business scheduler: it discovers the existing Go control host and shows
// host status + protocol version only. Node APIs never cross into the renderer except via
// the constrained preload bridge.
const { app, BrowserWindow, ipcMain } = require('electron');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const DISCOVERY = path.resolve(__dirname, '..', '..', '..', '.local', 'v24_host.json');
const SMOKE = process.env.ROS_DESKTOP_SMOKE === '1';

function hostStatus() {
  return new Promise((resolve) => {
    let d;
    try { d = JSON.parse(fs.readFileSync(DISCOVERY, 'utf8')); }
    catch { resolve({ health: 'NOT_FOUND', error: 'discovery absent' }); return; }
    const req = http.get(d.url + '/healthz', { timeout: 4000 }, (res) => {
      res.resume();
      resolve({ health: res.statusCode === 200 ? 'UP' : 'HTTP_' + res.statusCode, url: d.url, pid: d.pid, data_dir: d.data_dir });
    });
    req.on('error', (e) => resolve({ health: 'DOWN', url: d.url, error: String(e.code || e) }));
    req.on('timeout', () => { req.destroy(); resolve({ health: 'TIMEOUT', url: d.url }); });
  });
}

ipcMain.handle('ros:host-status', async () => {
  const s = await hostStatus();
  return { ...s, product: 'researchos-desktop', client_protocol: 'researchos-client/2', electron: process.versions.electron };
});

app.whenReady().then(async () => {
  const win = new BrowserWindow({
    width: 960, height: 640, title: 'ResearchOS', show: !SMOKE,
    webPreferences: { preload: path.join(__dirname, '..', 'preload', 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  win.loadFile(path.join(__dirname, 'status.html'));
  const status = await hostStatus();
  const report = { event: 'ready_to_show', host_health: status.health, host_url: status.url || null, electron: process.versions.electron, protocol: 'researchos-client/2', pid: process.pid };
  console.log('ROS_DESKTOP_REPORT ' + JSON.stringify(report));
  if (SMOKE) { setTimeout(() => app.exit(0), 300); }
});

'use strict';
// Keep one isolated, visible ResearchOS Electron window open for native NVDA navigation.
const fs = require('node:fs');
const path = require('node:path');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const root = path.resolve(__dirname, '../../..');
const fixture = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const ready = path.resolve(process.argv[3]);
const done = path.resolve(process.argv[4]);
const focusRequest = path.resolve(process.argv[5]);
const focusAck = path.resolve(process.argv[6]);

(async () => {
  const app = await playwright._electron.launch({
    executablePath: process.env.RESEARCHOS_ELECTRON || path.join(root, 'apps/desktop/node_modules/electron/dist/electron.exe'),
    args: [path.join(root, 'apps/desktop')], cwd: root,
    env: { ...process.env, RESEARCHOS_CLI_DISCOVERY: fixture.discovery_file }, timeout: 40000,
  });
  try {
    const page = await app.firstWindow();
    await page.locator('#main h1').waitFor({ timeout: 20000 });
    await page.goto(`ros-app://desktop/p/${fixture.project_id}/settings`, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.locator('#main h1').waitFor({ timeout: 20000 });
    await page.waitForFunction(() => !document.querySelector('#main .loading-state'), null, { timeout: 20000 });
    const native = await app.evaluate(({ BrowserWindow }) => {
      const win = BrowserWindow.getAllWindows()[0];
      win.setSize(1440, 950); win.show(); win.focus();
      return { pid: process.pid, hwnd: win.getNativeWindowHandle().readBigUInt64LE().toString() };
    });
    fs.writeFileSync(ready, JSON.stringify({ ...native, url: page.url(), title: await page.title() }));
    const deadline = Date.now() + 120000;
    while (!fs.existsSync(done) && Date.now() < deadline) {
      if (fs.existsSync(focusRequest) && !fs.existsSync(focusAck)) {
        const focused = await app.evaluate(({ BrowserWindow }) => {
          const win = BrowserWindow.getAllWindows()[0];
          win.show(); win.moveTop(); win.focus();
          return win.isFocused();
        });
        fs.writeFileSync(focusAck, JSON.stringify({ focused }));
      }
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  } finally {
    await app.close();
  }
})().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });

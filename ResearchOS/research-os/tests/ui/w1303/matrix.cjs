'use strict';
// The packaged application is driven through Electron, not a browser-only copy.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { createHash } = require('node:crypto');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const root = path.resolve(__dirname, '../../..');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (process.env.RESEARCHOS_UI_SCREENS) {
  const requested = process.env.RESEARCHOS_UI_SCREENS.split(',');
  input.routes = Object.fromEntries(Object.entries(input.routes).filter(([screen]) => requested.includes(screen)));
}
const out = path.resolve(process.argv[3]);
const report = { schema: 'researchos.electron-visual.v1', status: 'EXECUTING', checks: [], failures: [], matrix: [], states: [], accessibility: [], screenshots: [], limitations: [
  'Development fixture data served by the real local API; simulated runtime observations are marked FIXTURE.',
  'Fault recovery cases use a controlled loopback transport proxy and do not represent production outages.',
  'Accessibility tree and keyboard checks are machine observations; physical screen-reader speech is not asserted.',
  'No provider inference, physical mobile device or installed-release acceptance is asserted.',
] };
let electronApp, proxy, mode = 'ready', stateScreen = null, held = [], activeSockets = new Set(), upstreamRequests = new Set();
const proxyLog = [];
function check(id, okay, detail = null) {
  report.checks.push({ id, status: okay ? 'PASS' : 'FAIL', detail });
  if (!okay) report.failures.push(id);
}
function hash(file) { return createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
async function capture(page, name) {
  const file = path.join(out, name + '.png');
  await page.screenshot({ path: file, fullPage: true, timeout: 15000 });
  report.screenshots.push({ path: name + '.png', sha256: hash(file) });
}
async function settle(page, allowError = false) {
  await page.locator('#main h1').waitFor({ timeout: 15000 });
  await page.waitForFunction(allowError => !document.querySelector('#main .loading-state') && (allowError || !document.querySelector('#main .state-notice')), allowError, { timeout: 20000 });
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}
async function navigate(page, route) {
  await page.goto('ros-app://desktop' + route, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await settle(page);
}
async function metrics(page) {
  return page.evaluate(() => ({
    width: innerWidth, height: innerHeight, dpr: devicePixelRatio,
    scroll: document.documentElement.scrollWidth,
    mainText: document.querySelector('#main')?.innerText || '',
    title: document.querySelector('#main h1')?.textContent || '',
    inputs: [...document.querySelectorAll('#main input:not([type=hidden]),#main textarea,#main select')].map(el => ({
      type: el.tagName, label: el.getAttribute('aria-label') || [...(el.labels || [])].map(label => label.textContent).join(' '),
      width: Math.round(el.getBoundingClientRect().width),
    })),
  }));
}
async function setViewport(width, height, zoom = 1) {
  await electronApp.evaluate(({ BrowserWindow }, { width, height, zoom }) => {
    const win = BrowserWindow.getAllWindows()[0];
    win.setMinimumSize(0, 0); win.setContentSize(width, height); win.webContents.setZoomFactor(zoom);
  }, { width, height, zoom });
}
async function theme(page, value) {
  await page.evaluate(theme => { localStorage.setItem('researchos.theme', theme); }, value);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await settle(page);
}
async function proxyStart() {
  const upstream = new URL(input.base_url);
  proxy = http.createServer(async (req, res) => {
    const route = new URL(req.url, 'http://fixture').pathname;
    const business = /^\/v[12]\//.test(route);
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    let operation = null; try { operation = JSON.parse(body.toString()).method || null; } catch {}
    const entry = { method: req.method, path: route, operation, mode, status: null };
    if (business) proxyLog.push(entry);
    function failure(status) { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify({ code: 'W1303_TRANSPORT_FIXTURE', message: 'FIXTURE transport response', correlation_id: 'w1303-fault' })); }
    const forward = () => {
      if (res.destroyed) return;
      const target = http.request({ hostname: upstream.hostname, port: upstream.port, path: req.url, method: req.method, headers: { ...req.headers, host: upstream.host }, agent: false }, response => {
        entry.status = response.statusCode; entry.response_mode = mode;
        if (mode === 'empty' && response.statusCode === 200 && ((req.method === 'GET' && !/\/events\/(stream|poll)$/.test(route) && !route.endsWith('/events')) || operation === 'session.list')) {
          const pieces = []; response.on('data', piece => pieces.push(piece));
          response.on('end', () => {
            let bytes = Buffer.concat(pieces);
            try { const value = JSON.parse(bytes.toString()); if (Array.isArray(value)) bytes = Buffer.from('[]'); else if (Array.isArray(value.items)) bytes = Buffer.from(JSON.stringify({ ...value, items: [], ...('next_cursor' in value ? { next_cursor: null } : {}) })); else if (operation === 'session.list' && Array.isArray(value.result?.items)) bytes = Buffer.from(JSON.stringify({ ...value, result: { items: [], next_cursor: null } })); } catch {}
            const headers = { ...response.headers }; delete headers['content-length'];
            res.writeHead(response.statusCode, headers); res.end(bytes);
          });
        } else { res.writeHead(response.statusCode, response.headers); response.pipe(res); }
        res.on('close', () => response.destroy());
      });
      upstreamRequests.add(target); target.on('close', () => upstreamRequests.delete(target));
      target.on('error', () => { if (!res.headersSent) failure(502); else res.destroy(); });
      req.on('aborted', () => target.destroy()); target.end(body);
    };
    if (business && mode === 'loading') { held.push(forward); return; }
    if (business && mode === 'error') return failure(500);
    if (business && mode === 'forbidden') return failure(403);
    if (business && mode === 'stale') return failure(412);
    if (business && mode === 'offline') { req.socket.destroy(); return; }
    const partialPath = { S01: '/profile', S02: '/experiments', S03: '/artifacts', S04: '/artifacts', S05: '/evidence', S06: '/qualifications', S07: '/skills', S08: '/runs', S09: '/budget-ledger', S10: '/run-policy' }[stateScreen];
    const partialMatches = ['S05', 'S07'].includes(stateScreen)
      ? route.includes(partialPath + '/')
      : partialPath && (route.endsWith(partialPath) || (stateScreen === 'S04' && route.includes('/artifacts/')));
    if (business && mode === 'partial' && ((stateScreen === 'S00' && operation === 'host.status') || partialMatches)) { entry.status = 503; return failure(503); }
    forward();
  });
  proxy.on('connection', socket => { activeSockets.add(socket); socket.on('close', () => activeSockets.delete(socket)); });
  await new Promise(resolve => proxy.listen(0, '127.0.0.1', resolve));
  const discovery = JSON.parse(fs.readFileSync(input.discovery_file, 'utf8'));
  discovery.url = 'http://127.0.0.1:' + proxy.address().port;
  const file = path.join(path.dirname(input.discovery_file), 'w1303-proxy-discovery.json');
  fs.writeFileSync(file, JSON.stringify(discovery));
  return file;
}
async function main() {
  const discovery = await proxyStart();
  const errors = [];
  electronApp = await playwright._electron.launch({
    executablePath: process.env.RESEARCHOS_ELECTRON || path.join(root, 'apps/desktop/node_modules/electron/dist/electron.exe'),
    args: [path.join(root, 'apps/desktop')], cwd: root,
    env: { ...process.env, RESEARCHOS_CLI_DISCOVERY: discovery }, timeout: 40000,
  });
  const page = await electronApp.firstWindow();
  page.on('pageerror', error => errors.push(String(error)));
  await settle(page);
  report.electron = await electronApp.evaluate(() => process.versions.electron);
  report.origin = new URL(page.url()).protocol + '//' + new URL(page.url()).host;
  check('NATIVE_REACT_ENTRY', report.origin === 'ros-app://desktop' && await page.locator('#access-token').count() === 0);
  check('CREDENTIAL_NOT_IN_RENDERER', await page.evaluate(() => !window.researchos?.credential && !Object.keys(localStorage).some(key => /token|credential/i.test(key))));
  report.browser_origin = await page.evaluate(() => location.origin);
  if (input.routes.S01) {
    await page.locator('#main a[href="' + input.routes.S01 + '"]').click();
    await settle(page);
    check('ACTUAL_PROJECT_LINK_OPENS_WORKBENCH', new URL(page.url()).pathname === input.routes.S01 && await page.getByRole('heading', { name: '项目会话', exact: true }).count() === 1);
    if (input.sessions) {
      await page.getByRole('button', { name: '加载更多会话', exact: true }).click();
      await page.waitForFunction(count => document.querySelectorAll('.session-picker li').length === count, input.sessions.session_count);
      check('SESSION_LIST_SECOND_PAGE', await page.locator('.session-picker li').count() === input.sessions.session_count);
      await page.getByRole('button', { name: /FIXTURE · 消息与工具回执/ }).click();
      await page.getByText('FIXTURE：请检查已封存的本地研究结果。此消息未调用模型。', { exact: true }).waitFor();
      await page.getByRole('heading', { name: '工具与结果', exact: true }).waitFor();
      check('PERSISTED_SESSION_MESSAGES_AND_TOOLS', await page.locator('.conversation-message').count() === 2 && await page.locator('.session-center .event-list li').count() === 2);
    }
  }

  const viewports = [[1440, 1000], [1024, 768], [768, 1024], [390, 844], [320, 780]];
  for (const [screen, route] of Object.entries(input.routes)) {
    for (const color of ['light', 'dark']) {
      await setViewport(1440, 1000);
      await navigate(page, route); await theme(page, color);
      for (const [width, height] of viewports) {
        await setViewport(width, height);
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(resolve)));
        const value = await metrics(page);
        const name = `${screen}-${color}-${width}`;
        const overflow = value.scroll > value.width + 1;
        check(name + '-NO_OVERFLOW', !overflow, { width: value.width, scroll: value.scroll });
        check(name + '-LABELS', value.inputs.every(item => !!item.label.trim()), value.inputs);
        report.matrix.push({ screen, route, theme: color, viewport: [width, height], title: value.title, measured: { width: value.width, height: value.height, scroll: value.scroll } });
        if (width === 1440 && color === 'light') report.states.push({ screen, state: 'ready', source: 'REAL_LOCAL_API', text: value.mainText });
        await capture(page, name);
        fs.writeFileSync(path.join(out, name + '.dom.txt'), value.mainText);
      }
    }
    await setViewport(1440, 1000, 2);
    await navigate(page, route);
    const value = await metrics(page);
    check(screen + '-NATIVE_ZOOM_200', value.width <= 730 && value.scroll <= value.width + 1, { width: value.width, scroll: value.scroll, dpr: value.dpr });
    await capture(page, screen + '-zoom200');
    await setViewport(1440, 1000);
    const accessibility = await page.locator('body').ariaSnapshot();
    fs.writeFileSync(path.join(out, screen + '.aria.yml'), accessibility);
    report.accessibility.push({ screen, artifact: screen + '.aria.yml', heading: /heading/.test(accessibility), navigation: /navigation/.test(accessibility) });
    check(screen + '-AX_LANDMARKS', /heading/.test(accessibility) && /navigation/.test(accessibility));
    await page.keyboard.press('Tab');
    check(screen + '-KEYBOARD_FOCUS', await page.evaluate(() => document.activeElement && document.activeElement !== document.body));
  }

  await setViewport(1024, 768);
  for (const [screen, route] of Object.entries(input.routes)) {
    stateScreen = screen;
    mode = screen === 'S00' ? 'empty' : 'ready';
    const emptyRoute = (['S02', 'S03', 'S04', 'S06'].includes(screen) ? route.substring(0, route.lastIndexOf('/')) : route).replace(input.project_id, input.empty_project_id);
    await navigate(page, emptyRoute);
    const emptyValue = await metrics(page);
    report.states.push({ screen, state: 'empty', route: emptyRoute, source: screen === 'S00' ? 'CONTRACT_LIST_EMPTY_FIXTURE' : 'REAL_LOCAL_API_EMPTY_PROJECT', text: emptyValue.mainText });
    check(screen + '-EMPTY_SUCCESS', await page.locator('#main .empty-state').count() > 0 && await page.locator('#main .state-notice').count() === 0);
    mode = 'ready';
    for (const state of ['loading', 'error', 'forbidden', 'stale', 'offline', 'partial']) {
      mode = state;
      const before = proxyLog.length;
      await page.goto('ros-app://desktop' + route, { waitUntil: 'domcontentloaded' });
      await page.locator('#main h1').waitFor();
      if (state === 'partial' && ['S05', 'S07'].includes(screen)) {
        // Keep the successful list visible while the selected detail fails.
        // Failing the sole collection request would exercise a total outage.
        await page.locator('#main button.record-row').first().click();
      }
      if (state === 'loading') {
        await page.locator('#main .loading-state').first().waitFor();
      } else {
        await page.locator('#main .state-notice').first().waitFor({ timeout: 15000 });
      }
      const observed = await metrics(page);
      report.states.push({ screen, state, source: 'CONTROLLED_TRANSPORT_FIXTURE', text: observed.mainText });
      check(`${screen}-${state}-NOTICE`, await page.locator(state === 'loading' ? '#main .loading-state' : '#main .state-notice').count() > 0);
      if (state === 'partial') check(`${screen}-PARTIAL_SUCCESS_AND_FAILURE`, proxyLog.slice(before).some(row => row.status === 503) && proxyLog.slice(before).some(row => row.status === 200));
      if (screen === 'S09' && ['error', 'forbidden', 'stale', 'offline'].includes(state)) {
        check(`S09-${state}-NO_INVENTED_BUDGET`, !observed.mainText.includes('金额策略\n未设上限'));
      }
      if (['S01', 'S09'].includes(screen)) await capture(page, screen + '-' + state);
      mode = 'ready'; const release = held; held = []; release.forEach(resume => resume());
      if (state !== 'loading') {
        const retry = page.locator('#main .state-notice button').filter({ hasText: '重新读取' });
        check(`${screen}-${state}-RETRY_AVAILABLE`, await retry.count() > 0);
        for (let attempt = 0; attempt < 4 && await retry.count(); attempt++) {
          try { await retry.first().click({ timeout: 2000 }); }
          catch (error) { if (await page.locator('#main .state-notice').count()) throw error; }
          await page.waitForTimeout(150);
        }
      }
      await settle(page);
      report.states.push({ screen, state: 'RECOVERED_FROM_' + state, source: 'REAL_LOCAL_API', title: (await metrics(page)).title });
      check(`${screen}-${state}-RECOVERY`, await page.locator('#main .loading-state').count() === 0 && await page.locator('#main .state-notice').count() === 0 && proxyLog.slice(before).some(row => row.response_mode === 'ready' && row.status === 200));
    }
  }
  report.proxy_requests = proxyLog;
  report.renderer_errors = errors;
  check('NO_UNHANDLED_RENDERER_ERRORS', errors.length === 0, errors);
  report.status = report.failures.length ? 'FAIL' : 'PASS';
}
main().catch(error => { report.status = 'FAIL'; report.error = error.stack || String(error); }).finally(async () => {
  mode = 'ready'; held.splice(0).forEach(resume => resume());
  if (electronApp) await electronApp.close().catch(() => {});
  upstreamRequests.forEach(request => request.destroy());
  activeSockets.forEach(socket => socket.destroy());
  if (proxy) await new Promise(resolve => proxy.close(resolve));
  fs.writeFileSync(path.join(out, 'matrix.json'), JSON.stringify(report, null, 2));
  process.stdout.write(JSON.stringify({ status: report.status, checks: report.checks.length, failures: report.failures, error: report.error || null }) + '\n', () => process.exit(report.status === 'PASS' ? 0 : 1));
});

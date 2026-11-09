// Read-only source probes. Electron and DOM are simulated, not a native Windows startup.
// Does not start a host, access a product database, call providers, or change source files.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const repo = path.resolve(__dirname, '../../research-os');
const report = { scope: 'SIMULATED_ELECTRON_AND_DOM_NOT_NATIVE_WINDOWS_STARTUP', checks: {} };

async function main() {
  const entry = path.join(repo, 'apps/desktop/main/main.js');
  const mainDir = path.dirname(entry);
  const channels = new Set();
  let readyReached = false;
  const electron = {
    app: { whenReady() { readyReached = true; return new Promise(() => {}); } },
    BrowserWindow: function () {}, dialog: {},
    ipcMain: { handle(name) {
      if (channels.has(name)) throw new Error('Attempted to register a second handler for ' + name);
      channels.add(name);
    } },
  };
  try {
    vm.runInNewContext(fs.readFileSync(entry, 'utf8'), {
      require(id) {
        if (id === 'electron') return electron;
        if (id === 'node:child_process') return { spawn() { throw new Error('UNEXPECTED_PROCESS_SPAWN'); } };
        if (id.startsWith('./')) return require(path.resolve(mainDir, id));
        return require(id);
      },
      __dirname: mainDir, process: { env: {} }, console, Buffer, setTimeout, URL,
    });
    report.checks.main_registration = { error: null, app_whenReady_reached: readyReached };
  } catch (error) {
    report.checks.main_registration = { error: error.message, app_whenReady_reached: readyReached };
  }

  const root = path.resolve(mainDir, '..', '..');
  const paths = {
    computed_preload: path.join(root, 'preload/preload.js'),
    actual_preload: path.join(repo, 'apps/desktop/preload/preload.js'),
    computed_discovery: path.resolve(root, '..', '..', '.local/v24_host.json'),
  };
  report.checks.path_resolution = Object.fromEntries(Object.entries(paths).map(([key, value]) =>
    [key, { path: value, exists: fs.existsSync(value) }]));

  const html = fs.readFileSync(path.join(repo, 'apps/desktop/main/workbench.html'), 'utf8');
  let code = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  code = code.replace(/refresh\(\);\s*$/, 'globalThis.result=refresh().then(()=>null).catch(e=>e.message);');
  const ids = [...html.matchAll(/id="([^"]+)"/g)].map(x => x[1]);
  const nodes = Object.fromEntries(ids.map(id => [id, { addEventListener() {}, appendChild() {}, textContent: '', className: '' }]));
  const calls = [];
  const bridgeNames = require(path.join(repo, 'apps/desktop/main/lib/ipc.js')).BRIDGE;
  const api = Object.fromEntries(bridgeNames.map(name => [name, async () => { calls.push(name); return { ok: true, items: [] }; }]));
  const box = { window: { researchos: api }, document: {
    getElementById(id) { return nodes[id] || null; }, querySelectorAll() { return []; }, createElement() { return {}; },
  } };
  vm.createContext(box);
  vm.runInContext(code, box);
  report.checks.workbench_refresh = { error: await box.result, bridge_calls_before_error: calls };
  report.checks.desktop_v2_ui = { references_to_v2_bridge_in_loaded_page: (html.match(/(?:api|researchos)\.v2\b/g) || []).length };

  const source = fs.readFileSync(path.join(repo, 'apps/web/src/continuity.jsx'), 'utf8');
  const appendSource = source.slice(source.indexOf('  function appendEvents(page)'), source.indexOf('  async function run('));
  let watermark = 0, events = [];
  const eventBox = {
    seen: { current: new Set() }, setEvents(update) { events = update(events); },
    setWatermark(update) { watermark = update(watermark); },
  };
  vm.createContext(eventBox);
  vm.runInContext(appendSource, eventBox);
  const page = { events: Array.from({ length: 200 }, (_, i) => ({ event_id: 'fixture-' + (i + 1), sequence: i + 1 })),
    next_sequence: 200, high_watermark: 250, has_more: true };
  eventBox.appendEvents(page);
  report.checks.event_pagination = { received_events: events.length, next_after_sequence: watermark,
    expected_next_after_sequence: page.next_sequence, unrequested_events_skipped: watermark - page.next_sequence };
  console.log(JSON.stringify(report, null, 2));
}
main().catch(error => { console.error(error); process.exitCode = 1; });

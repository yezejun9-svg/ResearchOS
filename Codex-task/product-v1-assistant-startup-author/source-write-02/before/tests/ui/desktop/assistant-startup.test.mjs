import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';

// Only dependency-injected production functions are evaluated. No Electron,
// server, native pipe, user profile, credential store, or model is started.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const read = rel => fs.readFileSync(path.join(root, rel), 'utf8');
const startup = await import(pathToFileURL(path.join(root, 'apps/web/src/startup.js')));
const memoryStorage = () => {
  const data = new Map();
  return { getItem: key => data.get(key) ?? null, setItem: (key, value) => data.set(key, value), data };
};
const deferred = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return { promise, resolve, reject }; };
const flush = async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); };
const ready = { ok: true, status: 'ready', scope: 'DEVELOPMENT_ONLY', database: 'sqlite' };

test('fresh dark keeps explicit saved light and unavailable preference storage never blocks startup', () => {
  const storage = memoryStorage();
  assert.equal(startup.readTheme(storage), 'dark');
  startup.saveTheme('light', storage); assert.equal(startup.readTheme(storage), 'light');
  startup.saveTheme('dark', storage); assert.equal(startup.readTheme(storage), 'dark');
  storage.setItem('researchos.theme', 'unexpected'); assert.equal(startup.readTheme(storage), 'dark');
  const denied = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
  assert.equal(startup.readTheme(denied), 'dark'); assert.doesNotThrow(() => startup.saveTheme('light', denied));
});

test('recent rows use only accessible real projects, bounded actual opens, and no private content', () => {
  const storage = memoryStorage();
  for (let i = 0; i < 30; i++) startup.rememberProject('p' + i, storage, i);
  startup.rememberProject('p28', storage, 31);
  const recent = startup.readRecentProjects(storage);
  assert.equal(recent.length, 24); assert.equal(recent[0].project_id, 'p28');
  assert.deepEqual(Object.keys(recent[0]).sort(), ['opened_at', 'project_id']);
  const p28 = { project_id: 'p28', name: 'actual' }, p29 = { project_id: 'p29', name: 'second' }, untouched = { project_id: 'never-opened' };
  assert.deepEqual(startup.projectGroups([p29, p28, untouched, p28], recent), { recent: [p28, p29], other: [untouched] });
  assert.deepEqual(startup.projectGroups([], recent), { recent: [], other: [] });
  storage.setItem('researchos.recent-projects.v1', '{broken'); assert.deepEqual(startup.readRecentProjects(storage), []);
  storage.setItem('researchos.recent-projects.v1', JSON.stringify([{ project_id: 'p', opened_at: -1 }, { project_id: 'p', opened_at: 1 }, { project_id: 'p', opened_at: 2 }]));
  assert.deepEqual(startup.readRecentProjects(storage), [{ project_id: 'p', opened_at: 1 }]);
});

test('health needs all actual healthz fields; a bridge, HTTP ok, or project event flag is no proof', async t => {
  assert.equal(startup.healthFromReply(ready).state, 'ready');
  for (const [name, reply] of Object.entries({ absent: null, bridge: {}, okOnly: { ok: true }, unavailable: { ...ready, status: 'unavailable' }, falseOk: { ...ready, ok: false }, stringOk: { ...ready, ok: 'true' }, wrongScope: { ...ready, scope: 'PRODUCTION' }, wrongDatabase: { ...ready, database: 'other' }, eventOnline: { online: true } })) {
    await t.test(name, () => assert.notEqual(startup.healthFromReply(reply).state, 'ready'));
  }
});

test('bounded health monitor times out, rejects late success, recovers, and ignores results after disposal', async () => {
  let nextId = 0; const timers = new Map(), values = [], requests = [];
  const schedule = (fn, ms) => { const id = ++nextId; timers.set(id, { fn, ms }); return id; };
  const cancel = id => timers.delete(id);
  const fire = ms => { const entry = [...timers].find(([, timer]) => timer.ms === ms); assert.ok(entry, 'expected pending timer'); timers.delete(entry[0]); entry[1].fn(); };
  const stop = startup.startHostHealthMonitor({ read: () => { const d = deferred(); requests.push(d); return d.promise; }, onChange: value => values.push(value), schedule, cancel, timeoutMs: 5, intervalMs: 15 });
  await flush(); assert.equal(requests.length, 1); assert.equal(values.at(-1).state, 'checking');
  fire(5); assert.equal(values.at(-1).state, 'unavailable');
  requests[0].resolve(ready); await flush(); assert.equal(values.at(-1).state, 'unavailable');
  fire(15); await flush(); assert.equal(requests.length, 2);
  requests[1].resolve(ready); await flush(); assert.equal(values.at(-1).state, 'ready');
  fire(15); await flush(); const before = values.length;
  stop(); assert.equal(timers.size, 0); requests[2].resolve(ready); await flush(); assert.equal(values.length, before);
});

test('health bridge exception is unavailable and retains the bounded next check', async () => {
  const values = [], timers = new Map(); let id = 0;
  const stop = startup.startHostHealthMonitor({ read: () => { throw new Error('synthetic bridge failure'); }, onChange: value => values.push(value), schedule: (fn, ms) => { timers.set(++id, { fn, ms }); return id; }, cancel: key => timers.delete(key) });
  await flush(); assert.equal(values.at(-1).state, 'unavailable'); assert.equal(timers.size, 1); stop(); assert.equal(timers.size, 0);
});

test('actual directory handler accepts real registration without model configuration and rejects incomplete authority', async () => {
  const source = read('apps/web/src/workbench.jsx');
  const begin = source.indexOf('  async function choose() {', source.indexOf('export function NativeProjectEntry('));
  const end = source.indexOf('\n  return <', begin); assert.ok(begin >= 0 && end > begin);
  for (const [name, reply, accepts] of [
    ['registered', { ok: true, result: { project_id: 'p/real', workspace: { authorized_workspace_ref: 'opaque-real', display_path: 'synthetic-only' } } }, true],
    ['no-workspace', { ok: true, result: { project_id: 'p' } }, false],
    ['no-project', { ok: true, result: { workspace: { authorized_workspace_ref: 'opaque' } } }, false],
    ['cancelled', { ok: false, reason: 'PICKER_CANCELLED' }, false],
  ]) {
    const calls = []; let result, error, busy, refresh = 0;
    const context = { name: '  actual name  ', workspaceProjectPath: startup.workspaceProjectPath,
      setBusy: value => { busy = value; }, setError: value => { error = value; }, setResult: value => { result = value; }, onRefresh: () => refresh++,
      window: { researchos: { desktop: { chooseWorkspace: async body => { calls.push(body); return reply; } } } } };
    await vm.runInNewContext(source.slice(begin, end) + '\nchoose();', context);
    assert.equal(busy, false, name); assert.equal(!!result, accepts, name); assert.equal(!!error, !accepts, name); assert.equal(refresh, accepts ? 1 : 0);
    assert.equal(JSON.stringify(calls), '[{"display_name":"actual name"}]');
    if (accepts) assert.equal(startup.workspaceProjectPath(result), '/p/p%2Freal');
  }
  const entry = source.slice(source.indexOf('export function NativeProjectEntry('), source.indexOf('export function DesktopQualification('));
  assert.match(entry, />打开工作台 /); assert.doesNotMatch(entry, /配置模型并打开|provider_id|model_config_ref|probe\(/);
});

test('landing uses real project data, one real directory action, and keeps health separate from project write barriers', () => {
  const main = read('apps/web/src/main.jsx'), shell = read('apps/web/src/components/app-shell.jsx'), screens = read('apps/web/src/screens.jsx');
  assert.match(main, /read: \(\) => window\.researchos\.statusHealth\(\{\}\)/);
  assert.match(main, /if \(projectId && !events\.online && events\.lastSync\)/);
  assert.match(main, /if \(projectId && profile\) rememberProject\(projectId\)/);
  assert.match(shell, /connection\.state === 'ready'/);
  assert.match(shell, /\{projectId && !events\.online &&/);
  assert.doesNotMatch(shell, /window\.researchos|localStorage|\.statusHealth\(/);
  const landing = screens.slice(screens.indexOf('  if (window.researchos?.desktop) {', screens.indexOf('function Projects(')), screens.indexOf('  return <><Header title="项目入口"'));
  assert.match(landing, /projectGroups\(projects, readRecentProjects\(\)\)/); assert.match(landing, /<NativeProjectEntry/);
  assert.doesNotMatch(landing, /<textarea|contentEditable|fake|DEMO_PROJECTS/);
});

const require = createRequire(import.meta.url);
const lib = path.join(root, 'apps/desktop/main/lib');
const ipc = require(path.join(lib, 'ipc.js')), host = require(path.join(lib, 'host.js')), native = require(path.join(lib, 'native.js'));
const mainSource = read('apps/desktop/main/main.js');
const stateBegin = mainSource.indexOf('const selectedState = {'), stateEnd = mainSource.indexOf('const qualificationContext = ', stateBegin);
const pureBegin = mainSource.indexOf('function ownedCoreIdentity('), pureEnd = mainSource.indexOf('\nconst deps = {', pureBegin);
const { smokeNativeProbe } = Function('ipc', mainSource.slice(pureBegin, pureEnd) + '\nreturn {smokeNativeProbe};')(ipc);
const newState = () => vm.runInNewContext(mainSource.slice(stateBegin, stateEnd) + '\nsessionState;', { process: { env: {} } });

test('actual Main private smoke read and renderer display coexist while all original stale boundaries remain', async t => {
  const originals = { ensureCore: host.ensureCore, readDiscovery: host.readDiscovery, hostInstanceId: native.hostInstanceId };
  let current;
  const discovery = { url: 'http://fixture.invalid:1', pid: 1, data_dir: 'SYNTHETIC_NOT_OPENED', host_instance_id: 'host-0123456789ab' };
  host.ensureCore = async () => ({ discovery, health: 'UP' });
  host.readDiscovery = () => ({ ok: true, discovery: current });
  native.hostInstanceId = (_fs, value) => value.host_instance_id;
  const fixture = () => {
    current = discovery; const state = newState(), requests = []; let count = 0;
    return { state, requests, deps: { sessionState: state, fsImpl: {}, discoveryFile: 'NEVER_READ', clientId: 'desktop-shell',
      credentialFor: async () => 'SYNTHETIC_NOT_A_CREDENTIAL', commandIdFor: () => 'fixture-' + (++count),
      v2Transport: async () => { const d = deferred(); requests.push(d); return d.promise; } },
      reply: { validated: true, ok: true, body: { status: 'COMPLETED', result: { projects: [], workspaces: [], model_configurations: [] }, revision: null } } };
  };
  const wait = async (f, n) => { for (let i = 0; i < 100 && f.requests.length < n; i++) await new Promise(resolve => setImmediate(resolve)); assert.equal(f.requests.length, n); };
  try {
    for (const order of [[0, 1], [1, 0]]) await t.test('display and private probe complete in order ' + order, async () => {
      const f = fixture(); const promises = [ipc.callV2(f.deps, 'host.status', {}), smokeNativeProbe(f.deps)]; await wait(f, 2);
      for (const i of order) { f.requests[i].resolve(f.reply); await flush(); }
      const results = await Promise.all(promises); assert.equal(results[0].completed, true); assert.equal(results[1].ok, true); assert.equal(results[1].protocol_status, 'COMPLETED');
    });
    await t.test('ordinary display ticket still rejects an older result', async () => {
      const f = fixture(); const a = ipc.callV2(f.deps, 'host.status', {}), b = ipc.callV2(f.deps, 'host.status', {}); await wait(f, 2);
      f.requests.forEach(d => d.resolve(f.reply)); assert.equal((await a).reason, 'STALE_RESPONSE'); assert.equal((await b).completed, true);
    });
    await t.test('renderer string cannot select the private Symbol lane', async () => {
      const f = fixture(); const a = ipc.callV2(f.deps, 'host.status', {}, 'AUTHORITY_READ'), b = ipc.callV2(f.deps, 'host.status', {}); await wait(f, 2);
      f.requests.forEach(d => d.resolve(f.reply)); assert.equal((await a).reason, 'STALE_RESPONSE'); assert.equal((await b).completed, true);
    });
    for (const key of ['projectId', 'sessionId', 'writerEpoch', 'expectedRevision', 'writerClientId', 'writerExpiresAt']) await t.test('private read rejects ' + key + ' ABA', async () => {
      const f = fixture(); const p = smokeNativeProbe(f.deps); await wait(f, 1);
      const old = f.state[key]; f.state[key] = key === 'writerEpoch' || key === 'expectedRevision' ? 1 : 'changed'; f.state[key] = old;
      f.requests[0].resolve(f.reply); assert.equal((await p).reason, 'STALE_RESPONSE');
    });
    await t.test('private read rejects changed native host', async () => {
      const f = fixture(); const p = smokeNativeProbe(f.deps); await wait(f, 1); current = { ...discovery, host_instance_id: 'host-aaaaaaaaaaaa' };
      f.requests[0].resolve(f.reply); assert.equal((await p).reason, 'HOST_CHANGED_DURING_STATUS');
    });
    for (const scenario of ['entry-barrier', 'late-barrier', 'write-sequence']) await t.test('private read preserves ' + scenario, async () => {
      const f = fixture();
      if (scenario === 'entry-barrier') ipc.callV2.lifetimes.set(f.state, new Map([['held', { activity: true }]]));
      const p = smokeNativeProbe(f.deps);
      if (scenario === 'entry-barrier') { assert.equal((await p).reason, 'STALE_RESPONSE'); assert.equal(f.requests.length, 0); return; }
      await wait(f, 1);
      if (scenario === 'late-barrier') ipc.callV2.lifetimes.get(f.state).set('held', { acknowledged: true });
      else ipc.callV2.writeSequences.set(f.state, (ipc.callV2.writeSequences.get(f.state) || 0) + 1);
      f.requests[0].resolve(f.reply); assert.equal((await p).reason, 'STALE_RESPONSE');
    });
  } finally { host.ensureCore = originals.ensureCore; host.readDiscovery = originals.readDiscovery; native.hostInstanceId = originals.hostInstanceId; }
  assert.match(mainSource, /\? await smokeNativeProbe\(v2Deps\)/);
  assert.doesNotMatch(mainSource, /executeJavaScript\(`window\.researchos\.v2\['host\.status'\]/);
});

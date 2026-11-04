import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { EventEmitter } from 'node:events';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { buildChildEnv, executeDevelopmentLaunch, prepareDevelopmentLaunch,
  validateBundle, validateSmokeReports } from '../../../apps/desktop/launch-development.mjs';

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fixtureRoot = () => fs.mkdtempSync(path.join(os.tmpdir(), 'ros-desktop-development-mock-'));
function removeFixture(root) {
  const resolved = path.resolve(root), temp = path.resolve(os.tmpdir());
  assert.ok(resolved.startsWith(temp + path.sep) && path.basename(resolved).startsWith('ros-desktop-development-mock-'));
  fs.rmSync(resolved, { recursive: true, force: true });
}
function write(root, relative, content) {
  const target = path.join(root, relative);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content);
}
function fixture(root) {
  const bundle = path.join(root, 'bundle'); fs.mkdirSync(bundle);
  const files = [
    'apps/desktop/main/main.js', 'apps/desktop/preload/preload.js',
    'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe',
    'apps/desktop/resources/control/researchos-control.exe',
    'apps/desktop/resources/control/runtime-verifier.exe',
    'apps/desktop/resources/control/runtime/mu-worker.mjs',
    'apps/desktop/resources/control/runtime/node.exe',
    'apps/web/dist/index.html', 'apps/web/dist/assets/index.js', 'apps/web/dist/assets/index.css',
    'runtime/electron/electron.exe', 'spec/v2.0/contracts/domain.schema.json',
    'spec/v2.0/contracts/openapi.json', 'internal/api/contracts/client.protocol.schema.json',
    'internal/api/contracts/domain.schema.json', 'migrations/sqlite/0001_bootstrap.sql',
    'migrations/sqlite/0002_domain.sql', 'migrations/sqlite/next_v24_sessions.sql',
  ];
  for (const name of files) write(bundle, name, name.endsWith('.exe') ? Buffer.from('MZ-mock') : Buffer.from(name));
  const verifier = path.join(bundle, 'apps/desktop/resources/control/runtime-verifier.exe');
  write(bundle, 'apps/desktop/resources/control/runtime-verifier-installation.json', JSON.stringify({
    schema: 'researchos.runtime-verifier-installation.v1', service_id: 'researchos.runtime-qualification-verifier.v1',
    protocol: 'researchos.runtime-verifier/1', executable: verifier,
    executable_hash: 'sha256:' + sha(fs.readFileSync(verifier)), source_commit: 'a'.repeat(40), arguments: [],
  }));
  const mu = path.join(bundle, 'apps/desktop/resources/control/runtime/mu-worker.mjs');
  write(bundle, 'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json', JSON.stringify({
    mu_commit: '8dfebe36508ac0c2508735bb866756dab9283e74', vendored_files_verified: 5083,
    bundle_sha256: sha(fs.readFileSync(mu)), bundle_bytes: fs.statSync(mu).size,
  }));
  write(bundle, 'apps/desktop/resources/client-wire/descriptor.json', JSON.stringify({
    build_input_digest: 'b'.repeat(64),
    binary_sha256: sha(fs.readFileSync(path.join(bundle, 'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe'))),
  }));
  const inventory = [];
  function walk(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(target);
      else inventory.push({ path: path.relative(bundle, target).split(path.sep).join('/'),
        sha256: sha(fs.readFileSync(target)), bytes: fs.statSync(target).size });
    }
  }
  walk(bundle); inventory.sort((a, b) => a.path.localeCompare(b.path, 'en'));
  // The runtime contract sorts by UTF-16 codepoint order, which these ASCII
  // fixture paths share with ordinary JavaScript lexical order.
  inventory.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  write(bundle, 'development-manifest.json', JSON.stringify({
    schema: 'researchos.desktop-development-tree/1', mode: 'DEVELOPMENT_ONLY_BUILT_NOT_NATIVE_TESTED',
    bundle_root: bundle, client_wire: { build_input_digest: 'b'.repeat(64) }, files: inventory,
  }));
  return { bundle, state: path.join(root, 'fresh-state') };
}

test('mock complete tree dry-run validates every hash and does not create state or spawn', async () => {
  const root = fixtureRoot();
  try {
    const { bundle, state } = fixture(root);
    const ambient = { SystemRoot: process.env.SystemRoot || 'C:\\Windows',
      node_options: '--require evil', researchos_project_id: 'foreign', ROS_DESKTOP_LEGACY_WORKBENCH: '1' };
    let spawns = 0;
    const result = await executeDevelopmentLaunch({ bundle, state, ambient, dryRun: true, smoke: true },
      () => { spawns++; throw Error('must not spawn'); });
    assert.equal(result.mode, 'DRY_RUN_NO_STATE_NO_SPAWN');
    assert.equal(spawns, 0);
    assert.equal(fs.existsSync(state), false);
    const prepared = prepareDevelopmentLaunch({ bundle, state, ambient, smoke: true });
    assert.equal(prepared.env.ROS_DESKTOP_SMOKE, '1');
    assert.equal(prepared.env.ROS_DESKTOP_NATIVE_SMOKE, '1');
    assert.equal(prepared.env.RESEARCHOS_DATA_DIR, path.join(state, 'data'));
    assert.equal(prepared.env.RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED, '1');
    assert.equal(prepared.env.node_options, undefined);
    assert.equal(prepared.env.researchos_project_id, undefined);
    assert.equal(prepared.env.ROS_DESKTOP_LEGACY_WORKBENCH, undefined);
    assert.deepEqual(prepared.argv, [path.join(bundle, 'apps/desktop')]);
  } finally { removeFixture(root); }
});

test('mock launcher rejects changed, missing, alias and pre-existing state before spawn', async t => {
  const root = fixtureRoot();
  try {
    const { bundle, state } = fixture(root);
    const options = { bundle, state, ambient: { SystemRoot: process.env.SystemRoot || 'C:\\Windows' }, dryRun: true };
    fs.mkdirSync(state);
    assert.throws(() => prepareDevelopmentLaunch(options), /STATE_NOT_FRESH/);
    fs.rmdirSync(state);
    const target = path.join(bundle, 'apps/web/dist/index.html');
    fs.appendFileSync(target, 'tamper');
    assert.throws(() => validateBundle(bundle), /BUNDLE_FILE_CHANGED/);
    fs.writeFileSync(target, 'apps/web/dist/index.html');
    const control = path.join(bundle, 'apps/desktop/resources/control/researchos-control.exe');
    fs.unlinkSync(control);
    assert.throws(() => validateBundle(bundle), /PATH_UNAVAILABLE|BUNDLE_RESOURCE_MISSING/);
    write(bundle, 'apps/desktop/resources/control/researchos-control.exe', Buffer.from('MZ-mock'));
    const alias = path.join(root, 'state-alias');
    try {
      fs.symlinkSync(bundle, alias, 'junction');
      assert.throws(() => prepareDevelopmentLaunch({ ...options, state: path.join(alias, 'new-state') }), /PATH_ALIAS_REFUSED/);
    } catch (error) {
      if (error.code !== 'EPERM' && error.code !== 'EACCES') throw error;
      t.diagnostic('Windows did not allow this junction fixture');
    }
  } finally { removeFixture(root); }
});

test('Windows env case collisions and lowercase injection cannot become child variables', () => {
  const root = fixtureRoot();
  try {
    const { bundle, state } = fixture(root);
    assert.throws(() => buildChildEnv({ SystemRoot: 'C:\\Windows', systemroot: 'C:\\Windows' }, bundle, state), /ENV_CASE_COLLISION/);
    assert.throws(() => buildChildEnv({ SystemRoot: 'C:\\Windows', NODE_OPTIONS: 'x', node_options: 'y' }, bundle, state), /ENV_CASE_COLLISION/);
    const env = buildChildEnv({ SystemRoot: 'C:\\Windows', node_options: 'x', researchos_data_dir: 'foreign',
      ros_desktop_smoke: '0', ELECTRON_RUN_AS_NODE: '1', RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED: '0' }, bundle, state, true);
    assert.equal(env.NODE_OPTIONS, undefined);
    assert.equal(env.ELECTRON_RUN_AS_NODE, undefined);
    assert.equal(env.RESEARCHOS_DATA_DIR, path.join(state, 'data'));
    assert.equal(env.ROS_DESKTOP_SMOKE, '1');
    assert.equal(env.RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED, '1');
  } finally { removeFixture(root); }
});

test('mock launch creates only a fresh state and report verifier demands same owned exit', async () => {
  const root = fixtureRoot();
  try {
    const { bundle, state } = fixture(root);
    const owned = { pid: 121, created_ns: '1792057406096619100', image_sha256: 'a'.repeat(64), host_id: 'host-aaaaaaaaaaaa' };
    const ready = { event: 'ready_to_show', management_state: 'READY', host_health: 'UP',
      native_probe: { ok: true }, renderer: { bridge: true, react_root: true, mounted_title: '研究工作台', navigation: 3 },
      owned_core_identity: owned };
    const stopped = { event: 'shutdown_confirmed', process_exit_confirmed: true, owned_core_identity: owned };
    assert.deepEqual(validateSmokeReports([ready, stopped], 0), { status: 'NATIVE_SMOKE_CONFIRMED', owned_core_identity: owned, renderer_title: '研究工作台' });
    assert.throws(() => validateSmokeReports([ready, { ...stopped, owned_core_identity: { ...owned, created_ns: '1' } }], 0), /SMOKE_OUTCOME_UNCONFIRMED/);
    assert.throws(() => validateSmokeReports([{ ...ready, native_probe: null }, stopped], 0), /SMOKE_OUTCOME_UNCONFIRMED/);
    assert.throws(() => validateSmokeReports([ready, stopped], 2), /SMOKE_OUTCOME_UNCONFIRMED/);
    let observed;
    const mockSpawn = (exe, argv, opts) => {
      observed = { exe, argv, opts };
      const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
      process.nextTick(() => {
        const transcript = Buffer.from('ROS_DESKTOP_REPORT ' + JSON.stringify(ready) + '\n' +
          'ROS_DESKTOP_REPORT ' + JSON.stringify(stopped) + '\n');
        const chinese = transcript.indexOf(Buffer.from('研'));
        assert.ok(chinese >= 0);
        child.stdout.emit('data', transcript.subarray(0, chinese + 1));
        child.stdout.emit('data', transcript.subarray(chinese + 1));
        child.emit('close', 0, null);
      });
      return child;
    };
    const result = await executeDevelopmentLaunch({ bundle, state, ambient: { SystemRoot: process.env.SystemRoot || 'C:\\Windows' }, smoke: true }, mockSpawn);
    assert.equal(result.status, 'NATIVE_SMOKE_CONFIRMED');
    assert.equal(result.renderer_title, '研究工作台');
    assert.ok(fs.statSync(path.join(state, 'data')).isDirectory());
    assert.equal(observed.exe, path.join(bundle, 'runtime/electron/electron.exe'));
    assert.equal(observed.opts.env.RESEARCHOS_CLI_DISCOVERY, path.join(state, 'discovery.json'));
    const spawnWith = bytes => () => {
      const child = new EventEmitter(); child.stdout = new EventEmitter(); child.stderr = new EventEmitter();
      process.nextTick(() => { child.stdout.emit('data', bytes); child.emit('close', 0, null); });
      return child;
    };
    const readyLine = 'ROS_DESKTOP_REPORT ' + JSON.stringify(ready) + '\n';
    const stoppedLine = 'ROS_DESKTOP_REPORT ' + JSON.stringify(stopped);
    await assert.rejects(executeDevelopmentLaunch({ bundle, state: path.join(root, 'no-newline-state'),
      ambient: { SystemRoot: process.env.SystemRoot || 'C:\\Windows' }, smoke: true },
      spawnWith(Buffer.from(readyLine + stoppedLine))), /SMOKE_REPORT_TRAILING_FRAGMENT/);
    await assert.rejects(executeDevelopmentLaunch({ bundle, state: path.join(root, 'incomplete-utf8-state'),
      ambient: { SystemRoot: process.env.SystemRoot || 'C:\\Windows' }, smoke: true },
      spawnWith(Buffer.concat([Buffer.from(readyLine + stoppedLine + '\n'), Buffer.from([0xe7])]))),
      /SMOKE_REPORT_TRAILING_FRAGMENT/);
  } finally { removeFixture(root); }
});

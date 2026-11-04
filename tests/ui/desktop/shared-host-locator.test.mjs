import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { publishOwnedHostLocator, readLocator } = require('../../../apps/desktop/main/lib/shared-host-locator.js');
const vectors = JSON.parse(fs.readFileSync(new URL('./fixtures/shared-host-locator.json', import.meta.url), 'utf8'));

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-shared-host-fixture-'));
  t.after(() => {
    assert.ok(path.resolve(root).startsWith(path.resolve(os.tmpdir()) + path.sep));
    assert.ok(path.basename(root).startsWith('ros-shared-host-fixture-'));
    fs.rmSync(root, { recursive: true, force: true });
  });
  const dataRoot = path.join(root, 'Desktop 数据'); fs.mkdirSync(dataRoot);
  const local = path.join(root, 'AppData'); fs.mkdirSync(local);
  const discoveryFile = path.join(root, 'discovery.json');
  const d = { url: vectors.url, pid: 123, data_dir: dataRoot, host_instance_id: vectors.host_id };
  fs.writeFileSync(discoveryFile, JSON.stringify(d));
  const manager = { state: 'READY', hostId: vectors.host_id, options: { discoveryFile, dataRoot }, currentHost: () => ({ ...d }) };
  const options = { management: manager, discoveryFile, dataRoot, env: { LOCALAPPDATA: local } };
  const file = path.join(local, 'ResearchOS', 'host-locator-v1.json');
  const record = { schema: vectors.schema, discovery_file: discoveryFile, data_root: dataRoot, host_instance_id: vectors.host_id };
  return { root, d, file, record, options, manager };
}

test('owned READY publishes only a complete non-secret locator and is idempotent', t => {
  const f = fixture(t);
  assert.equal(publishOwnedHostLocator(f.options).status, 'PUBLISHED');
  assert.deepEqual({ ...readLocator(fs, f.file) }, f.record);
  const before = fs.readFileSync(f.file);
  assert.equal(publishOwnedHostLocator(f.options).status, 'UNCHANGED');
  assert.deepEqual(fs.readFileSync(f.file), before);
  assert.deepEqual(fs.readdirSync(path.dirname(f.file)), ['host-locator-v1.json']);
});

test('global conflict and invalid existing record are preserved byte for byte', t => {
  const f = fixture(t);
  publishOwnedHostLocator(f.options);
  for (const content of [JSON.stringify({ ...f.record, host_instance_id: 'host-bbbbbbbbbbbb' }), '{']) {
    fs.writeFileSync(f.file, content);
    assert.throws(() => publishOwnedHostLocator(f.options), /HOST_LOCATOR_CONFLICT/);
    assert.equal(fs.readFileSync(f.file, 'utf8'), content);
  }
});

test('two languages share schema and tamper vectors; no hint grants authorization', async t => {
  for (const vector of vectors.invalid) await t.test(vector.name, t => {
    const f = fixture(t);
    if (vector.target === 'discovery') {
      fs.writeFileSync(f.options.discoveryFile, JSON.stringify({ ...f.d, [vector.field]: vector.value }));
      assert.throws(() => publishOwnedHostLocator(f.options));
      assert.equal(fs.existsSync(f.file), false);
    } else {
      fs.mkdirSync(path.dirname(f.file));
      const contents = JSON.stringify({ ...f.record, [vector.field]: vector.value });
      fs.writeFileSync(f.file, contents);
      assert.throws(() => publishOwnedHostLocator(f.options), /HOST_LOCATOR_CONFLICT/);
      assert.equal(fs.readFileSync(f.file, 'utf8'), contents);
    }
  });
});

test('private ownership and identity verification are mandatory before any global write', t => {
  const f = fixture(t);
  f.manager.state = 'BROKEN';
  assert.throws(() => publishOwnedHostLocator(f.options), /OWNED_READY_REQUIRED/);
  f.manager.state = 'READY'; f.manager.currentHost = () => { throw Error('CONTROL_PROCESS_CHANGED'); };
  assert.throws(() => publishOwnedHostLocator(f.options), /CONTROL_PROCESS_CHANGED/);
  assert.equal(fs.existsSync(f.file), false);
  assert.equal(fs.existsSync(path.dirname(f.file)), false);
});

test('development disable performs no file operations, even when global environment is invalid', () => {
  const noFS = new Proxy({}, { get() { throw Error('must not touch any filesystem'); } });
  assert.deepEqual(publishOwnedHostLocator({ fsImpl: noFS,
    env: { LOCALAPPDATA: 'not-a-real-user-root', RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED: '1' } }), { status: 'DISABLED' });
});

test('exclusive publication handles a competing writer without replacement or leftovers', t => {
  const f = fixture(t);
  const racingFS = Object.create(fs);
  racingFS.linkSync = (_temporary, file) => {
    fs.writeFileSync(file, JSON.stringify({ ...f.record, host_instance_id: 'host-cccccccccccc' }), { flag: 'wx' });
    throw Object.assign(Error('race'), { code: 'EEXIST' });
  };
  assert.throws(() => publishOwnedHostLocator({ ...f.options, fsImpl: racingFS }), /HOST_LOCATOR_CONFLICT/);
  assert.equal(JSON.parse(fs.readFileSync(f.file)).host_instance_id, 'host-cccccccccccc');
  assert.deepEqual(fs.readdirSync(path.dirname(f.file)), ['host-locator-v1.json']);
});

test('global directory aliases cannot redirect publication', t => {
  const f = fixture(t);
  const elsewhere = path.join(f.root, 'elsewhere'); fs.mkdirSync(elsewhere);
  fs.symlinkSync(elsewhere, path.dirname(f.file), 'junction');
  assert.throws(() => publishOwnedHostLocator(f.options), /HOST_LOCATOR_PATH_ALIAS/);
  assert.deepEqual(fs.readdirSync(elsewhere), []);
});

test('duplicate locator and discovery fields fail before publication', t => {
  const f = fixture(t);
  fs.mkdirSync(path.dirname(f.file));
  const duplicated = '{"schema":"foreign/1",' + JSON.stringify(f.record).slice(1);
  fs.writeFileSync(f.file, duplicated);
  assert.throws(() => publishOwnedHostLocator(f.options), /HOST_LOCATOR_CONFLICT/);
  assert.equal(fs.readFileSync(f.file, 'utf8'), duplicated);
  fs.unlinkSync(f.file);
  fs.writeFileSync(f.options.discoveryFile, '{"url":"http://127.0.0.1:54321/",' + JSON.stringify(f.d).slice(1));
  assert.throws(() => publishOwnedHostLocator(f.options));
  assert.equal(fs.existsSync(f.file), false);
});

test('a changed private identity during publication cannot create a locator', t => {
  const f = fixture(t);
  let calls = 0;
  f.manager.currentHost = () => {
    if (++calls === 2) throw Error('CONTROL_PROCESS_CHANGED');
    return { ...f.d };
  };
  assert.throws(() => publishOwnedHostLocator(f.options), /CONTROL_PROCESS_CHANGED/);
  assert.equal(fs.existsSync(path.dirname(f.file)), false);
});

test('copied discovery cannot change the private manager-bound location', t => {
  const f = fixture(t);
  const copied = path.join(f.root, 'copied-discovery.json');
  fs.copyFileSync(f.options.discoveryFile, copied);
  assert.throws(() => publishOwnedHostLocator({ ...f.options, discoveryFile: copied }), /IDENTITY_MISMATCH/);
  assert.equal(fs.existsSync(path.dirname(f.file)), false);
});

test('different existing data root or discovery path is never overwritten', t => {
  const f = fixture(t);
  const otherRoot = path.join(f.root, 'old-data'); fs.mkdirSync(otherRoot);
  const otherDiscovery = path.join(f.root, 'old-discovery.json');
  fs.copyFileSync(f.options.discoveryFile, otherDiscovery);
  fs.mkdirSync(path.dirname(f.file));
  for (const old of [{ ...f.record, data_root: otherRoot }, { ...f.record, discovery_file: otherDiscovery }]) {
    const bytes = JSON.stringify(old);
    fs.writeFileSync(f.file, bytes);
    assert.throws(() => publishOwnedHostLocator(f.options), /HOST_LOCATOR_CONFLICT/);
    assert.equal(fs.readFileSync(f.file, 'utf8'), bytes);
  }
});

test('normal same-root same-SID restart changes URL and PID without replacing the stable locator', t => {
  const f = fixture(t);
  publishOwnedHostLocator(f.options);
  const before = fs.readFileSync(f.file);
  // Core derives Host ID from host directory and stable SID reference, not PID/URL.
  f.d.pid = 456; f.d.url = 'http://127.0.0.1:54322/';
  fs.writeFileSync(f.options.discoveryFile, JSON.stringify(f.d));
  assert.equal(publishOwnedHostLocator(f.options).status, 'UNCHANGED');
  assert.deepEqual(fs.readFileSync(f.file), before);
});

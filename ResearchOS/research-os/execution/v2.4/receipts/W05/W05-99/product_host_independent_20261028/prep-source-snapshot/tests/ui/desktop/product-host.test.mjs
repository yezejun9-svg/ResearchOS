import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import test from 'node:test';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const product = require('../../../apps/desktop/main/lib/product-layout.js');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');

function fixture(t) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'researchos-product-js-'));
  t.after(() => fs.rmSync(home, { recursive: true, force: true }));
  const previous = process.env.LOCALAPPDATA;
  process.env.LOCALAPPDATA = path.join(home, 'local');
  fs.mkdirSync(process.env.LOCALAPPDATA);
  t.after(() => { if (previous === undefined) delete process.env.LOCALAPPDATA;
    else process.env.LOCALAPPDATA = previous; });
  const root = path.join(home, 'product');
  fs.mkdirSync(root);
  const files = [];
  for (let i = 0; i < 101; i++) {
    const rel = `content/file-${i}.txt`;
    const bytes = Buffer.from(`fixture ${i}\n`);
    const full = path.join(root, rel);
    fs.mkdirSync(path.dirname(full), { recursive: true });
    fs.writeFileSync(full, bytes);
    files.push({ path: rel, bytes: bytes.length, sha256: hash(bytes) });
  }
  const binaries = Object.fromEntries(['cli', 'control', 'electron', 'verifier', 'validator']
    .map((key, i) => [key, { path: files[i].path, sha256: files[i].sha256 }]));
  files.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  const marker = { schema: product.SCHEMA, mode: 'OWNED_PRODUCT_LAYOUT_NOT_INSTALLER',
    install_root: root, source_commit: 'a'.repeat(40), source_digest: 'b'.repeat(64),
    inventory_digest: product.inventoryIdentity(files), product_version: '2.4.0',
    client_protocol: 'researchos-client/2', schema_version: 24, binaries, files };
  marker.installation_id = product.installationIdentity(marker);
  fs.writeFileSync(path.join(root, 'installed-product.json'), JSON.stringify(marker));
  return { root, marker, home };
}

test('location-bound inventory and installation identity fail closed', t => {
  const f = fixture(t);
  const layout = product.loadProductLayout(f.root);
  assert.equal(layout.installID, f.marker.installation_id);
  fs.writeFileSync(path.join(f.root, f.marker.files[12].path), 'changed');
  assert.throws(() => product.loadProductLayout(f.root), /PRODUCT_FILE_CHANGED/);
  fs.writeFileSync(path.join(f.root, f.marker.files[12].path), 'fixture 12\n');
  f.marker.installation_id = '0'.repeat(64);
  fs.writeFileSync(path.join(f.root, 'installed-product.json'), JSON.stringify(f.marker));
  assert.throws(() => product.loadProductLayout(f.root), /PRODUCT_MANIFEST_INVALID/);
});

test('duplicate intent is installation-bound; busy close retains host and confirmed stop exits', async () => {
  const id = 'a'.repeat(64);
  assert.equal(product.acceptProductIntent(id, { installation_id: id, intent: 'show-ui' }), 'show-ui');
  assert.equal(product.acceptProductIntent(id, { installation_id: 'b'.repeat(64), intent: 'show-ui' }), null);
  assert.equal(product.acceptProductIntent(id, { installation_id: id, intent: 'pause' }), null);
  let shutdownCalls = 0, exits = 0, refusals = 0;
  const management = { shutdown: async () => { shutdownCalls++; if (shutdownCalls === 1)
    throw Object.assign(new Error('SHUTDOWN_REFUSED'), { code: 'SHUTDOWN_REFUSED' });
    return { state: 'STOPPED', process_exit_confirmed: true }; } };
  const safeExit = product.createProductSafeExit({ management,
    ownedIdentity: () => ({ pid: 5 }), confirm: result => result.process_exit_confirmed,
    retire: () => false, onExit: async retired => { assert.equal(retired, false); exits++; },
    onRefused: async error => { assert.equal(error.code, 'SHUTDOWN_REFUSED'); refusals++; } });
  await assert.rejects(safeExit(), /SHUTDOWN_REFUSED/);
  assert.equal(exits, 0); assert.equal(refusals, 1);
  await safeExit();
  assert.equal(exits, 1); assert.equal(shutdownCalls, 2);
});

test('data binding refuses another installation and witness retires only exact host', t => {
  const f = fixture(t);
  const layout = product.loadProductLayout(f.root);
  const parent = { PID: process.pid, CreatedNS: '124', ImageSHA256: 'b'.repeat(64) };
  const startup = product.writeStartupWitness(layout, parent);
  product.claimProductData(layout);
  const owner = { PID: 100, CreatedNS: '123', ImageSHA256: 'a'.repeat(64) };
  const management = { state: 'READY', identity: owner, parentIdentity: parent, hostId: 'host-123456789abc',
    currentHost: () => ({ data_dir: layout.dataRoot, pid: owner.PID }) };
  const witness = product.writeSupervisorWitness(layout, management, startup);
  assert.equal(witness.host_id, management.hostId);
  assert.equal(product.retireSupervisorWitness(layout, { ...witness, host_id: 'host-ffffffffffff' }), false);
  assert.equal(product.retireSupervisorWitness(layout, witness), true);
  assert.equal(fs.existsSync(layout.witness), false);
  const binding = JSON.parse(fs.readFileSync(layout.binding, 'utf8'));
  binding.installation_id = 'f'.repeat(64);
  fs.writeFileSync(layout.binding, JSON.stringify(binding));
  assert.throws(() => product.claimProductData(layout), /PRODUCT_DATA_INSTALLATION_CONFLICT/);
});

test('startup refuses unbound old data before writing its witness', t => {
  const f = fixture(t);
  const layout = product.loadProductLayout(f.root);
  fs.mkdirSync(layout.dataRoot, { recursive: true });
  fs.writeFileSync(path.join(layout.dataRoot, 'researchos.sqlite'), 'old');
  const parent = { PID: process.pid, CreatedNS: '124', ImageSHA256: 'b'.repeat(64) };
  assert.throws(() => product.writeStartupWitness(layout, parent), /PRODUCT_DATA_UNBOUND/);
  assert.equal(fs.existsSync(layout.witness), false);
});

test('existing redirected LocalAppData child is refused before data write', t => {
  const f = fixture(t);
  const layout = product.loadProductLayout(f.root);
  const elsewhere = path.join(f.home, 'elsewhere');
  fs.mkdirSync(elsewhere);
  try { fs.symlinkSync(elsewhere, path.dirname(layout.dataRoot), 'junction'); }
  catch (error) { if (['EPERM', 'EACCES'].includes(error.code)) return t.skip('junction unavailable'); throw error; }
  assert.throws(() => product.validateProductPaths(layout), /PRODUCT_PATH_REDIRECTED/);
  assert.equal(fs.readdirSync(elsewhere).length, 0);
});

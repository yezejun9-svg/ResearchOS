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
  const marker = { schema: product.SCHEMA, mode: 'OWNED_PRODUCT_LAYOUT_NOT_INSTALLER',
    install_root: root, source_commit: 'a'.repeat(40), product_version: '2.4.0',
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

test('data binding refuses another installation and witness retires only exact host', t => {
  const f = fixture(t);
  const layout = product.loadProductLayout(f.root);
  product.claimProductData(layout);
  const owner = { PID: 100, CreatedNS: '123', ImageSHA256: 'a'.repeat(64) };
  const parent = { PID: 101, CreatedNS: '124', ImageSHA256: 'b'.repeat(64) };
  const management = { state: 'READY', identity: owner, parentIdentity: parent, hostId: 'host-123456789abc',
    currentHost: () => ({ data_dir: layout.dataRoot, pid: owner.PID }) };
  const witness = product.writeSupervisorWitness(layout, management);
  assert.equal(witness.host_id, management.hostId);
  assert.equal(product.retireSupervisorWitness(layout, { ...witness, host_id: 'host-ffffffffffff' }), false);
  assert.equal(product.retireSupervisorWitness(layout, witness), true);
  assert.equal(fs.existsSync(layout.witness), false);
  const binding = JSON.parse(fs.readFileSync(layout.binding, 'utf8'));
  binding.installation_id = 'f'.repeat(64);
  fs.writeFileSync(layout.binding, JSON.stringify(binding));
  assert.throws(() => product.claimProductData(layout), /PRODUCT_DATA_INSTALLATION_CONFLICT/);
});

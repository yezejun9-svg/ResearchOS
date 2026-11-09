'use strict';
// Hermetic review of the captured mutable source. Never imports Electron or starts Core.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const product = require('./prep-source-snapshot/apps/desktop/main/lib/product-layout.js');
const base = fs.mkdtempSync(path.join(__dirname, 'fixture-'));
const priorLocal = process.env.LOCALAPPDATA;
const results = [];
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
function makeFixture(mixedCase) {
  const root = path.join(base, mixedCase ? 'mixed' : 'lower');
  fs.mkdirSync(root);
  const names = Array.from({length: 100}, (_, i) => `runtime/file-${i}.bin`);
  if (mixedCase) names.push('runtime/LICENSE');
  names.sort(); // Matches build-development.py inventory and the Go loader.
  const files = names.map(name => {
    const content = Buffer.from(name);
    const target = path.join(root, name);
    fs.mkdirSync(path.dirname(target), {recursive: true});
    fs.writeFileSync(target, content);
    return {path: name, bytes: content.length, sha256: sha(content)};
  });
  const binaries = Object.fromEntries(['cli','control','electron','verifier','validator'].map((key,i) => [key, {path: files[i].path, sha256: files[i].sha256}]));
  const marker = {schema: product.SCHEMA, mode: 'OWNED_PRODUCT_LAYOUT_NOT_INSTALLER', install_root: root,
    source_commit: 'a'.repeat(40), source_digest: 'b'.repeat(64), inventory_digest: product.inventoryIdentity(files),
    product_version: '2.4.0', client_protocol: 'researchos-client/2', schema_version: 24, binaries, files};
  marker.installation_id = product.installationIdentity(marker);
  fs.writeFileSync(path.join(root, 'installed-product.json'), JSON.stringify(marker));
  return root;
}
async function main() {
  process.env.LOCALAPPDATA = path.join(base, 'home');
  fs.mkdirSync(process.env.LOCALAPPDATA);
  const layout = product.loadProductLayout(makeFixture(false));
  results.push({id: 'PREP-LOWERCASE-INVENTORY', observed: !!layout, expected: true, pass: !!layout});
  let code = null;
  try { product.loadProductLayout(makeFixture(true)); } catch (error) { code = error.code || error.message; }
  results.push({id: 'PREP-MIXED-CASE-BUILDER-INVENTORY', observed: code, expected: 'ACCEPT_VALID_CASE_SENSITIVE_SORT', pass: code === null,
    finding: 'F01_JS_REJECTS_BUILDER_ORDER'});
  let calls = 0, exits = 0, refused = 0, release;
  const deferred = new Promise(resolve => { release = resolve; });
  const safeExit = product.createProductSafeExit({management: {shutdown: async () => {calls++; await deferred; return {}; }},
    ownedIdentity: () => ({pid: 1}), confirm: () => true, retire: () => true,
    onExit: async () => {exits++;}, onRefused: async () => {refused++;}});
  const first = safeExit(), second = safeExit();
  release(); await Promise.all([first, second]);
  results.push({id: 'PREP-CONCURRENT-SAFE-EXIT', observed: {calls, exits, refused, samePromise: first === second},
    pass: calls === 1 && exits === 1 && refused === 0 && first === second});
  const rejected = product.createProductSafeExit({management: {shutdown: async () => ({})},
    ownedIdentity: () => ({pid: 1}), confirm: () => false, retire: () => {throw new Error('must not retire');},
    onExit: async () => {throw new Error('must not exit');}, onRefused: async () => {refused++;}});
  code = null; try { await rejected(); } catch(error) {code = error.code;}
  results.push({id: 'PREP-UNCONFIRMED-EXIT', observed: code, pass: code === 'OWNED_EXIT_IDENTITY_UNCONFIRMED' && refused === 1});
  const parent = {PID: process.pid, CreatedNS: '1', ImageSHA256: 'c'.repeat(64)};
  const startup = product.writeStartupWitness(layout, parent); product.claimProductData(layout);
  fs.writeFileSync(path.join(layout.dataRoot, 'nonempty-fixture.db'), 'preserved');
  product.retireSupervisorWitness(layout, startup);
  product.writeStartupWitness(layout, parent); product.claimProductData(layout);
  const preserved = fs.readFileSync(path.join(layout.dataRoot, 'nonempty-fixture.db'), 'utf8') === 'preserved';
  results.push({id: 'PREP-NONEMPTY-BINDING-HELPER', pass: preserved, limitation: 'No discovery/process/native/session reopen exercised'});
}
main().then(() => {
  fs.writeFileSync(path.join(__dirname, 'PREP-PROBES.json'), JSON.stringify({evidence: 'HERMETIC_CAPTURED_MUTABLE_SOURCE_ONLY', native_runs: 0, source_acceptance: false, results}, null, 2) + '\n');
  console.log(JSON.stringify(results));
}).finally(() => {
  if (priorLocal === undefined) delete process.env.LOCALAPPDATA; else process.env.LOCALAPPDATA = priorLocal;
  const resolved = path.resolve(base);
  if (path.dirname(resolved) !== path.resolve(__dirname) || !path.basename(resolved).startsWith('fixture-')) throw new Error('unsafe cleanup');
  fs.rmSync(resolved, {recursive: true, force: true});
});

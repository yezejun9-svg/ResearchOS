import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

// Evaluate the exact pure functions in the production main without loading
// Electron or starting Core. These are mock verdict tests, not native proof.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const source = fs.readFileSync(path.join(root, 'apps/desktop/main/main.js'), 'utf8');
const begin = source.indexOf('function ownedCoreIdentity(machine) {');
const end = source.indexOf('\nconst deps = {', begin);
assert.ok(begin >= 0 && end > begin);
const code = source.slice(begin, end);
const { ownedCoreIdentity, smokeReadyEvidence, smokeShutdownConfirmation } =
  Function(code + '\nreturn { ownedCoreIdentity, smokeReadyEvidence, smokeShutdownConfirmation };')();

const identity = { PID: 12345, CreatedNS: '1792057406096619100', ImageSHA256: 'a'.repeat(64) };
const machine = () => ({ state: 'READY', identity: { ...identity }, hostId: 'host-aaaaaaaaaaaa',
  currentHost: () => ({ pid: 12345 }), hasUnconfirmedChild: () => false });
const renderer = { bridge: true, react_root: true, mounted_title: 'ResearchOS', navigation: 3 };
const nativeProbe = { ok: true, protocol_status: 'COMPLETED' };
const started = { health: 'UP', discovery: { pid: 12345 } };

test('exact main smoke verdict binds READY, native probe, React and owned identity', () => {
  const owned = ownedCoreIdentity(machine());
  assert.deepEqual(owned, { pid: 12345, created_ns: identity.CreatedNS,
    image_sha256: identity.ImageSHA256, host_id: 'host-aaaaaaaaaaaa' });
  assert.equal(smokeReadyEvidence(renderer, nativeProbe, { state: 'READY' }, started, owned), true);
  assert.equal(smokeReadyEvidence(renderer, null, { state: 'READY' }, started, owned), false);
  assert.equal(smokeReadyEvidence(renderer, { ok: false }, { state: 'READY' }, started, owned), false);
  assert.equal(smokeReadyEvidence(renderer, nativeProbe, { state: 'BROKEN' }, started, owned), false);
  assert.equal(smokeReadyEvidence({ ...renderer, react_root: false }, nativeProbe, { state: 'READY' }, started, owned), false);
  assert.equal(smokeReadyEvidence(renderer, nativeProbe, { state: 'READY' }, { ...started, discovery: { pid: 9 } }, owned), false);
  const changed = machine(); changed.currentHost = () => ({ pid: 9 });
  assert.equal(ownedCoreIdentity(changed), null);
  assert.match(crypto.createHash('sha256').update(code).digest('hex'), /^[a-f0-9]{64}$/);
});

test('exact main shutdown verdict requires returned exit and original PID, creation, image and host ID', () => {
  const m = machine(), owned = ownedCoreIdentity(m);
  m.state = 'STOPPED';
  const stopped = { state: 'STOPPED', process_exit_confirmed: true };
  assert.deepEqual(smokeShutdownConfirmation(stopped, m, owned),
    { process_exit_confirmed: true, owned_core_identity: owned });
  assert.equal(smokeShutdownConfirmation({ ...stopped, process_exit_confirmed: false }, m, owned), null);
  assert.equal(smokeShutdownConfirmation({ state: 'SHUTDOWN_ACCEPTED', process_exit_confirmed: true }, m, owned), null);
  m.hasUnconfirmedChild = () => true;
  assert.equal(smokeShutdownConfirmation(stopped, m, owned), null);
  m.hasUnconfirmedChild = () => false;
  for (const [field, replacement] of [['PID', 999], ['CreatedNS', '1'], ['ImageSHA256', 'b'.repeat(64)]]) {
    const original = m.identity[field]; m.identity[field] = replacement;
    assert.equal(smokeShutdownConfirmation(stopped, m, owned), null, field);
    m.identity[field] = original;
  }
  m.hostId = 'host-bbbbbbbbbbbb';
  assert.equal(smokeShutdownConfirmation(stopped, m, owned), null);
});

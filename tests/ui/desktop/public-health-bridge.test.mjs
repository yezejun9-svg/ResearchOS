import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { createRequire } from 'node:module';
import test from 'node:test';

// Exercise actual callCore, ensureCore, discovery validation, principalFor and
// requestFor using only in-memory filesystem/HTTP substitutes. No real socket,
// process, Native call, credential file, profile, DB or model is accessed.
const require = createRequire(import.meta.url);
const ipc = require('../../../apps/desktop/main/lib/ipc.js');
const READY = { status: 'ready', scope: 'DEVELOPMENT_ONLY', database: 'sqlite' };
const DISCOVERY = { url: 'http://127.0.0.1:31415', pid: 1, data_dir: 'SYNTHETIC_NEVER_OPENED' };
function fixture(options = {}) {
  const calls = { reads: [], probes: [], requests: [], spawns: 0 };
  const deps = {
    discoveryFile: 'IN_MEMORY_DISCOVERY', principalFile: 'IN_MEMORY_LEGACY_PRINCIPAL', requireLaunchDisabled: true,
    fsImpl: { readFileSync(file) {
      calls.reads.push(file);
      if (file === 'IN_MEMORY_DISCOVERY') {
        if (options.discoveryMissing) throw Object.assign(new Error('synthetic absent'), { code: 'ENOENT' });
        return JSON.stringify(options.discovery || DISCOVERY);
      }
      assert.equal(file, 'IN_MEMORY_LEGACY_PRINCIPAL');
      if (options.principal === 'malformed') return '{}';
      if (options.principal === 'present') return '{"principal_id":"synthetic-owner"}';
      throw Object.assign(new Error('synthetic absent'), { code: 'ENOENT' });
    } },
    httpImpl: { get(url, _options, callback) {
      calls.probes.push(url);
      const request = new EventEmitter(); request.destroy = () => {};
      queueMicrotask(() => {
        const response = new EventEmitter(); response.statusCode = options.probeStatus ?? 200;
        callback(response); response.emit('data', '{}'); response.emit('end');
      });
      return request;
    } },
    spawnImpl() { calls.spawns++; throw new Error('process launch forbidden in fixture'); },
    async transport(...args) {
      calls.requests.push(args);
      if (options.transportThrows) throw new Error('synthetic transport failure');
      return Object.hasOwn(options, 'reply') ? options.reply : READY;
    },
  };
  return { deps, calls };
}
const principalReads = f => f.calls.reads.filter(file => file === 'IN_MEMORY_LEGACY_PRINCIPAL').length;

test('actual public health reaches fixed healthz without reading absent or malformed legacy principal', async t => {
  for (const principal of ['absent', 'malformed', 'present']) await t.test(principal, async () => {
    const f = fixture({ principal });
    const reply = await ipc.callCore(f.deps, 'status', 'health', {});
    assert.deepEqual(reply, { ok: true, ...READY });
    assert.deepEqual(f.calls.probes, ['http://127.0.0.1:31415/healthz']);
    assert.deepEqual(f.calls.requests, [['GET', 'http://127.0.0.1:31415/healthz', {}, {}]]);
    assert.equal(principalReads(f), 0); assert.equal(f.calls.spawns, 0);
  });
});

test('public health accepts only an empty observation and never adopts caller request fields', async t => {
  for (const [name, body] of [['empty', {}], ['omitted', undefined], ['null', null], ['empty null prototype', Object.create(null)]]) await t.test(name, async () => {
    const f = fixture(); assert.equal((await ipc.callCore(f.deps, 'status', 'health', body)).ok, true);
    assert.deepEqual(f.calls.requests[0], ['GET', 'http://127.0.0.1:31415/healthz', {}, {}]);
  });
  const nonenumerable = {}; Object.defineProperty(nonenumerable, 'url', { value: 'http://outside.invalid' });
  const symbol = { [Symbol('header')]: 'synthetic' };
  const getter = {}; Object.defineProperty(getter, 'token', { get() { throw new Error('caller getter must not execute'); } });
  for (const [name, body] of [
    ['url', { url: 'http://outside.invalid' }], ['path', { path: '/sessions/send' }], ['verb', { method: 'POST' }],
    ['headers', { headers: { Authorization: 'synthetic' } }], ['principal', { principal_id: 'forged' }], ['token', { token: 'synthetic' }],
    ['array', []], ['string', ''], ['number', 0], ['boolean', false], ['date', new Date(0)],
    ['inherited field', Object.create({ url: 'http://outside.invalid' })], ['nonenumerable', nonenumerable], ['symbol', symbol], ['getter', getter],
  ]) await t.test('reject ' + name, async () => {
    const f = fixture(); const result = await ipc.callCore(f.deps, 'status', 'health', body);
    assert.equal(result.reason, 'EMPTY_HEALTH_REQUEST_REQUIRED'); assert.equal(result.ok, false);
    assert.equal(f.calls.requests.length, 0); assert.equal(principalReads(f), 0); assert.equal(f.calls.spawns, 0);
  });
});

test('actual discovery validation and disabled launch stay ahead of the public route', async t => {
  for (const [name, options] of [
    ['missing', { discoveryMissing: true }],
    ...['https://example.invalid', 'http://example.invalid:80', 'http://127.0.0.1:31415/else', 'http://owner@127.0.0.1:31415', 'http://127.0.0.1:31415?x=1'].map(url => [url, { discovery: { ...DISCOVERY, url } }]),
  ]) await t.test(name, async () => {
    const f = fixture(options); const result = await ipc.callCore(f.deps, 'status', 'health', {});
    assert.equal(result.ok, false); assert.equal(result.reason, 'NOT_FOUND_NO_LAUNCH');
    assert.equal(f.calls.probes.length, 0); assert.equal(f.calls.requests.length, 0); assert.equal(principalReads(f), 0); assert.equal(f.calls.spawns, 0);
  });
});

test('all non-health routes retain missing and malformed legacy principal checks', async t => {
  const routes = [
    ['status', 'host'], ['workspace', 'list'], ['workspace', 'register'], ['workspace', 'pick_directory'],
    ['session', 'list'], ['session', 'create'], ['session', 'send'], ['provider', 'models'], ['provider', 'configure'], ['provider', 'probe'],
    ['status', 'Health'], ['STATUS', 'health'], ['unknown', 'health'],
  ];
  for (const principal of ['absent', 'malformed']) for (const [client, method] of routes) await t.test(`${principal}:${client}.${method}`, async () => {
    const f = fixture({ principal }); const result = await ipc.callCore(f.deps, client, method, {});
    assert.equal(result.ok, false); assert.equal(result.reason, principal === 'malformed' ? 'PRINCIPAL_STORE_MALFORMED' : 'PRINCIPAL_STORE_ABSENT');
    assert.equal(principalReads(f), 1); assert.equal(f.calls.requests.length, 0); assert.equal(f.calls.spawns, 0);
  });
});

test('authenticated reads and mutations retain their exact routes, payload filtering and principal header', async t => {
  for (const [client, method, verb, relative] of [
    ['status', 'host', 'GET', '/host/status'], ['workspace', 'list', 'GET', '/workspaces'],
    ['workspace', 'register', 'POST', '/workspaces'], ['session', 'send', 'POST', '/sessions/send'], ['provider', 'configure', 'POST', '/provider/configure'],
  ]) await t.test(client + '.' + method, async () => {
    const f = fixture({ principal: 'present', reply: { status: 'stored' } });
    const result = await ipc.callCore(f.deps, client, method, { value: 'kept', token: 'remove', owner_token: 'remove' });
    assert.deepEqual(result, { ok: true, status: 'stored' });
    assert.deepEqual(f.calls.requests, [[verb, DISCOVERY.url + relative, { value: 'kept' }, { 'X-ResearchOS-Principal': 'synthetic-owner' }]]);
    assert.equal(principalReads(f), 1);
  });
});

test('provider probe classification remains independent of public health success', async t => {
  for (const [reply, expected] of [[{ status: 'OK' }, true], [{ status: 'OK', degraded: true }, false], [{ status: 'AUTH_REQUIRED' }, false], [{ status: 'UNSUPPORTED' }, false]]) await t.test(JSON.stringify(reply), async () => {
    const f = fixture({ principal: 'present', reply }); const result = await ipc.callCore(f.deps, 'provider', 'probe', {});
    assert.equal(result.ok, expected); assert.equal(principalReads(f), 1);
    assert.deepEqual(f.calls.requests[0], ['POST', DISCOVERY.url + '/provider/probe', {}, { 'X-ResearchOS-Principal': 'synthetic-owner' }]);
  });
});

test('public health preserves failures and incomplete replies without fabricating ready fields', async t => {
  for (const [name, reply] of [['unavailable', { status: 'unavailable', scope: 'DEVELOPMENT_ONLY' }], ['transport error', { status: 'ERROR', error: 'SYNTHETIC_TIMEOUT' }], ['empty', {}], ['null', null], ['wrong scope', { ...READY, scope: 'OTHER' }], ['wrong database', { ...READY, database: 'OTHER' }]]) await t.test(name, async () => {
    const f = fixture({ reply }); const result = await ipc.callCore(f.deps, 'status', 'health', {});
    for (const field of ['status', 'scope', 'database']) assert.equal(result[field], reply?.[field]);
    if (reply?.error) assert.equal(result.ok, false);
    assert.equal(result.ok === true && result.status === 'ready' && result.scope === 'DEVELOPMENT_ONLY' && result.database === 'sqlite', false);
    assert.equal(principalReads(f), 0);
  });
  await t.test('transport throws remains a rejected observation', async () => {
    const f = fixture({ transportThrows: true }); await assert.rejects(ipc.callCore(f.deps, 'status', 'health', {}), /synthetic transport failure/);
    assert.equal(principalReads(f), 0); assert.equal(f.calls.requests.length, 1);
  });
});

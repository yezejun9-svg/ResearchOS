'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
// No real listener, native pipe, CLI child, authentication file or model.
require('node:http').request = () => { throw Error('REAL_HTTP_FORBIDDEN'); };
require('node:child_process').spawn = () => { throw Error('REAL_CHILD_FORBIDDEN'); };
const { registerHarness } = require('../../apps/desktop/main/lib/ipc.js');
const { createHarnessWire, createPendingJournal, validate, CONTRACT_SHA256 } = require('../../apps/desktop/main/lib/harness-wire.js');
const project = 'fixture-project', taskId = 'fixture-task';
const ref = { project_id: project, task_id: taskId };
const task = (extra = {}) => ({ task_ref: ref, request_id: 'fixture-request-1', harness_id: 'codex', workspace_ref: 'fixture-workspace', prompt: 'Inspect only', scope: 'workspace-read', ephemeral: true, status: 'QUEUED', terminal: false, task_revision: '1', run: null, created_at: '2026-11-04T00:00:00Z', updated_at: '2026-11-04T00:00:00Z', result: null, failure: null, ...extra });
function capabilities() {
  return { harness_id: 'codex', display_name: 'Codex CLI', backend: 'codex-cli-readonly-v1',
    installation: { present: true, version: 'synthetic-fixture', executable_sha256: null, checked_at: null },
    authentication: { state: 'UNPROBED', kind: null, checked_at: null },
    verification: { execution: 'FIXTURE_ONLY', workspace_read_scope: 'UNVERIFIED', cancellation: 'UNVERIFIED', checked_at: null },
    capabilities: { readonly_turn: true, event_stream: true, cancel: true, task_history: true, request_lookup: true,
      token_delta: false, write: false, resume: false, pause: false, per_tool_approval: false, file_diff: false, file_list: false, file_artifacts: false, attachments: false },
    security_scope: { mode: 'workspace-read', profile_id: 'synthetic-fixture', config_source: 'HOST_FIXED', hooks: 'PLATFORM_POLICY', mcp: 'PLATFORM_POLICY', native_auth: 'CLI_OWNED', enforcement_verified: false }, can_submit: true, reason_codes: [] };
}
const ok = data => ({ ok: true, outcome: 'REPLIED', data });
const ack = body => ok({ task_ref: ref, request_id: body.request_id, task_revision: '1', status: 'QUEUED', run: null });
function fixture(responder, journal) {
  const handlers = new Map(), calls = [];
  let origin = 'fixture-origin', sequence = 0;
  const state = { projectId: project, selectionGeneration: 0 };
  const deps = { sessionState: state, harnessJournal: journal || { entries: [], error: null, replace(entries) { this.entries = structuredClone(entries); } }, harnessSenderAllowed: event => event.allowed === true,
    harnessEnsureCore: async () => ({ discovery: { url: 'http://127.0.0.1:12345/', data_dir: 'synthetic-fixture' } }),
    harnessOrigin: () => origin, harnessCurrentOrigin: () => origin,
    credentialFor: async () => 'synthetic-main-only-bearer', harnessRequestId: () => 'fixture-request-' + (++sequence),
    harnessWire: async args => {
      if (!args.beforeSend()) return { ok: false, reason: 'HARNESS_CONTEXT_CHANGED', outcome: 'NOT_SENT' };
      calls.push(args);
      const result = await responder(args, calls.length);
      if (result.ok) validate(args.responseType, { api_version: 'harness.v1', data: result.data });
      return result;
    } };
  registerHarness({ handle: (name, fn) => handlers.set(name, fn) }, deps);
  return { deps, calls, state, setOrigin: value => { origin = value; },
    invoke: (name, body, event = { allowed: true }) => handlers.get('ros:harness:' + name)(event, body), handlers };
}
function httpFixture(raw, status = 200, contentType = 'application/json') {
  const requests = [];
  const httpImpl = { request(target, options, callback) {
    const req = new EventEmitter();
    req.destroy = () => {};
    req.end = body => {
      requests.push({ target, options, body });
      if (raw === null) return;
      queueMicrotask(() => {
        const res = new EventEmitter(); res.statusCode = status; res.headers = { 'content-type': contentType }; res.destroy = () => {};
        callback(res); res.emit('data', Buffer.isBuffer(raw) ? raw : Buffer.from(raw)); res.emit('end');
      });
    };
    return req;
  } };
  return { requests, wire: createHarnessWire({ httpImpl, timeoutMs: raw === null ? 10 : 1000 }) };
}
const send = (wire, extra = {}) => wire({ url: 'http://127.0.0.1:12345/harness/v1/capabilities', method: 'GET', credential: 'synthetic-main-only-bearer', responseType: 'CapabilitiesResponse', beforeSend: () => true, ...extra });

test('pinned contract and metadata retain independent unverified capabilities', () => {
  assert.equal(CONTRACT_SHA256, '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c');
  validate('CapabilitiesResponse', { api_version: 'harness.v1', data: capabilities() });
  assert.throws(() => validate('CapabilitiesResponse', { api_version: 'harness.v1', data: { ...capabilities(), can_Submit: true } }));
  const invalid = capabilities(); invalid.capabilities.pause = true;
  assert.throws(() => validate('Capabilities', invalid));
  assert.throws(() => validate('Task', task({ task_revision: 9007199254740993 })));
});
test('wire preserves query cursor and injects only the Main bearer', async () => {
  const f = httpFixture(JSON.stringify({ api_version: 'harness.v1', data: capabilities() }));
  const result = await send(f.wire, { url: 'http://127.0.0.1:12345/harness/v1/capabilities?cursor=9007199254740993' });
  assert.equal(result.ok, true); assert.equal(f.requests[0].target.search, '?cursor=9007199254740993');
  assert.equal(f.requests[0].options.headers.authorization, 'Bearer synthetic-main-only-bearer');
  assert.equal(JSON.stringify(result).includes('synthetic-main-only-bearer'), false);
});
test('raw response rejects duplicate, escaped duplicate, trailing, UTF8 and unknown fields', async t => {
  const raw = JSON.stringify({ api_version: 'harness.v1', data: capabilities() });
  const cases = [raw.replace('"can_submit":true', '"can_submit":true,"can_submit":false'),
    raw.replace('"can_submit":true', '"can_submit":true,"can_\\u0073ubmit":false'), raw + '{}', Buffer.from([0xff]),
    raw.replace('"can_submit":true', '"can_submit":"true"'), raw.replace('"can_submit":true', '"can_submit":true,"constructor":{}')];
  for (let i = 0; i < cases.length; i++) await t.test(String(i), async () => {
    const f = httpFixture(cases[i]); const result = await send(f.wire);
    assert.equal(result.ok, false); assert.equal(result.outcome, 'UNKNOWN'); assert.equal(f.requests.length, 1);
  });
});
test('wire refuses foreign routes before dispatch and never retries timeout or redirects', async () => {
  const f = httpFixture(null);
  assert.equal((await send(f.wire, { url: 'https://example.invalid/harness/v1/tasks' })).outcome, 'NOT_SENT');
  assert.equal(f.requests.length, 0);
  assert.equal((await send(f.wire)).outcome, 'UNKNOWN'); assert.equal(f.requests.length, 1);
  const redirected = httpFixture('{}', 302);
  assert.equal((await send(redirected.wire)).ok, false); assert.equal(redirected.requests.length, 1);
});
test('origin and strict intent gates reject before any injected dispatch', async () => {
  const f = fixture(() => { throw Error('dispatch forbidden'); });
  assert.equal((await f.invoke('submit', { workspace_ref: 'w', prompt: 'x' }, { allowed: false })).reason, 'DESKTOP_ORIGIN_REQUIRED');
  assert.equal((await f.invoke('submit', { workspace_ref: 'w', prompt: 'x', argv: ['bad'] })).reason, 'INVALID_REQUEST');
  assert.equal((await f.invoke('submit', { workspace_ref: 'w', prompt: ' \n ' })).reason, 'INVALID_REQUEST');
  assert.equal(f.calls.length, 0);
});
test('submit owns request identity and queued ACK remains bound until readback', async () => {
  const f = fixture(args => args.method === 'POST' ? ack(args.body) : ok(task()));
  const result = await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' });
  assert.equal(result.data.status, 'QUEUED'); assert.equal(result.data.run, null);
  assert.deepEqual(Object.keys(f.calls[0].body).sort(), ['harness_id', 'project_id', 'prompt', 'request_id', 'scope', 'workspace_ref']);
  assert.equal((await f.invoke('pending')).data.state, 'ACKNOWLEDGED');
  await f.invoke('get', { task_id: taskId }); assert.equal((await f.invoke('pending')).data, null);
});
test('uncertain submit and NOT_FOUND never allocate another request or POST', async () => {
  const f = fixture(args => args.method === 'POST' ? { ok: false, reason: 'HARNESS_TIMEOUT', outcome: 'UNKNOWN' } :
    ok({ items: [], next_cursor: '0', has_more: false, lookup: { request_id: 'fixture-request-1', state: 'NOT_FOUND' } }));
  await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' });
  assert.equal((await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'different' })).reason, 'HARNESS_REQUEST_PENDING');
  const result = await f.invoke('reconcile');
  assert.equal(result.data.pending.request_id, 'fixture-request-1'); assert.equal(result.data.task, null);
  assert.equal(f.calls.filter(item => item.method === 'POST').length, 1);
  assert.equal(new URL(f.calls[1].url).searchParams.get('request_id'), 'fixture-request-1');
});
test('matching persisted request resolves UNKNOWN without external launch', async () => {
  const f = fixture(args => args.method === 'POST' ? { ok: false, reason: 'HARNESS_TIMEOUT', outcome: 'UNKNOWN' } :
    ok({ items: [task()], next_cursor: '0', has_more: false, lookup: { request_id: 'fixture-request-1', state: 'FOUND' } }));
  await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' });
  assert.equal((await f.invoke('reconcile')).data.task.task_ref.task_id, taskId);
  assert.equal((await f.invoke('pending')).data, null); assert.equal(f.calls.length, 2);
});
test('internal error and foreign response retain the uncertain mutation barrier', async () => {
  for (const reply of [{ ok: false, outcome: 'REPLIED', reason: 'INTERNAL_ERROR' }, ok({ task_ref: { ...ref, project_id: 'foreign' }, request_id: 'fixture-request-1', task_revision: '1', status: 'QUEUED', run: null })]) {
    const f = fixture(() => reply);
    await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' });
    assert.equal((await f.invoke('pending')).data.state, 'UNKNOWN');
    assert.equal((await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).reason, 'HARNESS_REQUEST_PENDING');
    assert.equal(f.calls.length, 1);
  }
});
test('async project/Host change cannot dispatch under the new authority or adopt late ACK', async () => {
  const before = fixture(args => ack(args.body));
  before.deps.credentialFor = async () => { before.state.projectId = 'other'; before.state.selectionGeneration++; return 'synthetic'; };
  assert.equal((await before.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).outcome, 'NOT_SENT');
  assert.equal(before.calls.length, 0);
  const after = fixture(args => { after.setOrigin('other-origin'); return ack(args.body); });
  assert.equal((await after.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).outcome, 'UNKNOWN');
  assert.equal((await after.invoke('pending')).data.state, 'UNKNOWN');
  const reads = after.calls.length; assert.equal((await after.invoke('reconcile')).reason, 'HARNESS_HOST_CHANGED'); assert.equal(after.calls.length, reads);
});
test('cancel preserves nullable pair/exact strings, STATE_CONFLICT never retargets', async () => {
  const f = fixture(() => ({ ok: false, outcome: 'REPLIED', reason: 'STATE_CONFLICT' }));
  const queued = { task_id: taskId, expected_task_revision: '1', expected_run_id: null, expected_epoch: null };
  assert.equal((await f.invoke('cancel', { ...queued, expected_epoch: '1' })).reason, 'INVALID_REQUEST');
  assert.equal((await f.invoke('cancel', queued)).reason, 'STATE_CONFLICT');
  assert.equal(f.calls.length, 1); assert.equal(f.calls[0].body.expected_run_id, null);
  await f.invoke('cancel', { ...queued, expected_task_revision: '9007199254740993', expected_run_id: 'fixture-run', expected_epoch: '9007199254740994' });
  assert.equal(f.calls.length, 2); assert.equal(f.calls[1].body.expected_epoch, '9007199254740994');
});
test('event cursor uses a separate task query and foreign Task pages are refused', async () => {
  const f = fixture(() => ok({ task_ref: { ...ref, task_id: 'foreign' }, events: [], next_cursor: '9007199254740993', has_more: false, end: false, reset: false, snapshot: null }));
  assert.equal((await f.invoke('events', { task_id: taskId, cursor: '9007199254740993' })).reason, 'HARNESS_REPLY_MISMATCH');
  assert.equal(new URL(f.calls[0].url).searchParams.get('cursor'), '9007199254740993');
});

function memoryJournalFS() {
  const files = new Map(), descriptors = new Map(); let next = 0;
  return { files, failSync: false,
    existsSync: path => files.has(path),
    lstatSync: path => ({ size: files.get(path).length, isFile: () => true, isSymbolicLink: () => false }),
    readFileSync: path => Buffer.from(files.get(path)),
    openSync(path, flags) { assert.equal(flags, 'wx'); if (files.has(path)) throw Error('exists'); files.set(path, Buffer.alloc(0)); descriptors.set(++next, path); return next; },
    writeFileSync(fd, bytes) { files.set(descriptors.get(fd), Buffer.from(bytes)); },
    fsyncSync() { if (this.failSync) throw Error('synthetic fsync failure'); },
    closeSync(fd) { descriptors.delete(fd); },
    renameSync(from, to) { files.set(to, files.get(from)); files.delete(from); },
    unlinkSync: path => files.delete(path),
  };
}
test('private pending journal survives Main restart without a fresh mutation identity', async () => {
  const fsImpl = memoryJournalFS(), file = 'synthetic-userData/harness-pending.json';
  const journal = createPendingJournal({ file, fsImpl });
  const first = fixture(() => ({ ok: false, outcome: 'UNKNOWN', reason: 'HARNESS_TIMEOUT' }), journal);
  await first.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' });
  assert.equal(first.calls.length, 1);
  const persisted = fsImpl.files.get(file).toString();
  assert.equal(persisted.includes('synthetic-main-only-bearer'), false);
  assert.equal(JSON.parse(persisted).entries[0].requestId, 'fixture-request-1');
  assert.match(JSON.parse(persisted).entries[0].bodySHA256, /^[a-f0-9]{64}$/);
  const reopened = createPendingJournal({ file, fsImpl });
  const second = fixture(() => ok({ items: [], next_cursor: '0', has_more: false, lookup: { request_id: 'fixture-request-1', state: 'NOT_FOUND' } }), reopened);
  assert.equal((await second.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).reason, 'HARNESS_REQUEST_PENDING');
  assert.equal((await second.invoke('reconcile')).data.pending.request_id, 'fixture-request-1');
  assert.equal(second.calls.length, 1); assert.equal(second.calls[0].method, 'GET');
});
test('corrupt or failed atomic journal blocks dispatch and never silently evicts', async () => {
  const fsImpl = memoryJournalFS(), file = 'synthetic-userData/harness-pending.json';
  fsImpl.files.set(file, Buffer.from('{"schema":"researchos.harness.pending/1","entries":[],"entries":[]}'));
  const corrupt = createPendingJournal({ file, fsImpl });
  const blocked = fixture(() => { throw Error('must not dispatch'); }, corrupt);
  assert.equal((await blocked.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).reason, 'HARNESS_JOURNAL_INVALID');
  assert.equal(blocked.calls.length, 0);
  const failedFS = memoryJournalFS(); failedFS.failSync = true;
  const failed = createPendingJournal({ file, fsImpl: failedFS });
  const unsent = fixture(() => { throw Error('must not dispatch'); }, failed);
  assert.equal((await unsent.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).reason, 'HARNESS_JOURNAL_WRITE_FAILED');
  assert.equal(unsent.calls.length, 0);
  assert.equal(failedFS.files.size, 0);
  const limitedFS = memoryJournalFS(), limited = createPendingJournal({ file, fsImpl: limitedFS, maxEntries: 0 });
  const full = fixture(() => { throw Error('must not dispatch'); }, limited);
  assert.equal((await full.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })).reason, 'HARNESS_JOURNAL_LIMIT');
  assert.equal(full.calls.length, 0); assert.equal(limitedFS.files.size, 0);
});

test('a full journal preserves the original unresolved project instead of evicting it', async () => {
  const fsImpl = memoryJournalFS(), file = 'synthetic-userData/harness-pending.json';
  const journal = createPendingJournal({ file, fsImpl, maxEntries: 1 });
  const f = fixture(() => ({ ok: false, outcome: 'UNKNOWN', reason: 'HARNESS_TIMEOUT' }), journal);
  await f.invoke('submit', { workspace_ref: 'fixture-workspace', prompt: 'Inspect only' });
  const original = fsImpl.files.get(file).toString();
  f.state.projectId = 'other-project'; f.state.selectionGeneration++;
  assert.equal((await f.invoke('submit', { workspace_ref: 'other-workspace', prompt: 'Another task' })).reason, 'HARNESS_JOURNAL_LIMIT');
  assert.equal(f.calls.length, 1); assert.equal(fsImpl.files.get(file).toString(), original);
});

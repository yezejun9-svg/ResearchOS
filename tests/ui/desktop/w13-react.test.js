'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const protocol = require('../../../apps/desktop/main/lib/app-protocol.js');
const { chooseWorkspace } = require('../../../apps/desktop/main/lib/first-use.js');
const v2 = require('../../../apps/desktop/main/lib/v2.js');
const spec = require('../../../spec/v2.0/contracts/openapi.json');

const routes = protocol.routeTable(spec);

test('only published method and path pairs reach the local host', () => {
  assert.equal(protocol.allowedRoute(routes, 'GET', '/v1/projects'), true);
  assert.equal(protocol.allowedRoute(routes, 'POST', '/v1/projects'), true);
  assert.equal(protocol.allowedRoute(routes, 'DELETE', '/v1/projects'), false);
  assert.equal(protocol.allowedRoute(routes, 'GET', '/v1/projects/p/runs/x'), true);
  assert.equal(protocol.allowedRoute(routes, 'POST', '/v1/projects/p/runs/x'), false);
  assert.equal(protocol.allowedRoute(routes, 'GET', '/v1/projects/p/%2e%2e/secrets'), false);
  assert.equal(protocol.allowedRoute(routes, 'GET', '/v1/projects/p%2fx/state'), false);
  assert.equal(protocol.allowedRoute(routes, 'GET', '/v2/command'), false);
});

test('bundled SPA route fallback stays inside dist; missing assets fail', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-w13-static-'));
  try {
    fs.writeFileSync(path.join(dir, 'index.html'), '<h1>ResearchOS</h1>');
    const html = protocol.staticResponse(dir, '/p/123/cycles');
    assert.equal(html.status, 200);
    const csp = html.headers.get('content-security-policy');
    assert.match(csp, /img-src 'self' data: blob:/);
    assert.match(csp, /frame-src 'self' blob: about:/);
    assert.match(csp, /object-src 'none'/);
    assert.doesNotMatch(csp, /https?:|\*/);
    assert.equal(protocol.staticResponse(dir, '/assets/missing.js').status, 404);
    assert.equal(protocol.staticResponse(dir, '/%2e%2e/secret.txt').status, 400);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('proxy never replays a write on 401; explicit retry preserves upload, safe GET renews, redirects fail', async () => {
  const seen = [];
  const server = http.createServer((req, res) => {
    const parts = [];
    req.on('data', part => parts.push(part));
    req.on('end', () => {
      seen.push({ auth: req.headers.authorization, body: Buffer.concat(parts), key: req.headers['idempotency-key'] });
      if (req.headers.authorization === 'Bearer expired') { res.writeHead(401); res.end('expired'); return; }
      if (req.url.includes('redirect=1')) { res.writeHead(302, { location: 'https://example.invalid/' }); res.end(); return; }
      res.writeHead(200, { 'content-type': 'application/octet-stream', 'x-researchos-principal-id': 'owner' });
      res.end(Buffer.concat(parts));
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const url = `http://127.0.0.1:${server.address().port}/`;
    let renewals = 0;
    let currentCredential = 'expired';
    const handler = protocol.createAppProtocol({ dist: 'unused', routes,
      ensureCore: async () => ({ discovery: { url } }),
      credentialFor: async (_discovery, force) => { if (force) { renewals++; currentCredential = 'fresh'; } return currentCredential; },
    });
    const bytes = Buffer.from([0, 255, 1, 2, 13]);
    const request = new Request('ros-app://desktop/v1/projects/p/content', { method: 'POST',
      headers: { 'content-type': 'application/octet-stream', 'idempotency-key': 'fixed-key', authorization: 'Bearer renderer-spoof' },
      body: bytes });
    const refused = await handler(request);
    assert.equal(refused.status, 401);
    assert.equal((await refused.json()).code, 'AUTH_REFRESHED_RETRY_REQUIRED');
    assert.equal(renewals, 1);
    assert.equal(seen.length, 1);
    assert.equal(seen[0].auth, 'Bearer expired');
    assert.ok(seen[0].body.equals(bytes));
    const explicitRetry = await handler(new Request('ros-app://desktop/v1/projects/p/content', { method: 'POST',
      headers: { 'content-type': 'application/octet-stream', 'idempotency-key': 'fixed-key' }, body: bytes }));
    assert.equal(explicitRetry.status, 200);
    assert.deepEqual(Buffer.from(await explicitRetry.arrayBuffer()), bytes);
    assert.equal(explicitRetry.headers.get('x-researchos-principal-id'), 'owner');
    assert.equal(seen.length, 2);
    assert.equal(seen[1].auth, 'Bearer fresh');
    assert.equal(seen[1].key, 'fixed-key');
    currentCredential = 'expired';
    const safeRead = await handler(new Request('ros-app://desktop/v1/projects/p/state'));
    assert.equal(safeRead.status, 200);
    assert.equal(renewals, 2);
    assert.deepEqual(seen.slice(2, 4).map(x => x.auth), ['Bearer expired', 'Bearer fresh']);
    const redirected = await handler(new Request('ros-app://desktop/v1/projects/p/state?redirect=1'));
    assert.equal(redirected.status, 502);
    assert.equal(redirected.headers.get('location'), null);
  } finally { await new Promise(resolve => server.close(resolve)); }
});

test('SSE response is streamed with original event bytes', async () => {
  const server = http.createServer((_req, res) => {
    res.writeHead(200, { 'content-type': 'text/event-stream' });
    res.write(':heartbeat\n\n');
    setTimeout(() => res.end('id: 7\ndata: {"sequence":7}\n\n'), 20);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const handler = protocol.createAppProtocol({ dist: 'unused', routes,
      ensureCore: async () => ({ discovery: { url: `http://127.0.0.1:${server.address().port}/` } }),
      credentialFor: async () => 'main-only',
    });
    const response = await handler(new Request('ros-app://desktop/v1/projects/p/events/stream', { headers: { accept: 'text/event-stream', 'last-event-id': '6' } }));
    assert.equal(response.status, 200);
    assert.equal(response.headers.get('content-type'), 'text/event-stream');
    assert.equal(await response.text(), ':heartbeat\n\nid: 7\ndata: {"sequence":7}\n\n');
  } finally { await new Promise(resolve => server.close(resolve)); }
});

test('first use consumes native choice, registers and bootstraps before saving real IDs', async () => {
  const calls = [];
  const state = { projectId: null, sessionId: null, expectedRevision: null, writerEpoch: null };
  let saved;
  const result = await chooseWorkspace({
    host: { ensureCore: async () => ({ discovery: { data_dir: 'D:/host', url: 'http://127.0.0.1:1/', pid: 1 } }) },
    native: { hostInstanceId: () => 'host-123456789abc', dialNative: async (_pipe, frame) => {
      calls.push(frame.kind);
      assert.deepEqual(frame.payload, { requested_path: null, requested_access: 'READ_WRITE' });
      return { kind: 'NATIVE_WORKSPACE_CHOOSE_RESULT', payload: { selection_ref: 'sel-real', display_path: 'D:/研究/项目' } };
    } },
    callV2: async (_deps, method, body) => {
      calls.push(method);
      const wire = v2.envelopeFor({ clientId: _deps.clientId, credential: 'private', commandId: 'first-use-' + method },
        _deps.sessionState, method, body);
      assert.equal(wire.ok, true, wire.reason);
      assert.equal(wire.payload.project_id, null);
      assert.equal(wire.payload.session_id, null);
      assert.equal(wire.payload.expected_revision, null);
      assert.equal(wire.payload.writer_epoch, null);
      if (method === 'workspace.register') {
        assert.equal(body.selection_ref, 'sel-real');
        return { ok: true, completed: true, protocol_status: 'COMPLETED', result: { authorized_workspace_ref: 'ws-real' } };
      }
      assert.equal(body.authorized_workspace_ref, 'ws-real');
      return { ok: true, completed: true, protocol_status: 'COMPLETED', result: { project_id: 'p-real', project_profile_ref: { revision: 7 },
        workspace: { project_id: 'p-real', status: 'ACTIVE', authorized_workspace_ref: 'ws-real' } } };
    },
    deps: { fsImpl: {}, clientId: 'desktop-shell', credentialFor: async () => 'private' },
    contextStore: { save: next => { saved = { ...next }; } }, sessionState: state,
  }, {});
  assert.equal(result.ok, true);
  assert.equal(result.project_id, 'p-real');
  assert.deepEqual(calls, ['NATIVE_WORKSPACE_CHOOSE_REQUEST', 'workspace.register', 'project.bootstrap']);
  assert.equal(saved.projectId, 'p-real');
  assert.equal(state.expectedRevision, null);
  assert.equal(state.writerEpoch, null);
  const envelope = v2.envelopeFor({ clientId: 'desktop-shell', credential: 'private', commandId: 'first-use' },
    { projectId: null, sessionId: null, expectedRevision: null, writerEpoch: null },
    'project.bootstrap', { authorized_workspace_ref: 'ws-real', display_name: '项目' });
  assert.equal(envelope.ok, true);
  assert.equal(envelope.payload.project_id, null);
  const create = v2.envelopeFor({ clientId: 'desktop-shell', credential: 'private', commandId: 'first-session' },
    state, 'session.create', { workspace_ref: 'ws-real', model_config_ref: 'model-real', title: '首次会话' });
  assert.equal(create.ok, true, create.reason);
  assert.equal(create.payload.project_id, 'p-real');
  assert.equal(create.payload.session_id, null);
  assert.equal(create.payload.expected_revision, null);
  assert.equal(create.payload.writer_epoch, null);
});

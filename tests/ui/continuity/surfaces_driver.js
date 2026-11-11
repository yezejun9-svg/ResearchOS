const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');
const ROOT = process.argv[2];
const out = { checks: {}, errors: [] };

(async () => {
  const shell = require(path.join(ROOT, 'apps/desktop/main/lib/v2.js'));
  const web = await import(pathToFileURL(path.join(ROOT, 'apps/web/src/v2client.js')).href);
  const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'internal/api/contracts/client.protocol.schema.json'), 'utf8'));

  const VALUES = {
    text: 'hello', attachment_artifact_ids: [], delivery: 'NORMAL',
    action: 'PAUSE', target_id: 'run-1', reason: 'from the workbench',
    after_sequence: 0, limit: 50, cursor: null, request_write_owner: false,
    target_client_id: 'cli-1', handoff_mode: 'WHEN_SETTLED',
    objective: 'continue the goal', contract_artifact_ids: [], start_as_draft: true,
    provider_id: 'provider-x', refresh: false, allow_network: false, max_output_tokens: 64, timeout_ms: 1000,
    selection_ref: 'sel-1', display_name: 'workspace', requested_access: 'READ_WRITE',
    workspace_ref: 'ws-1', relative_path: 'notes/a.md', base: 'INDEX', max_bytes: 4096,
    task_id: 'task-1', expected_content_hash: null, create_if_missing: false, purpose: 'ATTACHMENT',
    config_revision: 1, base_url: 'http://127.0.0.1:1', model_id: 'model-x', credential_ref: null,
    authorized_workspace_ref: 'ws-1', model_config_ref: 'mc-1', title: null,
    resource_request_id: 'rr-1', resource_request_revision: 3, action_digest: 'sha256:abc', decision: 'ALLOW_ONCE',
  };
  const payloadFor = (method, contract) =>
    Object.fromEntries(contract[method].required.map(k => [k, VALUES[k] === undefined ? null : VALUES[k]]));
  const normalize = (e) => e.ok
    ? { ok: true, verb: e.verb, path: e.path, headers: e.headers, envelope: e.payload }
    : { ok: false, reason: e.reason };

  // The frozen schema is the third opinion: both tables must carry exactly its method set, and each method's
  // payload/result names and the required key set must be what the published $defs say.
  const published = Object.keys(schema['x-method-contracts']).sort();
  const requiredFrom = (name) => {
    const def = schema.$defs[name];
    return def && def.required ? def.required.slice().sort() : [];
  };
  const tableDiff = (label, contract) => {
    const names = Object.keys(contract).sort();
    const rows = [];
    for (const method of names) {
      const want = schema['x-method-contracts'][method];
      if (!want) { rows.push({ method, problem: 'not published' }); continue; }
      if (want.payload !== contract[method].payload) rows.push({ method, problem: 'payload ' + contract[method].payload + ' != ' + want.payload });
      if (want.result !== contract[method].result) rows.push({ method, problem: 'result ' + contract[method].result + ' != ' + want.result });
      const declared = contract[method].required.slice().sort();
      const publishedRequired = requiredFrom(want.payload);
      if (JSON.stringify(declared) !== JSON.stringify(publishedRequired)) {
        rows.push({ method, problem: 'required [' + declared.join(',') + '] != published [' + publishedRequired.join(',') + ']' });
      }
    }
    return { label, count: names.length, same_names: JSON.stringify(names) === JSON.stringify(published), rows };
  };
  out.checks.tables = {
    published: published.length,
    shell: tableDiff('shell', shell.CONTRACT),
    web: tableDiff('web', web.CONTRACT),
  };

  const states = [
    { name: 'full-session', identity: { clientId: 'desktop-renderer', credential: 'tok', commandId: 'cmd-1' },
      state: { projectId: 'proj-1', sessionId: 'sess-1', expectedRevision: 7, writerEpoch: 2 } },
    { name: 'host-level', identity: { clientId: 'desktop-renderer', credential: 'tok', commandId: 'cmd-2' }, state: {} },
    { name: 'no-epoch', identity: { clientId: 'desktop-renderer', credential: 'tok', commandId: 'cmd-3' },
      state: { projectId: 'proj-1', sessionId: 'sess-1', expectedRevision: 7 } },
  ];
  let legal = 0, legalAgree = 0;
  const legalRows = [];
  for (const probe of states) {
    for (const method of published) {
      const payload = payloadFor(method, web.CONTRACT);
      const a = JSON.stringify(normalize(web.envelopeFor(probe.identity, probe.state, method, payload)));
      const b = JSON.stringify(normalize(shell.envelopeFor(probe.identity, probe.state, method, payload)));
      legal++;
      if (a === b) legalAgree++; else legalRows.push({ probe: probe.name, method, a, b });
    }
  }
  out.checks.legal_envelopes = { count: legal, agree: legalAgree, rows: legalRows.slice(0, 4) };

  const id = states[0].identity, st = states[0].state, sendPayload = payloadFor('session.send', web.CONTRACT);
  const illegal = [
    ['unknown-method', id, st, 'session.nope', {}, 'UNKNOWN_METHOD'],
    ['no-credential', { ...id, credential: '' }, st, 'host.status', {}, 'CREDENTIAL_ABSENT'],
    ['payload-array', id, st, 'session.list', [], 'PAYLOAD_NOT_OBJECT'],
    ['payload-null', id, st, 'session.list', null, 'PAYLOAD_NOT_OBJECT'],
    ['missing-payload-field', id, st, 'session.send', { text: 'x' }, 'MISSING_PAYLOAD_FIELDS:attachment_artifact_ids,delivery'],
    ['empty-session-reference', id, { ...st, sessionId: '' }, 'session.send', sendPayload, 'MISSING_FIELD:session_id'],
    ['attach-claim-with-epoch', id, st, 'session.attach', { after_sequence: 0, request_write_owner: true }, 'ATTACKER_CLAIMED_EPOCH'],
    ['attach-read-without-epoch', id, { projectId: 'p', sessionId: 's', expectedRevision: 1 }, 'session.attach',
      { after_sequence: 0, request_write_owner: false }, 'MISSING_FIELD:writer_epoch'],
    ['write-without-project', id, { sessionId: 's', expectedRevision: 1, writerEpoch: 1 }, 'session.send', sendPayload, 'MISSING_FIELD:project_id'],
    ['model-change-incomplete-scope', { ...id, commandId: 'c' }, { projectId: 'p', sessionId: 's', expectedRevision: 1 }, 'host.configure',
      { config_revision: 1, provider_id: 'p', base_url: 'u', model_id: 'm', credential_ref: null }, 'CONFIGURATION_SCOPE_INCOMPLETE'],
    ['empty-payload-with-keys', id, st, 'host.status', { anything: 1 }, 'UNEXPECTED_PAYLOAD_KEYS:anything'],
  ];
  const refusalRows = [];
  for (const [name, i, s, method, payload, expect] of illegal) {
    const a = web.envelopeFor(i, s, method, payload);
    const b = shell.envelopeFor(i, s, method, payload);
    refusalRows.push({ name, web: a.reason || 'OK', shell: b.reason || 'OK', expected: expect,
      agree: a.reason === b.reason && a.reason === expect && a.ok === false && b.ok === false });
  }
  out.checks.refusals = { count: refusalRows.length, agree: refusalRows.filter(r => r.agree).length, rows: refusalRows };

  const replies = [
    { status: 200, body: '{"status":"COMPLETED","revision":8,"session_id":"sess-9","command_id":"c1"}' },
    { status: 202, body: { status: 'ACKNOWLEDGED' } },
    { status: 200, body: { status: 'IN_PROGRESS' } },
    { status: 422, body: { status: 'REJECTED', error_code: 'STALE_INPUT' } },
    { status: 501, body: { status: 'NOT_IMPLEMENTED' } },
    { status: 200, body: 'not json' },
    { status: 200, body: { status: 'WEIRD' } },
    { status: 0, error: 'connection refused' },
    null,
  ];
  out.checks.classify = {
    count: replies.length,
    agree: replies.filter(r => JSON.stringify(web.classify(r)) === JSON.stringify(shell.classify(r))).length,
    kinds: replies.map(r => web.classify(r).kind),
  };

  // The renderer client is behavioural, not textual: driven here with a recorder, it must refuse locally without
  // touching the network, must only re-baseline on a host reply that carries a revision, and must adopt ids only
  // from replies.
  const recorder = { sent: [], reply: { status: 200, body: { status: 'COMPLETED', revision: 42 } } };
  const fetcher = async (env) => { recorder.sent.push({ method: env.method, body: env.payload }); return recorder.reply; };
  const statuses = [];
  const mk = (state) => web.createV2Client({
    identity: { clientId: 'desktop-renderer', credential: 'tok' }, state, fetcher,
    onStatus: (s, m) => statuses.push({ kind: s.kind, method: m, reason: s.reason || null }),
  });

  const refusedClient = mk({ projectId: 'p1' });
  await refusedClient.send('session.send', { text: 'x' });
  out.checks.local_refusal_stops_the_command = { sent: recorder.sent.length, status: statuses[statuses.length - 1] };

  recorder.sent.length = 0;
  const baseClient = mk({ projectId: 'p1', sessionId: 's1', expectedRevision: 7, writerEpoch: 2 });
  const beforeRevision = baseClient.state().expectedRevision;
  await baseClient.send('session.control', { action: 'PAUSE', target_id: 'run-1', reason: 'x' });
  out.checks.completed_reply_rebaselines = { before: beforeRevision, after: baseClient.state().expectedRevision };

  recorder.reply = { status: 422, body: { status: 'REJECTED', error_code: 'STALE_INPUT', revision: 99 } };
  const held = baseClient.state().expectedRevision;
  await baseClient.send('session.control', { action: 'RESUME', target_id: 'run-1', reason: 'x' });
  out.checks.refused_write = { held, after: baseClient.state().expectedRevision };

  recorder.reply = { status: 200, body: { status: 'IN_PROGRESS' } };
  const heldIn = baseClient.state().expectedRevision;
  await baseClient.send('session.send', { text: 'q', attachment_artifact_ids: [], delivery: 'STEER' });
  out.checks.in_progress_reply = { held: heldIn, after: baseClient.state().expectedRevision };

  recorder.reply = { status: 200, body: { status: 'COMPLETED', result: { session_id: 'sess-in-result' }, revision: 5 } };
  const invented = mk({ projectId: 'p9' });
  await invented.send('host.status', {});
  out.checks.adopted_identity = { sessionIdFromResult: invented.state().sessionId || null, revision: invented.state().expectedRevision };

  recorder.reply = { status: 200, body: { status: 'COMPLETED', session_id: 'sess-on-envelope', revision: 6 } };
  const adopted = mk({ projectId: 'p9' });
  await adopted.send('host.status', {});
  out.checks.adopted_control = { sessionId: adopted.state().sessionId || null, revision: adopted.state().expectedRevision };

  recorder.reply = { status: 0, error: 'socket closed' };
  const lostBefore = baseClient.state().expectedRevision;
  await baseClient.send('session.send', { text: 'q', attachment_artifact_ids: [], delivery: 'NORMAL' });
  out.checks.transport_loss = { before: lostBefore, after: baseClient.state().expectedRevision,
    status: statuses[statuses.length - 1].kind };

  out.checks.producer_table = {
    methods: web.METHODS.length, producers: web.PRODUCERS.length,
    surfaces: Object.keys(web.SURFACES).length,
    missing_surface: web.METHODS.filter(m => !web.SURFACES[m]),
    extra_surface: Object.keys(web.SURFACES).filter(m => !web.CONTRACT[m]),
    duplicate_producers: web.PRODUCERS.length !== new Set(web.PRODUCERS).size,
  };
  out.checks.read_events_cursor = web.readEventsAfter(17);
  console.log(JSON.stringify(out));
})().catch((e) => { console.log(JSON.stringify({ checks: out.checks, errors: [String((e && e.stack) || e)] })); process.exit(3); });

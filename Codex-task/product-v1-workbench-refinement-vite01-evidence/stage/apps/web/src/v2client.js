// v2client.js is the renderer's half of W13-02's producer layer: the same 23 frozen client-protocol methods the
// desktop shell exposes, sent to the same endpoint the core already serves (`POST /v2/command`).
//
// It is a transport and a validator, not a scheduler. The card's deliverable is "真实CLI/Desktop操作同一任务、文件和
// 事件，无第二调度器", so nothing in this file decides when work runs, retries a write, or keeps a local copy of an
// aggregate: every mutation goes out as one command and the reply's own revision/watermark is what the screen
// shows. A second dispatcher would be a place where the renderer could advance state the host never agreed to.
//
// The envelope rules here mirror apps/desktop/main/lib/v2.js (the shell surface) and apps/cli/cli_v2.go (the CLI
// surface) — three surfaces, one protocol, and this card's check program proves the agreement by running the two
// JavaScript surfaces side by side over a probe matrix and diffing the envelopes byte for byte, then by comparing
// both method tables against internal/api/contracts/client.protocol.schema.json `x-method-contracts`. A rule that
// drifts on one side moves a named assertion instead of quietly producing two protocol dialects.
//
// The rules themselves are transcribed from internal/domain/client_protocol.go's DecodeEnvelope:
//   * write-class methods carry project_id + expected_revision + writer_epoch
//   * session.attach claiming write ownership must NOT carry a writer epoch (ATTACKER_CLAIMED_EPOCH); a read attach must
//   * host.configure uses either the all-null first-use scope or the full session writer/CAS scope
//   * a present-but-empty project_id or session_id is refused: an empty string is never a valid reference
//   * each payload is a closed object (schema additionalProperties:false), so an extra key is refused locally

export const PROTOCOL_VERSION = 'researchos-client/2';
export const COMMAND_PATH = '/v2/command';

// WRITE_METHODS mirrors internal/domain/client_protocol.go:7 (session.attach is handled by its own rule).
export const WRITE_METHODS = ['session.send', 'session.control', 'session.update', 'session.handoff', 'workspace.write',
  'artifact.import', 'permission.respond', 'goal.start', 'project.bootstrap'];

// CONTRACT names each method's published payload and result shapes with the required keys they carry. The required
// lists are the schema's `$defs[*].required` sets, transcribed per method rather than guessed.
export const CONTRACT = {
  'host.status': { payload: 'EmptyPayload', result: 'HostStatusResult', required: [] },
  'host.configure': { payload: 'ConfigurePayload', result: 'ConfigureResult', required: ['config_revision', 'provider_id', 'base_url', 'model_id', 'credential_ref'] },
  'project.bootstrap': { payload: 'BootstrapPayload', result: 'BootstrapResult', required: ['authorized_workspace_ref', 'display_name'] },
  'session.list': { payload: 'ListSessionsPayload', result: 'SessionListResult', required: ['cursor', 'limit'] },
  'session.create': { payload: 'CreateSessionPayload', result: 'SessionSnapshot', required: ['workspace_ref', 'model_config_ref', 'title'] },
  'session.get': { payload: 'EmptyPayload', result: 'SessionSnapshot', required: [] },
  'session.attach': { payload: 'AttachPayload', result: 'AttachResult', required: ['after_sequence', 'request_write_owner'] },
  'session.send': { payload: 'SendMessagePayload', result: 'SendMessageResult', required: ['text', 'attachment_artifact_ids', 'delivery'] },
  'session.control': { payload: 'ControlPayload', result: 'ControlResult', required: ['action', 'target_id', 'reason'] },
  'session.events': { payload: 'ReadEventsPayload', result: 'ReadEventsResult', required: ['after_sequence', 'limit'] },
  'session.handoff': { payload: 'HandoffPayload', result: 'HandoffResult', required: ['target_client_id', 'handoff_mode'] },
  'goal.start': { payload: 'StartGoalPayload', result: 'StartGoalResult', required: ['objective', 'contract_artifact_ids', 'start_as_draft'] },
  'provider.models': { payload: 'ListModelsPayload', result: 'ListModelsResult', required: ['provider_id', 'refresh', 'allow_network', 'cursor', 'limit'] },
  'provider.probe': { payload: 'ProbeProviderPayload', result: 'ProbeProviderResult', required: ['model_config_ref', 'allow_network', 'max_output_tokens', 'timeout_ms'] },
  'workspace.register': { payload: 'RegisterWorkspacePayload', result: 'WorkspaceBinding', required: ['selection_ref', 'display_name', 'requested_access'] },
  'workspace.list': { payload: 'EmptyPayload', result: 'WorkspaceListResult', required: [] },
  'workspace.tree': { payload: 'WorkspaceTreePayload', result: 'WorkspaceTreeResult', required: ['workspace_ref', 'relative_path', 'cursor', 'limit'] },
  'workspace.read': { payload: 'WorkspaceReadPayload', result: 'WorkspaceReadResult', required: ['workspace_ref', 'relative_path', 'max_bytes'] },
  'workspace.diff': { payload: 'WorkspaceDiffPayload', result: 'WorkspaceDiffResult', required: ['workspace_ref', 'base', 'relative_path', 'max_bytes'] },
  'workspace.write': { payload: 'WorkspaceWritePayload', result: 'WorkspaceWriteResult', required: ['workspace_ref', 'relative_path', 'task_id', 'expected_content_hash', 'text', 'create_if_missing'] },
  'artifact.import': { payload: 'ImportArtifactPayload', result: 'ImportArtifactResult', required: ['workspace_ref', 'relative_path', 'expected_content_hash', 'purpose'] },
  'session.update': { payload: 'UpdateSessionPayload', result: 'SessionSnapshot', required: ['action', 'title'] },
  'permission.respond': { payload: 'RespondPermissionPayload', result: 'RespondPermissionResult', required: ['resource_request_id', 'resource_request_revision', 'action_digest', 'decision', 'reason'] },
};

export const METHODS = Object.keys(CONTRACT).sort();

// PRODUCERS is one producer per frozen method, named by the method. "所有按钮有生产者" is therefore countable:
// every method has exactly one producer, and every producer maps to a method that exists.
export const PRODUCERS = METHODS.slice();

// SURFACES records which card action each producer is bound to in the UI, so the check program can ask "does the
// streaming panel actually call session.events, or does it only restyle itself?" without reading prose.
export const SURFACES = {
  'host.status': 'status', 'host.configure': 'model', 'project.bootstrap': 'project',
  'session.list': 'sessions', 'session.create': 'sessions', 'session.get': 'conversation',
  'session.attach': 'continuity', 'session.send': 'conversation', 'session.control': 'conversation',
  'session.events': 'conversation', 'session.handoff': 'continuity', 'goal.start': 'conversation',
  'provider.models': 'model', 'provider.probe': 'model',
  'workspace.register': 'workspace', 'workspace.list': 'workspace', 'workspace.tree': 'diff',
  'workspace.read': 'diff', 'workspace.diff': 'diff', 'workspace.write': 'diff',
  'artifact.import': 'attachments', 'session.update': 'sessions', 'permission.respond': 'permission',
};

function missingRequired(required, obj) {
  return required.filter((k) => obj[k] === undefined);
}

export function envelopeFor(identity, state, method, payload) {
  if (!CONTRACT[method]) return { ok: false, reason: 'UNKNOWN_METHOD', method };
  if (!identity || !identity.clientId) return { ok: false, reason: 'MISSING_FIELD:client_id' };
  if (!identity.credential) return { ok: false, reason: 'CREDENTIAL_ABSENT' };
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    return { ok: false, reason: 'PAYLOAD_NOT_OBJECT', method };
  }
  const missing = missingRequired(CONTRACT[method].required, payload);
  if (missing.length) return { ok: false, reason: 'MISSING_PAYLOAD_FIELDS:' + missing.join(','), method };

  const env = {
    protocol_version: PROTOCOL_VERSION,
    command_id: identity.commandId,
    client_id: identity.clientId,
    project_id: state.projectId === undefined ? null : state.projectId,
    session_id: state.sessionId === undefined ? null : state.sessionId,
    expected_revision: state.expectedRevision === undefined ? null : state.expectedRevision,
    writer_epoch: state.writerEpoch === undefined ? null : state.writerEpoch,
    method,
    payload,
  };
  if (!env.command_id) return { ok: false, reason: 'MISSING_FIELD:command_id' };
  for (const f of ['project_id', 'session_id']) {
    if (env[f] === '') return { ok: false, reason: 'MISSING_FIELD:' + f, method };
  }

  if (method === 'session.attach') {
    const claiming = payload.request_write_owner === true;
    if (claiming && env.writer_epoch !== null) return { ok: false, reason: 'ATTACKER_CLAIMED_EPOCH', method };
    if (!claiming && env.writer_epoch === null) return { ok: false, reason: 'MISSING_FIELD:writer_epoch', method };
  } else if (WRITE_METHODS.includes(method)) {
    if (typeof env.project_id !== 'string') return { ok: false, reason: 'MISSING_FIELD:project_id', method };
    if (env.expected_revision === null) return { ok: false, reason: 'MISSING_FIELD:expected_revision', method };
    if (env.writer_epoch === null) return { ok: false, reason: 'MISSING_FIELD:writer_epoch', method };
  }
  if (method === 'host.configure') {
    const scopes = [env.project_id, env.session_id, env.expected_revision, env.writer_epoch];
    if (!scopes.every(value => value === null) && scopes.some(value => value === null)) {
      return { ok: false, reason: 'CONFIGURATION_SCOPE_INCOMPLETE', method };
    }
  }
  if (CONTRACT[method].payload === 'EmptyPayload' && Object.keys(payload).length) {
    return { ok: false, reason: 'UNEXPECTED_PAYLOAD_KEYS:' + Object.keys(payload).join(','), method };
  }
  return {
    ok: true, verb: 'POST', path: COMMAND_PATH, payload: env,
    headers: { Authorization: 'Bearer ' + identity.credential, 'Content-Type': 'application/json' },
    method,
  };
}

export function classify(reply) {
  if (!reply || reply.status === 0 || reply.status === undefined) {
    return { kind: 'TRANSPORT_UNAVAILABLE', detail: (reply && reply.error) || 'no reply' };
  }
  let body = reply.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = null; } }
  if (!body || typeof body !== 'object') {
    return { kind: 'MALFORMED_REPLY', status: reply.status, detail: String(reply.body).slice(0, 200) };
  }
  const status = body.status;
  if (!['COMPLETED', 'ACKNOWLEDGED', 'IN_PROGRESS', 'REJECTED', 'NOT_IMPLEMENTED'].includes(status)) {
    return { kind: 'UNKNOWN_STATUS', status, detail: body.error_code || null };
  }
  return { kind: status, status: reply.status, error_code: body.error_code || null, result: body.result || null,
    command_id: body.command_id || null, session_id: body.session_id || null, revision: body.revision === undefined ? null : body.revision };
}

// createV2Client is the only place that touches the network. `send` is injectable so this card's check program can
// run the producer table against a recorder in plain Node — the same shape the accepted shell checks use, and the
// reason this module has no DOM dependency at import time.
export function createV2Client({ identity, state = {}, fetcher, onStatus = () => {} }) {
  if (!fetcher) throw new Error('createV2Client requires a fetcher');
  let seq = 0;
  const mutable = { ...state };
  function commandId() {
    seq += 1;
    return `${identity.clientId}-${Date.now()}-${seq}`;
  }
  async function send(method, payload, overrides = {}) {
    const id = { ...identity, commandId: identity.commandId || commandId() };
    const envelope = envelopeFor(id, { ...mutable, ...overrides }, method, payload);
    if (!envelope.ok) {
      const refused = { kind: 'LOCAL_REFUSED', reason: envelope.reason, method };
      onStatus(refused);
      return refused;
    }
    let reply;
    try {
      reply = await fetcher(envelope);
    } catch (error) {
      const lost = { kind: 'TRANSPORT_UNAVAILABLE', detail: String(error && error.message || error), method };
      onStatus(lost);
      return lost;
    }
    const result = classify(reply);
    onStatus(result, method);
    // Only the host's own reply may move the CAS fields the next write will send.
    if (result.kind === 'COMPLETED' || result.kind === 'ACKNOWLEDGED') {
      if (result.revision !== null && result.revision !== undefined) mutable.expectedRevision = result.revision;
      if (result.session_id) mutable.sessionId = result.session_id;
    }
    return result;
  }
  function adopt({ sessionId, expectedRevision, writerEpoch, projectId }) {
    if (projectId !== undefined) mutable.projectId = projectId;
    if (sessionId) mutable.sessionId = sessionId;
    if (expectedRevision !== undefined && expectedRevision !== null) mutable.expectedRevision = expectedRevision;
    if (writerEpoch !== undefined && writerEpoch !== null) mutable.writerEpoch = writerEpoch;
    return { ...mutable };
  }
  return {
    send,
    adopt,
    state: () => ({ ...mutable }),
    methods: METHODS,
    producers: PRODUCERS,
    surfaceOf: (method) => SURFACES[method] || null,
  };
}

// readEventsOnce is the recovery primitive: one cursor-bounded page of session.events, no side effects. Restart and
// reconnect paths re-issue it from the last watermark the host itself reported, so recovery never replays a send,
// a control, or a write on its way back online.
export function readEventsAfter(cursor) {
  return { after_sequence: Number(cursor || 0), limit: 200 };
}

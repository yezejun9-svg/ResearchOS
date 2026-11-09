// v2.js is W13-02's producer layer: the frozen client protocol's 23 methods, each with the payload contract it was
// published with, bound to the one endpoint the local core actually serves for them (`POST /v2/command`).
//
// Why this file exists instead of extending host.js's REST table: `internal/domain/http.go` registers its /v1
// operations from the OpenAPI contract, and 19 of the 23 protocol methods have no /v1 operation at all
// (measured against contracts/operation_coverage.json: only project.bootstrap→createGoal-style equivalents,
// session.events→streamEvents/listEvents, goal.start→createGoal and workspace.read→getArtifactContent have any v1
// face). The product contract's `local_protocol.methods` is the list this card must bind, and the core dispatches
// those names over the envelope endpoint, so a route added to the REST table would be a route to nothing.
//
// The envelope rules below are mirrors of internal/domain/client_protocol.go's DecodeEnvelope, transcribed from the
// file rather than guessed, because a doomed envelope should be refused here with a named reason rather than leave
// the renderer as an unexplained 400:
//   * write-class methods carry project_id + expected_revision + writer_epoch (session.attach is the exception below)
//   * session.attach claiming write ownership must NOT carry a writer epoch (ATTACKER_CLAIMED_EPOCH), while a read
//     attach must carry the observed epoch
//   * host.configure naming model_id or provider_id without a writer epoch is MODEL_CHANGE_WITHOUT_EPOCH, which is
//     the protocol-side half of "a model switch can never be silent"
//   * a present-but-empty project_id or session_id is refused: an empty string is never a valid reference
//   * each payload is a closed object, so an extra key is a local refusal rather than a field the core must catch
//
// The table is asserted against internal/api/contracts/client.protocol.schema.json by this card's check program
// (W1302-METHOD-TABLE-MATCHES-THE-FROZEN-SCHEMA), so a re-issued schema moves a named row instead of drifting silently.

const PROTOCOL_VERSION = 'researchos-client/2';
const COMMAND_PATH = '/v2/command';

// writeMethods mirrors internal/domain/client_protocol.go:7 (session.attach is handled by its own rule).
const WRITE_METHODS = ['session.send', 'session.control', 'session.update', 'session.handoff', 'workspace.write',
  'artifact.import', 'permission.respond', 'goal.start', 'project.bootstrap'];

// CONTRACT names each method's published payload and result shapes with the required keys they carry.
const CONTRACT = {
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

const METHODS = Object.keys(CONTRACT).sort();

// PRODUCERS is one entry per frozen protocol method, named by the method itself: the card's "所有按钮有生产者" is
// then a countable property (one channel per method, no extras, no gaps) rather than a slogan about the UI.
// Channels are namespaced `ros:v2:<method>` so they cannot collide with the eleven channels the accepted W13-01
// bridge registers, and `ipc.register()` keeps returning exactly that eleven.
const PRODUCERS = METHODS.slice();
const channelFor = (method) => 'ros:v2:' + method;

function bridgeFor(method) { return method; }

function missingRequired(required, obj) {
  return required.filter((k) => obj[k] === undefined);
}

// envelopeFor builds one command. `identity` is the shell's own client identity and the bearer it was given;
// `state` carries the references the method needs (project/session/revision/epoch), because the CAS fields belong
// to the session the user is looking at, not to a value the renderer may invent.
function envelopeFor(identity, state, method, payload) {
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
  // An empty string is never a valid reference, and the core refuses it; refusing here keeps the reason readable.
  for (const f of ['project_id', 'session_id']) {
    if (env[f] === '') return { ok: false, reason: 'MISSING_FIELD:' + f, method };
  }

  if (method === 'session.attach') {
    const claiming = payload.request_write_owner === true;
    if (claiming && env.writer_epoch !== null) return { ok: false, reason: 'ATTACKER_CLAIMED_EPOCH', method };
    if (!claiming && env.writer_epoch === null) return { ok: false, reason: 'MISSING_FIELD:writer_epoch', method };
  } else if (WRITE_METHODS.indexOf(method) >= 0 && method !== 'project.bootstrap') {
    if (typeof env.project_id !== 'string') return { ok: false, reason: 'MISSING_FIELD:project_id', method };
    if (env.expected_revision === null) return { ok: false, reason: 'MISSING_FIELD:expected_revision', method };
    if (env.writer_epoch === null) return { ok: false, reason: 'MISSING_FIELD:writer_epoch', method };
  }
  if (method === 'host.configure' && (Object.prototype.hasOwnProperty.call(payload, 'model_id') ||
    Object.prototype.hasOwnProperty.call(payload, 'provider_id')) && env.writer_epoch === null) {
    return { ok: false, reason: 'MODEL_CHANGE_WITHOUT_EPOCH', method };
  }
  // The published payloads are closed objects, so an unexpected key is a bug in this shell, not a question for the core.
  if (CONTRACT[method].payload === 'EmptyPayload' && Object.keys(payload).length) {
    return { ok: false, reason: 'UNEXPECTED_PAYLOAD_KEYS:' + Object.keys(payload).join(','), method };
  }
  return {
    ok: true, verb: 'POST', path: COMMAND_PATH, payload: env,
    headers: { Authorization: 'Bearer ' + identity.credential, 'Content-Type': 'application/json' },
    method, bridge: bridgeFor(method),
  };
}

// classify separates the five protocol statuses from a transport failure, because "the host refused", "the host is
// still working" and "nobody answered" are three different things to show a user.
function classify(reply) {
  if (!reply || reply.status === 0 || reply.status === undefined) {
    return { kind: 'TRANSPORT_UNAVAILABLE', detail: (reply && reply.error) || 'no reply' };
  }
  let body = reply.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = null; } }
  if (!body || typeof body !== 'object') {
    return { kind: 'MALFORMED_REPLY', status: reply.status, detail: String(reply.body).slice(0, 200) };
  }
  const status = body.status;
  if (['COMPLETED', 'ACKNOWLEDGED', 'IN_PROGRESS', 'REJECTED', 'NOT_IMPLEMENTED'].indexOf(status) < 0) {
    return { kind: 'UNKNOWN_STATUS', status, detail: body.error_code || null };
  }
  return { kind: status, status: reply.status, error_code: body.error_code || null, result: body.result || null,
    command_id: body.command_id || null, session_id: body.session_id || null, revision: body.revision === undefined ? null : body.revision };
}

module.exports = { PROTOCOL_VERSION, COMMAND_PATH, CONTRACT, METHODS, WRITE_METHODS, PRODUCERS, channelFor, bridgeFor, envelopeFor, classify };

// W13-01 IPC surface: one registration function that turns the routed clients in host.js into real
// desktop-prototype channels, and the single source of truth for what the preload bridge may expose.
//
// It takes ipcMain and its collaborators as arguments instead of requiring electron, so the check program can
// register the whole surface against a recorder and prove which channels exist, whether the core is started
// on demand, and that a provider that did not succeed is reported as a failure rather than painted green.
'use strict';

const host = require('./host.js');
const native = require('./native.js');
const v2 = require('./v2.js');
// Only Main holds this local call option. It is never decoded from an IPC body.
const AUTHORITY_READ = Symbol('qualification-authority-read');
const AUTHORITY_READ_METHODS = new Set(['session.get', 'host.status']);
// Only these protocol calls can be displaced by a newer display read. All
// other calls may change host/session state even when v2 does not require CAS.
const DISPLAY_READ_METHODS = new Set(['host.status', 'session.list', 'session.get',
  'session.events', 'workspace.list', 'workspace.tree', 'workspace.read', 'workspace.diff']);
const isDisplayRead = (method, payload) => DISPLAY_READ_METHODS.has(method) ||
  (method === 'provider.models' && payload?.refresh === false);

// The names the renderer may call. The preload file is checked against this list by tests/ui/check, so a
// channel added here without a bridge entry, or a bridge entry added without a handler, fails the suite.
const BRIDGE = [
  'statusHealth', 'statusHost',
  'workspaceList', 'workspaceRegister', 'workspacePickDirectory',
  'sessionList', 'sessionCreate', 'sessionSend',
  'providerModels', 'providerConfigure', 'providerProbe',
];

// method -> bridge name, mirroring ROUTES so one table drives both
const CHANNELS = {
  statusHealth: ['status', 'health'], statusHost: ['status', 'host'],
  workspaceList: ['workspace', 'list'], workspaceRegister: ['workspace', 'register'],
  workspacePickDirectory: ['workspace', 'pick_directory'],
  sessionList: ['session', 'list'], sessionCreate: ['session', 'create'], sessionSend: ['session', 'send'],
  providerModels: ['provider', 'models'], providerConfigure: ['provider', 'configure'],
  providerProbe: ['provider', 'probe'],
};

// Every client call begins by making sure a core is reachable, because the card promises install-and-run:
// the shell starts the local control host itself rather than telling the user to open a terminal.
async function callCore(deps, client, method, body) {
  const started = await host.ensureCore(deps);
  if (!started.discovery) {
    return { ok: false, reason: started.health, launched: started.launched, attempts: started.attempts.length };
  }
  let req;
  if (client === 'status' && method === 'health') {
    // /healthz is a public, empty observation. Fresh Native profiles need no
    // legacy principal file; caller fields cannot select a request or identity.
    const emptyBody = body == null || (typeof body === 'object' &&
      (Object.getPrototypeOf(body) === Object.prototype || Object.getPrototypeOf(body) === null) &&
      Reflect.ownKeys(body).length === 0);
    if (!emptyBody) return { ok: false, reason: 'EMPTY_HEALTH_REQUEST_REQUIRED', client, method };
    req = { verb: 'GET', path: '/healthz', payload: {}, headers: {} };
  } else {
    const principal = host.principalFor(deps.fsImpl, deps.principalFile);
    if (!principal.ok) return { ok: false, reason: principal.reason, detail: principal.detail || null };
    req = host.requestFor(client, method, body, principal.principal_id);
    if (!req.ok) return { ok: false, reason: req.reason, client, method };
  }
  const reply = await deps.transport(req.verb, started.discovery.url + req.path, req.payload, req.headers);
  if (client === 'provider' && method === 'probe') {
    const cls = host.classifyProvider(reply);
    return Object.assign({}, reply, cls);
  }
  if (reply && (reply.error || reply.status === 'ERROR')) {
    return Object.assign({ ok: false, reason: 'HOST_ERROR' }, reply);
  }
  return Object.assign({ ok: true }, reply);
}

// callV2 sends one client-protocol command. The eleven channels above are the accepted W13-01 surface and are not
// touched by W13-02; this is the second surface, because 19 of the 23 protocol methods have no REST operation at all
// and the shell must reach them over /v2/command instead of being wired to paths that answer nothing.
//
// The credential is never invented: deps.credential (or RESEARCHOS_HOST_CREDENTIAL) supplies a bearer the host
// issued, and its absence is reported as CREDENTIAL_ABSENT rather than as a completed action.
async function callV2Internal(deps, method, payload, localOrigin, readPurpose) {
  const state = deps.sessionState || {};
  const authorityRead = readPurpose === AUTHORITY_READ && AUTHORITY_READ_METHODS.has(method);
  const entryContext = [state.projectId, state.sessionId, state.expectedRevision, state.writerEpoch,
    state.writerClientId, state.writerExpiresAt, state.selectionGeneration, state.authorityGeneration];
  // This generation also records non-CAS activity that can change authority.
  const writes = (callV2.writeSequences ||= new WeakMap());
  const entryWriteSequence = writes.get(state) || 0;
  const lifetimes = (callV2.lifetimes ||= new WeakMap());
  if (!lifetimes.has(state)) lifetimes.set(state,new Map());
  const operations = lifetimes.get(state);
  const barrier = () => [...operations.values()].find(operation=>operation.activity || operation.write || operation.acknowledged);
  const entryBarrier = authorityRead && barrier();
  const contextUnchanged = () => [state.projectId, state.sessionId, state.expectedRevision, state.writerEpoch,
    state.writerClientId, state.writerExpiresAt, state.selectionGeneration, state.authorityGeneration]
    .every((value, index) => value === entryContext[index]);
  const started = await host.ensureCore(deps);
  if (!started.discovery) return { ok: false, reason: started.health, method };
  // Local-only receipt metadata. This is derived from native discovery, never
  // from a protocol response or a renderer-supplied request field.
  const nativeOrigin = discovery => {
    const key=JSON.stringify([native.hostInstanceId(deps.fsImpl,discovery),discovery.data_dir]);
    return {key,ref:require('node:crypto').createHash('sha256').update(key).digest('hex')};
  };
  let statusHostKey;
  const currentHostKey = () => {
    const latest=host.readDiscovery(deps.fsImpl,deps.discoveryFile);
    if (!latest.ok) return null;
    try { return nativeOrigin(latest.discovery).key; }
    catch { return null; }
  };
  if (method === 'host.status') {
    try { const origin=nativeOrigin(started.discovery); statusHostKey=origin.key; localOrigin.ref=origin.ref; }
    catch { return {ok:false,reason:'HOST_IDENTITY_UNAVAILABLE',method,dispatch_state:'NOT_SENT'}; }
  }
  const exact = await import('./wire-values.mjs');
  let payloadKey;
  try { payloadKey = exact.stringify(payload || {}); } catch { return {ok:false,reason:'INVALID_LOCAL_VALUE',method}; }
  // Command lifetime is independent of which read owns the presentation ticket.
  if (authorityRead && (entryBarrier || barrier() || !contextUnchanged() || (writes.get(state) || 0) !== entryWriteSequence))
    return {ok:false,reason:'STALE_RESPONSE',method};
  const write = v2.WRITE_METHODS.includes(method) || method === 'host.configure' || (method === 'session.attach' && payload?.request_write_owner === true);
  const presentationRead = !authorityRead && !write && isDisplayRead(method,payload);
  const activity = !authorityRead && !presentationRead;
  const pending = barrier();
  const replay = activity && pending && pending.method === method && pending.payloadKey === payloadKey;
  if (pending && activity && !replay) return {ok:false,reason:'COMMAND_PENDING',method,protocol_status:'ACKNOWLEDGED',dispatch_state:'NOT_SENT'};
  // The command belongs to a logical native host, not its current port/PID.
  // A replay against another data root or instance must stay unresolved.
  let hostKey;
  if (activity) {
    try { const bound=nativeOrigin(started.discovery);hostKey=bound.key;localOrigin.ref=replay ? pending.hostOriginRef : bound.ref; }
    catch { return {ok:false,reason:'HOST_IDENTITY_UNAVAILABLE',method,...(pending?{}:{dispatch_state:'NOT_SENT'})}; }
    if (replay && pending.hostKey !== hostKey) return {ok:false,reason:'HOST_CHANGED_PENDING',method,protocol_status:'ACKNOWLEDGED'};
  }
  // A readonly foreign writer snapshot is valid; it is never write authority.
  if (write && state.sessionId && method !== 'session.attach' && !replay &&
      (state.writerClientId !== (deps.clientId || 'desktop-shell') || !(Date.parse(state.writerExpiresAt) > Date.now()))) {
    return {ok:false,reason:'WRITE_OWNER_REQUIRED',method,dispatch_state:'NOT_SENT'};
  }
  let credential;
  try { credential = deps.credentialFor ? await deps.credentialFor(started.discovery) : (deps.credential || ''); }
  catch { return {ok:false,reason:'CREDENTIAL_UNAVAILABLE',method,...(pending?{}:{dispatch_state:'NOT_SENT'})}; }
  // A readonly status is authoritative only for the currently selected native
  // host. Credential renewal can yield while discovery changes to another host.
  if (method === 'host.status' && currentHostKey() !== statusHostKey)
    return {ok:false,reason:'HOST_CHANGED_BEFORE_SEND',method,dispatch_state:'NOT_SENT'};
  if (activity) {
    const latest=host.readDiscovery(deps.fsImpl,deps.discoveryFile);
    let latestKey;
    try { if (latest.ok) latestKey=nativeOrigin(latest.discovery).key; }
    catch { /* A replacement discovery cannot inherit this command. */ }
    if (latestKey !== hostKey) return {ok:false,reason:replay?'HOST_CHANGED_PENDING':'HOST_CHANGED_BEFORE_SEND',method,...(replay?{protocol_status:'ACKNOWLEDGED'}:{dispatch_state:'NOT_SENT'})};
  }
  const identity = {clientId:deps.clientId || 'desktop-shell',credential,
    commandId: replay ? pending.commandId : ((deps.commandIdFor && deps.commandIdFor(method)) || require('node:crypto').randomUUID())};
  // Credential acquisition can yield; another command may have reserved meanwhile.
  if (activity && barrier() !== pending) return {ok:false,reason:'COMMAND_PENDING',method,protocol_status:'ACKNOWLEDGED'};
  if (replay && pending.inFlight) return {ok:false,reason:'COMMAND_PENDING',method,protocol_status:'ACKNOWLEDGED'};
  const original = replay ? pending.original : {...state};
  // A selected project without a session is still first-use host configuration.
  // Keep an active session's full writer/CAS tuple for model changes.
  const envelopeState = method === 'host.status' || (method === 'host.configure' && state.sessionId == null)
    ? {projectId:null,sessionId:null,expectedRevision:null,writerEpoch:null}
    : method === 'session.list' ? {...state,sessionId:null,expectedRevision:null,writerEpoch:null}
    : method === 'session.attach' && payload?.request_write_owner === true ? {...state,writerEpoch:null} : state;
  const req = replay ? { ...pending.request, headers:{...pending.request.headers,Authorization:'Bearer '+credential} }
    : v2.envelopeFor(identity,envelopeState,method,payload || {});
  if (!req.ok) return {ok:false,reason:req.reason,method,...(replay?{}:{dispatch_state:'NOT_SENT'})};
  if (typeof deps.v2Transport !== 'function') return {ok:false,reason:'VALIDATOR_UNAVAILABLE',method,...(replay?{}:{dispatch_state:'NOT_SENT'})};
  let beforeSend;
  if (method==='session.create' && deps.nativeCreatePilot===true) {
    if (typeof deps.nativeCreateAttest!=='function') return {ok:false,reason:'NATIVE_CREATE_ATTESTATION_UNAVAILABLE',method,dispatch_state:'NOT_SENT'};
    const createHostIdentity=JSON.stringify([native.hostInstanceId(deps.fsImpl,started.discovery),
      started.discovery.url,started.discovery.data_dir,started.discovery.pid]);
    const verifyOrigin=()=>{
      const latest=host.readDiscovery(deps.fsImpl,deps.discoveryFile);
      let currentIdentity;
      try { if(latest.ok) currentIdentity=JSON.stringify([native.hostInstanceId(deps.fsImpl,latest.discovery),
        latest.discovery.url,latest.discovery.data_dir,latest.discovery.pid]); } catch { /* fail closed */ }
      return currentIdentity===createHostIdentity;
    };
    beforeSend=async(raw,headers)=>{
      const ref=await deps.nativeCreateAttest(started.discovery,raw,headers);
      if (!verifyOrigin()) throw Error('HOST_CHANGED_BEFORE_SEND');
      return ref;
    };
    beforeSend.verifyOrigin=verifyOrigin; // Main-only synchronous final-send guard.
  }
  // Presentation reads race only with newer reads of the same method. A Main
  // authority read has no presentation ticket and cannot be displaced by polls.
  const sequences = (callV2.sequences ||= new WeakMap());
  if (!sequences.has(state)) sequences.set(state,new Map());
  const sequence = sequences.get(state);
  const ticket = presentationRead ? (sequence.get(method) || 0) + 1 : null;
  if (presentationRead) sequence.set(method,ticket);
  const operation = replay ? pending : {method,payloadKey,commandId:identity.commandId,write,activity,hostKey,hostOriginRef:localOrigin.ref,original,possiblySent:false,
    request:{...req,headers:{'Content-Type':'application/json'}},acknowledged:false};
  operation.inFlight=true;operations.set(identity.commandId,operation);
  if (activity && !replay) writes.set(state,(writes.get(state) || 0) + 1);
  let reply;
  try { reply = beforeSend
    ? await deps.v2Transport(req.verb,started.discovery.url + req.path,req.payload,req.headers,beforeSend)
    : await deps.v2Transport(req.verb,started.discovery.url + req.path,req.payload,req.headers); }
  catch { operation.inFlight=false; operation.possiblySent=true; return {ok:false,reason:'TRANSPORT_FAILURE',method}; }
  operation.inFlight=false;
  // Keep the original response origin separate from the current selection.
  // Never deliver an old host's status as proof of a configuration on a new host.
  if (method === 'host.status' && currentHostKey() !== statusHostKey) {
    operations.delete(identity.commandId);
    return {ok:false,reason:'HOST_CHANGED_DURING_STATUS',method};
  }
  // Once any attempt may have reached HTTP, a later preflight refusal cannot
  // release the original command lifetime.
  if (reply?.dispatch_state !== 'NOT_SENT') operation.possiblySent=true;
  if (reply?.http_status === 401 && deps.credentialFor) {
    try { await deps.credentialFor(started.discovery,true); } catch { return {ok:false,reason:'AUTH_REFRESH_FAILED',method}; }
    return {ok:false,reason:'AUTH_REFRESHED_RETRY_REQUIRED',method};
  }
  if (!reply?.validated || !reply.ok) {
    const definitelyUnsent=reply?.dispatch_state === 'NOT_SENT' && !operation.possiblySent && !operation.acknowledged;
    if (definitelyUnsent || (!operation.activity && !operation.write && !operation.acknowledged)) operations.delete(identity.commandId);
    return {ok:false,reason:reply?.reason || 'MALFORMED_HOST_REPLY',http_status:reply?.http_status,method,...(definitelyUnsent ? {dispatch_state:'NOT_SENT'} : {})};
  }
  const body=reply.body;
  const tupleUnchanged = ['projectId','sessionId','expectedRevision','writerEpoch',
    'selectionGeneration','authorityGeneration'].every(key=>state[key]===original[key]);
  if (body.status==='ACKNOWLEDGED') {
    // Store only public command bytes/identity, never the bearer header.
    operation.acknowledged=true;
    state.pendingOperation=barrier();
    return {ok:true,completed:false,method,protocol_status:body.status,kind:body.status,result:body.result,revision:body.revision,requests:[method]};
  }
  if (body.status!=='COMPLETED' && body.status!=='REJECTED') return {ok:false,reason:'MALFORMED_HOST_REPLY',method};
  operations.delete(identity.commandId);
  if (barrier()) state.pendingOperation=barrier(); else delete state.pendingOperation;
  if (body.status==='REJECTED') return {ok:false,completed:false,method,protocol_status:body.status,kind:body.status,error_code:body.error_code,error:body.error,reason:body.error_code};
  if ((presentationRead && sequence.get(method)!==ticket) || !tupleUnchanged ||
      (authorityRead && (!contextUnchanged() || (writes.get(state) || 0) !== entryWriteSequence || barrier())))
    return {ok:false,reason:'STALE_RESPONSE',method,
    ...(method==='host.configure'?{local_terminal_result:body.result}:{})};
  const value=body.result;
  const snapshot = value?.snapshot || (['session.get','session.create','session.update'].includes(method) ? value : null);
  // A later GET cannot complete an earlier acknowledged attach/write command.
  if (!barrier() && snapshot && snapshot.project_id===state.projectId &&
      (snapshot.session_id===state.sessionId || method==='session.create')) {
    const candidate={projectId:snapshot.project_id,sessionId:snapshot.session_id,expectedRevision:snapshot.revision,
      writerEpoch:snapshot.writer?.epoch ?? null,writerClientId:snapshot.writer?.client_id ?? null,
      writerExpiresAt:snapshot.writer?.expires_at ?? null,eventSequence:snapshot.event_sequence};
    Object.assign(state,candidate);
  }
  return {ok:true,completed:true,method,bridge:req.bridge,protocol_status:body.status,kind:body.status,
    result:value,revision:body.revision,requests:[method]};
}

async function callV2(deps, method, payload, readPurpose) {
  const localOrigin={ref:null};
  const reply=await callV2Internal(deps,method,payload,localOrigin,readPurpose);
  if (method !== 'host.status' && method !== 'host.configure') return reply;
  return {...reply,local_host_origin:localOrigin.ref};
}

function registerDesktopReview(ipcMain, deps) {
  ipcMain.handle('ros:desktop:context', async () => {
    if (deps.contextStore && deps.sessionState.projectId && deps.sessionState.sessionId && !deps.contextVerified) {
      const candidate = Object.assign({}, deps.sessionState, { expectedRevision: null, writerEpoch: null });
      const reply = await callV2(Object.assign({}, deps, { sessionState: candidate }), 'session.get', {});
      if (reply.completed && reply.result?.project_id === candidate.projectId && reply.result?.session_id === candidate.sessionId) {
        Object.assign(deps.sessionState, candidate);
        deps.contextVerified = true;
      } else {
        return { project_id: deps.sessionState.projectId, session_id: null, restore_reason: reply.ok ? 'SESSION_ID_MISMATCH' : reply.reason || reply.protocol_status };
      }
    }
    return { project_id: deps.sessionState.projectId || null, session_id: deps.sessionState.sessionId || null };
  });
  ipcMain.handle('ros:desktop:selectProject', async (_event, body) => {
    const projectId = body?.project_id;
    if (typeof projectId !== 'string' || !projectId.trim() || projectId.length > 256) {
      return { ok: false, reason: 'PROJECT_ID_REQUIRED' };
    }
    if (deps.sessionState.projectId !== projectId.trim()) {
      const selected = { projectId: projectId.trim(), sessionId: null, expectedRevision: null, writerEpoch: null };
      try { if (deps.contextStore) deps.contextStore.save(selected); }
      catch { return { ok: false, reason: 'CONTEXT_STORE_FAILED' }; }
      Object.assign(deps.sessionState, selected);
      deps.contextVerified = true;
    }
    return { ok: true, project_id: deps.sessionState.projectId };
  });
  ipcMain.handle('ros:desktop:openSession', async (_event, body) => {
    const sessionId = body?.session_id;
    if (!deps.sessionState.projectId || typeof sessionId !== 'string' || !sessionId.trim() || sessionId.length > 256) {
      return { ok: false, reason: 'PROJECT_AND_SESSION_REQUIRED' };
    }
    const selected = Object.assign({}, deps.sessionState, { sessionId: sessionId.trim(), expectedRevision: null, writerEpoch: null });
    const reply = await callV2(Object.assign({}, deps, { sessionState: selected }), 'session.get', {});
    const snapshot = reply.result;
    if (reply.completed && snapshot?.session_id === selected.sessionId && snapshot?.project_id === selected.projectId) {
      try { if (deps.contextStore) deps.contextStore.save(selected); }
      catch { return { ok: false, reason: 'CONTEXT_STORE_FAILED' }; }
      Object.assign(deps.sessionState, selected);
      deps.contextVerified = true;
      return reply;
    }
    return reply.ok ? { ok: false, reason: 'SESSION_ID_MISMATCH' } : reply;
  });
  ipcMain.handle('ros:desktop:readArtifact', async (_event, body) => {
    if (!deps.sessionState.sessionId || !deps.sessionState.projectId) return { ok: false, reason: 'SESSION_NOT_SELECTED' };
    if (typeof deps.readArtifact !== 'function') return { ok: false, reason: 'ARTIFACT_READ_UNAVAILABLE' };
    return deps.readArtifact(body || {}, deps.sessionState.projectId);
  });
}

// Private Desktop intent surface. Renderer methods take no scope, token,
// request frame or request ID; main resolves the currently selected session.
function registerDesktopQualification(ipcMain, deps) {
  const guarded = action => async event => {
    if (!deps.qualifierSenderAllowed?.(event)) return { ok: false, reason: 'DESKTOP_ORIGIN_REQUIRED' };
    try {
      const result = await action();
      // The action can cross an async private/HTTP boundary. Check the native
      // host again at the last synchronous point before the IPC reply.
      return { ok: true, ...result, ...deps.desktopManagement.summary() };
    }
    catch (error) { return { ok: false, reason: error?.code || error?.message || 'QUALIFICATION_UNAVAILABLE' }; }
  };
  ipcMain.handle('ros:desktop:qualification:current', guarded(() => ({})));
  ipcMain.handle('ros:desktop:qualification:prepare', guarded(async () => {
    const scoped = await deps.prepareQualificationScope();
    return deps.desktopManagement.prepare(scoped.scope, scoped.context);
  }));
  ipcMain.handle('ros:desktop:qualification:confirm', guarded(() => deps.desktopManagement.confirm()));
  ipcMain.handle('ros:desktop:qualification:status', guarded(() => deps.desktopManagement.status()));
}

function registerDesktopCoding(ipcMain, deps) {
  const guarded = action => async (event, body) => {
    if (!deps.codingSenderAllowed?.(event)) return { ok: false, reason: 'DESKTOP_ORIGIN_REQUIRED' };
    try {
      const result = await action(event, body);
      return { ok: true, ...result, ...deps.desktopManagement.codingSummary() };
    } catch (error) { return { ok: false, reason: error?.code || error?.message || 'CODING_UNAVAILABLE' }; }
  };
  ipcMain.handle('ros:desktop:coding:current', guarded(() => deps.desktopManagement.codingSummary()));
  ipcMain.handle('ros:desktop:coding:pickToolchain', guarded(event => deps.pickCodingDirectory('toolchain', event)));
  ipcMain.handle('ros:desktop:coding:pickVendor', guarded(event => deps.pickCodingDirectory('vendor', event)));
  ipcMain.handle('ros:desktop:coding:prepare', guarded(async (_event, body) => {
    deps.desktopManagement.commandIdle();
    const scoped = await deps.prepareCodingScope(body);
    return deps.desktopManagement.prepareCoding(scoped.scope, scoped.context, scoped.review);
  }));
  ipcMain.handle('ros:desktop:coding:confirm', guarded(event =>
    deps.desktopManagement.confirmCoding(
      typeof deps.privilegedCodingConsent === 'function'
        ? frozen => deps.privilegedCodingConsent(event, frozen) : null,
      deps.recheckCodingScope)));
  ipcMain.handle('ros:desktop:coding:status', guarded(() => deps.desktopManagement.statusCoding()));
}

// registerV2 installs one channel per protocol method, named ros:v2:<method> so it cannot collide with an accepted
// channel. register() above still returns exactly the eleven it returned for W13-01, which is what the accepted
// W1301-ALL-CLIENT-CHANNELS-REGISTERED row measures; the v2 surface is measured by this card's own check.
function registerV2(ipcMain, deps) {
  const registered = [];
  v2.METHODS.forEach((method) => {
    ipcMain.handle(v2.channelFor(method), async (_event, body) => callV2(deps, method, body));
    registered.push(v2.channelFor(method));
  });
  return registered;
}

// A separate intent lane for the readonly Harness contract. No V2 Session,
// provider configuration, renderer authority or arbitrary URL is accepted.
function registerHarness(ipcMain, deps) {
  const crypto = require('node:crypto');
  const { validate } = require('./harness-wire.js');
  const journal = deps.harnessJournal || { entries: [], error: 'HARNESS_JOURNAL_UNAVAILABLE', replace() { throw new Error('HARNESS_JOURNAL_UNAVAILABLE'); } };
  const outstanding = new Map(journal.entries.map(entry => { const { projectId, bodySHA256, ...operation } = entry; return [projectId, operation]; }));
  const persist = () => journal.replace([...outstanding].map(([projectId, op]) => ({ projectId, ...op })));
  const allowed = event => deps.harnessSenderAllowed?.(event) === true;
  const error = (reason, outcome = 'NOT_SENT', pending = null) => ({ ok: false, reason, outcome, pending });
  const publicPending = op => op ? { kind: op.kind, request_id: op.requestId, state: op.state,
    task_ref: op.taskRef || null, workspace_ref: op.payload.workspace_ref || null, prompt: op.payload.prompt || null } : null;
  const keys = (value, required = [], optional = []) => {
    if (!value || typeof value !== 'object' || Array.isArray(value) || required.some(key => !Object.hasOwn(value, key)) ||
        Object.keys(value).some(key => !required.includes(key) && !optional.includes(key))) throw Object.assign(new Error(), { code: 'INVALID_REQUEST' });
  };
  const id = value => { if (typeof value !== 'string' || !value || value.length > 128) throw Object.assign(new Error(), { code: 'INVALID_REQUEST' }); return value; };
  const sameRef = (a, b) => a?.project_id === b?.project_id && a?.task_id === b?.task_id;
  const definiteRejection = reply => reply.outcome === 'REPLIED' && ['INVALID_REQUEST', 'HOST_AUTH_REQUIRED', 'FORBIDDEN', 'WORKSPACE_REVOKED', 'UNSUPPORTED_CAPABILITY', 'HARNESS_AUTH_REQUIRED', 'STATE_CONFLICT'].includes(reply.reason);
  const origin = discovery => deps.harnessOrigin ? deps.harnessOrigin(discovery) : JSON.stringify([native.hostInstanceId(deps.fsImpl, discovery), discovery.data_dir]);
  const currentOrigin = () => {
    if (deps.harnessCurrentOrigin) return deps.harnessCurrentOrigin();
    const latest = host.readDiscovery(deps.fsImpl, deps.discoveryFile);
    return latest.ok ? origin(latest.discovery) : null;
  };
  const targetUnchanged = discovery => {
    if (deps.harnessTargetUnchanged) return deps.harnessTargetUnchanged(discovery);
    if (deps.harnessCurrentOrigin) return true;
    const latest = host.readDiscovery(deps.fsImpl, deps.discoveryFile);
    return latest.ok && latest.discovery.url === discovery.url && latest.discovery.pid === discovery.pid && latest.discovery.data_dir === discovery.data_dir;
  };
  async function route(event, projectId, path, responseType, query, body, op) {
    const selection = deps.sessionState.selectionGeneration;
    const unchanged = () => allowed(event) && deps.sessionState.projectId === projectId && deps.sessionState.selectionGeneration === selection;
    const started = await (deps.harnessEnsureCore ? deps.harnessEnsureCore() : host.ensureCore(deps));
    if (!started.discovery) return error('HOST_UNAVAILABLE');
    let binding;
    try { binding = origin(started.discovery); } catch { return error('HOST_IDENTITY_UNAVAILABLE'); }
    if (op?.origin && op.origin !== binding) return error('HARNESS_HOST_CHANGED', 'UNKNOWN', publicPending(op));
    if (op) { op.origin = binding; persist(); }
    if (!unchanged() || currentOrigin() !== binding || !targetUnchanged(started.discovery)) return error('HARNESS_CONTEXT_CHANGED');
    let credential;
    try { credential = await deps.credentialFor(started.discovery); } catch { return error('HOST_AUTH_REQUIRED'); }
    const url = new URL('/harness/v1/' + path, started.discovery.url);
    for (const [key, value] of Object.entries(query || {})) if (value != null) url.searchParams.set(key, String(value));
    const reply = await deps.harnessWire({ url: url.href, method: body == null ? 'GET' : 'POST', body, credential, responseType,
      beforeSend: () => unchanged() && currentOrigin() === binding && targetUnchanged(started.discovery) });
    if (!unchanged() || currentOrigin() !== binding || !targetUnchanged(started.discovery)) return error('HARNESS_CONTEXT_CHANGED', reply.outcome === 'NOT_SENT' ? 'NOT_SENT' : 'UNKNOWN', publicPending(op));
    return reply;
  }
  const matchingSubmission = (task, op, projectId) => task?.task_ref?.project_id === projectId && task.request_id === op.requestId &&
    task.workspace_ref === op.payload.workspace_ref && task.prompt === op.payload.prompt && task.harness_id === 'codex';
  const install = (name, action) => ipcMain.handle('ros:harness:' + name, async (event, input) => {
    if (!allowed(event)) return error('DESKTOP_ORIGIN_REQUIRED');
    const projectId = deps.sessionState.projectId;
    if (typeof projectId !== 'string' || !projectId) return error('PROJECT_NOT_SELECTED');
    if (journal.error && ['submit', 'cancel', 'pending', 'reconcile'].includes(name)) return error(journal.error, 'UNKNOWN');
    try { return await action(event, input ?? {}, projectId); }
    catch (failure) { const op = outstanding.get(projectId); if (op) op.state = 'UNKNOWN'; return error(failure.code || 'HARNESS_UNAVAILABLE', op ? 'UNKNOWN' : 'NOT_SENT', publicPending(op)); }
  });
  install('capabilities', async (event, body, project) => { keys(body); return route(event, project, 'capabilities', 'CapabilitiesResponse'); });
  install('pending', async (_event, body, project) => { keys(body); return { ok: true, data: publicPending(outstanding.get(project)) }; });
  install('list', async (event, body, project) => {
    keys(body, [], ['cursor', 'limit']);
    validate('Decimal', body.cursor ?? '0');
    if (body.limit != null && (!Number.isInteger(body.limit) || body.limit < 1 || body.limit > 100)) return error('INVALID_REQUEST');
    const result = await route(event, project, 'tasks', 'ListResponse', { project_id: project, cursor: body.cursor ?? '0', limit: body.limit ?? 100 });
    if (result.ok && (result.data.lookup !== null || result.data.items.some(task => task.task_ref.project_id !== project))) return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN');
    return result;
  });
  install('get', async (event, body, project) => {
    keys(body, ['task_id']); id(body.task_id);
    const reply = await route(event, project, 'tasks/' + encodeURIComponent(body.task_id), 'TaskResponse', { project_id: project });
    if (reply.ok) {
      if (!sameRef(reply.data.task_ref, { project_id: project, task_id: body.task_id })) return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN');
      const op = outstanding.get(project);
      if (op?.kind === 'submit' && op.origin === currentOrigin() && matchingSubmission(reply.data, op, project)) { outstanding.delete(project); persist(); }
    }
    return reply;
  });
  install('events', async (event, body, project) => {
    keys(body, ['task_id', 'cursor'], ['limit']); id(body.task_id); validate('Decimal', body.cursor);
    if (body.limit != null && (!Number.isInteger(body.limit) || body.limit < 1 || body.limit > 500)) return error('INVALID_REQUEST');
    const reply = await route(event, project, 'tasks/' + encodeURIComponent(body.task_id) + '/events', 'EventsResponse', { project_id: project, cursor: body.cursor, limit: body.limit ?? 100 });
    const ref = { project_id: project, task_id: body.task_id };
    if (reply.ok && (!sameRef(reply.data.task_ref, ref) || reply.data.events.some(item => !sameRef(item.task_ref, ref)) || reply.data.snapshot && !sameRef(reply.data.snapshot.task_ref, ref))) return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN');
    return reply;
  });
  install('submit', async (event, body, project) => {
    keys(body, ['workspace_ref', 'prompt']);
    if (outstanding.has(project)) return error('HARNESS_REQUEST_PENDING', 'UNKNOWN', publicPending(outstanding.get(project)));
    const requestId = (deps.harnessRequestId || crypto.randomUUID)();
    const payload = { request_id: requestId, project_id: project, workspace_ref: body.workspace_ref, harness_id: 'codex', scope: 'workspace-read', prompt: body.prompt };
    validate('SubmitRequest', payload);
    if (!payload.prompt.trim()) return error('INVALID_REQUEST');
    const op = { kind: 'submit', requestId, payload, state: 'SENDING' };
    outstanding.set(project, op);
    const reply = await route(event, project, 'tasks', 'SubmitResponse', null, payload, op);
    if (reply.ok && (reply.data.request_id !== requestId || reply.data.task_ref.project_id !== project)) {
      op.state = 'UNKNOWN'; return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN', publicPending(op));
    }
    if (reply.ok) { op.state = 'ACKNOWLEDGED'; op.taskRef = reply.data.task_ref; }
    else if (reply.outcome === 'NOT_SENT' || definiteRejection(reply)) outstanding.delete(project);
    else op.state = 'UNKNOWN';
    persist();
    return { ...reply, pending: publicPending(outstanding.get(project)) };
  });
  install('cancel', async (event, body, project) => {
    keys(body, ['task_id', 'expected_task_revision', 'expected_run_id', 'expected_epoch']); id(body.task_id);
    if (outstanding.has(project)) return error('HARNESS_REQUEST_PENDING', 'UNKNOWN', publicPending(outstanding.get(project)));
    const { task_id: taskId, ...target } = body;
    const requestId = (deps.harnessRequestId || crypto.randomUUID)();
    const payload = { request_id: requestId, ...target };
    validate('CancelRequest', payload);
    if ((payload.expected_run_id === null) !== (payload.expected_epoch === null)) return error('INVALID_REQUEST');
    const op = { kind: 'cancel', requestId, payload, taskRef: { project_id: project, task_id: taskId }, state: 'SENDING' };
    outstanding.set(project, op);
    const reply = await route(event, project, 'tasks/' + encodeURIComponent(taskId) + '/cancel', 'CancelResponse', { project_id: project }, payload, op);
    if (reply.ok && !sameRef(reply.data.task.task_ref, op.taskRef)) { op.state = 'UNKNOWN'; return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN', publicPending(op)); }
    if (reply.ok || definiteRejection(reply) || reply.outcome === 'NOT_SENT') outstanding.delete(project);
    else op.state = 'UNKNOWN';
    persist();
    return { ...reply, pending: publicPending(outstanding.get(project)) };
  });
  install('reconcile', async (event, body, project) => {
    keys(body);
    const op = outstanding.get(project);
    if (!op) return { ok: true, data: { pending: null, task: null } };
    let task;
    if (op.kind === 'submit' && !op.taskRef) {
      const reply = await route(event, project, 'tasks', 'ListResponse', { project_id: project, request_id: op.requestId }, null, op);
      if (!reply.ok) return { ...reply, pending: publicPending(op) };
      if (reply.data.lookup?.request_id !== op.requestId) return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN', publicPending(op));
      if (reply.data.lookup.state === 'NOT_FOUND') return { ok: true, data: { pending: publicPending(op), task: null } };
      if (reply.data.items.length !== 1 || !matchingSubmission(reply.data.items[0], op, project)) return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN', publicPending(op));
      task = reply.data.items[0];
    } else {
      const reply = await route(event, project, 'tasks/' + encodeURIComponent(op.taskRef.task_id), 'TaskResponse', { project_id: project }, null, op);
      if (!reply.ok) return { ...reply, pending: publicPending(op) };
      task = reply.data;
      if (!sameRef(task.task_ref, op.taskRef) || op.kind === 'submit' && !matchingSubmission(task, op, project)) return error('HARNESS_REPLY_MISMATCH', 'UNKNOWN', publicPending(op));
      if (op.kind === 'cancel' && !task.terminal && task.status !== 'CANCEL_REQUESTED') return { ok: true, data: { pending: publicPending(op), task } };
    }
    outstanding.delete(project);
    persist();
    return { ok: true, data: { pending: null, task } };
  });
}

function register(ipcMain, deps) {
  const registered = [];
  Object.keys(CHANNELS).forEach((name) => {
    const route = CHANNELS[name];
    ipcMain.handle('ros:' + name, async (event, body) => {
      if (name === 'workspacePickDirectory' && typeof deps.pickDirectory === 'function') {
        return deps.pickDirectory(event, body);
      }
      return callCore(deps, route[0], route[1], body);
    });
    registered.push(name);
  });
  return registered;
}

module.exports = { BRIDGE, CHANNELS, AUTHORITY_READ, callCore, register, callV2, registerV2, registerDesktopReview,
  registerDesktopQualification, registerDesktopCoding, registerHarness, V2_METHODS: v2.METHODS };

// ResearchOS Desktop main (W13-01 increment on the W02-03 thin shell).
//
// It still does not start a second business scheduler: it discovers the existing Go control host, starts it
// when it is genuinely unreachable, and exposes the four native clients through the channels declared in
// main/lib/ipc.js. The registration and the routing are pure functions of injected collaborators, so
// tests/ui/check drives them without an Electron runtime; what only a real session can prove stays disclosed.
const { app, BrowserWindow, ipcMain, dialog, protocol } = require('electron');
const childProcess = require('node:child_process');
const crypto = require('node:crypto');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { TextDecoder } = require('node:util');
const host = require('./lib/host.js');
const ipc = require('./lib/ipc.js');
const { createTransport } = require('./lib/http-wire.js');
const { createHarnessWire, createPendingJournal } = require('./lib/harness-wire.js');
const native = require('./lib/native.js');
const { createAppProtocol, routeTable, APP_ORIGIN } = require('./lib/app-protocol.js');
const { chooseWorkspace } = require('./lib/first-use.js');
const { createContextStore } = require('./lib/context.js');
const { createDesktopManagement } = require('./lib/desktop-management.js');
const { publishOwnedHostLocator } = require('./lib/shared-host-locator.js');

protocol.registerSchemesAsPrivileged([{ scheme: 'ros-app', privileges: {
  standard: true, secure: true, supportFetchAPI: true, stream: true, corsEnabled: false,
} }]);
if (process.env.RESEARCHOS_DESKTOP_USER_DATA) {
  const isolatedUserData = path.resolve(process.env.RESEARCHOS_DESKTOP_USER_DATA);
  fs.mkdirSync(isolatedUserData, { recursive: true });
  app.setPath('userData', isolatedUserData);
}

const ROOT = path.resolve(__dirname, '..');
const validatedV2Transport = createTransport({ appRoot: ROOT });
const REPO = path.resolve(ROOT, '..', '..');
const WEB_DIST = path.join(REPO, 'apps', 'web', 'dist');
const DISCOVERY = path.resolve(REPO, process.env.RESEARCHOS_CLI_DISCOVERY ||
  process.env.RESEARCHOS_HOST_DISCOVERY || path.join('.local', 'v24_host.json'));
const PRINCIPAL = path.join(REPO, '.local', 'v24_principal.json');
const SMOKE = process.env.ROS_DESKTOP_SMOKE === '1';
const configuredCore = process.env.RESEARCHOS_CONTROL_EXE || '';
const coreExecutable = configuredCore ? path.resolve(REPO, configuredCore) : path.join(ROOT, 'resources', 'control', 'researchos-control.exe');
const dataRoot = path.resolve(REPO, process.env.RESEARCHOS_DATA_DIR || path.join('.local', 'data'));
const verifierManifest = process.env.RESEARCHOS_DESKTOP_VERIFIER_MANIFEST ||
  path.join(path.dirname(coreExecutable), 'runtime-verifier-installation.json');
const runtimeAssetsDir = process.env.RESEARCHOS_DESKTOP_RUNTIME_ASSETS_DIR ||
  path.join(path.dirname(coreExecutable), 'runtime');

// The smoke report must describe the same owned process observed on the
// private management channel. A healthy HTTP endpoint alone is insufficient.
function ownedCoreIdentity(machine) {
  if (machine.state !== 'READY') return null;
  try {
    const discovery = machine.currentHost();
    const identity = machine.identity;
    if (!identity || discovery.pid !== identity.PID || !machine.hostId) return null;
    return { pid: identity.PID, created_ns: identity.CreatedNS,
      image_sha256: identity.ImageSHA256, host_id: machine.hostId };
  } catch { return null; }
}

function smokeReadyEvidence(renderer, nativeProbe, management, started, owned) {
  return !!(renderer?.bridge && renderer.react_root && renderer.mounted_title &&
    renderer.navigation > 0 && nativeProbe?.ok === true &&
    management?.state === 'READY' && started?.health === 'UP' &&
    started.discovery?.pid === owned?.pid && owned?.pid > 0 &&
    typeof owned.created_ns === 'string' && /^[0-9]+$/.test(owned.created_ns) &&
    /^[a-f0-9]{64}$/.test(owned.image_sha256) && /^host-[a-f0-9]{12}$/.test(owned.host_id));
}

function smokeShutdownConfirmation(result, machine, owned) {
  const identity = machine.identity;
  if (result?.state !== 'STOPPED' || result.process_exit_confirmed !== true ||
      machine.state !== 'STOPPED' || machine.hasUnconfirmedChild() ||
      !identity || !owned || identity.PID !== owned.pid ||
      identity.CreatedNS !== owned.created_ns || identity.ImageSHA256 !== owned.image_sha256 ||
      machine.hostId !== owned.host_id) return null;
  return { process_exit_confirmed: true, owned_core_identity: owned };
}

// Main-only status observation must not compete with a renderer presentation
// ticket. The private lane retains host/context and pending-write validation.
async function smokeNativeProbe(dependencies) {
  const reply = await ipc.callV2(dependencies, 'host.status', {}, ipc.AUTHORITY_READ);
  return { ok: reply.ok === true, protocol_status: reply.protocol_status || null, reason: reply.reason || null };
}

const deps = {
  fsImpl: fs,
  httpImpl: http,
  // A normal Desktop may only launch an owned control through the inherited
  // private management pipes below. The older health route cannot spawn one.
  requireLaunchDisabled: true,
  discoveryFile: DISCOVERY,
  credentialFor: native.createCredentialProvider({ clientId: 'desktop-shell' }),
  nativeCreatePilot: process.env.RESEARCHOS_NATIVE_CREATE_PILOT === '1',
  nativeCreateAttest: native.createClientAttestor(),
  principalFile: PRINCIPAL,
  coreArgv: [],
  sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
  transport: (verb, url, payload, headers) => request(verb, url, payload, headers),
  pickDirectory: async (event, body) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    const picked = await dialog.showOpenDialog(win, { properties: ['openDirectory', 'createDirectory'], title: 'Choose the ResearchOS workspace' });
    if (picked.canceled || !picked.filePaths.length) return { ok: false, reason: 'PICKER_CANCELLED' };
    return ipc.callCore(deps, 'workspace', 'register', Object.assign({}, body || {}, { path: picked.filePaths[0] }));
  },
  readArtifact: async (ref, projectId) => {
    if (typeof ref.id !== 'string' || !ref.id || !/^sha256:[a-f0-9]{64}$/.test(ref.content_hash || '')) {
      return { ok: false, reason: 'ARTIFACT_REF_REQUIRED' };
    }
    const started = await host.ensureCore(deps);
    if (!started.discovery) return { ok: false, reason: started.health };
    let credential;
    try { credential = await deps.credentialFor(started.discovery); }
    catch (error) { return { ok: false, reason: String(error.message || error) }; }
    const url = new URL('/v1/projects/' + encodeURIComponent(projectId) + '/artifacts/' + encodeURIComponent(ref.id) + '/content', started.discovery.url);
    if (!['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)) return { ok: false, reason: 'NONLOCAL_HOST' };
    const reply = await requestArtifactText(url, credential, ref.content_hash);
    if (reply.reason === 'HTTP_401') {
      try { await deps.credentialFor(started.discovery, true); }
      catch (error) { return { ok: false, reason: 'AUTH_REFRESH_FAILED', detail: String(error.message || error) }; }
      return { ok: false, reason: 'AUTH_REFRESHED_RETRY_REQUIRED' };
    }
    return reply;
  },
};

function request(verb, url, payload, headers) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const body = payload && Object.keys(payload).length ? JSON.stringify(payload) : null;
    const req = http.request({
      hostname: u.hostname, port: u.port, path: u.pathname, method: verb, agent: false, timeout: 8000,
      headers: Object.assign({ 'content-type': 'application/json' }, headers || {},
        body ? { 'content-length': Buffer.byteLength(body) } : {}),
    }, (res) => {
      const parts = [];
      res.on('data', (c) => { parts.push(c); });
      res.on('end', () => {
        let text;
        try { text = new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(parts)); }
        catch { return resolve({ status: 'ERROR', error: 'MALFORMED_HOST_REPLY' }); }
        if (res.statusCode >= 400) return resolve({ status: 'ERROR', http_status: res.statusCode, error: 'HTTP_' + res.statusCode, body: text.slice(0, 400) });
        try { resolve(JSON.parse(text || '{}')); } catch { resolve({ status: 'ERROR', error: 'MALFORMED_HOST_REPLY' }); }
      });
    });
    req.on('error', (e) => resolve({ status: 'ERROR', error: String(e.code || e.message || e) }));
    req.on('timeout', () => { req.destroy(); resolve({ status: 'ERROR', error: 'TIMEOUT' }); });
    if (body) req.write(body);
    req.end();
  });
}

function requestArtifactText(url, credential, expectedHash) {
  const maxBytes = 1 << 20;
  return new Promise((resolve) => {
    const req = http.request(url, { method: 'GET', agent: false, timeout: 8000,
      headers: { Authorization: 'Bearer ' + credential, Accept: 'text/plain, text/markdown, application/json' } }, (res) => {
      if (res.statusCode !== 200) { res.resume(); resolve({ ok: false, reason: 'HTTP_' + res.statusCode }); return; }
      const mediaType = String(res.headers['content-type'] || '').split(';')[0].trim().toLowerCase();
      if (!['text/plain', 'text/markdown', 'application/json'].includes(mediaType)) {
        res.resume(); resolve({ ok: false, reason: 'TEXT_PREVIEW_UNAVAILABLE', media_type: mediaType }); return;
      }
      const parts = [];
      let length = 0;
      res.on('data', (part) => {
        length += part.length;
        if (length > maxBytes) { resolve({ ok: false, reason: 'ARTIFACT_TOO_LARGE' }); req.destroy(); return; }
        parts.push(part);
      });
      res.on('end', () => {
        if (length > maxBytes) { resolve({ ok: false, reason: 'ARTIFACT_TOO_LARGE' }); return; }
        const bytes = Buffer.concat(parts);
        const hash = 'sha256:' + crypto.createHash('sha256').update(bytes).digest('hex');
        if (hash !== expectedHash) { resolve({ ok: false, reason: 'ARTIFACT_HASH_MISMATCH' }); return; }
        try {
          resolve({ ok: true, content_hash: hash, media_type: mediaType, byte_size: bytes.length,
            text: new TextDecoder('utf-8', { fatal: true }).decode(bytes) });
        } catch { resolve({ ok: false, reason: 'ARTIFACT_NOT_UTF8' }); }
      });
    });
    req.on('error', (error) => resolve({ ok: false, reason: String(error.code || error.message || error) }));
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, reason: 'TIMEOUT' }); });
    req.end();
  });
}

ipc.register(ipcMain, deps);

// The main process alone reads the host's private session file and renews it over the native pipe.
// The renderer receives only protocol outcomes and session references.
const selectedState = {
  projectId: process.env.RESEARCHOS_PROJECT_ID || null,
  sessionId: process.env.RESEARCHOS_SESSION_ID || null,
  expectedRevision: null,
  writerEpoch: null,
  selectionGeneration: 0,
  authorityGeneration: 0,
};
const sessionState = new Proxy(selectedState, { set(target, key, value) {
  if (target[key] !== value) {
    if (key === 'projectId' || key === 'sessionId') target.selectionGeneration++;
    if (['expectedRevision', 'writerEpoch', 'writerClientId', 'writerExpiresAt'].includes(key)) target.authorityGeneration++;
  }
  target[key] = value; return true;
} });
const qualificationContext = () => JSON.stringify([
  sessionState.projectId, sessionState.sessionId,
  sessionState.expectedRevision == null ? null : String(sessionState.expectedRevision),
  sessionState.writerEpoch == null ? null : String(sessionState.writerEpoch),
  sessionState.writerClientId || null, sessionState.writerExpiresAt || null,
  sessionState.selectionGeneration, sessionState.authorityGeneration,
]);
// Raw startup diagnostics stay in the privileged main process and are bounded
// across all chunks. Renderer responses carry only stable error codes.
const managementDiagnostic = { chunks: [], bytes: 0, truncated: false };
const captureManagementDiagnostic = input => {
  const bytes = Buffer.from(input);
  const remaining = 8192 - managementDiagnostic.bytes;
  if (remaining > 0) {
    const kept = bytes.subarray(0, remaining);
    managementDiagnostic.chunks.push(kept); managementDiagnostic.bytes += kept.length;
  }
  if (bytes.length > remaining) managementDiagnostic.truncated = true;
};
const desktopManagement = createDesktopManagement({
  fsImpl: fs, spawn: childProcess.spawn, httpImpl: http, discoveryFile: DISCOVERY,
  dataRoot, controlExe: coreExecutable, verifierManifest, runtimeAssetsDir,
  webDir: WEB_DIST, cwd: REPO, context: qualificationContext,
  codingResourceGeneration: () => codingDirectories.generation,
  diagnostic: captureManagementDiagnostic,
});
const v2Deps = Object.assign({}, deps, {
  v2Transport: validatedV2Transport,
  clientId: 'desktop-shell',
  commandIdFor: () => crypto.randomUUID(),
  sessionState,
});

async function prepareQualificationScope() {
  if (!v2Deps.contextVerified || !sessionState.projectId || !sessionState.sessionId)
    throw Object.assign(new Error('SESSION_NOT_SELECTED'), { code: 'SESSION_NOT_SELECTED' });
  const projectId = sessionState.projectId, sessionId = sessionState.sessionId;
  const selectionGeneration = sessionState.selectionGeneration;
  desktopManagement.currentHost();
  const opened = await ipc.callV2(v2Deps, 'session.get', {}, ipc.AUTHORITY_READ);
  desktopManagement.currentHost();
  if (!opened?.completed || opened.result?.project_id !== projectId || opened.result?.session_id !== sessionId ||
      sessionState.projectId !== projectId || sessionState.sessionId !== sessionId ||
      sessionState.selectionGeneration !== selectionGeneration)
    throw Object.assign(new Error('SESSION_CHANGED'), { code: 'SESSION_CHANGED' });
  const snapshot = opened.result, context = qualificationContext();
  if (snapshot.writer?.client_id !== 'desktop-shell' || Date.parse(snapshot.writer?.expires_at) <= Date.now() ||
      String(snapshot.writer?.epoch) !== String(sessionState.writerEpoch) ||
      String(snapshot.revision) !== String(sessionState.expectedRevision))
    throw Object.assign(new Error('WRITE_OWNER_REQUIRED'), { code: 'WRITE_OWNER_REQUIRED' });
  const status = await ipc.callV2(v2Deps, 'host.status', {}, ipc.AUTHORITY_READ);
  const currentHost = desktopManagement.currentHost();
  if (qualificationContext() !== context || !status?.completed ||
      status.local_host_origin !== crypto.createHash('sha256').update(JSON.stringify([
        desktopManagement.hostId, currentHost.data_dir])).digest('hex'))
    throw Object.assign(new Error('HOST_OR_CONTEXT_CHANGED'), { code: 'HOST_OR_CONTEXT_CHANGED' });
  const modelRef = snapshot.model_config_ref;
  const model = status.result?.model_configurations?.find(item => item.model_config_ref === modelRef);
  if (!model || !model.provider_id || !model.model_id)
    throw Object.assign(new Error('SESSION_MODEL_UNAVAILABLE'), { code: 'SESSION_MODEL_UNAVAILABLE' });
  return { context, snapshot, hostStatus: status.result, scope: { projectId, sessionId, modelRef,
    model: { provider_id: model.provider_id, model_id: model.model_id } } };
}

const codingDirectories = { context: null, toolchain: null, vendor: null, generation: 0 };
async function pickCodingDirectory(kind, event) {
  desktopManagement.commandIdle();
  if (!sessionState.projectId || !sessionState.sessionId) throw Object.assign(new Error('SESSION_NOT_SELECTED'), { code: 'SESSION_NOT_SELECTED' });
  const selected = qualificationContext();
  const win = BrowserWindow.fromWebContents(event.sender);
  const picked = await dialog.showOpenDialog(win, { properties: ['openDirectory'],
    title: kind === 'toolchain' ? '选择已安装的 Go 工具链目录' : '选择离线 vendor 目录' });
  if (picked.canceled || picked.filePaths.length !== 1) return { cancelled: true };
  desktopManagement.commandIdle();
  if (qualificationContext() !== selected) throw Object.assign(new Error('CONTEXT_CHANGED'), { code: 'CONTEXT_CHANGED' });
  const directory = path.resolve(picked.filePaths[0]);
  if (codingDirectories.context !== selected) {
    codingDirectories.context = selected; codingDirectories.toolchain = null; codingDirectories.vendor = null;
  }
  codingDirectories[kind] = directory;
  codingDirectories.generation++;
  return { selected: true, name: path.basename(directory) };
}
async function prepareCodingScope(input) {
  const scoped = await prepareQualificationScope();
  if (!input || typeof input !== 'object' || Array.isArray(input) ||
      Object.keys(input).sort().join(',') !== 'checks,max_output_tokens,max_read_bytes,max_tool_calls,max_write_bytes,read_paths,write_paths')
    throw Object.assign(new Error('CODING_INPUT_INVALID'), { code: 'CODING_INPUT_INVALID' });
  if (codingDirectories.context !== scoped.context || !codingDirectories.toolchain)
    throw Object.assign(new Error('GO_TOOLCHAIN_SELECTION_REQUIRED'), { code: 'GO_TOOLCHAIN_SELECTION_REQUIRED' });
  if (!Array.isArray(input.checks) || input.checks.length < 1 || input.checks.length > 8 ||
      input.checks.some(check => !check || Object.keys(check).sort().join(',') !==
        'id,max_text_bytes,memory_mib,package,process_limit,source_paths,test_pattern,timeout_seconds'))
    throw Object.assign(new Error('CODING_CHECKS_INVALID'), { code: 'CODING_CHECKS_INVALID' });
  const coding = { client_id: 'desktop-shell', expected_revision: scoped.snapshot.revision,
    writer_epoch: scoped.snapshot.writer.epoch, config_revision: scoped.hostStatus.config_revision + 1,
    workspace_ref: scoped.snapshot.workspace_ref, read_paths: input.read_paths,
    write_paths: input.write_paths, max_read_bytes: input.max_read_bytes,
    max_write_bytes: input.max_write_bytes, max_tool_calls: input.max_tool_calls,
    max_output_tokens: input.max_output_tokens,
    checks: input.checks.map(check => ({ ...check, toolchain_root: codingDirectories.toolchain,
      ...(codingDirectories.vendor ? { vendor_root: codingDirectories.vendor } : {}) })) };
  if (![coding.expected_revision, coding.writer_epoch, coding.config_revision].every(Number.isSafeInteger) ||
      !coding.workspace_ref || coding.config_revision < 1)
    throw Object.assign(new Error('CODING_AUTHORITY_INVALID'), { code: 'CODING_AUTHORITY_INVALID' });
  const workspace = scoped.hostStatus.workspaces?.find(item =>
    item.authorized_workspace_ref === coding.workspace_ref && item.project_id === scoped.scope.projectId &&
    item.status === 'ACTIVE');
  if (!workspace || typeof workspace.display_name !== 'string' || !workspace.display_name.trim() ||
      typeof workspace.display_path !== 'string' || !workspace.display_path.trim() ||
      !Number.isSafeInteger(workspace.revision))
    throw Object.assign(new Error('CODING_WORKSPACE_DESCRIPTION_UNAVAILABLE'),
      { code: 'CODING_WORKSPACE_DESCRIPTION_UNAVAILABLE' });
  return { context: scoped.context, scope: { ...scoped.scope, coding },
    review: { resource_generation: codingDirectories.generation,
      workspace: { authorized_workspace_ref: workspace.authorized_workspace_ref,
      display_name: workspace.display_name, display_path: workspace.display_path,
      project_id: workspace.project_id, revision: workspace.revision,
      access: workspace.access, status: workspace.status } } };
}

function originalCodingInput() {
  const coding = desktopManagement.codingIntent?.scope;
  if (!coding) throw Object.assign(new Error('CODING_ORIGINAL_REQUEST_REQUIRED'),
    { code: 'CODING_ORIGINAL_REQUEST_REQUIRED' });
  return { read_paths: coding.read_paths, write_paths: coding.write_paths,
    max_read_bytes: coding.max_read_bytes, max_write_bytes: coding.max_write_bytes,
    max_tool_calls: coding.max_tool_calls, max_output_tokens: coding.max_output_tokens,
    checks: coding.checks.map(({ toolchain_root, vendor_root, ...check }) => check) };
}

async function privilegedCodingConsent(event, frozen) {
  const win = BrowserWindow.fromWebContents(event?.sender);
  if (!win || win.isDestroyed() || typeof dialog.showMessageBox !== 'function')
    throw Object.assign(new Error('PRIVILEGED_CONFIRM_UNAVAILABLE'), { code: 'PRIVILEGED_CONFIRM_UNAVAILABLE' });
  const lines = [
    `主机：${frozen.host_id}`,
    `主机数据目录：${frozen.data_root}`,
    `控制进程 PID ${frozen.control_process.PID}；桌面进程 PID ${frozen.parent_process.PID}`,
    `项目：${frozen.project_id}；会话：${frozen.session_id}；当前模型：${frozen.current_model_ref}`,
    `工作区：${frozen.workspace.display_name}`,
    `路径：${frozen.workspace.display_path}`,
    `工作区引用：${frozen.workspace.authorized_workspace_ref}；修订：${frozen.workspace.revision}；权限：${frozen.workspace.access}`,
    `可读：${frozen.scope.read_paths.join('、')}`,
    `可写：${frozen.scope.write_paths.join('、')}`,
    `单文件读取 ${frozen.scope.max_read_bytes} 字节；单文件写入 ${frozen.scope.max_write_bytes} 字节；工具调用上限 ${frozen.scope.max_tool_calls}；模型输出上限 ${frozen.scope.max_output_tokens} token`,
    `写入者 epoch ${frozen.scope.writer_epoch}；会话修订 ${frozen.scope.expected_revision}；配置修订 ${frozen.scope.config_revision}；客户端 ${frozen.scope.client_id}`,
    '普通模型调用上限 8 次；资格验证上限 1 次模型调用、0 次工具调用；当前模型调用 0 次',
    ...frozen.scope.checks.flatMap(check => [
      `检查 ${check.id}：${check.package}，${check.test_pattern}；源文件 ${check.source_paths.join('、')}`,
      `超时 ${check.timeout_seconds} 秒；进程 ${check.process_limit}；内存 ${check.memory_mib} MiB；文本 ${check.max_text_bytes} 字节`,
      `Go 工具链：${check.toolchain_root}；离线 vendor：${check.vendor_root || '无'}`,
    ]),
    ...frozen.frozen_checks.map(check =>
      `冻结 ${check.id}：源文件 ${check.source_count} 个/${check.source_bytes} 字节；源清单 ${check.source_manifest_hash}；Go ${check.toolchain_hash}；构建 ${check.build_hash}；vendor ${check.vendor_hash || '无'}`),
    `有效期至：${frozen.expires_at}`,
    '确认只保存编码配置；不会调用模型或执行检查。',
  ];
  const answer = await dialog.showMessageBox(win, { type: 'question',
    title: '确认冻结的工作区编码配置', message: '确认保存以下冻结范围？',
    detail: lines.join('\n'), buttons: ['确认保存', '取消'], defaultId: 1, cancelId: 1,
    noLink: true, normalizeAccessKeys: true });
  if (win.isDestroyed() || BrowserWindow.fromWebContents(event.sender) !== win)
    throw Object.assign(new Error('PRIVILEGED_CONFIRM_UNAVAILABLE'), { code: 'PRIVILEGED_CONFIRM_UNAVAILABLE' });
  return answer?.response === 0;
}

// The directory picker answers from the native dialog, so the first-run path never sends the user to a
// terminal to type a path.
async function boot() {
  const contextStore = createContextStore(path.join(app.getPath('userData'), 'desktop-context.json'));
  const saved = contextStore.load();
  if (!sessionState.projectId) sessionState.projectId = saved.projectId;
  if (!sessionState.sessionId && sessionState.projectId === saved.projectId) sessionState.sessionId = saved.sessionId;
  v2Deps.contextStore = contextStore;
  v2Deps.contextVerified = !sessionState.sessionId;
  ipc.registerV2(ipcMain, v2Deps);
  ipc.registerDesktopReview(ipcMain, v2Deps);
  ipc.registerHarness(ipcMain, { ...v2Deps, harnessWire: createHarnessWire({ httpImpl: http }),
    harnessJournal: createPendingJournal({ file: path.join(app.getPath('userData'), 'harness-pending.json') }),
    harnessSenderAllowed: event => {
      const url = event?.senderFrame?.url || '';
      return event?.senderFrame === event?.sender?.mainFrame &&
        (url === APP_ORIGIN + '/' || url.startsWith(APP_ORIGIN + '/'));
    },
  });
  ipc.registerDesktopQualification(ipcMain, {
    desktopManagement, prepareQualificationScope,
    qualifierSenderAllowed: event => {
      const url = event?.sender?.getURL?.() || '';
      return url === APP_ORIGIN + '/' || url.startsWith(APP_ORIGIN + '/');
    },
  });
  ipc.registerDesktopCoding(ipcMain, {
    desktopManagement, prepareCodingScope, pickCodingDirectory,
    privilegedCodingConsent,
    recheckCodingScope: () => prepareCodingScope(originalCodingInput()),
    codingSenderAllowed: event => {
      const url = event?.sender?.getURL?.() || '';
      return url === APP_ORIGIN + '/' || url.startsWith(APP_ORIGIN + '/');
    },
  });
  ipcMain.handle('ros:desktop:chooseWorkspace', (_event, body) => chooseWorkspace({
    host, native, callV2: ipc.callV2, deps: v2Deps, contextStore, sessionState,
  }, body));
  const routes = routeTable(require(path.join(REPO, 'spec', 'v2.0', 'contracts', 'openapi.json')));
  protocol.handle('ros-app', createAppProtocol({
    dist: WEB_DIST, routes, ensureCore: () => host.ensureCore(deps), credentialFor: deps.credentialFor,
  }));
  const management = await desktopManagement.start();
  let sharedHostLocator;
  try {
    sharedHostLocator = publishOwnedHostLocator({ management: desktopManagement,
      discoveryFile: DISCOVERY, dataRoot });
  } catch (error) {
    sharedHostLocator = { status: 'BLOCKED', reason: error.code || 'HOST_LOCATOR_PUBLISH_FAILED' };
  }
  const started = await host.ensureCore(deps);
  const win = new BrowserWindow({
    width: 1180, height: 760, title: 'ResearchOS', show: !SMOKE || !!process.env.ROS_DESKTOP_CAPTURE_PATH,
    webPreferences: { preload: path.join(ROOT, 'preload', 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, target) => {
    const destination = new URL(target);
    if (destination.protocol !== 'ros-app:' || destination.hostname !== 'desktop') event.preventDefault();
  });
  let closing = false;
  win.on('close', event => {
    if (closing || !desktopManagement.hasUnconfirmedChild()) return;
    event.preventDefault();
    if (desktopManagement.state !== 'READY') {
      dialog.showMessageBox(win, { type: 'warning', message: '当前主机无法安全退出',
        detail: desktopManagement.failure || '管理连接中断，主机进程退出尚未确认' });
      return;
    }
    desktopManagement.shutdown().then(() => {
      closing = true; win.close();
    }).catch(error => dialog.showMessageBox(win, { type: 'warning',
      message: '当前主机无法安全退出', detail: String(error.code || error.message || error) }));
  });
  await win.loadURL(process.env.ROS_DESKTOP_LEGACY_WORKBENCH === '1'
    ? 'file://' + path.join(__dirname, 'workbench.html').replaceAll('\\', '/') : APP_ORIGIN + '/');
  const renderer = await win.webContents.executeJavaScript(`({
    bridge: !!window.researchos?.desktop && !!window.researchos?.v2,
    review: !!document.getElementById('root') || (!!document.getElementById('review') && !!document.getElementById('review-open')),
    react_root: !!document.getElementById('root'),
    mounted_title: document.querySelector('#root h1')?.textContent || null,
    navigation: document.querySelectorAll('[aria-label="主导航"] a').length,
    status: document.getElementById('review-report')?.textContent || '',
    health: document.getElementById('host-health')?.textContent || ''
  })`);
  const nativeProbe = SMOKE
    ? await smokeNativeProbe(v2Deps)
    : null;
  const owned = ownedCoreIdentity(desktopManagement);
  const report = {
    event: 'ready_to_show', host_health: started.health, host_launched_by_shell: started.launched,
    spawns: started.spawns, host_url: started.discovery ? started.discovery.url : null,
    channels: ipc.BRIDGE.length, electron: process.versions.electron, protocol: 'researchos-client/2',
    renderer, native_probe: nativeProbe, pid: process.pid,
    owned_core_identity: owned,
    management_state: management.state, management_reason: management.reason || null,
    shared_host_locator: sharedHostLocator,
    management_diagnostic_bytes: managementDiagnostic.bytes,
    management_diagnostic_sha256: managementDiagnostic.bytes ? crypto.createHash('sha256').update(Buffer.concat(managementDiagnostic.chunks)).digest('hex') : null,
    management_diagnostic_truncated: managementDiagnostic.truncated,
  };
  if (SMOKE && process.env.ROS_DESKTOP_CAPTURE_PATH) {
    const capturePath = path.resolve(process.env.ROS_DESKTOP_CAPTURE_PATH);
    await win.webContents.executeJavaScript('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
    await new Promise(resolve => setTimeout(resolve, 400));
    await fs.promises.writeFile(capturePath, (await win.webContents.capturePage()).toPNG());
    report.capture_path = capturePath;
  }
  console.log('ROS_DESKTOP_REPORT ' + JSON.stringify(report));
  if (!SMOKE && sharedHostLocator.status === 'BLOCKED') {
    dialog.showMessageBox(win, { type: 'warning', message: '终端自动发现主机暂不可用',
      detail: '共享主机定位未能安全建立；现有数据和主机定位未被覆盖。原因：' + sharedHostLocator.reason });
  }
  if (SMOKE) {
    let code = smokeReadyEvidence(renderer, nativeProbe, management, started, owned) ? 0 : 2;
    if (desktopManagement.state === 'READY') {
      try {
        const stopped = await desktopManagement.shutdown();
        const confirmed = smokeShutdownConfirmation(stopped, desktopManagement, owned);
        if (confirmed) console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'shutdown_confirmed', ...confirmed }));
        else {
          code = 2;
          console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'shutdown_unconfirmed', reason: 'OWNED_EXIT_IDENTITY_UNCONFIRMED' }));
        }
      }
      catch (error) {
        code = 2;
        console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'shutdown_unconfirmed', reason: error.code || error.message }));
      }
    }
    if (desktopManagement.hasUnconfirmedChild()) {
      console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'shutdown_unconfirmed', reason: desktopManagement.failure || 'CONTROL_EXIT_UNCONFIRMED' }));
      return;
    }
    app.exit(code);
  }
}

app.whenReady().then(boot).catch(async (e) => {
  console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'boot_failed', error: String(e && e.message || e) }));
  if (desktopManagement.state === 'READY') {
    try { await desktopManagement.shutdown(); }
    catch (error) { console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'shutdown_unconfirmed', reason: error.code || error.message })); }
  }
  if (desktopManagement.hasUnconfirmedChild()) {
    console.log('ROS_DESKTOP_REPORT ' + JSON.stringify({ event: 'shutdown_unconfirmed', reason: desktopManagement.failure || 'CONTROL_EXIT_UNCONFIRMED' }));
    return;
  }
  app.exit(2);
});

module.exports = { ownedCoreIdentity, smokeReadyEvidence, smokeShutdownConfirmation };

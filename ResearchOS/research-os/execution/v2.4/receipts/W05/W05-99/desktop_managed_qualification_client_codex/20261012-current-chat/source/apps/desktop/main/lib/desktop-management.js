'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const childProcess = require('node:child_process');
const { TextDecoder } = require('node:util');
const host = require('./host.js');
const native = require('./native.js');

const PROTOCOL = 'researchos-desktop-management/1';
const FRAME_LIMIT = 65536;
const HASH = /^sha256:[a-f0-9]{64}$/;
const ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const DECIMAL = /^(0|[1-9][0-9]*)$/;
const START_LIMIT_MS = 15000;

function failure(code) { const e = new Error(code); e.code = code; return e; }
function object(value) { return value && typeof value === 'object' && !Array.isArray(value); }
function keys(value, required, optional = []) {
  if (!object(value)) throw failure('PRIVATE_FRAME_INVALID');
  const allowed = new Set([...required, ...optional]);
  if (required.some(name => !Object.hasOwn(value, name)) || Object.keys(value).some(name => !allowed.has(name)))
    throw failure('PRIVATE_FRAME_FIELDS');
}

// JSON.parse silently accepts duplicate keys and rounds large integers. The
// private pipe must reject both before any result can influence confirmation.
function strictJSON(bytes) {
  if (!Buffer.isBuffer(bytes) || !bytes.length || bytes.length > FRAME_LIMIT) throw failure('PRIVATE_FRAME_SIZE');
  let text;
  try { text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: false }).decode(bytes); }
  catch { throw failure('PRIVATE_FRAME_UTF8'); }
  if (text.charCodeAt(0) === 0xfeff) throw failure('PRIVATE_FRAME_UTF8');
  let i = 0, nodes = 0;
  const whitespace = () => { while (/[\x20\t\r\n]/.test(text[i] || '') && i < text.length) i++; };
  const string = () => {
    const start = i++;
    let escaped = false;
    while (i < text.length) {
      const c = text[i++];
      if (escaped) { escaped = false; continue; }
      if (c === '\\') { escaped = true; continue; }
      if (c === '"') {
        let value;
        try { value = JSON.parse(text.slice(start, i)); } catch { throw failure('PRIVATE_FRAME_JSON'); }
        for (let n = 0; n < value.length; n++) {
          const code = value.charCodeAt(n);
          if (code >= 0xd800 && code <= 0xdbff) {
            const next = value.charCodeAt(++n);
            if (!(next >= 0xdc00 && next <= 0xdfff)) throw failure('PRIVATE_FRAME_UNICODE');
          } else if (code >= 0xdc00 && code <= 0xdfff) throw failure('PRIVATE_FRAME_UNICODE');
        }
        return value;
      }
      if (c.charCodeAt(0) < 32) throw failure('PRIVATE_FRAME_JSON');
    }
    throw failure('PRIVATE_FRAME_JSON');
  };
  const value = depth => {
    if (++nodes > 10000 || depth > 64) throw failure('PRIVATE_FRAME_SIZE');
    whitespace(); const c = text[i];
    if (c === '"') return string();
    if (c === '{') {
      i++; whitespace(); const result = Object.create(null);
      if (text[i] === '}') { i++; return result; }
      for (;;) {
        whitespace(); if (text[i] !== '"') throw failure('PRIVATE_FRAME_JSON');
        const key = string(); if (Object.hasOwn(result, key)) throw failure('PRIVATE_FRAME_DUPLICATE');
        whitespace(); if (text[i++] !== ':') throw failure('PRIVATE_FRAME_JSON');
        result[key] = value(depth + 1); whitespace();
        const ending = text[i++]; if (ending === '}') return result;
        if (ending !== ',') throw failure('PRIVATE_FRAME_JSON');
      }
    }
    if (c === '[') {
      i++; whitespace(); const result = [];
      if (text[i] === ']') { i++; return result; }
      for (;;) {
        result.push(value(depth + 1)); whitespace();
        const ending = text[i++]; if (ending === ']') return result;
        if (ending !== ',') throw failure('PRIVATE_FRAME_JSON');
      }
    }
    for (const [word, parsed] of [['true', true], ['false', false], ['null', null]]) {
      if (text.startsWith(word, i)) { i += word.length; return parsed; }
    }
    const number = text.slice(i).match(/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/);
    if (!number) throw failure('PRIVATE_FRAME_JSON');
    i += number[0].length;
    const parsed = Number(number[0]);
    if (!DECIMAL.test(number[0]) && !/^-?[1-9][0-9]*$/.test(number[0])) throw failure('PRIVATE_FRAME_NUMBER');
    if (!Number.isSafeInteger(parsed)) throw failure('PRIVATE_FRAME_NUMBER');
    return parsed;
  };
  const parsed = value(0); whitespace();
  if (i !== text.length) throw failure('PRIVATE_FRAME_TRAILING');
  return parsed;
}

function exactFile(file, max, fsImpl = fs) {
  if (typeof file !== 'string' || !path.isAbsolute(file)) throw failure('INSTALLED_PATH_REQUIRED');
  let info, resolved;
  try { info = fsImpl.lstatSync(file); resolved = fsImpl.realpathSync.native(file); }
  catch { throw failure('INSTALLED_RESOURCE_UNAVAILABLE'); }
  if (!info.isFile() || info.isSymbolicLink() || info.size < 1 || info.size > max ||
      path.normalize(resolved).toLowerCase() !== path.normalize(file).toLowerCase())
    throw failure('INSTALLED_RESOURCE_REDIRECTED');
  return fsImpl.readFileSync(file);
}
function digest(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function installedResources({ controlExe, verifierManifest, runtimeAssetsDir, fsImpl = fs }) {
  const control = exactFile(controlExe, 128 << 20, fsImpl);
  if (control.subarray(0, 2).toString() !== 'MZ' || path.extname(controlExe).toLowerCase() !== '.exe')
    throw failure('CONTROL_INSTALLATION_INVALID');
  const manifest = strictJSON(exactFile(verifierManifest, 65536, fsImpl));
  keys(manifest, ['schema', 'service_id', 'protocol', 'executable', 'executable_hash', 'source_commit', 'arguments']);
  if (manifest.schema !== 'researchos.runtime-verifier-installation.v1' ||
      manifest.service_id !== 'researchos.runtime-qualification-verifier.v1' ||
      manifest.protocol !== 'researchos.runtime-verifier/1' || !Array.isArray(manifest.arguments) ||
      manifest.arguments.length || !/^[a-f0-9]{40}$/.test(manifest.source_commit) || !HASH.test(manifest.executable_hash))
    throw failure('VERIFIER_INSTALLATION_INVALID');
  const verifier = exactFile(manifest.executable, 128 << 20, fsImpl);
  if (verifier.subarray(0, 2).toString() !== 'MZ' || `sha256:${digest(verifier)}` !== manifest.executable_hash)
    throw failure('VERIFIER_INSTALLATION_CHANGED');
  if (typeof runtimeAssetsDir !== 'string' || !path.isAbsolute(runtimeAssetsDir)) throw failure('RUNTIME_ASSETS_REQUIRED');
  const metadata = strictJSON(exactFile(path.join(runtimeAssetsDir, 'mu-worker.mjs.build.json'), 65536, fsImpl));
  if (metadata.mu_commit !== '8dfebe36508ac0c2508735bb866756dab9283e74' ||
      metadata.vendored_files_verified !== 5083 || !/^[a-f0-9]{64}$/.test(metadata.source_sha256 || '') ||
      typeof metadata.sdk_version !== 'string' || !metadata.sdk_version ||
      typeof metadata.ai_version !== 'string' || !metadata.ai_version ||
      !/^[a-f0-9]{64}$/.test(metadata.bundle_sha256 || '') || !Number.isSafeInteger(metadata.bundle_bytes))
    throw failure('RUNTIME_ASSETS_INVALID');
  const bundle = exactFile(path.join(runtimeAssetsDir, 'mu-worker.mjs'), 128 << 20, fsImpl);
  const node = exactFile(path.join(runtimeAssetsDir, 'node.exe'), 256 << 20, fsImpl);
  if (bundle.length !== metadata.bundle_bytes || digest(bundle) !== metadata.bundle_sha256 ||
      node.subarray(0, 2).toString() !== 'MZ') throw failure('RUNTIME_ASSETS_CHANGED');
  return { controlHash: digest(control), verifierHash: digest(verifier), bundleHash: digest(bundle), nodeHash: digest(node) };
}

function observeWindowsProcess(pid, fsImpl = fs, execFileSync = childProcess.execFileSync) {
  if (!Number.isSafeInteger(pid) || pid < 1 || pid > 0xffffffff) throw failure('PROCESS_ID_INVALID');
  const powershell = path.join(process.env.SystemRoot || 'C:\\Windows', 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
  const script = `$ErrorActionPreference='Stop';[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);` +
    `try{$p=[System.Diagnostics.Process]::GetProcessById(${pid})}catch [System.ArgumentException]{exit 44};` +
    `$v=@{PID=$p.Id;FileTime=$p.StartTime.ToUniversalTime().ToFileTimeUtc().ToString();Image=$p.MainModule.FileName};` +
    `[Console]::Out.WriteLine(($v|ConvertTo-Json -Compress))`;
  let observed;
  try { observed = JSON.parse(execFileSync(powershell, ['-NoProfile', '-NonInteractive', '-Command', script],
    { encoding: 'utf8', windowsHide: true, timeout: 5000, maxBuffer: 8192 }).trim()); }
  catch (error) { throw failure(error.status === 44 ? 'PROCESS_NOT_FOUND' : 'PROCESS_IDENTITY_UNAVAILABLE'); }
  if (observed.PID !== pid || typeof observed.FileTime !== 'string' || !DECIMAL.test(observed.FileTime))
    throw failure('PROCESS_IDENTITY_INVALID');
  const ns = (BigInt(observed.FileTime) - 116444736000000000n) * 100n;
  if (ns <= 0n) throw failure('PROCESS_IDENTITY_INVALID');
  return { PID: pid, CreatedNS: ns.toString(), ImageSHA256: digest(exactFile(observed.Image, 256 << 20, fsImpl)) };
}

function validIdentity(value) {
  keys(value, ['PID', 'CreatedNS', 'ImageSHA256']);
  if (!Number.isSafeInteger(value.PID) || value.PID < 1 || value.PID > 0xffffffff ||
      typeof value.CreatedNS !== 'string' || !DECIMAL.test(value.CreatedNS) ||
      !/^[a-f0-9]{64}$/.test(value.ImageSHA256)) throw failure('READY_IDENTITY_INVALID');
  return value;
}
function sameIdentity(a, b) {
  return a.PID === b.PID && a.CreatedNS === b.CreatedNS && a.ImageSHA256 === b.ImageSHA256;
}

class DesktopManagement {
  constructor(options) {
    this.options = options;
    this.fsImpl = options.fsImpl || fs;
    this.observe = options.observeProcess || (pid => observeWindowsProcess(pid, this.fsImpl));
    this.spawn = options.spawn || childProcess.spawn;
    this.state = 'NOT_STARTED';
    this.child = null; this.hostId = null; this.identity = null;
    this.parentIdentity = null; this.pending = null; this.intent = null;
    this.buffer = Buffer.alloc(0); this.ready = null; this.failure = null;
    this.exitPromise = null; this.resolveExit = null; this.shutdownAccepted = false; this.childExited = true;
  }
  hasUnconfirmedChild() { return !!this.child && !this.childExited; }
  summary() {
    const intent = this.intent;
    if (!intent) return { available: this.state === 'READY', state: this.state, reason: this.failure };
    const same = this.sameContext(intent.context);
    return { available: this.state === 'READY', state: same ? intent.state : 'CONTEXT_CHANGED_PENDING',
      reason: this.failure, model: same ? intent.model : null, request_id: same ? intent.requestId : null,
      expires_at: same ? intent.expiresAt : null, model_calls: 1, tools: [], cost_basis: 'UNKNOWN', money: null,
      purpose: 'mu_turn', purpose_seconds: 600, consumed: !!intent.confirmSent,
      // A historical RESULT never proves that the current purpose is still valid.
      authorized: same && intent.state === 'QUALIFIED_PURPOSE_AUTHORIZED' && Date.now() - intent.checkedAt < 10000,
      checked_at: same && intent.checkedAt ? new Date(intent.checkedAt).toISOString() : null };
  }
  sameContext(expected) {
    try { return this.options.context() === expected; }
    catch { return false; }
  }
  currentHost() {
    if (!this.child || !this.identity || this.state !== 'READY') throw failure('MANAGEMENT_LINK_UNAVAILABLE');
    const actual = this.observe(this.child.pid);
    if (!sameIdentity(actual, this.identity)) throw failure('CONTROL_PROCESS_CHANGED');
    const parent = this.observe(process.pid);
    if (!sameIdentity(parent, this.parentIdentity)) throw failure('DESKTOP_PROCESS_CHANGED');
    const discovery = host.readDiscovery(this.fsImpl, this.options.discoveryFile);
    if (!discovery.ok) throw failure('HOST_DISCOVERY_UNAVAILABLE');
    const item = discovery.discovery;
    if (native.hostInstanceId(this.fsImpl, item) !== this.hostId || item.pid !== this.child.pid ||
        path.resolve(item.data_dir).toLowerCase() !== path.resolve(this.options.dataRoot).toLowerCase())
      throw failure('HOST_CHANGED');
    return item;
  }
  onLine(raw) {
    let frame;
    try { frame = strictJSON(raw); }
    catch (error) { this.broken(error.code || 'PRIVATE_FRAME_INVALID'); return; }
    if (this.state === 'STARTING') {
      try {
        keys(frame, ['protocol', 'kind', 'host_id', 'control_process', 'parent_process', 'mode', 'confirmation_ttl_seconds']);
        if (frame.protocol !== PROTOCOL || frame.kind !== 'READY' || frame.mode !== 'IN_PLACE' ||
            frame.confirmation_ttl_seconds !== 60 || !native.HOST_ID.test(frame.host_id)) throw failure('READY_INVALID');
        const child = validIdentity(frame.control_process), parent = validIdentity(frame.parent_process);
        if (!sameIdentity(child, this.observe(this.child.pid)) || !sameIdentity(parent, this.parentIdentity) ||
            child.PID !== this.child.pid || parent.PID !== process.pid) throw failure('READY_PROCESS_MISMATCH');
        this.identity = child; this.hostId = frame.host_id; this.state = 'READY';
        this.currentHost(); this.ready?.resolve(this.summary());
      } catch (error) { this.broken(error.code || 'READY_INVALID'); }
      return;
    }
    const pending = this.pending;
    if (!pending || this.state !== 'READY') { this.broken('UNEXPECTED_PRIVATE_REPLY'); return; }
    try {
      keys(frame, ['protocol', 'message_id', 'operation', 'host_id', 'kind', 'result'], ['error']);
      if (frame.protocol !== PROTOCOL || frame.message_id !== pending.messageId ||
          frame.operation !== pending.operation || frame.host_id !== this.hostId ||
          !['RESULT', 'ERROR'].includes(frame.kind) || (frame.kind === 'ERROR') !== Object.hasOwn(frame, 'error'))
        throw failure('PRIVATE_REPLY_MISMATCH');
      if (frame.kind === 'ERROR') {
        keys(frame.error, ['code', 'message']);
        if (frame.error.code !== 'MANAGEMENT_REJECTED' || typeof frame.error.message !== 'string')
          throw failure('PRIVATE_REPLY_ERROR');
      }
      this.pending = null; clearTimeout(pending.timer);
      pending.resolve(frame);
    } catch (error) { this.broken(error.code || 'PRIVATE_REPLY_INVALID'); }
  }
  onData(chunk) {
    if (!Buffer.isBuffer(chunk)) { this.broken('PRIVATE_FRAME_INVALID'); return; }
    this.buffer = Buffer.concat([this.buffer, chunk]);
    if (this.buffer.length > FRAME_LIMIT + 1 && this.buffer.indexOf(10) < 0) { this.broken('PRIVATE_FRAME_SIZE'); return; }
    for (;;) {
      const end = this.buffer.indexOf(10);
      if (end < 0) { if (this.buffer.length > FRAME_LIMIT + 1) this.broken('PRIVATE_FRAME_SIZE'); return; }
      const raw = this.buffer.subarray(0, end); this.buffer = this.buffer.subarray(end + 1);
      if (!raw.length || raw.length > FRAME_LIMIT) { this.broken('PRIVATE_FRAME_SIZE'); return; }
      this.onLine(raw); if (this.state === 'BROKEN') return;
    }
  }
  broken(reason) {
    if (this.state === 'BROKEN') return;
    this.state = 'BROKEN'; this.failure = reason;
    if (this.ready) { clearTimeout(this.ready.timer); this.ready.reject(failure(reason)); this.ready = null; }
    if (this.pending) { const pending = this.pending; this.pending = null; clearTimeout(pending.timer); pending.reject(failure(reason)); }
    if (this.intent?.confirmSent) this.intent.state = 'UNRESOLVED';
  }
  onExit(code, signal) {
    this.childExited = true;
    this.resolveExit?.({ code, signal });
    if (this.shutdownAccepted && code === 0 && !signal) {
      this.state = 'STOPPED'; this.failure = null;
    } else this.broken('CONTROL_EXITED');
  }
  async start() {
    if (this.state !== 'NOT_STARTED') return this.summary();
    const o = this.options;
    try {
      const installed = installedResources({ controlExe: o.controlExe, verifierManifest: o.verifierManifest,
        runtimeAssetsDir: o.runtimeAssetsDir, fsImpl: this.fsImpl });
      if (!path.isAbsolute(o.dataRoot) || !path.isAbsolute(o.discoveryFile) || !path.isAbsolute(o.webDir))
        throw failure('MANAGED_PATH_REQUIRED');
      const existing = host.readDiscovery(this.fsImpl, o.discoveryFile);
      if (existing.ok) {
        let alive = true;
        try { this.observe(existing.discovery.pid); } catch (error) { if (error.code === 'PROCESS_NOT_FOUND') alive = false; else throw error; }
        const health = await host.probe(o.httpImpl, existing.discovery.url, host.ROUTES.status.health[1], 1500);
        if (alive || health.status === 200) throw failure('EXTERNAL_HOST_PRESENT');
      } else if (this.fsImpl.existsSync(o.discoveryFile)) throw failure('DISCOVERY_UNCERTAIN');
      this.parentIdentity = this.observe(process.pid);
      if (this.parentIdentity.PID !== process.pid) throw failure('DESKTOP_PROCESS_CHANGED');
      const env = {};
      for (const name of ['SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA'])
        if (process.env[name]) env[name] = process.env[name];
      Object.assign(env, { RESEARCHOS_DATA_DIR: o.dataRoot, RESEARCHOS_WEB_DIR: o.webDir, RESEARCHOS_LISTEN: '127.0.0.1:0' });
      this.state = 'STARTING';
      const readyPromise = new Promise((resolve, reject) => {
        const timer = setTimeout(() => this.broken('READY_TIMEOUT'), START_LIMIT_MS);
        this.ready = { resolve, reject, timer };
      });
      readyPromise.catch(() => {});
      this.child = this.spawn(o.controlExe, ['--desktop-management-stdio', '--runtime-verifier-manifest', o.verifierManifest,
        '--discovery-file', o.discoveryFile, '--runtime-assets-dir', o.runtimeAssetsDir],
      { cwd: o.cwd, env, detached: false, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
      if (!this.child || !Number.isSafeInteger(this.child.pid) || !this.child.stdin || !this.child.stdout)
        throw failure('CONTROL_SPAWN_FAILED');
      this.childExited = false;
      this.exitPromise = new Promise(resolve => { this.resolveExit = resolve; });
      this.child.stdout.on('data', bytes => this.onData(bytes));
      this.child.stdout.on('end', () => this.broken('MANAGEMENT_PIPE_EOF'));
      this.child.stdout.on('error', () => this.broken('MANAGEMENT_PIPE_ERROR'));
      this.child.stdin.on('error', () => this.broken('MANAGEMENT_PIPE_ERROR'));
      this.child.on('exit', (code, signal) => this.onExit(code, signal));
      this.child.on('error', () => this.broken('CONTROL_SPAWN_FAILED'));
      // Diagnostics remain private to main and bounded. They are never a protocol response.
      this.child.stderr?.on('data', bytes => { o.diagnostic?.(String(bytes).slice(0, 1024)); });
      const result = await readyPromise;
      if (this.ready) { clearTimeout(this.ready.timer); this.ready = null; }
      if (installed.controlHash !== this.identity.ImageSHA256) throw failure('CONTROL_IMAGE_CHANGED');
      this.currentHost();
      return result;
    } catch (error) {
      this.broken(error.code || 'MANAGEMENT_START_FAILED');
      return this.summary();
    }
  }
  async exchange(operation, scope, timeoutMs) {
    this.currentHost();
    if (this.pending) throw failure('MANAGEMENT_COMMAND_PENDING');
    const messageId = crypto.randomUUID();
    const request = { protocol: PROTOCOL, message_id: messageId, operation, host_id: this.hostId, ...scope };
    const bytes = Buffer.from(JSON.stringify(request) + '\n');
    if (bytes.length - 1 > FRAME_LIMIT) throw failure('PRIVATE_FRAME_SIZE');
    return new Promise((resolve, reject) => {
      const pending = { messageId, operation, resolve, reject, timer: null };
      this.pending = pending;
      pending.timer = setTimeout(() => {
        // A timed-out write may already be executing. Keep the barrier until a
        // late terminal reply or process exit; never issue a second CONFIRM.
        pending.timedOut = true; reject(failure('MANAGEMENT_REPLY_UNCERTAIN'));
      }, timeoutMs);
      try { this.child.stdin.write(bytes, error => { if (error) this.broken('MANAGEMENT_PIPE_ERROR'); }); }
      catch { this.broken('MANAGEMENT_PIPE_ERROR'); }
    }).then(reply => { if (operation !== 'SHUTDOWN') this.currentHost(); return reply; });
  }
  async prepare(scope, context) {
    if (this.intent && (this.intent.confirmSent || this.intent.state !== 'EXPIRED'))
      throw failure('QUALIFICATION_INTENT_PENDING');
    if (!this.sameContext(context)) throw failure('CONTEXT_CHANGED');
    const { projectId, sessionId, modelRef, model } = scope;
    if (![projectId, sessionId, modelRef].every(v => typeof v === 'string' && ID.test(v)))
      throw failure('QUALIFICATION_SCOPE_INVALID');
    const reply = await this.exchange('PREPARE', { project_id: projectId, session_id: sessionId,
      model_config_ref: modelRef }, 30000);
    if (!this.sameContext(context)) throw failure('CONTEXT_CHANGED');
    if (reply.kind !== 'RESULT') throw failure('PREPARE_REJECTED');
    const value = reply.result, request = value?.request;
    if (!object(value) || value.state !== 'AWAITING_CONFIRMATION' || value.model_calls !== 1 ||
        !Array.isArray(value.tools) || value.tools.length || value.purpose !== 'mu_turn' ||
        value.purpose_seconds !== 600 || value.cost_basis !== 'UNKNOWN' || value.money !== null ||
        !object(request) || typeof request.request_id !== 'string' || !ID.test(request.request_id) ||
        request.project_id !== projectId || request.session_id !== sessionId ||
        request.model_config_ref !== modelRef || request.owner_host !== this.hostId ||
        request.authorize_purpose !== 'mu_turn' || !HASH.test(value.request_hash))
      throw failure('PREPARE_RESULT_INVALID');
    const issued = Date.parse(request.issued_at), expires = Date.parse(request.expires_at), now = Date.now();
    if (!Number.isFinite(issued) || !Number.isFinite(expires) || issued > now || expires <= now ||
        expires <= issued || expires - issued > 60000) throw failure('PREPARE_EXPIRED');
    this.intent = { state: 'AWAITING_CONFIRMATION', context, projectId, sessionId, modelRef, model,
      requestId: request.request_id, requestHash: value.request_hash, expiresAt: request.expires_at,
      confirmedAt: null, checkedAt: 0, confirmSent: false };
    return this.summary();
  }
  async confirm() {
    const intent = this.intent;
    if (!intent || intent.confirmSent || intent.state !== 'AWAITING_CONFIRMATION') throw failure('CONFIRM_NOT_AVAILABLE');
    if (!this.sameContext(intent.context)) throw failure('CONTEXT_CHANGED');
    if (!(Date.parse(intent.expiresAt) > Date.now())) { intent.state = 'EXPIRED'; throw failure('CONFIRM_EXPIRED'); }
    this.currentHost();
    intent.confirmSent = true; intent.state = 'CONFIRM_SENT';
    try {
      const reply = await this.exchange('CONFIRM', { project_id: intent.projectId, request_id: intent.requestId,
        request_hash: intent.requestHash }, 195000);
      if (reply.kind !== 'RESULT') { intent.state = 'UNRESOLVED'; throw failure('CONFIRM_REJECTED_CHECK_STATUS'); }
      intent.state = 'EXECUTION_SETTLED'; intent.confirmedAt = Date.now();
      // The confirmation reply is historical; only STATUS rechecks current purpose.
      return await this.status();
    } catch (error) { if (intent.state === 'CONFIRM_SENT') intent.state = 'UNRESOLVED'; throw error; }
  }
  async status() {
    const intent = this.intent;
    if (!intent) throw failure('STATUS_ORIGINAL_REQUEST_REQUIRED');
    if (!this.sameContext(intent.context)) throw failure('CONTEXT_CHANGED');
    const reply = await this.exchange('STATUS', { project_id: intent.projectId,
      request_id: intent.requestId, request_hash: intent.requestHash }, 30000);
    if (!this.sameContext(intent.context)) throw failure('CONTEXT_CHANGED');
    if (reply.kind !== 'RESULT') throw failure('STATUS_REJECTED');
    const value = reply.result;
    if (!object(value) || value.request_id !== intent.requestId || value.request_hash !== intent.requestHash ||
        !['AWAITING_CONFIRMATION', 'EXPIRED', 'UNRESOLVED', 'EXECUTION_SETTLED', 'QUALIFIED_PURPOSE_AUTHORIZED'].includes(value.state) ||
        typeof value.consumed !== 'boolean') throw failure('STATUS_RESULT_INVALID');
    intent.state = value.state; intent.checkedAt = Date.now();
    if (value.consumed) intent.confirmSent = true;
    return this.summary();
  }
  async shutdown() {
    if (this.state === 'STOPPED') return { state: 'STOPPED', process_exit_confirmed: true };
    if (this.state !== 'READY') throw failure('SAFE_SHUTDOWN_UNAVAILABLE');
    const reply = await this.exchange('SHUTDOWN', {}, 30000);
    if (reply.kind !== 'RESULT' || reply.result?.state !== 'SHUTDOWN_ACCEPTED')
      throw failure('SHUTDOWN_REFUSED');
    this.shutdownAccepted = true;
    let timer;
    let outcome;
    try {
      outcome = await Promise.race([
        this.exitPromise,
        new Promise((_, reject) => { timer = setTimeout(() => reject(failure('SHUTDOWN_EXIT_UNCONFIRMED')), 15000); }),
      ]);
    } finally { clearTimeout(timer); }
    if (outcome.code !== 0 || outcome.signal || this.state !== 'STOPPED')
      throw failure('SHUTDOWN_EXIT_UNCONFIRMED');
    return { state: 'STOPPED', process_exit_confirmed: true };
  }
}

function createDesktopManagement(options) { return new DesktopManagement(options); }
module.exports = { PROTOCOL, FRAME_LIMIT, strictJSON, installedResources, observeWindowsProcess,
  createDesktopManagement, DesktopManagement };

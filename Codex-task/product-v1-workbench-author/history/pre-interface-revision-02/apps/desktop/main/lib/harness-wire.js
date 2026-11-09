'use strict';
const http = require('node:http');
const fs = require('node:fs');
const crypto = require('node:crypto');
const { TextDecoder } = require('node:util');
const { privateJSON } = require('./http-wire.js');
// Frozen researchos.host-harness.v1 revision1, not the legacy V2 wire lane.
const CONTRACT_SHA256 = '90d235a5ea83ecd282ae0490708e81d76a244947b90d4841b6a9da50bbc2cc66';
const DEFINITIONS = {"Decimal":{"type":"string","pattern":"^(0|[1-9][0-9]{0,18})$","x-int64-max":"9223372036854775807"},"PositiveDecimal":{"type":"string","pattern":"^[1-9][0-9]{0,18}$","x-int64-max":"9223372036854775807"},"TaskRef":{"type":"object","additionalProperties":false,"properties":{"project_id":{"type":"string","minLength":1,"maxLength":128},"task_id":{"type":"string","minLength":1,"maxLength":128}},"required":["project_id","task_id"]},"RunRef":{"type":"object","additionalProperties":false,"properties":{"run_id":{"type":"string","minLength":1,"maxLength":128},"epoch":{"$ref":"#/$defs/PositiveDecimal"}},"required":["run_id","epoch"]},"RequestID":{"type":"string","pattern":"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"},"Error":{"type":"object","additionalProperties":false,"properties":{"code":{"enum":["INVALID_REQUEST","HOST_AUTH_REQUIRED","FORBIDDEN","NOT_FOUND","STATE_CONFLICT","IDEMPOTENCY_CONFLICT","UNSUPPORTED_CAPABILITY","HARNESS_UNAVAILABLE","HARNESS_AUTH_REQUIRED","WORKSPACE_REVOKED","EXECUTION_UNKNOWN","INTERNAL_ERROR"]},"message":{"type":"string","maxLength":1024},"retryable":{"type":"boolean"},"task_ref":{"anyOf":[{"$ref":"#/$defs/TaskRef"},{"type":"null"}]},"current_task_revision":{"anyOf":[{"$ref":"#/$defs/PositiveDecimal"},{"type":"null"}]},"current_run":{"anyOf":[{"$ref":"#/$defs/RunRef"},{"type":"null"}]}},"required":["code","message","retryable","task_ref","current_task_revision","current_run"]},"ErrorResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"error":{"$ref":"#/$defs/Error"}},"required":["api_version","error"]},"Capabilities":{"type":"object","additionalProperties":false,"properties":{"harness_id":{"const":"codex"},"display_name":{"const":"Codex CLI"},"backend":{"const":"codex-cli-readonly-v1"},"installation":{"type":"object","additionalProperties":false,"properties":{"present":{"type":"boolean"},"version":{"anyOf":[{"type":"string","minLength":1,"maxLength":128},{"type":"null"}]},"executable_sha256":{"anyOf":[{"type":"string","pattern":"^sha256:[0-9a-f]{64}$"},{"type":"null"}]},"checked_at":{"anyOf":[{"type":"string","format":"date-time"},{"type":"null"}]}},"required":["present","version","executable_sha256","checked_at"]},"authentication":{"type":"object","additionalProperties":false,"properties":{"state":{"enum":["UNPROBED","LOGGED_IN","LOGGED_OUT","ERROR"]},"kind":{"anyOf":[{"enum":["chatgpt","api_key","other"]},{"type":"null"}]},"checked_at":{"anyOf":[{"type":"string","format":"date-time"},{"type":"null"}]}},"required":["state","kind","checked_at"]},"verification":{"type":"object","additionalProperties":false,"properties":{"execution":{"enum":["UNVERIFIED","FIXTURE_ONLY","LIVE_OBSERVED"]},"workspace_read_scope":{"enum":["UNVERIFIED","FIXTURE_ONLY","LIVE_OBSERVED"]},"cancellation":{"enum":["UNVERIFIED","FIXTURE_ONLY","LIVE_OBSERVED"]},"checked_at":{"anyOf":[{"type":"string","format":"date-time"},{"type":"null"}]}},"required":["execution","workspace_read_scope","cancellation","checked_at"]},"capabilities":{"type":"object","additionalProperties":false,"properties":{"readonly_turn":{"type":"boolean"},"event_stream":{"type":"boolean"},"cancel":{"type":"boolean"},"task_history":{"type":"boolean"},"request_lookup":{"type":"boolean"},"token_delta":{"const":false},"write":{"const":false},"resume":{"const":false},"pause":{"const":false},"per_tool_approval":{"const":false},"file_diff":{"const":false},"file_list":{"const":false},"file_artifacts":{"const":false},"attachments":{"const":false}},"required":["readonly_turn","event_stream","cancel","task_history","request_lookup","token_delta","write","resume","pause","per_tool_approval","file_diff","file_list","file_artifacts","attachments"]},"security_scope":{"type":"object","additionalProperties":false,"properties":{"mode":{"const":"workspace-read"},"profile_id":{"type":"string","minLength":1,"maxLength":128},"config_source":{"const":"HOST_FIXED"},"hooks":{"const":"DISABLED"},"mcp":{"const":"DISABLED"},"native_auth":{"const":"CLI_OWNED"},"enforcement_verified":{"type":"boolean"}},"required":["mode","profile_id","config_source","hooks","mcp","native_auth","enforcement_verified"]},"can_submit":{"type":"boolean"},"reason_codes":{"type":"array","items":{"type":"string","minLength":1,"maxLength":128},"maxItems":16}},"required":["harness_id","display_name","backend","installation","authentication","verification","capabilities","security_scope","can_submit","reason_codes"]},"Task":{"type":"object","additionalProperties":false,"properties":{"task_ref":{"$ref":"#/$defs/TaskRef"},"request_id":{"$ref":"#/$defs/RequestID"},"harness_id":{"const":"codex"},"workspace_ref":{"type":"string","minLength":1,"maxLength":256},"prompt":{"type":"string","maxLength":65536,"x-maxUtf8Bytes":65536},"scope":{"const":"workspace-read"},"ephemeral":{"const":true},"status":{"enum":["QUEUED","STARTING","RUNNING","CANCEL_REQUESTED","COMPLETED","FAILED","CANCELLED","BLOCKED","UNKNOWN"]},"terminal":{"type":"boolean"},"task_revision":{"$ref":"#/$defs/PositiveDecimal"},"run":{"anyOf":[{"$ref":"#/$defs/RunRef"},{"type":"null"}]},"created_at":{"type":"string","format":"date-time"},"updated_at":{"type":"string","format":"date-time"},"result":{"anyOf":[{"type":"object","additionalProperties":false,"properties":{"assistant_text":{"type":"string","maxLength":1048576,"x-maxUtf8Bytes":1048576},"cli_thread_id":{"anyOf":[{"type":"string","minLength":1,"maxLength":256},{"type":"null"}]}},"required":["assistant_text","cli_thread_id"]},{"type":"null"}]},"failure":{"anyOf":[{"$ref":"#/$defs/Error"},{"type":"null"}]}},"required":["task_ref","request_id","harness_id","workspace_ref","prompt","scope","ephemeral","status","terminal","task_revision","run","created_at","updated_at","result","failure"]},"SubmitRequest":{"type":"object","additionalProperties":false,"properties":{"request_id":{"$ref":"#/$defs/RequestID"},"project_id":{"type":"string","minLength":1,"maxLength":128},"workspace_ref":{"type":"string","minLength":1,"maxLength":256},"harness_id":{"const":"codex"},"scope":{"const":"workspace-read"},"prompt":{"type":"string","maxLength":65536,"x-maxUtf8Bytes":65536}},"required":["request_id","project_id","workspace_ref","harness_id","scope","prompt"]},"SubmitData":{"type":"object","additionalProperties":false,"properties":{"task_ref":{"$ref":"#/$defs/TaskRef"},"request_id":{"$ref":"#/$defs/RequestID"},"task_revision":{"$ref":"#/$defs/PositiveDecimal"},"status":{"const":"QUEUED"},"run":{"const":null}},"required":["task_ref","request_id","task_revision","status","run"]},"CancelRequest":{"type":"object","additionalProperties":false,"properties":{"request_id":{"$ref":"#/$defs/RequestID"},"expected_task_revision":{"$ref":"#/$defs/PositiveDecimal"},"expected_run_id":{"anyOf":[{"type":"string","minLength":1,"maxLength":128},{"type":"null"}]},"expected_epoch":{"anyOf":[{"$ref":"#/$defs/PositiveDecimal"},{"type":"null"}]}},"required":["request_id","expected_task_revision","expected_run_id","expected_epoch"]},"CancelData":{"type":"object","additionalProperties":false,"properties":{"task":{"$ref":"#/$defs/Task"},"disposition":{"enum":["CANCEL_REQUESTED","CANCELLED_BEFORE_LAUNCH","ALREADY_TERMINAL"]}},"required":["task","disposition"]},"ListData":{"type":"object","additionalProperties":false,"properties":{"items":{"type":"array","items":{"$ref":"#/$defs/Task"},"maxItems":100},"next_cursor":{"$ref":"#/$defs/Decimal"},"has_more":{"type":"boolean"},"lookup":{"anyOf":[{"type":"object","additionalProperties":false,"properties":{"request_id":{"$ref":"#/$defs/RequestID"},"state":{"enum":["FOUND","NOT_FOUND"]}},"required":["request_id","state"]},{"type":"null"}]}},"required":["items","next_cursor","has_more","lookup"]},"Event":{"type":"object","additionalProperties":false,"properties":{"event_id":{"type":"string","minLength":1,"maxLength":128},"task_ref":{"$ref":"#/$defs/TaskRef"},"run":{"anyOf":[{"$ref":"#/$defs/RunRef"},{"type":"null"}]},"sequence":{"$ref":"#/$defs/PositiveDecimal"},"timestamp":{"type":"string","format":"date-time"},"kind":{"enum":["TASK_QUEUED","RUN_STARTED","RUN_STATE","ASSISTANT_MESSAGE","TOOL_EVENT","LOG","TASK_TERMINAL"]},"payload":{"type":"object","additionalProperties":false,"properties":{"status":{"anyOf":[{"enum":["QUEUED","STARTING","RUNNING","CANCEL_REQUESTED","COMPLETED","FAILED","CANCELLED","BLOCKED","UNKNOWN"]},{"type":"null"}]},"text":{"anyOf":[{"type":"string","maxLength":1048576,"x-maxUtf8Bytes":1048576},{"type":"null"}]},"tool":{"anyOf":[{"type":"object","additionalProperties":false,"properties":{"id":{"type":"string","minLength":1,"maxLength":256},"name":{"type":"string","minLength":1,"maxLength":128},"phase":{"enum":["STARTED","COMPLETED","FAILED"]},"summary":{"type":"string","maxLength":4096}},"required":["id","name","phase","summary"]},{"type":"null"}]},"task":{"anyOf":[{"$ref":"#/$defs/Task"},{"type":"null"}]},"error":{"anyOf":[{"$ref":"#/$defs/Error"},{"type":"null"}]}},"required":["status","text","tool","task","error"]}},"required":["event_id","task_ref","run","sequence","timestamp","kind","payload"]},"EventsData":{"type":"object","additionalProperties":false,"properties":{"task_ref":{"$ref":"#/$defs/TaskRef"},"events":{"type":"array","items":{"$ref":"#/$defs/Event"},"maxItems":500},"next_cursor":{"$ref":"#/$defs/Decimal"},"has_more":{"type":"boolean"},"end":{"type":"boolean"},"reset":{"type":"boolean"},"snapshot":{"anyOf":[{"$ref":"#/$defs/Task"},{"type":"null"}]}},"required":["task_ref","events","next_cursor","has_more","end","reset","snapshot"]},"CapabilitiesResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"data":{"$ref":"#/$defs/Capabilities"}},"required":["api_version","data"]},"SubmitResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"data":{"$ref":"#/$defs/SubmitData"}},"required":["api_version","data"]},"TaskResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"data":{"$ref":"#/$defs/Task"}},"required":["api_version","data"]},"ListResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"data":{"$ref":"#/$defs/ListData"}},"required":["api_version","data"]},"CancelResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"data":{"$ref":"#/$defs/CancelData"}},"required":["api_version","data"]},"EventsResponse":{"type":"object","additionalProperties":false,"properties":{"api_version":{"const":"harness.v1"},"data":{"$ref":"#/$defs/EventsData"}},"required":["api_version","data"]}};
const fail = code => { throw Object.assign(new Error(code), { code }); };
function validateSchema(schema, value) {
  if (schema.$ref) return validateSchema(DEFINITIONS[schema.$ref.split('/').at(-1)], value);
  if (schema.anyOf) {
    for (const item of schema.anyOf) { try { validateSchema(item, value); return value; } catch {} }
    fail('HARNESS_SCHEMA');
  }
  if (Object.hasOwn(schema, 'const') && value !== schema.const || schema.enum && !schema.enum.includes(value)) fail('HARNESS_SCHEMA');
  if (schema.type === 'null' && value !== null || schema.type === 'boolean' && typeof value !== 'boolean') fail('HARNESS_SCHEMA');
  if (schema.type === 'integer' && (!Number.isSafeInteger(value) || schema.minimum != null && value < schema.minimum || schema.maximum != null && value > schema.maximum)) fail('HARNESS_SCHEMA');
  if (schema.type === 'string') {
    if (typeof value !== 'string') fail('HARNESS_SCHEMA');
    for (const c of value) if (c.codePointAt(0) >= 0xd800 && c.codePointAt(0) <= 0xdfff) fail('HARNESS_UNICODE');
    const length = [...value].length;
    if (schema.minLength != null && length < schema.minLength || schema.maxLength != null && length > schema.maxLength ||
        schema.pattern && !new RegExp(schema.pattern).test(value) || schema['x-maxUtf8Bytes'] != null && Buffer.byteLength(value) > schema['x-maxUtf8Bytes'] ||
        schema.format === 'date-time' && !Number.isFinite(Date.parse(value))) fail('HARNESS_SCHEMA');
    if (schema['x-int64-max'] && (value.length > 19 || value.length === 19 && value > schema['x-int64-max'])) fail('HARNESS_SCHEMA');
  }
  if (schema.type === 'array') {
    if (!Array.isArray(value) || schema.maxItems != null && value.length > schema.maxItems) fail('HARNESS_SCHEMA');
    value.forEach(item => validateSchema(schema.items, item));
  }
  if (schema.type === 'object') {
    if (!value || typeof value !== 'object' || Array.isArray(value)) fail('HARNESS_SCHEMA');
    if (schema.required?.some(key => !Object.hasOwn(value, key)) || schema.additionalProperties === false && Object.keys(value).some(key => !Object.hasOwn(schema.properties, key))) fail('HARNESS_SCHEMA');
    for (const [key, item] of Object.entries(value)) if (schema.properties[key]) validateSchema(schema.properties[key], item);
  }
  return value;
}
function validate(name, value) {
  if (!DEFINITIONS[name]) fail('HARNESS_SCHEMA');
  validateSchema(DEFINITIONS[name], value);
  return value;
}
function createHarnessWire({ httpImpl = http, timeoutMs = 8000, maxResponseBytes = 16 * 1024 * 1024 } = {}) {
  return ({ url, method, body, credential, responseType, beforeSend }) => new Promise(resolve => {
    let request, response, sent = false, finished = false;
    const finish = result => { if (!finished) { finished = true; clearTimeout(deadline); resolve(result); } };
    const failure = reason => { finish({ ok: false, reason, outcome: sent ? 'UNKNOWN' : 'NOT_SENT' }); response?.destroy?.(); request?.destroy?.(); };
    const deadline = setTimeout(() => failure('HARNESS_TIMEOUT'), timeoutMs);
    try {
      const target = new URL(url);
      if (target.protocol !== 'http:' || !['127.0.0.1', '[::1]', 'localhost'].includes(target.hostname) || target.username || target.password || target.hash ||
          !target.pathname.startsWith('/harness/v1/') || !['GET', 'POST'].includes(method)) fail('HARNESS_LOCAL_ROUTE_REQUIRED');
      if (typeof credential !== 'string' || !credential || /[\r\n]/.test(credential)) fail('HOST_AUTH_REQUIRED');
      const raw = body == null ? null : Buffer.from(JSON.stringify(body), 'utf8');
      if (raw && raw.length > 128 * 1024) fail('HARNESS_REQUEST_TOO_LARGE');
      if (beforeSend?.() !== true) fail('HARNESS_CONTEXT_CHANGED');
      request = httpImpl.request(target, { method, agent: false, headers: {
        authorization: 'Bearer ' + credential, accept: 'application/json',
        ...(raw ? { 'content-type': 'application/json', 'content-length': raw.length } : {}),
      } }, res => {
        response = res;
        if (finished) { res.destroy?.(); return; }
        if (String(res.headers['content-type'] || '').split(';')[0].trim().toLowerCase() !== 'application/json') { failure('HARNESS_REPLY_TYPE'); return; }
        let length = 0;
        const chunks = [];
        res.on('data', chunk => {
          if (finished) return;
          length += chunk.length;
          if (length > maxResponseBytes) { failure('HARNESS_REPLY_TOO_LARGE'); return; }
          chunks.push(Buffer.from(chunk));
        });
        res.on('aborted', () => failure('HARNESS_REPLY_ABORTED'));
        res.on('error', () => failure('HARNESS_REPLY_ABORTED'));
        res.on('end', () => {
          if (finished) return;
          try {
            const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(Buffer.concat(chunks));
            if (text.charCodeAt(0) === 0xfeff) fail('HARNESS_REPLY_JSON');
            const envelope = privateJSON(text);
            if (res.statusCode >= 400) {
              validate('ErrorResponse', envelope);
              finish({ ok: false, reason: envelope.error.code, error: envelope.error, outcome: 'REPLIED' });
            } else {
              if (res.statusCode !== (responseType === 'SubmitResponse' ? 202 : 200)) fail('HARNESS_HTTP_STATUS');
              validate(responseType, envelope);
              finish({ ok: true, data: envelope.data, outcome: 'REPLIED' });
            }
          } catch { failure('HARNESS_REPLY_INVALID'); }
        });
      });
      request.on('error', () => failure('HARNESS_TRANSPORT_ERROR'));
      // No await, logging or IO can intervene between the final origin check
      // and dispatch. This request is never retried here, including on401.
      if (beforeSend?.() !== true) { failure('HARNESS_CONTEXT_CHANGED'); return; }
      sent = true;
      request.end(raw);
    } catch (error) { failure(error.code || 'HARNESS_TRANSPORT_ERROR'); }
  });
}
function createPendingJournal({ file, fsImpl = fs, maxBytes = 2 * 1024 * 1024, maxEntries = 32 } = {}) {
  const hash = value => crypto.createHash('sha256').update(JSON.stringify(Object.fromEntries(Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)))).digest('hex');
  const journal = { entries: [], error: null };
  const check = entries => {
    if (!Array.isArray(entries) || entries.length > maxEntries) fail('HARNESS_JOURNAL_LIMIT');
    const projects = new Set();
    return entries.map(entry => {
      const allowed = ['projectId', 'kind', 'requestId', 'payload', 'origin', 'state', 'taskRef', 'bodySHA256'];
      if (!entry || Object.keys(entry).some(key => !allowed.includes(key)) ||
          typeof entry.projectId !== 'string' || !entry.projectId || projects.has(entry.projectId) ||
          !['submit', 'cancel'].includes(entry.kind) || !['SENDING', 'UNKNOWN', 'ACKNOWLEDGED'].includes(entry.state) ||
          typeof entry.origin !== 'string' || !entry.origin || entry.origin.length > 4096 ||
          entry.requestId !== entry.payload?.request_id || entry.bodySHA256 !== hash(entry.payload)) fail('HARNESS_JOURNAL_INVALID');
      projects.add(entry.projectId);
      validate(entry.kind === 'submit' ? 'SubmitRequest' : 'CancelRequest', entry.payload);
      if (entry.kind === 'submit' && entry.payload.project_id !== entry.projectId) fail('HARNESS_JOURNAL_INVALID');
      if (entry.taskRef) { validate('TaskRef', entry.taskRef); if (entry.taskRef.project_id !== entry.projectId) fail('HARNESS_JOURNAL_INVALID'); }
      if (entry.kind === 'cancel' && !entry.taskRef) fail('HARNESS_JOURNAL_INVALID');
      return structuredClone(entry);
    });
  };
  try {
    if (fsImpl.existsSync(file)) {
      const stat = fsImpl.lstatSync(file);
      if (stat.isSymbolicLink() || !stat.isFile() || stat.size > maxBytes) fail('HARNESS_JOURNAL_INVALID');
      const bytes = fsImpl.readFileSync(file);
      if (bytes.length > maxBytes) fail('HARNESS_JOURNAL_LIMIT');
      const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
      if (text.charCodeAt(0) === 0xfeff) fail('HARNESS_JOURNAL_INVALID');
      const value = privateJSON(text);
      if (!value || Object.keys(value).length !== 2 || value.schema !== 'researchos.harness.pending/1' || !Object.hasOwn(value, 'entries')) fail('HARNESS_JOURNAL_INVALID');
      journal.entries = check(value.entries).map(entry => ({ ...entry, state: entry.state === 'SENDING' ? 'UNKNOWN' : entry.state }));
    }
  } catch { journal.error = 'HARNESS_JOURNAL_INVALID'; }
  journal.replace = entries => {
    if (journal.error) fail(journal.error);
    const prepared = check(entries.map(entry => ({ ...entry, bodySHA256: hash(entry.payload) })));
    const raw = Buffer.from(JSON.stringify({ schema: 'researchos.harness.pending/1', entries: prepared }), 'utf8');
    if (raw.length > maxBytes) fail('HARNESS_JOURNAL_LIMIT');
    const temporary = file + '.' + crypto.randomUUID() + '.tmp';
    let fd, created = false;
    try {
      // In the existing protected app userData directory. Prompts are private
      // user data. Never store bearer/native credentials or server Task truth.
      fd = fsImpl.openSync(temporary, 'wx', 0o600); created = true;
      fsImpl.writeFileSync(fd, raw); fsImpl.fsyncSync(fd); fsImpl.closeSync(fd); fd = undefined;
      fsImpl.renameSync(temporary, file);
      journal.entries = prepared;
    } catch {
      journal.error = 'HARNESS_JOURNAL_WRITE_FAILED';
      if (fd !== undefined) { try { fsImpl.closeSync(fd); } catch {} }
      if (created) { try { fsImpl.unlinkSync(temporary); } catch {} }
      fail(journal.error);
    }
  };
  return journal;
}
module.exports = { CONTRACT_SHA256, validate, createHarnessWire, createPendingJournal };

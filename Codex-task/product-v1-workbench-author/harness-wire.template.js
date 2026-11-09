'use strict';
const http = require('node:http');
const fs = require('node:fs');
const crypto = require('node:crypto');
const { TextDecoder } = require('node:util');
const { privateJSON } = require('./http-wire.js');
// Frozen researchos.host-harness.v1 revision2, not the legacy V2 wire lane.
const CONTRACT_SHA256 = '046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c';
const DEFINITIONS = __DEFINITIONS__;
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

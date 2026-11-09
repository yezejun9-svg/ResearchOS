// Private Desktop HTTP lane. Each request is schema-checked before any POST.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const PROTOCOL = 'researchos.desktop.http-validation/1';
const LIMIT = { request: 8388608, response: 16777216, frame: 33555460, output: 67108864, stderr: 16384, queued: 67108864 };
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const error = reason => Object.assign(new Error(reason), { reason });
const schemas = ['8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b', 'b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54'];
let valuesPromise;
const values = () => valuesPromise ||= import(pathToFileURL(path.join(__dirname, 'wire-values.mjs')).href);
function regular(root, relative) {
  if (typeof relative !== 'string' || path.isAbsolute(relative) || relative.split(/[\\/]/).some(s => !s || s === '.' || s === '..')) throw error('VALIDATOR_RESOURCE_PATH');
  const resolved = path.resolve(root, relative);
  let current = root;
  for (const part of relative.split(/[\\/]/)) { current = path.join(current, part); if (fs.lstatSync(current).isSymbolicLink()) throw error('VALIDATOR_RESOURCE_ALIAS'); }
  if (fs.realpathSync(resolved) !== resolved || !fs.statSync(resolved).isFile()) throw error('VALIDATOR_RESOURCE_PATH');
  return resolved;
}
function resource(appRoot) {
  const root = path.resolve(appRoot);
  if (fs.realpathSync(root) !== root || fs.lstatSync(root).isSymbolicLink()) throw error('VALIDATOR_RESOURCE_ALIAS');
  const descriptorPath = regular(root, 'resources/client-wire/descriptor.json');
  if (fs.statSync(descriptorPath).size > 4 * 1024 * 1024) throw error('VALIDATOR_DESCRIPTOR');
  const descriptor = privateJSON(new TextDecoder('utf-8', {fatal:true}).decode(fs.readFileSync(descriptorPath)));
  if (descriptor.schema !== 'researchos.desktop.client-wire-release/1' || descriptor.child_protocol !== PROTOCOL ||
      JSON.stringify(descriptor.schema_sha256_pair) !== JSON.stringify(schemas) || !/^[a-f0-9]{64}$/.test(descriptor.build_input_digest)) throw error('VALIDATOR_DESCRIPTOR');
  const exe = regular(root, 'resources/client-wire/researchos-client-wire-validator.exe');
  if (sha(fs.readFileSync(exe)) !== descriptor.binary_sha256) throw error('VALIDATOR_BINARY_DIGEST');
  if (!Array.isArray(descriptor.exact_module_source_inventory) || !descriptor.exact_module_source_inventory.length) throw error('VALIDATOR_MODULES');
  const required = ['main/main.js','main/lib/http-wire.js','main/lib/wire-values.mjs','main/lib/ipc.js','main/lib/v2.js','main/lib/first-use.js','main/workbench.html'];
  const names = new Set();
  for (const entry of descriptor.exact_module_source_inventory) {
    if (names.has(entry.path)) throw error('VALIDATOR_MODULES'); names.add(entry.path);
    if (sha(fs.readFileSync(regular(root, entry.path))) !== entry.sha256) throw error('VALIDATOR_MODULE_DIGEST');
  }
  if (required.some(name => !names.has(name))) throw error('VALIDATOR_MODULES');
  const actual = [];
  const inventory = directory => { for (const entry of fs.readdirSync(path.join(root,directory),{withFileTypes:true})) {
    const relative = directory+'/'+entry.name;
    if (entry.isSymbolicLink()) throw error('VALIDATOR_RESOURCE_ALIAS');
    if (entry.isDirectory()) inventory(relative); else if (entry.isFile()) actual.push(relative); else throw error('VALIDATOR_MODULES');
  } };
  inventory('main'); inventory('preload');
  if (actual.length!==names.size || actual.some(name=>!names.has(name))) throw error('VALIDATOR_MODULES');
  return { root, exe, descriptor, descriptorHash: sha(fs.readFileSync(descriptorPath)) };
}
// The trusted binary emits JSON, but a broken private stream still cannot hide
// duplicates, invalid Unicode, trailing values or unsafe framing numbers.
function privateJSON(text) {
  let i = 0, nodes = 0;
  const space = () => {
    while (i < text.length && ' \t\n\r'.includes(text[i])) i++;
    if (i < text.length && /\s/.test(text[i])) throw Object.assign(error('PRIVATE_JSON'),{invalidWhitespace:true});
  };
  const string = () => {
    const start = i++;
    while (i < text.length) { if (text[i] === '\\') { i += 2; continue; } if (text[i++] === '"') {
      const value = JSON.parse(text.slice(start, i));
      for (const char of value) { const code = char.codePointAt(0); if (code >= 0xd800 && code <= 0xdfff) throw error('PRIVATE_JSON'); }
      return value;
    } }
    throw error('PRIVATE_JSON');
  };
  const read = depth => {
    if (++nodes > 1572864 || depth > 780) throw error('LOCAL_RESOURCE_LIMIT'); space();
    if (text[i] === '"') return string();
    if (text[i] === '[') { i++; space(); const a = []; if (text[i] === ']') { i++; return a; } while (true) { a.push(read(depth+1)); space(); if (text[i++] === ']') return a; if (text[i-1] !== ',') throw error('PRIVATE_JSON'); } }
    if (text[i] === '{') { i++; space(); const o = Object.create(null), keys = new Set(); if (text[i] === '}') { i++; return o; } while (true) { space(); if (text[i] !== '"') throw error('PRIVATE_JSON'); const key = string(); if (keys.has(key)) throw error('PRIVATE_JSON'); keys.add(key); space(); if (text[i++] !== ':') throw error('PRIVATE_JSON'); o[key] = read(depth+1); space(); if (text[i++] === '}') return o; if (text[i-1] !== ',') throw error('PRIVATE_JSON'); } }
    for (const [literal,value] of [['true',true],['false',false],['null',null]]) if (text.startsWith(literal,i)) { i+=literal.length; return value; }
    const m = /^-?(?:0|[1-9][0-9]*)/.exec(text.slice(i)); if (!m) throw error('PRIVATE_JSON'); i+=m[0].length; const v = Number(m[0]); if (!Number.isSafeInteger(v)) throw error('PRIVATE_JSON'); return v;
  };
  const result = read(0); space(); if (i !== text.length) throw error('PRIVATE_JSON'); return result;
}
function child(resource, packet, record, lane) {
  const input = Buffer.from(JSON.stringify(packet));
  if (input.length > LIMIT.frame) return Promise.reject(error('LOCAL_RESOURCE_LIMIT'));
  return new Promise((resolve, reject) => {
    const runtimeEnv = { SystemRoot: process.env.SystemRoot || process.env.WINDIR || 'C:\\Windows' };
    const proc = spawn(resource.exe, [], { shell: false, windowsHide: true, detached: false, stdio: ['pipe','pipe','pipe'], env: runtimeEnv, cwd: resource.root });
    const facts = { nonce: packet.nonce, phase: packet.phase, spawnfile: proc.spawnfile, spawnargs: proc.spawnargs, pid: proc.pid, spawned: false, exited: false, stdoutClosed: false, stderrClosed: false, stdinClosed: false, closed: false, killRequested: false };
    let stdout = [], stderr = [], outBytes = 0, errBytes = 0, fault = null, settled = false, cleanupRecorded = false, reapTimer;
    const terminate = reason => {
      if (!fault) fault = error(reason);
      if (!facts.killRequested && !facts.exited) { facts.killRequested = true; facts.killRequestReturned = proc.kill(); }
      if (!reapTimer) reapTimer = setTimeout(() => { lane.blocked = true; facts.cleanupUnconfirmed = true; finish(); }, 5000);
    };
    const finish = () => {
      const closed = facts.exited && facts.closed && facts.stdoutClosed && facts.stderrClosed && facts.stdinClosed;
      if (settled) {
        if (closed && !cleanupRecorded) { cleanupRecorded=true; record({kind:'child-cleanup',facts:{...facts}}); lane.handles.delete(proc); }
        return;
      }
      if (!facts.cleanupUnconfirmed && !closed) return;
      if (closed) { cleanupRecorded=true; lane.handles.delete(proc); }
      settled = true; clearTimeout(deadline); clearTimeout(reapTimer);
      record({ kind: 'child', input, stdout: Buffer.concat(stdout), stderr: Buffer.concat(stderr), facts: { ...facts } });
      if (facts.cleanupUnconfirmed || fault || facts.exitCode !== 0 || !facts.exited) return reject(fault || error('VALIDATOR_EXIT'));
      try {
        const value = privateJSON(new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(Buffer.concat(stdout)));
        if (value.schema !== PROTOCOL || value.phase !== packet.phase || value.nonce !== packet.nonce || value.http_status !== packet.http_status ||
            value.request_sha256 !== sha(Buffer.from(packet.request_raw_base64,'base64')) || value.response_sha256 !== sha(Buffer.from(packet.response_raw_base64,'base64')) ||
            JSON.stringify(value.schema_sha256_pair) !== JSON.stringify(schemas) || value.build_input_digest !== resource.descriptor.build_input_digest) throw error('PRIVATE_CORRELATION');
        resolve(value);
      } catch (cause) { reject(error(cause?.invalidWhitespace ? 'PRIVATE_JSON' : 'PRIVATE_CORRELATION')); }
    };
    const deadline = setTimeout(() => terminate('VALIDATOR_TIMEOUT'), 5000);
    proc.on('spawn', () => { facts.spawned = true; });
    proc.on('error', () => { fault = error('VALIDATOR_SPAWN'); });
    proc.on('exit', (code,signal) => { facts.exited = true; facts.exitCode = code; facts.signal = signal; });
    proc.on('close', (code,signal) => { facts.closed = true; facts.closeCode = code; facts.closeSignal = signal; finish(); });
    proc.stdout.on('data', data => { outBytes += data.length; if (outBytes > LIMIT.output) terminate('LOCAL_RESOURCE_LIMIT'); else stdout.push(data); });
    proc.stderr.on('data', data => { errBytes += data.length; if (errBytes > LIMIT.stderr) terminate('LOCAL_RESOURCE_LIMIT'); else stderr.push(data); });
    proc.stdout.on('close', () => { facts.stdoutClosed = true; finish(); });
    proc.stderr.on('close', () => { facts.stderrClosed = true; finish(); });
    proc.stdin.on('close', () => { facts.stdinClosed = true; finish(); });
    proc.stdin.on('error', () => { if (!facts.exited) terminate('VALIDATOR_INPUT_IO'); });
    proc.stdin.end(input);
    // The closure retains the actual ChildProcess/pipe objects through unresolved
    // cleanup; a recycled numeric PID is never used to signal anything.
    lane.handles.add(proc);
  });
}
function post(url, raw, headers, record) {
  return new Promise((resolve,reject) => {
    const u = new URL(url);
    if (u.protocol !== 'http:' || !['127.0.0.1','localhost','[::1]'].includes(u.hostname) || u.username || u.password || u.search || u.hash || u.pathname !== '/v2/command') return reject(error('NONLOCAL_HOST'));
    let bytes = 0, parts = [], done = false;
    const finish = (err,value) => { if (done) return; done=true; clearTimeout(timer); err ? reject(err) : resolve(value); };
    const req = http.request(u, { method:'POST', agent:false, headers:{ ...headers,'Content-Type':'application/json','Content-Length':raw.length } }, res => {
      res.on('data', data => { bytes += data.length; if (bytes > LIMIT.response) { req.destroy(); finish(error('LOCAL_RESOURCE_LIMIT')); } else parts.push(data); });
      res.on('aborted', () => finish(error('HTTP_INCOMPLETE')));
      res.on('error', () => finish(error('HTTP_INCOMPLETE')));
      res.on('end', () => { const response=Buffer.concat(parts); record({kind:'http',request:raw,response,status:res.statusCode}); finish(null,{raw:response,status:res.statusCode}); });
    });
    const timer=setTimeout(() => { req.destroy(); finish(error('HTTP_TIMEOUT')); },10000);
    req.on('error', () => finish(error('HTTP_UNREACHABLE'))); req.end(raw);
  });
}
function boundLocalInput(value) {
  let nodes = 0, chars = 0; const seen = new Set();
  const visit = (v, depth) => {
    if (++nodes > 262144 || depth > 256) throw error('LOCAL_RESOURCE_LIMIT');
    if (typeof v === 'string') chars += v.length;
    if (chars > LIMIT.request) throw error('LOCAL_RESOURCE_LIMIT');
    if (v && typeof v === 'object') {
      if (seen.has(v)) throw error('INVALID_LOCAL_VALUE'); seen.add(v);
      for (const key in v) if (Object.hasOwn(v, key)) { chars += key.length; visit(v[key], depth + 1); }
      seen.delete(v);
    }
  };
  visit(value, 0);
}
function createTransport({ appRoot, record = () => {} }) {
  const lane = { blocked:false, handles:new Set(), pending:0, bytes:0, tail:Promise.resolve() };
  return async function transport(verb,url,envelope,headers,beforeSend) {
    let raw;
    try { boundLocalInput(envelope); const captured = structuredClone(envelope); headers = {...headers}; raw=Buffer.from((await values()).stringify(captured)); } catch(e) { return {ok:false,reason:e.reason||e.message,dispatch_state:'NOT_SENT'}; }
    if (verb !== 'POST' || raw.length > LIMIT.request || lane.pending >= 9 || lane.bytes + raw.length + LIMIT.response > LIMIT.queued || lane.blocked) return {ok:false,reason:'LOCAL_RESOURCE_LIMIT',dispatch_state:'NOT_SENT'};
    lane.pending++;lane.bytes+=raw.length+LIMIT.response;
    const queuedAt=Date.now();
    // This local fact is set before calling HTTP; validator output cannot claim it.
    let dispatchAttempted=false;
    const run=async()=>{
      if (lane.blocked || Date.now()-queuedAt>30000) throw error('VALIDATOR_LANE_UNAVAILABLE');
      const fixed=resource(appRoot);
      const packet=phase=>({schema:PROTOCOL,phase,nonce:crypto.randomUUID(),http_status:null,request_raw_base64:raw.toString('base64'),response_raw_base64:''});
      const before=packet('REQUEST'); const pre=await child(fixed,before,record,lane);
      if (pre.outcome!=='VALID') throw error(pre.reason||'REQUEST_REFUSED');
      boundLocalInput(envelope);
      if (!Buffer.from((await values()).stringify(envelope)).equals(raw)) throw error('REQUEST_CHANGED_AFTER_PREFLIGHT');
      // Validate bytes/modules again after child reaping, before exposing any request.
      if(resource(appRoot).descriptorHash!==fixed.descriptorHash) throw error('VALIDATOR_RESOURCE_CHANGED');
      if (beforeSend !== undefined) {
        if (typeof beforeSend !== 'function' || envelope.method !== 'session.create') throw error('NATIVE_CREATE_ATTESTATION_UNAVAILABLE');
        const ref=await beforeSend(Buffer.from(raw),Object.freeze({...headers}));
        if (typeof ref!=='string' || !/^natt-[0-9a-f]{64}$/.test(ref)) throw error('NATIVE_CREATE_ATTESTATION_UNAVAILABLE');
        boundLocalInput(envelope);
        if (!Buffer.from((await values()).stringify(envelope)).equals(raw)) throw error('REQUEST_CHANGED_AFTER_ATTESTATION');
        if(resource(appRoot).descriptorHash!==fixed.descriptorHash) throw error('VALIDATOR_RESOURCE_CHANGED');
        headers['X-ResearchOS-Native-Attestation']=ref; // This attempt only, never retained in IPC state.
      }
      dispatchAttempted=true;
      const reply=await post(url,raw,headers,record); const after=packet('RESPONSE');after.http_status=reply.status;after.response_raw_base64=reply.raw.toString('base64');
      const result=await child(fixed,after,record,lane);
      if(resource(appRoot).descriptorHash!==fixed.descriptorHash) throw error('VALIDATOR_RESOURCE_CHANGED');
      if(result.outcome==='HTTP_ERROR') return {ok:false,http_status:reply.status,reason:result.reason};
      if(result.outcome!=='VALID') throw error(result.reason||'RESPONSE_REFUSED');
      return {ok:true,http_status:reply.status,validated:true,body:(await values()).reify(result.value)};
    };
    const promise=lane.tail.then(run);lane.tail=promise.catch(()=>{});
    try{return await promise;}catch(e){return {ok:false,reason:e.reason||'VALIDATOR_FAILURE',...(dispatchAttempted?{}:{dispatch_state:'NOT_SENT'})};}
    finally{lane.pending--;lane.bytes-=raw.length+LIMIT.response;}
  };
}
module.exports={createTransport,privateJSON};

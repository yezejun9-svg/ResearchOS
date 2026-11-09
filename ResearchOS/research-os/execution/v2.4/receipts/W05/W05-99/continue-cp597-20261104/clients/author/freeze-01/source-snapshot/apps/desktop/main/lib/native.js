'use strict';

const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');
const crypto = require('node:crypto');
const { privateJSON } = require('./http-wire.js');

const HOST_ID = /^host-[0-9a-f]{12}$/;
const MAX_FRAME = 8192;

function hostInstanceId(fsImpl, discovery) {
  if (!discovery || !discovery.data_dir || !discovery.url || !Number.isInteger(discovery.pid)) {
    throw Error('HOST_NATIVE_DISCOVERY_INCOMPLETE');
  }
  let id = discovery.host_instance_id;
  if (!id) {
    let current;
    try { current = JSON.parse(fsImpl.readFileSync(path.join(discovery.data_dir, 'discovery.json'), 'utf8')); }
    catch { throw Error('HOST_NATIVE_DISCOVERY_INCOMPLETE'); }
    if (current.url !== discovery.url || current.pid !== discovery.pid || current.data_dir !== discovery.data_dir) {
      throw Error('HOST_NATIVE_DISCOVERY_MISMATCH');
    }
    id = current.host_instance_id;
  }
  if (!HOST_ID.test(id)) throw Error('HOST_NATIVE_DISCOVERY_INCOMPLETE');
  return id;
}

function dialNative(pipeName, frame, timeoutMs = 5000, rawReply = false) {
  return new Promise((resolve, reject) => {
    const request = Buffer.from(JSON.stringify(frame));
    if (!request.length || request.length > MAX_FRAME) return reject(Error('NATIVE_FRAME_TOO_LARGE'));
    const socket = net.connect(pipeName);
    let done = false;
    const parts = [];
    let size = 0;
    function finish(error, reply) {
      if (done) return;
      done = true;
      socket.destroy();
      if (error) reject(error); else resolve(reply);
    }
    socket.setTimeout(timeoutMs, () => finish(Error('NATIVE_TRANSPORT_TIMEOUT')));
    socket.on('connect', () => socket.write(request));
    socket.on('data', part => {
      size += part.length;
      if (size > MAX_FRAME) return finish(Error('NATIVE_FRAME_TOO_LARGE'));
      parts.push(part);
      // The host writes one message frame per connection. A complete JSON reply is
      // sufficient; waiting for EOF can deadlock against FlushFileBuffers on Windows.
      try { const raw=Buffer.concat(parts); const parsed=JSON.parse(raw.toString('utf8')); finish(null, rawReply ? raw : parsed); }
      catch { /* the message may span Node data chunks */ }
    });
    socket.on('error', error => finish(error));
    socket.on('end', () => finish(Error('NATIVE_MALFORMED_REPLY')));
  });
}

function readSession(fsImpl, discovery, now = Date.now()) {
  if (!discovery?.data_dir) throw Error('HOST_DATA_DIR_ABSENT');
  const file = path.join(discovery.data_dir, 'host', 'session.json');
  const stat = fsImpl.lstatSync(file);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size <= 0 || stat.size > MAX_FRAME) {
    throw Error('HOST_SESSION_FILE_INVALID');
  }
  let session;
  try { session = JSON.parse(fsImpl.readFileSync(file, 'utf8')); }
  catch { throw Error('HOST_SESSION_FILE_INVALID'); }
  const expires = typeof session.expires_at === 'string' &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(session.expires_at)
    ? Date.parse(session.expires_at) : NaN;
  if (typeof session.token !== 'string' || !session.token || !Number.isFinite(expires) || now >= expires) {
    throw Error('HOST_SESSION_EXPIRED');
  }
  return session.token;
}

function createCredentialProvider({ fsImpl = fs, dial = dialNative, now = Date.now, clientId = 'desktop-shell' } = {}) {
  let renewing = null;
  function identityFor(discovery) {
    const id = hostInstanceId(fsImpl, discovery);
    // Copy the verified fields: a caller changing its discovery object while
    // the pipe request is pending must not redirect the session-file read.
    const bound = { host_instance_id: id, url: discovery.url, data_dir: discovery.data_dir, pid: discovery.pid };
    return { id, bound, key: JSON.stringify([id, bound.url, bound.data_dir, bound.pid]) };
  }
  return async function credentialFor(discovery, force = false) {
    if (renewing) {
      if (identityFor(discovery).key !== renewing.key) throw Error('HOST_CHANGED_DURING_RENEWAL');
      return renewing.promise;
    }
    if (!force) {
      try { return readSession(fsImpl, discovery, now()); } catch { /* bootstrap a new session */ }
    }
    const identity = identityFor(discovery);
    const promise = (async () => {
      const reply = await dial('\\\\.\\pipe\\ResearchOSHost-v1-' + identity.id.slice(5),
        { kind: 'NATIVE_USER_BOOTSTRAP_REQUEST', client_id: clientId, payload: {} });
      if (reply?.kind === 'NATIVE_ERROR') throw Error('NATIVE_' + String(reply.error?.code || 'ERROR'));
      if (reply?.kind !== 'NATIVE_USER_BOOTSTRAP_RESULT' || reply.payload?.host_instance_id !== identity.id ||
          reply.payload?.client_id !== clientId || reply.payload?.credential_exposed_to_renderer !== false) {
        throw Error('NATIVE_WRONG_REPLY');
      }
      return readSession(fsImpl, identity.bound, now());
    })();
    renewing = { key: identity.key, promise };
    try { return await promise; }
    finally { if (renewing?.promise === promise) renewing = null; }
  };
}

// Separate from credential acquisition: this operation never bootstraps,
// renews, reads session.json or accepts a renderer-provided proof label.
function createClientAttestor({ fsImpl = fs, dial = (pipe, frame) => dialNative(pipe, frame, 5000, true), now = Date.now } = {}) {
  const closed = (value, keys) => value && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value,key));
  const validExpiry = value => {
    if (typeof value!=='string') return false;
    const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/.exec(value);
    if (!m) return false;
    const y=Number(m[1]),month=Number(m[2]),day=Number(m[3]);
    const days=[31,28+Number(y%4===0&&(y%100!==0||y%400===0)),31,30,31,30,31,31,30,31,30,31];
    return month>=1 && month<=12 && day>=1 && day<=days[month-1] && Number(m[4])<=23 &&
      Number(m[5])<=59 && Number(m[6])<=59 && (m[7]==='Z' || (Number(m[7].slice(1,3))<=23 && Number(m[7].slice(4))<=59)) && Date.parse(value)>now();
  };
  return async function attestCreate(discovery, raw, headers) {
    try {
      if (!Buffer.isBuffer(raw)) throw Error();
      const id=hostInstanceId(fsImpl,discovery);
      const identity=JSON.stringify([id,discovery.url,discovery.data_dir,discovery.pid]);
      const request=privateJSON(new TextDecoder('utf-8',{fatal:true}).decode(raw));
      const auth=headers?.Authorization;
      if (typeof auth!=='string' || !auth.startsWith('Bearer ')) throw Error();
      const credential=auth.slice(7);
      if (!credential || [...credential].length>1024 || [...credential].some(c=>c.codePointAt(0)>=0xd800&&c.codePointAt(0)<=0xdfff) || request.method!=='session.create' ||
          typeof request.client_id!=='string' || !request.client_id ||
          !/^[A-Za-z0-9._:-]{1,64}$/.test(request.command_id) ||
          typeof request.project_id!=='string' || !request.project_id ||
          request.session_id!==null || request.expected_revision!==null || request.writer_epoch!==null) throw Error();
      const frame={kind:'NATIVE_CLIENT_ATTEST_REQUEST',client_id:request.client_id,payload:{
        schema_version:1,credential_value:credential,command_id:request.command_id,method:'session.create',
        project_id:request.project_id,request_raw_sha256:'sha256:'+crypto.createHash('sha256').update(raw).digest('hex'),
        session_id:null,expected_revision:null,writer_epoch:null}};
      if (Buffer.byteLength(JSON.stringify(frame))>MAX_FRAME) throw Error();
      const response=await dial('\\\\.\\pipe\\ResearchOSHost-v1-'+id.slice(5),frame);
      if (!Buffer.isBuffer(response) && typeof response!=='string') throw Error();
      if (Buffer.byteLength(response)>MAX_FRAME) throw Error();
      const reply=privateJSON(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.from(response)));
      if (!closed(reply,['kind','payload']) || reply.kind!=='NATIVE_CLIENT_ATTEST_RESULT') throw Error();
      const proof=reply.payload;
      if (!closed(proof,['schema_version','attestation_ref','client_instance_ref','host_instance_id','expires_at']) ||
          proof.schema_version!==1 || typeof proof.attestation_ref!=='string' || !/^natt-[0-9a-f]{64}$/.test(proof.attestation_ref) ||
          typeof proof.client_instance_ref!=='string' || !/^nci-[0-9a-f]{32}$/.test(proof.client_instance_ref) || proof.host_instance_id!==id ||
          !validExpiry(proof.expires_at)) throw Error();
      if (identity!==JSON.stringify([hostInstanceId(fsImpl,discovery),discovery.url,discovery.data_dir,discovery.pid])) throw Error();
      return proof.attestation_ref;
    } catch { throw Error('NATIVE_CREATE_ATTESTATION_UNAVAILABLE'); }
  };
}

module.exports = { HOST_ID, MAX_FRAME, hostInstanceId, dialNative, readSession, createCredentialProvider, createClientAttestor };

'use strict';

const fs = require('node:fs');
const net = require('node:net');
const path = require('node:path');

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

function dialNative(pipeName, frame) {
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
    socket.setTimeout(5000, () => finish(Error('NATIVE_TRANSPORT_TIMEOUT')));
    socket.on('connect', () => socket.write(request));
    socket.on('data', part => {
      size += part.length;
      if (size > MAX_FRAME) return finish(Error('NATIVE_FRAME_TOO_LARGE'));
      parts.push(part);
      // The host writes one message frame per connection. A complete JSON reply is
      // sufficient; waiting for EOF can deadlock against FlushFileBuffers on Windows.
      try { finish(null, JSON.parse(Buffer.concat(parts).toString('utf8'))); }
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

module.exports = { HOST_ID, MAX_FRAME, hostInstanceId, dialNative, readSession, createCredentialProvider };

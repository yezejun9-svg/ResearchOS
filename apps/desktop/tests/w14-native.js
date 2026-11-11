'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const host = require('../main/lib/host.js');
const native = require('../main/lib/native.js');
const ipc = require('../main/lib/ipc.js');
const { createContextStore } = require('../main/lib/context.js');

const discovery = { url: 'http://127.0.0.1:18999', pid: 1234, data_dir: 'C:\\researchos-host',
  host_instance_id: 'host-012345abcdef' };

function coreDeps(extra = {}) {
  return Object.assign({
    fsImpl: { readFileSync: () => JSON.stringify(discovery) }, discoveryFile: 'discovery.json',
    httpImpl: { get(_url, _options, callback) {
      const req = new EventEmitter();
      process.nextTick(() => {
        const response = new EventEmitter();
        response.statusCode = 200;
        callback(response);
        response.emit('end');
      });
      return req;
    } },
    clientId: 'desktop-shell', commandIdFor: () => 'cmd-test',
    sessionState: { projectId: 'project-one', sessionId: 'session-one', expectedRevision: null, writerEpoch: null },
  }, extra);
}

async function main() {
  assert.equal(host.readDiscovery({ readFileSync: () => JSON.stringify(discovery) }, 'd').ok, true);
  for (const url of ['http://example.com:18999', 'https://127.0.0.1:18999', 'http://127.0.0.1:18999@evil.test']) {
    assert.equal(host.readDiscovery({ readFileSync: () => JSON.stringify({ url }) }, 'd').ok, false);
  }
  assert.equal(native.hostInstanceId({ readFileSync() { throw Error('not needed'); } }, discovery), discovery.host_instance_id);
  const legacy = { ...discovery, host_instance_id: '' };
  assert.equal(native.hostInstanceId({ readFileSync: () => JSON.stringify(discovery) }, legacy), discovery.host_instance_id);
  assert.throws(() => native.hostInstanceId({ readFileSync: () => JSON.stringify({ ...discovery, pid: 9 }) }, legacy),
    /HOST_NATIVE_DISCOVERY_MISMATCH/);

  let expires = Date.now() - 1000;
  let token = 'old-token';
  const stat = { isFile: () => true, isSymbolicLink: () => false, size: 80 };
  const sessionFs = {
    lstatSync: () => stat,
    readFileSync: () => JSON.stringify({ token, expires_at: new Date(expires).toISOString() }),
  };
  const frames = [];
  const credentialFor = native.createCredentialProvider({ fsImpl: sessionFs, dial: async (name, frame) => {
    frames.push({ name, frame });
    token = 'renewed-token';
    expires = Date.now() + 60_000;
    return { kind: 'NATIVE_USER_BOOTSTRAP_RESULT', payload: {
      host_instance_id: discovery.host_instance_id, client_id: 'desktop-shell', credential_exposed_to_renderer: false,
    } };
  } });
  assert.equal(await credentialFor(discovery), 'renewed-token');
  assert.equal(await credentialFor(discovery), 'renewed-token');
  assert.equal(frames.length, 1);
  assert.equal(frames[0].name, '\\\\.\\pipe\\ResearchOSHost-v1-012345abcdef');
  assert.deepEqual(frames[0].frame, { kind: 'NATIVE_USER_BOOTSTRAP_REQUEST', client_id: 'desktop-shell', payload: {} });

  // A pending renewal can be shared only by callers for that exact host.
  // B must not receive A's actual session token, even if A's discovery object
  // changes while the native pipe awaits its reply.
  const hostA = { ...discovery, data_dir: 'C:\\host-a' };
  const hostB = { url: 'http://127.0.0.1:19000', pid: 5678, data_dir: 'C:\\host-b',
    host_instance_id: 'host-fedcba987654' };
  const tokenByFile = new Map([
    [path.join(hostA.data_dir, 'host', 'session.json'), 'old-A'],
    [path.join(hostB.data_dir, 'host', 'session.json'), 'old-B'],
  ]);
  const twoHostFs = { lstatSync: () => stat, readFileSync(file) {
    assert(tokenByFile.has(file), `unexpected session file: ${file}`);
    return JSON.stringify({ token: tokenByFile.get(file), expires_at: new Date(Date.now() + 60_000).toISOString() });
  } };
  let finishA;
  const waitA = new Promise(resolve => { finishA = resolve; });
  const pipes = [];
  const twoHostCredential = native.createCredentialProvider({ fsImpl: twoHostFs, dial: async (name) => {
    pipes.push(name);
    const forA = name.endsWith('012345abcdef');
    if (forA) await waitA;
    const target = forA ? hostA : hostB;
    tokenByFile.set(path.join(target.data_dir, 'host', 'session.json'), forA ? 'actual-token-A' : 'actual-token-B');
    return { kind: 'NATIVE_USER_BOOTSTRAP_RESULT', payload: {
      host_instance_id: target.host_instance_id, client_id: 'desktop-shell', credential_exposed_to_renderer: false,
    } };
  } });
  const mutableA = { ...hostA };
  const firstA = twoHostCredential(mutableA, true);
  const sharedA = twoHostCredential({ ...hostA }, true);
  mutableA.data_dir = hostB.data_dir;
  await assert.rejects(twoHostCredential(hostB, true), /HOST_CHANGED_DURING_RENEWAL/);
  assert.equal(pipes.length, 1, 'B did not launch a pipe request while A was renewing');
  finishA();
  assert.equal(await firstA, 'actual-token-A');
  assert.equal(await sharedA, 'actual-token-A');
  const tokenB = await twoHostCredential(hostB, true);
  assert.equal(tokenB, 'actual-token-B');
  assert.notEqual(tokenB, 'actual-token-A');
  assert.equal(pipes.length, 2);

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-desktop-context-'));
  const file = path.join(tempDir, 'desktop-context.json');
  try {
    const store = createContextStore(file);
    store.save({ projectId: 'project-one', sessionId: 'session-one' });
    assert.deepEqual(store.load(), { projectId: 'project-one', sessionId: 'session-one' });
    store.save({ projectId: 'project-one', sessionId: 'session-one' });
    assert.equal(fs.readFileSync(file, 'utf8').includes('token'), false);
    const handlers = new Map();
    const register = { handle: (name, callback) => handlers.set(name, callback) };
    let calls = 0;
    const { harness, snapshot } = await import('../../../tests/ui/desktop/http-wire-boundary.test.mjs');
    const fixtures = [];
    try {
      const good = await harness(async raw => {
        calls++;
        const envelope = JSON.parse(raw.toString('utf8'));
        assert.equal(envelope.method, 'session.get');
        return {body:{protocol_version:envelope.protocol_version,command_id:envelope.command_id,method:envelope.method,
          session_id:'session-one',revision:7,status:'COMPLETED',error_code:null,error:null,
          result:snapshot({project_id:'project-one',session_id:'session-one',revision:7})}};
      }); fixtures.push(good);
      const deps = coreDeps({contextStore:store,contextVerified:false,credentialFor:async()=> 'renewed-token',
        v2Transport:(_verb,_url,envelope,headers)=>good.transport(_verb,good.url+'/v2/command',envelope,headers)});
      ipc.registerDesktopReview(register,deps);
      const context = await handlers.get('ros:desktop:context')();
      assert.deepEqual(context, { project_id: 'project-one', session_id: 'session-one' });
      assert.equal(calls, 1);
      assert.equal(deps.sessionState.expectedRevision, 7);
      assert.equal((await handlers.get('ros:desktop:context')()).session_id, 'session-one');
      assert.equal(calls, 1);
      const wrong = await harness(async raw => {
        const envelope=JSON.parse(raw.toString('utf8'));
        return {body:{protocol_version:envelope.protocol_version,command_id:envelope.command_id,method:envelope.method,
          session_id:'session-one',revision:1,status:'COMPLETED',error_code:null,error:null,
          result:snapshot({project_id:'other-project',session_id:'session-one',revision:1})}};
      }); fixtures.push(wrong);
      const mismatched=coreDeps({contextStore:store,contextVerified:false,credentialFor:async()=> 'renewed-token',
        v2Transport:(verb,_url,envelope,headers)=>wrong.transport(verb,wrong.url+'/v2/command',envelope,headers)});
      const negativeHandlers = new Map();
      ipc.registerDesktopReview({ handle: (name, callback) => negativeHandlers.set(name, callback) }, mismatched);
      assert.equal((await negativeHandlers.get('ros:desktop:context')()).session_id, null);
      let commandCalls = 0;
      let forced = 0;
      const auth = await harness(async()=>{commandCalls++;return {status:401,raw:Buffer.from('unauthorized')};});fixtures.push(auth);
      const unauthorized = await ipc.callV2(coreDeps({
        sessionState:{projectId:'project-one',sessionId:'session-one',expectedRevision:7,writerEpoch:2,writerClientId:'desktop-shell',writerExpiresAt:'2099-01-01T00:00:00Z'},
        credentialFor:async(_d,force)=>{if(force)forced++;return 'renewed-token';},
        v2Transport:(verb,_url,envelope,headers)=>auth.transport(verb,auth.url+'/v2/command',envelope,headers)}),
        'session.send',{text:'one command only',attachment_artifact_ids:[],delivery:'NORMAL'});
      assert.equal(unauthorized.reason, 'AUTH_REFRESHED_RETRY_REQUIRED');
      assert.equal(commandCalls, 1);
      assert.equal(forced, 1);
    } finally { for(const fixture of fixtures)await fixture.close(); }
  } finally {
    if (fs.existsSync(file)) fs.unlinkSync(file);
    fs.rmdirSync(tempDir);
  }
  console.log(JSON.stringify({ status: 'PASS', scope: 'DESKTOP_NATIVE_CREDENTIAL_AND_CONTEXT',
    native_bootstraps: frames.length, concurrent_host_isolation: true, unsafe_retries: 0 }));
}

main().catch(error => { console.error(error); process.exitCode = 1; });

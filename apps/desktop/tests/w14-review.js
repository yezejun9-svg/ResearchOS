'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const ipc = require('../main/lib/ipc.js');

const handlers = new Map();
const ipcMain = { handle(name, fn) {
  assert(!handlers.has(name), `duplicate IPC channel: ${name}`);
  handlers.set(name, fn);
} };
const state = { projectId: null, sessionId: null, expectedRevision: null, writerEpoch: null };
const calls = [];
let claimed = false;
function snapshot() {
  return {
    project_id: 'project-one', session_id: 'session-one', revision: claimed ? 8 : 7,
    writer: { client_id: claimed ? 'desktop-shell' : 'cli', epoch: claimed ? 4 : 2 },
    active_run_id: null, run_status: 'SETTLED', event_sequence: 3,
    earliest_event_sequence: 1, messages: [],
  };
}
const deps = {
  sessionState: state, clientId: 'desktop-shell', credential: 'test-credential',
  commandIdFor: method => `test-${method}-${calls.length}`,
  fsImpl: { readFileSync: () => JSON.stringify({ url: 'http://127.0.0.1:18999' }) },
  discoveryFile: 'test-discovery',
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
  transport: async (_verb, _url, envelope) => {
    calls.push(envelope);
    let status = 'COMPLETED';
    let result = {};
    let revision = snapshot().revision;
    switch (envelope.method) {
      case 'session.list': result = { items: [snapshot()], next_cursor: null }; break;
      case 'session.get': result = snapshot(); break;
      case 'session.events': result = { events: [], next_sequence: 3, high_watermark: 3, has_more: false }; break;
      case 'session.attach':
        if (envelope.payload.request_write_owner) {
          assert.equal(envelope.expected_revision, 7);
          assert.equal(envelope.writer_epoch, null);
          claimed = true;
          status = 'ACKNOWLEDGED';
          revision = 8;
        } else {
          assert.equal(envelope.writer_epoch, 2);
          result = { snapshot: snapshot(), write_owner_acquired: false };
        }
        break;
      case 'session.send':
        assert.equal(envelope.project_id, 'project-one');
        assert.equal(envelope.session_id, 'session-one');
        assert.equal(envelope.expected_revision, 8);
        assert.equal(envelope.writer_epoch, 4);
        result = { message_id: 'message-one', queue_position: 0, run_id: 'run-one', snapshot: snapshot() };
        break;
      default: throw Error(`unexpected method ${envelope.method}`);
    }
    return { status, revision, result };
  },
  pickDirectory: async () => ({ ok: false, reason: 'PICKER_CANCELLED' }),
};

async function main() {
  ipc.register(ipcMain, deps);
  ipc.registerV2(ipcMain, deps);
  ipc.registerDesktopReview(ipcMain, deps);
  assert.equal(handlers.size, ipc.BRIDGE.length + ipc.V2_METHODS.length + 4);
  const invoke = (name, body) => handlers.get(name)({}, body);
  assert.equal((await invoke('ros:workspacePickDirectory', {})).reason, 'PICKER_CANCELLED');
  assert.equal((await invoke('ros:desktop:selectProject', { project_id: 'project-one' })).ok, true);
  assert.equal((await invoke('ros:v2:session.list', { cursor: null, limit: 50 })).result.items.length, 1);
  const opened = await invoke('ros:desktop:openSession', { session_id: 'session-one' });
  assert.equal(opened.ok, true);
  assert.equal(state.writerEpoch, 2);
  assert.equal((await invoke('ros:v2:session.attach', { after_sequence: 3, request_write_owner: false })).ok, true);
  assert.equal((await invoke('ros:v2:session.events', { after_sequence: 0, limit: 200 })).result.next_sequence, 3);
  assert.equal((await invoke('ros:v2:session.attach', { after_sequence: 3, request_write_owner: true })).ok, true);
  assert.equal(state.writerEpoch, null);
  assert.equal((await invoke('ros:v2:session.get', {})).ok, true);
  assert.equal(state.writerEpoch, 4);
  assert.equal((await invoke('ros:v2:session.send', { text: 'continue', attachment_artifact_ids: [], delivery: 'NORMAL' })).ok, true);
  assert.deepEqual(calls.map(call => call.method), [
    'session.list', 'session.get', 'session.attach', 'session.events',
    'session.attach', 'session.get', 'session.send',
  ]);
  console.log(JSON.stringify({ status: 'PASS', scope: 'IPC_FIXTURE', channels: handlers.size,
    methods: calls.map(call => call.method), final_writer_epoch: state.writerEpoch }));
}

main().catch(error => { console.error(error); process.exitCode = 1; });

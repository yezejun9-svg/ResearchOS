import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { EventEmitter } from 'node:events'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const { strictJSON, createDesktopManagement, observeWindowsProcess } = require('../../../apps/desktop/main/lib/desktop-management.js')
const { registerDesktopQualification } = require('../../../apps/desktop/main/lib/ipc.js')

test('private JSON rejects duplicate, unsafe, malformed and trailing frames', () => {
  assert.equal(strictJSON(Buffer.from('{"a":1}')).a, 1)
  for (const raw of ['{"a":1,"a":2}', '{"a":9007199254740993}', '{"a":1.5}',
    '{"a":1}{}', '{"a":"\\ud800"}']) assert.throws(() => strictJSON(Buffer.from(raw)))
  assert.throws(() => strictJSON(Buffer.from([0xff])))
})

test('Windows process observation requests UTF-8 before hashing a Unicode image path', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-进程-'))
  const image = path.join(dir, 'process.exe')
  fs.writeFileSync(image, Buffer.from('MZ-process-fixture'))
  try {
    const identity = observeWindowsProcess(1234, fs, (_file, _argv, options) => {
      assert.equal(options.encoding, 'utf8')
      assert.match(_argv.at(-1), /\[Console\]::OutputEncoding=\[System\.Text\.UTF8Encoding\]/)
      return JSON.stringify({ PID: 1234, FileTime: '134362726341143644', Image: image })
    })
    assert.equal(identity.PID, 1234)
    assert.match(identity.ImageSHA256, /^[a-f0-9]{64}$/)
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
})

function fixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-managed-client-'))
  const discoveryFile = path.join(dir, 'discovery.json')
  const hostId = 'host-aaaaaaaaaaaa', pid = 24680
  fs.writeFileSync(discoveryFile, JSON.stringify({ url: 'http://127.0.0.1:54321/',
    pid, data_dir: dir, host_instance_id: hostId }))
  let context = 'session-a', confirmCount = 0, prepareCount = 0, operationLog = []
  let suppress = false, transform = value => value
  const queued = []
  const identity = id => ({ PID: id, CreatedNS: String(id) + '000000000', ImageSHA256: 'a'.repeat(64) })
  const child = new EventEmitter()
  child.pid = pid
  child.stdin = { write(bytes, callback) {
    const request = JSON.parse(bytes.toString('utf8'))
    operationLog.push(request)
    if (request.operation === 'CONFIRM') confirmCount++
    if (request.operation === 'PREPARE') prepareCount++
    const requestBody = { request_id: `req-${prepareCount}`, project_id: request.project_id || 'project-1',
      session_id: request.session_id || 'session-1',
      model_config_ref: 'model-1', owner_host: hostId, authorize_purpose: 'mu_turn',
      issued_at: new Date(Date.now() - 1000).toISOString(), expires_at: new Date(Date.now() + 58000).toISOString() }
    const result = request.operation === 'PREPARE' ? { state: 'AWAITING_CONFIRMATION', request: requestBody,
      request_hash: 'sha256:' + 'b'.repeat(64), model_calls: 1, tools: [], purpose: 'mu_turn',
      purpose_seconds: 600, cost_basis: 'UNKNOWN', money: null }
      : request.operation === 'STATUS' ? { request_id: manager.intent?.requestId, request_hash: 'sha256:' + 'b'.repeat(64),
        state: 'QUALIFIED_PURPOSE_AUTHORIZED', consumed: true }
      : { state: request.operation === 'SHUTDOWN' ? 'SHUTDOWN_ACCEPTED' : 'QUALIFIED_PURPOSE_AUTHORIZED' }
    const answer = { protocol: 'researchos-desktop-management/1',
        message_id: request.message_id, operation: request.operation, host_id: hostId,
        kind: 'RESULT', result }
    if (suppress) queued.push(answer)
    else setImmediate(() => {
      manager.onLine(Buffer.from(JSON.stringify(transform(answer))))
      if (request.operation === 'SHUTDOWN') setImmediate(() => child.emit('exit', 0, null))
    })
    callback?.()
    return true
  } }
  const manager = createDesktopManagement({ fsImpl: fs, discoveryFile, dataRoot: dir,
    context: () => context, observeProcess: identity })
  manager.state = 'READY'; manager.child = child; manager.childExited = false; manager.hostId = hostId
  manager.identity = identity(pid); manager.parentIdentity = identity(process.pid)
  manager.exitPromise = new Promise(resolve => { manager.resolveExit = resolve })
  child.on('exit', (code, signal) => manager.onExit(code, signal))
  return { manager, child, dir, log: operationLog, confirmCount: () => confirmCount,
    suppress: value => { suppress = value }, transform: value => { transform = value },
    release: change => { const answer = queued.shift(); manager.onLine(Buffer.from(JSON.stringify(change ? change(answer) : answer))) },
    setContext: value => { context = value }, close: () => fs.rmSync(dir, { recursive: true, force: true }) }
}

const nativeContext = (changes = {}) => JSON.stringify(Object.assign(
  ['project-1', 'session-1', '1', '1', 'desktop-shell', '2026-10-14T01:00:00Z', 2, 4], changes))
const qualificationScope = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1', model: {} }

test('bound original STATUS survives writer renewal without transferring authorization or rearming confirmation', async () => {
  const f = fixture(), handlers = new Map()
  try {
    f.setContext(nativeContext())
    await f.manager.prepare(qualificationScope, nativeContext())
    await f.manager.confirm()
    const original = { ...f.manager.intent }
    f.setContext(nativeContext({ 2: '9', 3: '3', 5: '2026-10-14T02:00:00Z', 7: 12 }))
    registerDesktopQualification({ handle(name, fn) { handlers.set(name, fn) } }, {
      qualifierSenderAllowed: () => true, desktopManagement: f.manager,
    })
    // A server consumed=false reply must never undo the local one-shot barrier.
    f.transform(answer => { answer.result.consumed = false; return answer })
    const reply = await handlers.get('ros:desktop:qualification:status')({}, { request_id: 'forged' })
    assert.equal(reply.ok, true)
    assert.equal(reply.state, 'ORIGINAL_REQUEST_HISTORY')
    assert.equal(reply.status_scope, 'ORIGINAL_REQUEST_HISTORY')
    assert.equal(reply.original_state, 'QUALIFIED_PURPOSE_AUTHORIZED')
    assert(reply.original_checked_at)
    assert.equal(reply.authorized, false)
    assert.equal(reply.checked_at, null)
    assert.equal(reply.consumed, true)
    for (const key of ['requestId', 'requestHash', 'context', 'modelRef'])
      assert.equal(f.manager.intent[key], original[key])
    assert.equal(f.log.at(-1).request_id, original.requestId)
    assert.equal(f.log.at(-1).request_hash, original.requestHash)
    await assert.rejects(f.manager.confirm(), { code: 'CONFIRM_NOT_AVAILABLE' })
    f.setContext(nativeContext())
    assert.equal(f.manager.summary().authorized, false)
    assert.equal((await f.manager.status()).authorized, true)
    assert.equal(f.confirmCount(), 1)
  } finally { f.close() }
})

test('historical unconsumed STATUS keeps original confirmation context strict', async () => {
  const f = fixture()
  try {
    f.setContext(nativeContext())
    await f.manager.prepare(qualificationScope, nativeContext())
    f.setContext(nativeContext({ 2: '2', 7: 5 }))
    f.transform(answer => { answer.result.state = 'AWAITING_CONFIRMATION'; answer.result.consumed = false; return answer })
    const result = await f.manager.status()
    assert.equal(result.authorized, false)
    assert.equal(result.consumed, false)
    await assert.rejects(f.manager.confirm(), { code: 'CONTEXT_CHANGED' })
    assert.equal(f.confirmCount(), 0)
  } finally { f.close() }
})

test('writer changes while STATUS is in flight return history without claiming current authorization', async () => {
  const f = fixture()
  try {
    f.setContext(nativeContext())
    await f.manager.prepare(qualificationScope, nativeContext())
    await f.manager.confirm()
    f.suppress(true)
    const pending = f.manager.status()
    f.setContext(nativeContext({ 2: '9', 3: '3', 7: 12 }))
    f.release()
    const result = await pending
    assert.equal(result.status_scope, 'ORIGINAL_REQUEST_HISTORY')
    assert.equal(result.authorized, false)
    assert(result.original_checked_at)
    assert.equal(f.manager.intent.checkedContext, null)
    assert.equal(f.confirmCount(), 1)
  } finally { f.close() }
})

test('original STATUS blocks project, session, selection generation changes before and after async dispatch', async () => {
  for (const changed of [{ 0: 'project-2' }, { 1: 'session-2' }, { 6: 4 }]) {
    const f = fixture()
    try {
      f.setContext(nativeContext())
      await f.manager.prepare(qualificationScope, nativeContext())
      await f.manager.confirm()
      const count = f.log.length, checkedAt = f.manager.intent.checkedAt
      f.setContext(nativeContext(changed))
      await assert.rejects(f.manager.status(), { code: 'CONTEXT_CHANGED' })
      assert.equal(f.log.length, count)
      f.setContext(nativeContext({ 7: 5 }))
      f.suppress(true)
      const pending = f.manager.status()
      f.setContext(nativeContext(changed))
      f.release()
      await assert.rejects(pending, { code: 'CONTEXT_CHANGED' })
      assert.equal(f.manager.intent.checkedAt, checkedAt)
      assert.equal(f.manager.intent.needsRecheck, true)
      assert.equal(f.manager.summary().authorized, false)
    } finally { f.close() }
  }
})

test('historical STATUS validates original native identity before and after async reply', async () => {
  for (const during of [false, true]) {
    const f = fixture()
    try {
      f.setContext(nativeContext())
      await f.manager.prepare(qualificationScope, nativeContext())
      await f.manager.confirm()
      f.setContext(nativeContext({ 7: 5 }))
      f.suppress(true)
      const before = f.log.length
      const pending = during ? f.manager.status() : null
      // Even a self-consistent replacement manager/native identity is not this request's origin.
      f.manager.identity = { ...f.manager.identity, CreatedNS: '999999999' }
      f.manager.observe = id => id === f.child.pid ? f.manager.identity : f.manager.parentIdentity
      if (during) f.release()
      await assert.rejects(pending || f.manager.status(), { code: 'QUALIFICATION_ORIGIN_CHANGED' })
      assert.equal(f.log.length, before + Number(during))
      assert.equal(f.manager.summary().authorized, false)
    } finally { f.close() }
  }
})

test('historical STATUS rejects malformed and replayed results without a fresh timestamp', async () => {
  for (const mutate of [answer => { answer.result.request_id = 'foreign' },
    answer => { answer.result.request_hash = 'sha256:' + 'c'.repeat(64) },
    answer => { answer.result.state = 'UNKNOWN' }, answer => { answer.result.consumed = 'true' },
    answer => { answer.message_id = 'replayed' }]) {
    const f = fixture()
    try {
      f.setContext(nativeContext())
      await f.manager.prepare(qualificationScope, nativeContext())
      await f.manager.confirm()
      f.setContext(nativeContext({ 7: 5 }))
      const checkedAt = f.manager.intent.checkedAt
      f.transform(answer => { mutate(answer); return answer })
      await assert.rejects(f.manager.status(), error => ['STATUS_RESULT_INVALID', 'PRIVATE_REPLY_MISMATCH'].includes(error.code))
      assert.equal(f.manager.intent.checkedAt, checkedAt)
      assert.equal(f.manager.intent.needsRecheck, true)
      assert.equal(f.manager.summary().authorized, false)
    } finally { f.close() }
  }
})

test('historical STATUS timeout preserves the private pending barrier until the original late reply', async () => {
  const f = fixture()
  try {
    f.setContext(nativeContext())
    await f.manager.prepare(qualificationScope, nativeContext())
    await f.manager.confirm()
    f.setContext(nativeContext({ 7: 5 }))
    f.suppress(true)
    const exchange = f.manager.exchange.bind(f.manager)
    f.manager.exchange = (operation, scope) => exchange(operation, scope, 5)
    await assert.rejects(f.manager.status(), { code: 'MANAGEMENT_REPLY_UNCERTAIN' })
    assert.equal(f.manager.summary().state, 'PRIVATE_COMMAND_UNCERTAIN')
    await assert.rejects(f.manager.status(), { code: 'MANAGEMENT_COMMAND_PENDING' })
    await assert.rejects(f.manager.confirm(), { code: 'MANAGEMENT_COMMAND_PENDING' })
    f.release()
    assert.equal(f.manager.intent.needsRecheck, true)
    assert.equal(f.manager.pending, null)
    assert.equal(f.confirmCount(), 1)
  } finally { f.close() }
})

test('one trusted session intent survives renderer calls and never resends CONFIRM', async () => {
  const f = fixture()
  try {
    const scope = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1',
      model: { provider_id: 'local', model_id: 'qwen3:4b-instruct' } }
    const ready = await f.manager.prepare(scope, 'session-a')
    assert.equal(ready.state, 'AWAITING_CONFIRMATION')
    assert.equal(f.log[0].operation, 'PREPARE')
    assert.deepEqual(Object.keys(f.log[0]).sort(), ['host_id', 'message_id', 'model_config_ref',
      'operation', 'project_id', 'protocol', 'session_id'].sort())
    assert.equal(f.confirmCount(), 0)
    const result = await f.manager.confirm()
    assert.equal(result.state, 'QUALIFIED_PURPOSE_AUTHORIZED')
    assert.equal(result.authorized, true)
    assert.equal(f.confirmCount(), 1)
    await assert.rejects(f.manager.confirm(), { code: 'CONFIRM_NOT_AVAILABLE' })
    await f.manager.status()
    assert.equal(f.confirmCount(), 1)
    f.setContext('session-b')
    assert.equal(f.manager.summary().state, 'CONTEXT_CHANGED_PENDING')
    await assert.rejects(f.manager.status(), { code: 'CONTEXT_CHANGED' })
    assert.equal(f.confirmCount(), 1)
  } finally { f.close() }
})

test('managed shutdown waits for actual normal child exit', async () => {
  const f = fixture()
  try {
    assert.equal(f.manager.hasUnconfirmedChild(), true)
    assert.deepEqual(await f.manager.shutdown(), { state: 'STOPPED', process_exit_confirmed: true })
    assert.equal(f.manager.hasUnconfirmedChild(), false)
    assert.equal(f.log.at(-1).operation, 'SHUTDOWN')
  } finally { f.close() }
})

test('validated unconfirmed expiry retires across a context change without losing original audit identity', async () => {
  const f = fixture(), realNow = Date.now
  try {
    const first = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1', model: {} }
    await f.manager.prepare(first, 'session-a')
    f.setContext('session-b')
    Date.now = () => realNow() + 61000
    assert.equal(f.manager.summary().state, 'EXPIRED')
    assert.equal(f.manager.summary().request_id, 'req-1')
    const next = await f.manager.prepare({ ...first, sessionId: 'session-2' }, 'session-b')
    assert.equal(next.request_id, 'req-2')
    assert.equal(next.previous_request_id, 'req-1')
    assert.equal(f.manager.retiredIntents.length, 1)
    assert.equal(f.manager.retiredIntents[0].requestHash, 'sha256:' + 'b'.repeat(64))
    assert.equal(f.manager.retiredIntents[0].retireReason, 'VALIDATED_UNCONFIRMED_EXPIRED')
    assert.equal(f.confirmCount(), 0)
    assert.deepEqual(f.log.map(frame => frame.operation), ['PREPARE', 'PREPARE'])
  } finally { Date.now = realNow; f.close() }
})

test('expiry never retires consumed or uncertain private operations', async () => {
  const f = fixture(), realNow = Date.now
  try {
    const scope = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1', model: {} }
    await f.manager.prepare(scope, 'session-a')
    Date.now = () => realNow() + 61000
    f.manager.pending = { operation: 'STATUS', timedOut: true }
    assert.equal(f.manager.summary().available, false)
    assert.equal(f.manager.summary().state, 'PRIVATE_COMMAND_UNCERTAIN')
    await assert.rejects(f.manager.prepare(scope, 'session-a'), { code: 'MANAGEMENT_COMMAND_PENDING' })
    assert.equal(f.manager.intent.requestId, 'req-1')
    assert.equal(f.manager.retiredIntents.length, 0)
    f.manager.pending = null
    f.manager.intent.confirmSent = true
    await assert.rejects(f.manager.prepare(scope, 'session-a'), { code: 'QUALIFICATION_INTENT_PENDING' })
    assert.equal(f.manager.retiredIntents.length, 0)
  } finally { Date.now = realNow; f.close() }
})

test('host switch immediately revokes current authorization and requires fresh original STATUS after return', async () => {
  const f = fixture()
  try {
    const scope = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1', model: {} }
    await f.manager.prepare(scope, 'session-a')
    assert.equal((await f.manager.confirm()).authorized, true)
    const discovery = path.join(f.dir, 'discovery.json')
    const original = fs.readFileSync(discovery)
    fs.writeFileSync(discovery, JSON.stringify({ url: 'http://127.0.0.1:54321/', pid: f.child.pid,
      data_dir: f.dir, host_instance_id: 'host-bbbbbbbbbbbb' }))
    const switched = f.manager.summary()
    assert.equal(switched.available, false)
    assert.equal(switched.authorized, false)
    assert.equal(switched.state, 'HOST_UNAVAILABLE')
    assert.equal(switched.reason, 'HOST_CHANGED')
    assert.equal(switched.request_id, 'req-1')
    const handlers = new Map()
    registerDesktopQualification({ handle(name, fn) { handlers.set(name, fn) } }, {
      qualifierSenderAllowed: () => true, desktopManagement: f.manager,
    })
    const current = await handlers.get('ros:desktop:qualification:current')({})
    assert.equal(current.available, false)
    assert.equal(current.authorized, false)
    assert.equal(current.request_id, 'req-1')
    fs.writeFileSync(discovery, original)
    assert.equal(f.manager.summary().authorized, false)
    assert.equal((await f.manager.status()).authorized, true)
    assert.equal(f.confirmCount(), 1)
  } finally { f.close() }
})

test('broken management pipe retains exit barrier until child exit is observed', () => {
  const f = fixture()
  try {
    f.manager.broken('MANAGEMENT_PIPE_EOF')
    assert.equal(f.manager.state, 'BROKEN')
    assert.equal(f.manager.hasUnconfirmedChild(), true)
    f.child.emit('exit', 2, null)
    assert.equal(f.manager.hasUnconfirmedChild(), false)
  } finally { f.close() }
})

test('changed session or native host refuses confirmation before dispatch', async () => {
  const f = fixture()
  try {
    const scope = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1', model: {} }
    await f.manager.prepare(scope, 'session-a')
    f.setContext('session-b')
    await assert.rejects(f.manager.confirm(), { code: 'CONTEXT_CHANGED' })
    assert.equal(f.confirmCount(), 0)
    f.setContext('session-a')
    fs.writeFileSync(path.join(f.dir, 'discovery.json'), JSON.stringify({ url: 'http://127.0.0.1:54321/',
      pid: f.child.pid, data_dir: f.dir, host_instance_id: 'host-bbbbbbbbbbbb' }))
    await assert.rejects(f.manager.confirm(), { code: 'HOST_CHANGED' })
    assert.equal(f.confirmCount(), 0)
  } finally { f.close() }
})

test('renderer cannot supply confirmation request ID, token or scope', async () => {
  const handlers = new Map()
  const calls = []
  let state = 'READY'
  registerDesktopQualification({ handle(name, fn) { handlers.set(name, fn) } }, {
    qualifierSenderAllowed: event => event?.sender?.getURL() === 'ros-app://desktop/',
    prepareQualificationScope: async () => ({ scope: { projectId: 'trusted' }, context: 'trusted-context' }),
    desktopManagement: {
      summary: () => ({ state }),
      prepare: (...args) => { calls.push(['PREPARE', args]); state = 'AWAITING_CONFIRMATION'; return { state } },
      confirm: (...args) => { calls.push(['CONFIRM', args]); state = 'UNRESOLVED'; return { state } },
      status: (...args) => { calls.push(['STATUS', args]); state = 'UNRESOLVED'; return { state } },
    },
  })
  const allowed = { sender: { getURL: () => 'ros-app://desktop/' } }
  const forged = { project_id: 'forged', request_id: 'forged', token: 'forged' }
  assert.deepEqual(await handlers.get('ros:desktop:qualification:prepare')(allowed, forged),
    { ok: true, state: 'AWAITING_CONFIRMATION' })
  await handlers.get('ros:desktop:qualification:confirm')(allowed, forged)
  await handlers.get('ros:desktop:qualification:status')(allowed, forged)
  assert.deepEqual(calls, [['PREPARE', [{ projectId: 'trusted' }, 'trusted-context']],
    ['CONFIRM', []], ['STATUS', []]])
  assert.deepEqual(await handlers.get('ros:desktop:qualification:confirm')({ sender: { getURL: () => 'https://evil/' } }, forged),
    { ok: false, reason: 'DESKTOP_ORIGIN_REQUIRED' })
})

test('IPC postflight catches a host switch after async STATUS but before the reply', async () => {
  const f = fixture(), handlers = new Map()
  try {
    const scope = { projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1', model: {} }
    await f.manager.prepare(scope, 'session-a')
    await f.manager.confirm()
    const discovery = path.join(f.dir, 'discovery.json')
    registerDesktopQualification({ handle(name, fn) { handlers.set(name, fn) } }, {
      qualifierSenderAllowed: () => true,
      desktopManagement: {
        summary: () => f.manager.summary(),
        status: async () => {
          const completed = await f.manager.status()
          assert.equal(completed.authorized, true)
          fs.writeFileSync(discovery, JSON.stringify({ url: 'http://127.0.0.1:54321/', pid: f.child.pid,
            data_dir: f.dir, host_instance_id: 'host-bbbbbbbbbbbb' }))
          return completed
        },
      },
    })
    const reply = await handlers.get('ros:desktop:qualification:status')({})
    assert.equal(reply.ok, true)
    assert.equal(reply.available, false)
    assert.equal(reply.authorized, false)
    assert.equal(reply.state, 'HOST_UNAVAILABLE')
    assert.equal(reply.request_id, 'req-1')
    assert.equal(f.confirmCount(), 1)
  } finally { f.close() }
})

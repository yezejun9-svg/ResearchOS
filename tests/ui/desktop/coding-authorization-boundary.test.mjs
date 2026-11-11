import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { EventEmitter } from 'node:events'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const { createDesktopManagement } = require('../../../apps/desktop/main/lib/desktop-management.js')
const { registerDesktopCoding, registerDesktopQualification } = require('../../../apps/desktop/main/lib/ipc.js')
const protocol = 'researchos-desktop-management/1'
const hash = 'sha256:' + 'b'.repeat(64)
const profileRef = () => ({ entity_type: 'Artifact', id: 'd'.repeat(32), revision: 1,
  content_hash: 'sha256:' + 'c'.repeat(64) })

function fixture() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ros-coding-client-'))
  const hostId = 'host-aaaaaaaaaaaa', pid = 24680
  const discoveryFile = path.join(dir, 'discovery.json')
  fs.writeFileSync(discoveryFile, JSON.stringify({ url: 'http://127.0.0.1:54321/', pid,
    data_dir: dir, host_instance_id: hostId }))
  let context = JSON.stringify(['project-1', 'session-1', 1, 1]), suppress = false, expiryMs = 55000
  let resourceGeneration = 0, rejectPrepareOnce = false
  let qualificationState = 'EXECUTION_SETTLED', qualificationConsumed = true
  let profileRefValue = profileRef()
  const queued = []
  const log = [], identity = id => ({ PID: id, CreatedNS: String(id) + '000000000', ImageSHA256: 'a'.repeat(64) })
  const child = new EventEmitter(); child.pid = pid
  const manager = createDesktopManagement({ fsImpl: fs, discoveryFile, dataRoot: dir,
    context: () => context, observeProcess: identity,
    codingResourceGeneration: () => resourceGeneration })
  child.stdin = { write(bytes, callback) {
    const frame = JSON.parse(bytes.toString('utf8')); log.push(frame)
    const base = { state: 'AWAITING_CODING_CONFIRMATION', request_id: 'coding-1', request_hash: hash,
      expires_at: new Date(Date.now() + expiryMs).toISOString(), project_id: 'project-1',
      session_id: 'session-1', old_model_config_ref: 'model-1', scope: coding(),
      frozen_checks: [{ id: 'value-check', package: './calc', test_pattern: '^TestValue$',
        source_count: 3, source_bytes: 123, source_manifest_hash: hash, toolchain_hash: hash,
        build_hash: hash, vendor_hash: '' }], normal_max_model_calls: 8,
      qualification_model_calls: 1, qualification_tool_calls: 0, model_calls: 0 }
    let result = frame.operation === 'PREPARE_CODING' ? { ...base, scope: frame.coding } :
      frame.operation === 'CONFIRM_CODING' || (frame.operation === 'STATUS_CODING' && log.some(item => item.operation === 'CONFIRM_CODING'))
        ? { ...base, state: 'CODING_CONFIGURED', scope: frame.operation === 'CONFIRM_CODING' ? log[0].coding : log[0].coding,
          model_config_ref: 'model-2', runtime_status: 'REGISTERED', profile_ref: profileRefValue,
          revision: 2, config_revision: 2 } : frame.operation === 'STATUS_CODING' &&
          Date.parse(manager.codingIntent?.expiresAt) <= Date.now()
            ? { ...base, state: 'EXPIRED' } : base
    if (frame.operation === 'PREPARE') result = { state: 'AWAITING_CONFIRMATION',
      request: { request_id: 'original-qualification', project_id: frame.project_id, session_id: frame.session_id,
        model_config_ref: frame.model_config_ref, owner_host: hostId, authorize_purpose: 'mu_turn',
        issued_at: new Date(Date.now() - 1000).toISOString(), expires_at: new Date(Date.now() + 55000).toISOString() },
      request_hash: hash, model_calls: 1, tools: [], purpose: 'mu_turn', purpose_seconds: 600,
      cost_basis: 'UNKNOWN', money: null }
    if (frame.operation === 'STATUS') result = { request_id: 'original-qualification', request_hash: hash,
      state: qualificationState, consumed: qualificationConsumed }
    if (frame.operation === 'CONFIRM') result = { state: 'EXECUTION_SETTLED' }
    const answer = { protocol, message_id: frame.message_id, operation: frame.operation,
      host_id: hostId, kind: 'RESULT', result }
    if (frame.operation === 'PREPARE_CODING' && rejectPrepareOnce) {
      rejectPrepareOnce = false; answer.kind = 'ERROR'; answer.result = null
      answer.error = { code: 'MANAGEMENT_REJECTED', message: 'fixture source path is missing' }
    }
    if (suppress) queued.push(answer)
    else setImmediate(() => manager.onLine(Buffer.from(JSON.stringify(answer))))
    callback?.(); return true
  } }
  manager.state = 'READY'; manager.child = child; manager.childExited = false; manager.hostId = hostId
  manager.identity = identity(pid); manager.parentIdentity = identity(process.pid)
  return { manager, log, dir, setContext: value => { context = value },
    setResourceGeneration: value => { resourceGeneration = value }, suppress: value => { suppress = value },
    rejectNextPrepare: () => { rejectPrepareOnce = true }, expiry: value => { expiryMs = value },
    qualification: (state, consumed = true) => { qualificationState = state; qualificationConsumed = consumed },
    setProfileRef: value => { profileRefValue = value },
    release: change => { const answer = queued.shift(); manager.onLine(Buffer.from(JSON.stringify(change ? change(answer) : answer))) },
    close: () => fs.rmSync(dir, { recursive: true, force: true }) }
}

function coding() { return { client_id: 'desktop-shell', expected_revision: 1, writer_epoch: 1,
  config_revision: 2, workspace_ref: 'workspace-1', read_paths: ['go.mod', 'calc/value.go', 'calc/value_test.go'],
  write_paths: ['calc/value.go'], max_read_bytes: 8192, max_write_bytes: 8192,
  max_tool_calls: 8, max_output_tokens: 2048, checks: [{ id: 'value-check', package: './calc',
    test_pattern: '^TestValue$', source_paths: ['go.mod', 'calc/value.go', 'calc/value_test.go'],
    toolchain_root: 'C:/trusted-go', timeout_seconds: 90, process_limit: 32,
    memory_mib: 1024, max_text_bytes: 4096 }] } }
const scope = () => ({ projectId: 'project-1', sessionId: 'session-1', modelRef: 'model-1',
  model: { provider_id: 'local', model_id: 'fixture' }, coding: coding() })
const review = () => ({ resource_generation: 0, workspace: { authorized_workspace_ref: 'workspace-1',
  display_name: 'Trusted workspace', display_path: 'C:/trusted-workspace', project_id: 'project-1',
  revision: 1, access: 'READ_WRITE', status: 'ACTIVE' } })
const original = JSON.stringify(['project-1', 'session-1', 1, 1])
const recheck = () => ({ context: original, scope: scope(), review: review() })
const prepare = f => f.manager.prepareCoding(scope(), original, review())
const approve = f => f.manager.confirmCoding(async () => true, async () => recheck())
const configuredResult = (f, ref) => ({ state: 'CODING_CONFIGURED', request_id: 'coding-1',
  request_hash: hash, project_id: 'project-1', session_id: 'session-1',
  old_model_config_ref: 'model-1', model_config_ref: 'model-2', runtime_status: 'REGISTERED',
  profile_ref: ref, model_calls: 0, normal_max_model_calls: 8, qualification_model_calls: 1,
  qualification_tool_calls: 0, scope: coding(), frozen_checks: f.manager.codingIntent.frozenChecks,
  revision: 2, config_revision: 2 })

const qualificationContext = (changes = {}) => JSON.stringify(Object.assign(
  ['project-1', 'session-1', '1', '1', 'desktop-shell', '2026-10-14T01:00:00Z', 2, 4], changes))
async function settledQualification(f) {
  f.setContext(qualificationContext())
  await f.manager.prepare(scope(), qualificationContext())
  await f.manager.confirm()
}

test('actual bound STATUS then coding PREPARE uses historical settlement and current model/config authority', async () => {
  const f = fixture(), handlers = new Map()
  try {
    await settledQualification(f)
    const originalRequest = { ...f.manager.intent }
    const current = qualificationContext({ 2: '9', 3: '3', 5: '2026-10-14T02:00:00Z', 7: 12 })
    f.setContext(current)
    const currentScope = scope()
    currentScope.modelRef = 'current-model-9'
    currentScope.coding.expected_revision = 9
    currentScope.coding.writer_epoch = 3
    currentScope.coding.config_revision = 10
    // Mirror the host's current model/config fields without changing production handlers.
    f.suppress(true)
    registerDesktopQualification({ handle(name, fn) { handlers.set(name, fn) } }, {
      qualifierSenderAllowed: () => true, desktopManagement: f.manager,
    })
    registerDesktopCoding({ handle(name, fn) { handlers.set(name, fn) } }, {
      codingSenderAllowed: () => true, desktopManagement: f.manager,
      prepareCodingScope: async () => ({ context: current, scope: currentScope, review: review() }),
    })
    const statusPromise = handlers.get('ros:desktop:qualification:status')({})
    f.release()
    const history = await statusPromise
    assert.equal(history.original_state, 'EXECUTION_SETTLED')
    assert.equal(history.status_scope, 'ORIGINAL_REQUEST_HISTORY')
    assert.equal(history.authorized, false)
    const preparedPromise = handlers.get('ros:desktop:coding:prepare')({}, {})
    await new Promise(resolve => setImmediate(resolve))
    f.release(answer => { answer.result.old_model_config_ref = currentScope.modelRef; return answer })
    const prepared = await preparedPromise
    assert.equal(prepared.ok, true)
    assert.equal(prepared.state, 'AWAITING_CODING_CONFIRMATION')
    assert.equal(prepared.model_calls, 0)
    assert.equal(f.log.at(-1).model_config_ref, 'current-model-9')
    assert.equal(f.log.at(-1).coding.expected_revision, 9)
    assert.equal(f.log.at(-1).coding.writer_epoch, 3)
    assert.equal(f.log.at(-1).coding.config_revision, 10)
    for (const key of ['requestId', 'requestHash', 'context', 'modelRef', 'confirmSent'])
      assert.equal(f.manager.intent[key], originalRequest[key])
    assert.equal(f.manager.intent.modelRef, 'model-1')
    assert.equal(f.manager.summary().authorized, false)
    assert.equal(f.log.filter(item => item.operation === 'CONFIRM').length, 1)
  } finally { f.close() }
})

test('coding PREPARE preserves terminal, consumed, freshness, selection and current resource gates after historical STATUS', async () => {
  for (const scenario of ['nonterminal', 'unconsumed', 'stale', 'future', 'project', 'session', 'generation', 'resource', 'context', 'host', 'pending']) {
    const f = fixture()
    try {
      if (scenario === 'unconsumed') {
        f.setContext(qualificationContext())
        await f.manager.prepare(scope(), qualificationContext())
        f.qualification('EXECUTION_SETTLED', false)
      } else await settledQualification(f)
      const current = qualificationContext({ 2: '9', 3: '3', 7: 12 })
      f.setContext(current)
      if (scenario === 'nonterminal') f.qualification('UNRESOLVED')
      await f.manager.status()
      let context = current, reason = 'QUALIFICATION_ORIGINAL_REQUEST_PENDING'
      if (scenario === 'stale') f.manager.intent.checkedAt = Date.now() - 10000
      if (scenario === 'future') f.manager.intent.checkedAt = Date.now() + 10000
      if (['project', 'session', 'generation'].includes(scenario)) {
        context = qualificationContext({ [scenario === 'project' ? 0 : scenario === 'session' ? 1 : 6]: scenario === 'generation' ? 4 : 'other' })
        f.setContext(context)
      }
      if (scenario === 'resource') { f.setResourceGeneration(1); reason = 'CODING_RESOURCE_CHANGED' }
      if (scenario === 'context') { context = qualificationContext(); reason = 'CONTEXT_CHANGED' }
      if (scenario === 'host') {
        fs.writeFileSync(path.join(f.dir, 'discovery.json'), JSON.stringify({ url: 'http://127.0.0.1:54321/',
          pid: 24680, data_dir: f.dir, host_instance_id: 'host-bbbbbbbbbbbb' }))
        reason = 'HOST_CHANGED'
      }
      if (scenario === 'pending') { f.manager.pending = { timedOut: true }; reason = 'MANAGEMENT_COMMAND_PENDING' }
      await assert.rejects(f.manager.prepareCoding(scope(), context, review()), { code: reason }, scenario)
      assert.equal(f.log.filter(item => item.operation === 'PREPARE_CODING').length, 0, scenario)
      f.manager.pending = null
    } finally { f.close() }
  }
})

test('coding prepare freezes one original intent, explicit confirm writes configuration once and status never resends it', async () => {
  const f = fixture()
  try {
    const prepared = await prepare(f)
    assert.equal(prepared.state, 'AWAITING_CODING_CONFIRMATION')
    assert.equal(prepared.model_calls, 0)
    assert(!JSON.stringify(prepared).includes('C:/trusted-go'))
    assert.equal(Object.hasOwn(prepared, 'request_hash'), false)
    assert.equal(Object.hasOwn(prepared, 'request_id'), false)
    for (const key of ['client_id', 'expected_revision', 'writer_epoch', 'config_revision', 'workspace_ref'])
      assert.equal(Object.hasOwn(prepared.scope, key), false)
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
    const settled = await approve(f)
    assert.equal(settled.state, 'CODING_CONFIGURED')
    assert.equal(settled.runtime_status, 'REGISTERED')
    assert.equal(settled.model_config_ref, 'model-2')
    assert.deepEqual(settled.profile_ref, profileRef())
    assert.match(settled.commit_key, /^[a-f0-9]{64}$/)
    assert.notEqual(settled.commit_key, hash)
    await assert.rejects(approve(f), { code: 'CODING_CONFIRM_NOT_AVAILABLE' })
    f.setContext(JSON.stringify(['project-1', 'session-1', 2, 1]))
    const recovered = await f.manager.statusCoding()
    assert.equal(recovered.state, 'CODING_CONFIGURED')
    assert.equal(recovered.commit_key, settled.commit_key)
    assert.deepEqual(recovered.profile_ref, profileRef())
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'CONFIRM_CODING', 'STATUS_CODING'])
  } finally { f.close() }
})

test('accepted profile reference is copied and frozen before entering canonical intent', async () => {
  const f = fixture()
  try {
    await prepare(f)
    const returned = profileRef()
    const result = configuredResult(f, returned)
    f.manager.acceptCodingResult(f.manager.codingIntent, result)
    assert.notStrictEqual(f.manager.codingIntent.profileRef, returned)
    assert(Object.isFrozen(f.manager.codingIntent.profileRef))
    returned.id = 'changed-after-validation'
    assert.deepEqual(f.manager.codingSummary().profile_ref, profileRef())
  } finally { f.close() }
})

test('invalid Core profile references cannot settle CONFIRM or original STATUS', async () => {
  const valid = profileRef()
  const cases = [
    ['string', 'profile-1'], ['null', null], ['array', [valid]], ['missing', undefined],
    ['missing id', { entity_type: 'Artifact', revision: 1, content_hash: valid.content_hash }],
    ['extra key', { ...valid, source: 'untrusted' }],
    ['wrong kind', { ...valid, entity_type: 'Task' }],
    ['numeric id', { ...valid, id: 123 }],
    ['invalid id', { ...valid, id: 'bad/id' }],
    ['empty id', { ...valid, id: '' }],
    ['long id', { ...valid, id: 'a'.repeat(161) }],
    ['missing hash', { entity_type: 'Artifact', id: valid.id, revision: 1 }],
    ['null hash', { ...valid, content_hash: null }],
    ['malformed hash', { ...valid, content_hash: 'sha256:xyz' }],
    ['uppercase hash', { ...valid, content_hash: 'sha256:' + 'A'.repeat(64) }],
    ['zero revision', { ...valid, revision: 0 }],
    ['negative revision', { ...valid, revision: -1 }],
    ['fractional revision', { ...valid, revision: 1.5 }],
    ['string revision', { ...valid, revision: '1' }],
    ['unsafe revision', { ...valid, revision: Number.MAX_SAFE_INTEGER + 1 }],
  ]
  for (const [name, invalid] of cases) {
    const f = fixture()
    try {
      f.setProfileRef(invalid)
      await prepare(f)
      assert.throws(() => f.manager.acceptCodingResult(f.manager.codingIntent,
        configuredResult(f, invalid)), { code: 'CODING_RESULT_INVALID' }, name + ' direct')
      assert.equal(f.manager.codingIntent.state, 'AWAITING_CODING_CONFIRMATION', name)
      const wireNumber = name === 'fractional revision' || name === 'unsafe revision'
      const expected = wireNumber ? 'PRIVATE_FRAME_NUMBER' : 'CODING_RESULT_INVALID'
      await assert.rejects(approve(f), { code: expected }, name + ' CONFIRM')
      assert.equal(f.manager.codingIntent.state, 'UNRESOLVED', name)
      assert.equal(f.manager.codingSummary().commit_key, null, name)
      assert.equal(f.manager.codingIntent.profileRef, undefined, name)
      if (!wireNumber) {
        await assert.rejects(f.manager.statusCoding(), { code: expected }, name + ' STATUS')
        assert.equal(f.manager.codingIntent.state, 'UNRESOLVED', name)
        assert.equal(f.manager.codingSummary().commit_key, null, name)
        assert.deepEqual(f.log.map(item => item.operation),
          ['PREPARE_CODING', 'CONFIRM_CODING', 'STATUS_CODING'], name)
      }
    } finally { f.close() }
  }
})

test('changed selection or native host blocks coding confirmation without dispatch', async () => {
  const f = fixture()
  try {
    await prepare(f)
    f.setContext(JSON.stringify(['project-1', 'session-2', 1, 1]))
    await assert.rejects(approve(f), { code: 'CONTEXT_CHANGED' })
    f.setContext(JSON.stringify(['project-1', 'session-1', 1, 1]))
    fs.writeFileSync(path.join(f.dir, 'discovery.json'), JSON.stringify({ url: 'http://127.0.0.1:54321/',
      pid: 24680, data_dir: f.dir, host_instance_id: 'host-bbbbbbbbbbbb' }))
    await assert.rejects(approve(f), { code: 'HOST_CHANGED' })
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
  } finally { f.close() }
})

test('unconfirmed expiry requires original STATUS before a new preparation', async () => {
  const f = fixture()
  try {
    const original = JSON.stringify(['project-1', 'session-1', 1, 1])
    await prepare(f)
    f.manager.codingIntent.expiresAt = new Date(Date.now() - 1000).toISOString()
    await assert.rejects(prepare(f), { code: 'CODING_ORIGINAL_REQUEST_PENDING' })
    assert.equal((await f.manager.statusCoding()).state, 'EXPIRED')
    const next = await prepare(f)
    assert.equal(next.state, 'AWAITING_CODING_CONFIRMATION')
    assert.equal(f.manager.retiredCodingIntents.length, 1)
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'STATUS_CODING', 'PREPARE_CODING'])
  } finally { f.close() }
})

test('uncertain confirmation keeps original request and cannot send a second confirm', async () => {
  const f = fixture()
  try {
    await prepare(f)
    f.manager.pending = { operation: 'STATUS_CODING', timedOut: true }
    await assert.rejects(approve(f), { code: 'MANAGEMENT_COMMAND_PENDING' })
    assert.equal(f.manager.codingSummary().state, 'PRIVATE_COMMAND_UNCERTAIN')
    f.manager.pending = null
    const originalExchange = f.manager.exchange.bind(f.manager)
    f.manager.exchange = async (operation, ...args) => {
      if (operation === 'CONFIRM_CODING') { args[3].beforeWrite(); f.log.push({ operation });
        throw Object.assign(new Error('MANAGEMENT_REPLY_UNCERTAIN'), { code: 'MANAGEMENT_REPLY_UNCERTAIN' }) }
      return originalExchange(operation, ...args)
    }
    await assert.rejects(approve(f), { code: 'MANAGEMENT_REPLY_UNCERTAIN' })
    await assert.rejects(approve(f), { code: 'CODING_CONFIRM_NOT_AVAILABLE' })
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'CONFIRM_CODING'])
  } finally { f.close() }
})

test('original STATUS resolving a committed coding request retires only a settled old qualification', async () => {
  const f = fixture()
  try {
    await prepare(f)
    f.manager.intent = { confirmSent: true, state: 'QUALIFIED_PURPOSE_AUTHORIZED',
      requestId: 'old-qualification', checkedAt: Date.now() }
    f.log.push({ operation: 'CONFIRM_CODING' }) // Host already committed; reply was lost.
    const result = await f.manager.statusCoding()
    assert.equal(result.state, 'CODING_CONFIGURED')
    assert.equal(f.manager.intent, null)
    assert.equal(f.manager.retiredIntents.at(-1).retireReason, 'CODING_COMMITTED')
    assert.equal(f.log.filter(item => item.operation === 'CONFIRM_CODING').length, 1)
  } finally { f.close() }
})

test('IPC accepts only desktop origin, derives private request identity and does not forward forged fields', async () => {
  const handlers = new Map(), calls = []
  const management = { commandIdle: () => {}, codingSummary: () => ({ available: true, state: 'READY' }),
    prepareCoding: (...args) => { calls.push(['PREPARE', args]); return { state: 'AWAITING_CODING_CONFIRMATION' } },
    confirmCoding: (...args) => { calls.push(['CONFIRM', args]); return { state: 'CODING_CONFIGURED' } },
    statusCoding: (...args) => { calls.push(['STATUS', args]); return { state: 'CODING_CONFIGURED' } } }
  registerDesktopCoding({ handle(name, fn) { handlers.set(name, fn) } }, {
    codingSenderAllowed: event => event?.sender?.getURL() === 'ros-app://desktop/',
    desktopManagement: management,
    prepareCodingScope: async body => { assert.deepEqual(body, { read_paths: ['go.mod'] });
      return { scope: { projectId: 'trusted' }, context: 'trusted-context', review: review() } },
    privilegedCodingConsent: async () => true, recheckCodingScope: async () => recheck(),
    pickCodingDirectory: async kind => ({ selected: true, name: kind }),
  })
  const allowed = { sender: { getURL: () => 'ros-app://desktop/' } }
  const forged = { request_id: 'forged', request_hash: hash, token: 'forged' }
  assert.equal((await handlers.get('ros:desktop:coding:prepare')(allowed, { read_paths: ['go.mod'] })).ok, true)
  await handlers.get('ros:desktop:coding:confirm')(allowed, forged)
  await handlers.get('ros:desktop:coding:status')(allowed, forged)
  assert.deepEqual(calls[0], ['PREPARE', [{ projectId: 'trusted' }, 'trusted-context', review()]])
  assert.equal(calls[1][0], 'CONFIRM')
  assert.deepEqual(calls[2], ['STATUS', []])
  assert.equal((await handlers.get('ros:desktop:coding:confirm')({ sender: { getURL: () => 'https://evil/' } }, forged)).reason,
    'DESKTOP_ORIGIN_REQUIRED')
})

test('direct renderer confirm requires privileged consent; cancel and failure retain original', async () => {
  const f = fixture()
  try {
    await prepare(f)
    await assert.rejects(f.manager.confirmCoding(), { code: 'PRIVILEGED_CONFIRM_UNAVAILABLE' })
    await assert.rejects(f.manager.confirmCoding(async frozen => {
      assert.equal(frozen.workspace.display_path, 'C:/trusted-workspace')
      assert.equal(frozen.scope.checks[0].toolchain_root, 'C:/trusted-go')
      assert.equal(frozen.frozen_checks[0].source_manifest_hash, hash)
      return false
    }, async () => recheck()), { code: 'PRIVILEGED_CONFIRM_CANCELLED' })
    await assert.rejects(f.manager.confirmCoding(async () => { throw new Error('dialog failed') },
      async () => recheck()), /dialog failed/)
    assert.equal(f.manager.codingIntent.requestId, 'coding-1')
    assert.equal(f.manager.codingIntent.confirmSent, false)
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
    await approve(f)
    assert.equal(f.log.filter(item => item.operation === 'CONFIRM_CODING').length, 1)
  } finally { f.close() }
})

test('same-origin IPC cannot send CONFIRM when privileged dialog capability is unavailable', async () => {
  const f = fixture(), handlers = new Map()
  try {
    await prepare(f)
    registerDesktopCoding({ handle(name, fn) { handlers.set(name, fn) } }, {
      codingSenderAllowed: event => event?.sender?.getURL() === 'ros-app://desktop/',
      desktopManagement: f.manager, recheckCodingScope: async () => recheck(),
    })
    const reply = await handlers.get('ros:desktop:coding:confirm')(
      { sender: { getURL: () => 'ros-app://desktop/' } }, { accept: true, request_id: 'forged' })
    assert.equal(reply.ok, false)
    assert.equal(reply.reason, 'PRIVILEGED_CONFIRM_UNAVAILABLE')
    assert.equal(f.manager.codingIntent.confirmSent, false)
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
  } finally { f.close() }
})

test('dialog keeps all private operations behind one barrier and rechecks changed authority', async () => {
  const f = fixture()
  try {
    await prepare(f)
    let release
    const held = new Promise(resolve => { release = resolve })
    const pending = f.manager.confirmCoding(async () => held, async () => recheck())
    await new Promise(resolve => setImmediate(resolve))
    assert.equal(f.manager.codingSummary().state, 'PRIVILEGED_CONFIRM_PENDING')
    await assert.rejects(approve(f), { code: 'PRIVILEGED_CONFIRM_PENDING' })
    await assert.rejects(prepare(f), { code: 'PRIVILEGED_CONFIRM_PENDING' })
    await assert.rejects(f.manager.statusCoding(), { code: 'PRIVILEGED_CONFIRM_PENDING' })
    await assert.rejects(f.manager.prepare({ projectId: 'project-1', sessionId: 'session-1',
      modelRef: 'model-1', model: {} }, original), { code: 'PRIVILEGED_CONFIRM_PENDING' })
    await assert.rejects(f.manager.shutdown(), { code: 'PRIVILEGED_CONFIRM_PENDING' })
    f.setContext(JSON.stringify(['project-1', 'session-1', 2, 1]))
    release(true)
    await assert.rejects(pending, { code: 'CODING_CONSENT_CONTEXT_CHANGED' })
    assert.equal(f.manager.codingIntent.confirmSent, false)
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
  } finally { f.close() }
})

test('privileged approval rejects changed writer, model, workspace or resource without consuming request', async () => {
  for (const change of [
    fresh => { fresh.scope.coding.writer_epoch++ },
    fresh => { fresh.scope.modelRef = 'model-new' },
    fresh => { fresh.review.workspace.display_path = 'C:/other-workspace' },
    fresh => { fresh.scope.coding.checks[0].toolchain_root = 'C:/other-go' },
  ]) {
    const f = fixture()
    try {
      await prepare(f)
      let current = recheck()
      await assert.rejects(f.manager.confirmCoding(async () => {
        current = structuredClone(current); change(current); return true
      }, async () => current), { code: 'CODING_CONSENT_CONTEXT_CHANGED' })
      assert.equal(f.manager.codingIntent.confirmSent, false)
      assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
    } finally { f.close() }
  }
})

test('expiry during privileged dialog invalidates approval while retaining original request', async () => {
  const f = fixture()
  try {
    f.expiry(400)
    await prepare(f)
    await assert.rejects(f.manager.confirmCoding(async () => {
      await new Promise(resolve => setTimeout(resolve, 450)); return true
    }, async () => recheck()), { code: 'CODING_CONSENT_CONTEXT_CHANGED' })
    assert.equal(f.manager.codingIntent.requestId, 'coding-1')
    assert.equal(f.manager.codingIntent.confirmSent, false)
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
  } finally { f.close() }
})

test('real expiry plus an in-flight original STATUS preserves exact coding identity and audit', async () => {
  const f = fixture()
  try {
    f.expiry(400)
    await prepare(f)
    const requestId = f.manager.codingIntent.requestId, requestHash = f.manager.codingIntent.requestHash
    await new Promise(resolve => setTimeout(resolve, 450))
    assert.equal((await f.manager.statusCoding()).state, 'EXPIRED')
    f.suppress(true)
    const pending = f.manager.statusCoding()
    await new Promise(resolve => setImmediate(resolve))
    await assert.rejects(prepare(f), { code: 'MANAGEMENT_COMMAND_PENDING' })
    assert.equal(f.manager.codingIntent.requestId, requestId)
    assert.equal(f.manager.codingIntent.requestHash, requestHash)
    assert.equal(f.manager.retiredCodingIntents.length, 0)
    f.manager.pending.timedOut = true
    await assert.rejects(prepare(f), { code: 'MANAGEMENT_COMMAND_PENDING' })
    assert.equal(f.manager.codingIntent.requestId, requestId)
    assert.equal(f.manager.retiredCodingIntents.length, 0)
    f.release(); await pending
    f.suppress(false); f.expiry(55000)
    await prepare(f)
    assert.equal(f.manager.retiredCodingIntents.length, 1)
    assert.equal(f.manager.retiredCodingIntents[0].requestId, requestId)
    assert.deepEqual(f.log.map(item => item.operation),
      ['PREPARE_CODING', 'STATUS_CODING', 'STATUS_CODING', 'PREPARE_CODING'])
  } finally { f.close() }
})

test('late PREPARE result after selection change retains original request for STATUS', async () => {
  const f = fixture()
  try {
    f.suppress(true)
    const pending = prepare(f)
    await new Promise(resolve => setImmediate(resolve))
    assert.equal(f.manager.codingIntent.state, 'PREPARE_UNRESOLVED')
    f.setContext(JSON.stringify(['project-1', 'session-2', 1, 1]))
    f.release()
    const blocked = await pending
    assert.equal(blocked.state, 'CONTEXT_CHANGED_PENDING')
    assert.equal(f.manager.codingIntent.requestId, 'coding-1')
    assert.equal(f.manager.codingIntent.requestHash, hash)
    await assert.rejects(prepare(f), { code: 'CONTEXT_CHANGED' })
    f.setContext(original); f.suppress(false)
    assert.equal((await f.manager.statusCoding()).state, 'AWAITING_CODING_CONFIRMATION')
    await assert.rejects(prepare(f), { code: 'CODING_ORIGINAL_REQUEST_PENDING' })
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'STATUS_CODING'])
  } finally { f.close() }
})

test('returning to same session after selection generation changes permits original STATUS but blocks adoption', async () => {
  const f = fixture()
  try {
    const first = JSON.stringify(['project-1', 'session-1', 1, 1, 'desktop-shell', null, 7])
    f.setContext(first)
    await f.manager.prepareCoding(scope(), first, review())
    const result = await f.manager.confirmCoding(async () => true,
      async () => ({ context: first, scope: scope(), review: review() }))
    assert.equal(result.state, 'CODING_CONFIGURED')
    f.setContext(JSON.stringify(['project-1', 'session-1', 1, 1, 'desktop-shell', null, 9]))
    const historical = await f.manager.statusCoding()
    assert.equal(historical.state, 'CONTEXT_CHANGED_PENDING')
    assert.equal(historical.available, false)
    assert.equal(f.manager.codingIntent.state, 'CODING_CONFIGURED')
    assert.equal(f.log.filter(item => item.operation === 'CONFIRM_CODING').length, 1)
  } finally { f.close() }
})

test('unchanged 45000ms PREPARE timeout retains a valid late expired terminal for original STATUS',
  { timeout: 60000 }, async () => {
    const f = fixture()
    try {
      f.expiry(400); f.suppress(true)
      const pending = prepare(f)
      await assert.rejects(pending, { code: 'MANAGEMENT_REPLY_UNCERTAIN' })
      assert.equal(f.manager.pending.operation, 'PREPARE_CODING')
      assert.equal(f.manager.pending.timedOut, true)
      await assert.rejects(prepare(f), { code: 'MANAGEMENT_COMMAND_PENDING' })
      f.release()
      assert.equal(f.manager.pending, null)
      assert.equal(f.manager.codingIntent.prepareTerminal, 'RESULT')
      assert.equal(f.manager.codingIntent.requestId, 'coding-1')
      assert.equal(f.manager.codingIntent.requestHash, hash)
      assert.equal(f.manager.codingIntent.state, 'EXPIRED')
      f.suppress(false)
      assert.equal((await f.manager.statusCoding()).state, 'EXPIRED')
      assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'STATUS_CODING'])
    } finally { f.close() }
  })

test('authoritative original PREPARE error permits only a corrected explicit retry with audit', async () => {
  const f = fixture()
  try {
    f.rejectNextPrepare()
    await assert.rejects(prepare(f), { code: 'CODING_PREPARE_REJECTED' })
    assert.equal(f.manager.codingIntent.state, 'PREPARE_REJECTED')
    assert.equal(f.manager.codingSummary().available, true)
    assert.equal(f.manager.codingIntent.prepareRejection.code, 'MANAGEMENT_REJECTED')
    assert.equal(f.manager.pending, null)
    const corrected = scope()
    corrected.coding.read_paths = ['go.mod', 'calc/corrected.go', 'calc/value_test.go']
    assert.equal((await f.manager.prepareCoding(corrected, original, review())).state,
      'AWAITING_CODING_CONFIRMATION')
    assert.equal(f.manager.retiredCodingIntents.length, 1)
    assert.equal(f.manager.retiredCodingIntents[0].retireReason, 'AUTHORITATIVE_PREPARE_REJECTION')
    assert.equal(f.manager.retiredCodingIntents[0].prepareRejection.code, 'MANAGEMENT_REJECTED')
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'PREPARE_CODING'])
  } finally { f.close() }
})

test('PREPARE error permits an explicit retry after reselecting the Go resource', async () => {
  const f = fixture()
  try {
    f.rejectNextPrepare()
    await assert.rejects(prepare(f), { code: 'CODING_PREPARE_REJECTED' })
    assert.equal(f.manager.codingSummary().available, true)
    f.setResourceGeneration(1)
    const corrected = scope()
    corrected.coding.read_paths = ['go.mod', 'calc/corrected.go', 'calc/value_test.go']
    assert.equal((await f.manager.prepareCoding(corrected, original,
      { ...review(), resource_generation: 1 })).state, 'AWAITING_CODING_CONFIRMATION')
    assert.equal(f.manager.retiredCodingIntents[0].retireReason, 'AUTHORITATIVE_PREPARE_REJECTION')
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'PREPARE_CODING'])
  } finally { f.close() }
})

test('fixture-timed-out PREPARE only rearms after its exact late terminal ERROR', async () => {
  const f = fixture()
  try {
    f.suppress(true); f.rejectNextPrepare()
    const pending = prepare(f)
    const originalPending = f.manager.pending
    clearTimeout(originalPending.timer)
    originalPending.timedOut = true
    originalPending.reject(Object.assign(new Error('MANAGEMENT_REPLY_UNCERTAIN'),
      { code: 'MANAGEMENT_REPLY_UNCERTAIN' }))
    await assert.rejects(pending, { code: 'MANAGEMENT_REPLY_UNCERTAIN' })
    await assert.rejects(prepare(f), { code: 'MANAGEMENT_COMMAND_PENDING' })
    f.release()
    assert.equal(f.manager.pending, null)
    assert.equal(f.manager.codingIntent.prepareTerminal, 'ERROR')
    assert.equal(f.manager.codingIntent.prepareRejection.messageId, f.log[0].message_id)
    f.suppress(false)
    assert.equal((await prepare(f)).state, 'AWAITING_CODING_CONFIRMATION')
    assert.equal(f.manager.retiredCodingIntents[0].retireReason, 'AUTHORITATIVE_PREPARE_REJECTION')
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING', 'PREPARE_CODING'])
  } finally { f.close() }
})

test('wrong-host PREPARE terminal never rearms or overwrites the original operation', async () => {
  const f = fixture()
  try {
    f.suppress(true)
    const pending = prepare(f)
    f.release(frame => ({ ...frame, host_id: 'host-bbbbbbbbbbbb' }))
    await assert.rejects(pending, { code: 'PRIVATE_REPLY_MISMATCH' })
    assert.equal(f.manager.codingIntent.state, 'PREPARE_UNRESOLVED')
    assert.equal(f.manager.codingIntent.requestId, undefined)
    await assert.rejects(prepare(f), { code: 'CODING_ORIGINAL_REQUEST_PENDING' })
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
  } finally { f.close() }
})

test('malformed frozen check in an original PREPARE result remains quarantined', async () => {
  const f = fixture()
  try {
    f.suppress(true)
    const pending = prepare(f)
    f.release(frame => {
      frame.result.frozen_checks[0].id = 'different-check'
      return frame
    })
    await assert.rejects(pending, { code: 'CODING_FROZEN_CHECK_INVALID' })
    assert.equal(f.manager.codingIntent.state, 'PREPARE_UNRESOLVED')
    assert.equal(f.manager.codingIntent.requestId, undefined)
    await assert.rejects(prepare(f), { code: 'CODING_ORIGINAL_REQUEST_PENDING' })
    assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
  } finally { f.close() }
})

test('a post-inner-check microtask changing session or resource generation blocks final CONFIRM write', async () => {
  for (const kind of ['session', 'resource']) {
    const f = fixture()
    try {
      await prepare(f)
      const observe = f.manager.observe
      let checks = 0, armed = false, queued = false
      f.manager.observe = pid => {
        const value = observe(pid)
        if (armed && pid === process.pid && !queued) {
          queued = true
          queueMicrotask(() => {
            if (kind === 'session') f.setContext(JSON.stringify(['project-1', 'session-2', 1, 1]))
            else f.setResourceGeneration(1)
          })
        }
        return value
      }
      await assert.rejects(f.manager.confirmCoding(async () => true, async () => {
        if (++checks === 2) armed = true
        return recheck()
      }), { code: 'CODING_CONSENT_CONTEXT_CHANGED' })
      assert.equal(queued, true)
      assert.equal(f.manager.codingIntent.confirmSent, false)
      assert.equal(f.manager.codingIntent.state, 'AWAITING_CODING_CONFIRMATION')
      assert.deepEqual(f.log.map(item => item.operation), ['PREPARE_CODING'])
    } finally { f.close() }
  }
})

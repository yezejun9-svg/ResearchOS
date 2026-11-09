import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import { decimal, canSubmitHarness, hasHarnessCapability, applyHarnessPage, cancelIntent, createHarnessController, harnessStatusLabel } from '../../../apps/web/src/harness.js'
import { composerSubmitKey, harnessActivityRows } from '../../../apps/web/src/activity.js'
import { projectHarnessReceipt } from '../../../apps/web/src/harness-progress.js'

const ref = { project_id: 'fixture-project', task_id: 'fixture-task' }
const task = (extra = {}) => ({ task_ref: ref, request_id: 'fixture-request', harness_id: 'codex', workspace_ref: 'fixture-workspace', prompt: 'Inspect only', scope: 'workspace-read', ephemeral: true, status: 'QUEUED', terminal: false, task_revision: '1', run: null, created_at: '2026-11-04T00:00:00Z', updated_at: '2026-11-04T00:00:00Z', result: null, failure: null, ...extra })
const capabilities = { harness_id: 'codex', can_submit: true, capabilities: { readonly_turn: true, event_stream: true, cancel: true, pause: false, resume: false, write: false, per_tool_approval: false } }
const ok = data => ({ ok: true, data })
function bridge(extra = {}) {
  return { capabilities: async () => ok(capabilities), list: async () => ok({ items: [], lookup: null }), pending: async () => ok(null), get: async () => ok(task()), ...extra }
}
const event = (sequence, extra = {}) => ({ event_id: 'fixture-' + sequence, task_ref: ref, run: null, sequence, kind: 'RUN_STATE', payload: { status: 'RUNNING', text: null, tool: null, task: null, error: null }, ...extra })

test('capabilities fail closed and metadata does not imply execution verification', () => {
  assert.equal(canSubmitHarness(null), false)
  assert.equal(canSubmitHarness({ ...capabilities, can_submit: false }), false)
  assert.equal(canSubmitHarness(capabilities), true)
  for (const name of ['pause', 'resume', 'write', 'per_tool_approval']) assert.equal(hasHarnessCapability(capabilities, name), false)
  assert.equal(hasHarnessCapability({ ...capabilities, harness_id: 'other' }, 'readonly_turn'), false)
})
test('decimal identifiers remain exact strings at int64 boundaries', () => {
  for (const value of ['0', '9007199254740993', '9223372036854775807']) assert.equal(decimal(value), true)
  for (const value of [0, 9007199254740993, '01', '-1', '1.0', '9223372036854775808']) assert.equal(decimal(value), false)
  assert.equal(decimal('0', true), false)
})
test('real controller sends a readonly intent without provider configuration and keeps queued ACK nonterminal', async () => {
  const seen = []
  const control = createHarnessController(bridge({ submit: async body => { seen.push(body); return ok({ task_ref: ref, request_id: 'fixture-request', task_revision: '1', status: 'QUEUED', run: null }) } }), ref.project_id)
  await control.load()
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' }), true)
  assert.deepEqual(seen, [{ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' }])
  assert.equal(control.getSnapshot().task.run, null)
  assert.equal(control.getSnapshot().task.terminal, false)
  assert.match(harnessStatusLabel(control.getSnapshot().task.status), /尚未执行/)
  control.dispose()
})
test('blank and oversized UTF8 prompts never call the bridge', async () => {
  let sends = 0
  const control = createHarnessController(bridge({ submit: async () => { sends++; throw Error('unexpected') } }), ref.project_id)
  await control.load()
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: ' \n\t' }), false)
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: '界'.repeat(22000) }), false)
  assert.equal(sends, 0)
})
test('UNKNOWN blocks new submission and NOT_FOUND only performs read-only reconciliation', async () => {
  let sends = 0, reads = 0, pending = null
  const control = createHarnessController(bridge({
    pending: async () => ok(pending),
    submit: async () => { sends++; pending = { request_id: 'same-original', kind: 'submit', state: 'UNKNOWN' }; return { ok: false, outcome: 'UNKNOWN', reason: 'HARNESS_TIMEOUT', pending } },
    reconcile: async () => { reads++; return ok({ pending, task: null }) },
  }), ref.project_id)
  await control.load()
  await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })
  await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })
  await control.reconcile()
  assert.equal(sends, 1); assert.equal(reads, 1)
  assert.equal(control.getSnapshot().pending.request_id, 'same-original')
})
test('accepted submission remains accepted if the immediate snapshot read disconnects', async () => {
  const control = createHarnessController(bridge({ submit: async () => ok({ task_ref: ref, request_id: 'r', task_revision: '1', status: 'QUEUED', run: null }), get: async () => { throw Error('read disconnected') } }), ref.project_id)
  await control.load()
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' }), true)
  assert.match(control.getSnapshot().error.message, /disconnected/)
  assert.match(projectHarnessReceipt(control.getSnapshot(), true).summary, /已接收.*读取失败/)
})
test('accepted ACK followed by an immediate failed Task renders the Host failure without replay', async () => {
  let submits = 0
  const failure = { code: 'HARNESS_UNAVAILABLE', message: 'Native preparation failed before model launch; no automatic replay' }
  const control = createHarnessController(bridge({
    submit: async () => { submits++; return ok({ task_ref: ref, request_id: 'fixture-request', task_revision: '1', status: 'QUEUED', run: null }) },
    get: async () => ok(task({ status: 'FAILED', terminal: true, failure })),
  }), ref.project_id)
  await control.load()
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' }), true)
  const view = projectHarnessReceipt(control.getSnapshot(), true)
  assert.equal(view.kind, 'FAILED')
  assert.match(view.summary, /准备阶段失败/)
  assert.equal(view.message, failure.message)
  assert.equal(submits, 1)
  control.dispose()
})
test('a later failed Task replaces the queued receipt without resubmitting', async () => {
  let reads = 0, submits = 0
  const control = createHarnessController(bridge({
    submit: async () => { submits++; return ok({ task_ref: ref, request_id: 'fixture-request', task_revision: '1', status: 'QUEUED', run: null }) },
    get: async () => ok(++reads === 1 ? task() : task({ status: 'FAILED', terminal: true, failure: { code: 'HARNESS_UNAVAILABLE', message: 'Host execution unavailable' } })),
    events: async () => ok({ task_ref: ref, events: [], next_cursor: '0', has_more: false, end: false, reset: false, snapshot: null }),
  }), ref.project_id)
  await control.load()
  await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' })
  assert.equal(projectHarnessReceipt(control.getSnapshot(), true).kind, 'QUEUED')
  await control.tick()
  const view = projectHarnessReceipt(control.getSnapshot(), true)
  assert.equal(view.kind, 'FAILED')
  assert.doesNotMatch(view.summary, /准备阶段失败/)
  assert.equal(submits, 1)
  control.dispose()
})
test('history selection clears the prior ACK before a different Task read fails', async () => {
  const other = { project_id: ref.project_id, task_id: 'other-task' }
  let submits = 0
  const control = createHarnessController(bridge({
    submit: async () => { submits++; return ok({ task_ref: ref, request_id: 'fixture-request', task_revision: '1', status: 'QUEUED', run: null }) },
    get: async ({ task_id }) => task_id === other.task_id ? { ok: false, reason: 'READ_DISCONNECTED' } : ok(task()),
  }), ref.project_id)
  await control.load()
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Inspect only' }), true)
  const acknowledgements = []
  const errorContexts = []
  let draft = 'initial draft'
  const edit = vm.runInNewContext('(' + editSource + ')', {
    draftVersion: { current: 0 },
    setDraft: value => { draft = value },
  })
  edit('new unsent draft')
  const select = vm.runInNewContext('(' + selectSource + ')', {
    setAcknowledgement: value => acknowledgements.push(value),
    setErrorContext: value => errorContexts.push(value),
    controller: { current: control },
  })
  await select(other.task_id)
  assert.deepEqual(acknowledgements, [null])
  assert.deepEqual(errorContexts, ['read'])
  assert.equal(draft, 'new unsent draft')
  assert.equal(submits, 1)
  assert.equal(control.getSnapshot().task, null)
  const receipt = projectHarnessReceipt(control.getSnapshot(), false, 'read')
  assert.equal(receipt.kind, 'READ_ERROR')
  assert.doesNotMatch(receipt.summary, /请求已接收/)
  control.dispose()
})
test('UNKNOWN submission keeps the older Task distinct and reconciles only the original request', async () => {
  let submits = 0, reconciles = 0
  const unresolved = { request_id: 'new-original-request', kind: 'submit', state: 'UNKNOWN' }
  const control = createHarnessController(bridge({
    pending: async () => ok(submits ? unresolved : null),
    submit: async () => { submits++; return { ok: false, reason: 'HARNESS_TIMEOUT', outcome: 'UNKNOWN', pending: unresolved } },
    reconcile: async () => { reconciles++; return ok({ pending: unresolved, task: null }) },
  }), ref.project_id)
  await control.load(); await control.select(ref.task_id)
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'New task' }), false)
  const view = projectHarnessReceipt(control.getSnapshot(), false, 'submit')
  assert.equal(view.kind, 'PENDING')
  assert.equal(view.requestId, unresolved.request_id)
  assert.equal(view.pendingKind, 'submit')
  assert.equal(view.previousTaskId, ref.task_id)
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Retry' }), false)
  await control.reconcile()
  assert.equal(submits, 1)
  assert.equal(reconciles, 1)
  control.dispose()
})
test('UNKNOWN cancellation keeps its original request identity and blocks a second submit', async () => {
  let cancels = 0, submits = 0, reconciles = 0
  const unresolved = { request_id: 'cancel-original-request', kind: 'cancel', state: 'UNKNOWN' }
  const control = createHarnessController(bridge({
    pending: async () => ok(cancels ? unresolved : null),
    cancel: async () => { cancels++; return { ok: false, reason: 'HARNESS_TIMEOUT', outcome: 'UNKNOWN', pending: unresolved } },
    submit: async () => { submits++; throw Error('must stay blocked') },
    reconcile: async () => { reconciles++; return ok({ pending: unresolved, task: null }) },
  }), ref.project_id)
  await control.load(); await control.select(ref.task_id); await control.cancel()
  const view = projectHarnessReceipt(control.getSnapshot(), false, 'cancel')
  assert.equal(view.kind, 'PENDING')
  assert.equal(view.requestId, unresolved.request_id)
  assert.equal(view.pendingKind, 'cancel')
  assert.equal(view.previousTaskId, ref.task_id)
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'New task' }), false)
  await control.reconcile()
  assert.equal(cancels, 1); assert.equal(submits, 0); assert.equal(reconciles, 1)
  control.dispose()
})
test('Run epoch changes preserve Task history and explicit reset adopts authoritative state', () => {
  let state = { task: task(), events: [], cursor: '9007199254740992', end: false }
  const page = (item, cursor) => ({ task_ref: ref, events: [item], next_cursor: cursor, has_more: false, end: false, reset: false, snapshot: null })
  state = applyHarnessPage(state, page(event('9007199254740993', { run: { run_id: 'r1', epoch: '9007199254740993' } }), '9007199254740993'), ref)
  state = applyHarnessPage(state, page(event('9007199254740993', { run: { run_id: 'r1', epoch: '9007199254740993' } }), '9007199254740993'), ref)
  assert.equal(state.events.length, 1)
  state = applyHarnessPage(state, page(event('9007199254740994', { run: { run_id: 'r2', epoch: '9007199254740994' } }), '9007199254740994'), ref)
  assert.equal(state.events.length, 2); assert.equal(state.cursor, '9007199254740994')
  state = applyHarnessPage(state, { task_ref: ref, events: [], next_cursor: '9007199254740995', has_more: false, end: true, reset: true, snapshot: task({ status: 'FAILED', terminal: true }) }, ref)
  assert.equal(state.events.length, 0); assert.equal(state.task.status, 'FAILED'); assert.equal(state.end, true)
})
test('foreign events or invalid cursor cannot partially apply a page', () => {
  const state = { task: task(), events: [], cursor: '0', end: false }
  assert.throws(() => applyHarnessPage(state, { task_ref: ref, events: [event('1'), event('2', { task_ref: { ...ref, project_id: 'foreign' } })], next_cursor: '2', has_more: false, end: false, reset: false, snapshot: null }, ref))
  assert.equal(state.cursor, '0'); assert.equal(state.events.length, 0)
  assert.throws(() => applyHarnessPage(state, { task_ref: ref, events: [], next_cursor: 1, has_more: false, end: false, reset: false, snapshot: null }, ref))
})
test('cancel uses queued null pair or the exact current Run/epoch and revision', () => {
  assert.deepEqual(cancelIntent(task()), { task_id: ref.task_id, expected_task_revision: '1', expected_run_id: null, expected_epoch: null })
  assert.deepEqual(cancelIntent(task({ task_revision: '9007199254740993', run: { run_id: 'r', epoch: '9007199254740994' } })), { task_id: ref.task_id, expected_task_revision: '9007199254740993', expected_run_id: 'r', expected_epoch: '9007199254740994' })
})
test('STATE_CONFLICT refreshes without automatically cancelling the newly observed Run', async () => {
  let cancels = 0, reads = 0
  const control = createHarnessController(bridge({ get: async () => { reads++; return ok(task({ run: { run_id: 'r' + reads, epoch: String(reads) } })) }, cancel: async () => { cancels++; return { ok: false, reason: 'STATE_CONFLICT', outcome: 'REPLIED' } } }), ref.project_id)
  await control.load(); await control.select(ref.task_id); await control.cancel()
  assert.equal(cancels, 1); assert.equal(reads, 2); assert.equal(control.getSnapshot().task.run.run_id, 'r2')
})
test('late async snapshot cannot update a disposed project controller', async () => {
  let release
  const control = createHarnessController(bridge({ get: () => new Promise(resolve => { release = resolve }) }), ref.project_id)
  await control.load()
  const selecting = control.select(ref.task_id)
  control.dispose(); release(ok(task()))
  await selecting
  assert.equal(control.getSnapshot().task, null)
})
test('activity projects actual tool observations and preserves IME/multiline behavior', () => {
  const rows = harnessActivityRows([event('9007199254740993', { kind: 'TOOL_EVENT', payload: { tool: { name: 'command_execution', phase: 'COMPLETED', summary: 'observed result' } } }), event('2', { task_ref: { ...ref, task_id: 'foreign' } })], ref)
  assert.equal(rows.length, 1); assert.equal(rows[0].title, 'command_execution'); assert.match(rows[0].summary, /COMPLETED/)
  assert.equal(composerSubmitKey({ key: 'Enter', isComposing: true }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', shiftKey: true }), false)
  assert.equal(composerSubmitKey({ key: 'Enter' }), true)
})

// Exercise the real React handler and textarea callback with a controlled
// bridge promise; do not replace send() with a hand-written draft simulation.
const workbench = fs.readFileSync(new URL('../../../apps/web/src/workbench.jsx', import.meta.url), 'utf8')
const codexBlock = workbench.slice(workbench.indexOf('function NativeHarnessWorkbench('), workbench.indexOf('function NativeMuWorkbench('))
const sendSource = /async function send\(event\) \{[\s\S]*?\n  \}/.exec(codexBlock)?.[0]
const cancelSource = /async function cancelTask\(\) \{[\s\S]*?\n  \}/.exec(codexBlock)?.[0]
const editSource = /function editDraft\(value\) \{[\s\S]*?\n  \}/.exec(codexBlock)?.[0]
const selectSource = /function selectTask\(id\) \{[\s\S]*?\n  \}/.exec(codexBlock)?.[0]
const textareaSource = /<textarea[^>]*onChange=\{(event => \w+\(event.target.value\))\}/.exec(codexBlock)?.[1]
const scopeSource = /  if \(draftScope.current.projectId[\s\S]*?\n  \}/.exec(codexBlock)?.[0]
const cleanupSource = /return \(\) => \{ stopped = true; draftVersion[^\n]*/.exec(codexBlock)?.[0]?.replace(/^return /, '')
assert.ok(sendSource && cancelSource && editSource && selectSource && textareaSource && scopeSource && cleanupSource, 'actual send, cancel, draft and selection handlers and view cleanup must be isolated')
function activeHandlers(control) {
  let draft = 'Inspect only', acknowledgement = null, errorContext = 'read'
  const changes = []
  const context = vm.createContext({
    canSend: true, projectId: ref.project_id, workspace: 'fixture-workspace', draft,
    draftVersion: { current: 0 }, controller: { current: control },
    setDraft: value => { draft = value },
    setAcknowledgement: value => { acknowledgement = value; changes.push(value) },
    setErrorContext: value => { errorContext = value },
  })
  const send = vm.runInContext('(' + sendSource + ')', context)
  const cancel = vm.runInContext('(' + cancelSource + ')', context)
  return { send: () => send({ preventDefault() {} }), cancel, acknowledgement: () => acknowledgement,
    errorContext: () => errorContext, changes, draft: () => draft }
}
test('real send then failed cancel clears ACK before STATE_CONFLICT refresh failure', async () => {
  let reads = 0, submits = 0, cancels = 0
  const control = createHarnessController(bridge({
    submit: async () => { submits++; return ok({ task_ref: ref, request_id: 'fixture-request', task_revision: '1', status: 'QUEUED', run: null }) },
    get: async () => ++reads === 1 ? ok(task()) : { ok: false, reason: 'READ_DISCONNECTED' },
    cancel: async () => { cancels++; return { ok: false, reason: 'STATE_CONFLICT', outcome: 'REPLIED' } },
  }), ref.project_id)
  await control.load()
  const view = activeHandlers(control)
  await view.send()
  assert.equal(view.acknowledgement().taskId, ref.task_id)
  await view.cancel()
  assert.equal(view.acknowledgement(), null)
  assert.equal(view.errorContext(), 'cancel')
  assert.equal(projectHarnessReceipt(control.getSnapshot(), !!view.acknowledgement(), view.errorContext()).kind, 'OPERATION_ERROR')
  assert.equal(control.getSnapshot().error.code, 'STATE_CONFLICT')
  assert.equal(view.draft(), '')
  assert.equal(submits, 1); assert.equal(cancels, 1); assert.equal(reads, 2)
  control.dispose()
})
test('real send then UNKNOWN cancel shows the cancel request, never the previous submit ACK', async () => {
  let submits = 0, cancels = 0, reconciles = 0
  const unresolved = { request_id: 'original-cancel', kind: 'cancel', state: 'UNKNOWN' }
  const control = createHarnessController(bridge({
    submit: async () => { submits++; return ok({ task_ref: ref, request_id: 'fixture-request', task_revision: '1', status: 'QUEUED', run: null }) },
    pending: async () => ok(cancels ? unresolved : null),
    cancel: async () => { cancels++; return { ok: false, reason: 'HARNESS_TIMEOUT', outcome: 'UNKNOWN', pending: unresolved } },
    reconcile: async () => { reconciles++; return ok({ pending: unresolved, task: null }) },
  }), ref.project_id)
  await control.load()
  const view = activeHandlers(control)
  await view.send()
  assert.equal(view.acknowledgement().taskId, ref.task_id)
  await view.cancel()
  const receipt = projectHarnessReceipt(control.getSnapshot(), !!view.acknowledgement(), view.errorContext())
  assert.equal(view.acknowledgement(), null)
  assert.equal(receipt.kind, 'PENDING')
  assert.equal(receipt.requestId, 'original-cancel')
  assert.equal(receipt.pendingKind, 'cancel')
  assert.equal(receipt.previousTaskId, ref.task_id)
  assert.equal(await control.submit({ workspace_ref: 'fixture-workspace', prompt: 'Must remain blocked' }), false)
  await control.reconcile()
  assert.equal(submits, 1); assert.equal(cancels, 1); assert.equal(reconciles, 1)
  control.dispose()
})
function pendingDraftSend() {
  let resolve, currentDraft = 'submitted text'
  const acknowledgements = [], submissions = []
  const accepted = new Promise(done => { resolve = done })
  const control = { submit: value => { submissions.push(value); return accepted }, getSnapshot: () => ({ task: { task_ref: ref } }), dispose() {} }
  const context = vm.createContext({ canSend: true, draft: 'submitted text', workspace: 'fixture-workspace', projectId: ref.project_id,
    draftVersion: { current: 0 }, draftScope: { current: { projectId: ref.project_id, workspace: 'fixture-workspace' } },
    controller: { current: control }, control, setDraft: value => { currentDraft = typeof value === 'function' ? value(currentDraft) : value },
    setAcknowledgement: value => acknowledgements.push(value), setErrorContext() {}, stopped: false, unsubscribe() {}, clearInterval() {}, timer: 1, removeEventListener() {}, changed() {}, tick() {}, visible() {}, document: { removeEventListener() {} } })
  context.editDraft = vm.runInContext('(' + editSource + ')', context)
  const send = vm.runInContext('(' + sendSource + ')', context)
  const onChange = vm.runInContext('(' + textareaSource + ')', context)
  const pending = send({ preventDefault() {} })
  return { context, pending, resolve, acknowledgements, submissions, value: () => currentDraft,
    edit: text => onChange({ target: { value: text } }),
    scope: workspace => { context.workspace = workspace; vm.runInContext(scopeSource, context) },
    cleanup: () => vm.runInContext('(' + cleanupSource + ')', context)() }
}
for (const editBack of [false, true]) test('actual send preserves unsent draft edits before late success; editBack=' + editBack, async () => {
  const run = pendingDraftSend()
  run.edit('new unsent text')
  if (editBack) run.edit('submitted text')
  const expected = run.value()
  run.resolve(true); await run.pending
  assert.equal(run.value(), expected)
  assert.equal(run.submissions.length, 1)
  assert.equal(run.context.draftVersion.current, editBack ? 2 : 1)
})
test('actual send still clears an unchanged successfully submitted draft', async () => {
  const run = pendingDraftSend()
  run.resolve(true); await run.pending
  assert.equal(run.value(), '')
  assert.equal(run.submissions[0].prompt, 'submitted text')
  assert.equal(run.acknowledgements.at(-1).taskId, ref.task_id)
  assert.equal(run.acknowledgements.at(-1).controller, run.context.controller.current)
})
test('actual send keeps draft after view cleanup while its promise is pending', async () => {
  const run = pendingDraftSend()
  run.cleanup()
  run.resolve(true); await run.pending
  assert.equal(run.value(), 'submitted text')
  assert.equal(run.context.controller.current, null)
  assert.deepEqual(run.acknowledgements, [null], 'unmounted view cannot publish the late success receipt')
})
test('actual scope generations preserve draft after workspace changes away and back', async () => {
  const run = pendingDraftSend()
  run.scope('other-workspace'); run.scope('fixture-workspace')
  run.resolve(true); await run.pending
  assert.equal(run.value(), 'submitted text')
  assert.equal(run.context.draftVersion.current, 2)
})
test('actual send cannot clear a draft owned by a replacement controller', async () => {
  const run = pendingDraftSend()
  run.context.controller.current = { submit() { throw Error('unexpected resubmit') } }
  run.resolve(true); await run.pending
  assert.equal(run.value(), 'submitted text')
  assert.deepEqual(run.acknowledgements, [null])
})

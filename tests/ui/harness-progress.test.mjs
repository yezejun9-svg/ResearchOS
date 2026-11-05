import test from 'node:test'
import assert from 'node:assert/strict'
import { projectHarnessProgress, projectHarnessReceipt } from '../../apps/web/src/harness-progress.js'
import { harnessSubmissionBlockers } from '../../apps/web/src/harness.js'

const ref = { project_id: 'p', task_id: 't' }
const run = { run_id: 'r2', epoch: '2' }
const task = (status = 'QUEUED', currentRun = null) => ({ task_ref: ref, status, run: currentRun })
const tool = (id, currentRun = run, extra = {}) => ({ event_id: id, task_ref: ref, run: currentRun,
  sequence: String(Number(id.replace(/\D/g, '')) || 1), kind: 'TOOL_EVENT', payload: { tool: { name: 'command_execution', phase: 'COMPLETED' } }, ...extra })
const stage = (view, key) => view.stages.find(row => row.key === key)

test('no selected Task is an honest empty state; queued Task has no Run or result', () => {
  assert.deepEqual(projectHarnessProgress(null), { empty: true, stages: [], observedToolCount: 0 })
  const view = projectHarnessProgress(task())
  assert.match(stage(view, 'run').detail, /尚未关联 Run/)
  assert.equal(stage(view, 'result').state, 'waiting')
  assert.match(stage(view, 'tools').detail, /不代表此前从未使用/)
})

test('failure before a Run, unknown outcome, and cancel request never look complete', () => {
  const failed = projectHarnessProgress(task('FAILED'))
  assert.match(stage(failed, 'run').detail, /尚未关联 Run/)
  assert.equal(stage(failed, 'result').state, 'unresolved')
  const unknown = projectHarnessProgress(task('UNKNOWN', run))
  assert.match(stage(unknown, 'result').detail, /结果未知/)
  assert.equal(stage(unknown, 'result').state, 'unresolved')
  const cancel = projectHarnessProgress(task('CANCEL_REQUESTED', run))
  assert.match(stage(cancel, 'run').detail, /等待原 Run 结果/)
  assert.match(stage(cancel, 'result').detail, /尚未形成终态/)
  assert.notEqual(stage(cancel, 'result').state, 'observed')
})

test('completed Task reports execution end without claiming independent verification', () => {
  const view = projectHarnessProgress(task('COMPLETED', run))
  const result = stage(view, 'result')
  assert.equal(stage(view, 'run').state, 'observed')
  assert.match(result.detail, /独立核对/)
  assert.doesNotMatch(result.detail, /验收通过|验证通过/)
})

test('tool count is only the observed current Run window, deduplicated and scope-bound', () => {
  const rows = [tool('e1'), tool('e1'), tool('e2', { run_id: 'r1', epoch: '1' }),
    tool('e3', run, { task_ref: { project_id: 'p', task_id: 'foreign' } }),
    tool('e4', run, { sequence: 'bad' }), { ...tool('e5'), kind: 'LOG' }]
  const view = projectHarnessProgress(task('RUNNING', run), rows)
  assert.equal(view.observedToolCount, 1)
  assert.match(stage(view, 'tools').detail, /当前事件窗口已观测 1 条/)
  const reset = projectHarnessProgress(task('RUNNING', run), [])
  assert.equal(reset.observedToolCount, 0)
  assert.match(stage(reset, 'tools').detail, /不代表此前从未使用/)
})

test('read-only permission blockers explain current reasons and retain raw codes', () => {
  const blockers = harnessSubmissionBlockers({ can_submit: false, reason_codes: ['PERMISSION_PROFILE_UNVERIFIED', 'CODEX_POLICY_IDENTITY_MISMATCH', 'PERMISSION_PROFILE_UNVERIFIED'] })
  assert.equal(blockers.length, 2)
  assert.match(blockers[0].message, /只读权限/)
  assert.match(blockers[1].message, /策略/)
  assert.deepEqual(harnessSubmissionBlockers({ can_submit: true, reason_codes: [] }), [])
  assert.match(harnessSubmissionBlockers({ can_submit: false, reason_codes: [] })[0].message, /尚未确认/)
})

test('receipt follows the authoritative Task after ACK, including terminal and cancel states', () => {
  for (const status of ['FAILED', 'COMPLETED', 'CANCELLED', 'BLOCKED', 'UNKNOWN', 'CANCEL_REQUESTED']) {
    const view = projectHarnessReceipt({ task: task(status) }, true)
    assert.equal(view.kind, status)
    assert.doesNotMatch(view.summary, /等待真实运行回执/)
  }
  assert.match(projectHarnessReceipt({ task: task('UNKNOWN') }, true).summary, /核对原请求/)
  assert.match(projectHarnessReceipt({ task: task('CANCEL_REQUESTED') }, true).summary, /等待原任务/)
})

test('preparation wording requires the actual Host message, not an error code alone', () => {
  const generic = projectHarnessReceipt({ task: { ...task('FAILED'), failure: { code: 'HARNESS_UNAVAILABLE', message: 'Host unavailable' } } }, true)
  assert.doesNotMatch(generic.summary, /模型未启动/)
  assert.equal(generic.message, 'Host unavailable')
  const explicit = projectHarnessReceipt({ task: { ...task('FAILED'), failure: { code: 'HARNESS_UNAVAILABLE', message: 'Native preparation failed before model launch; no automatic replay' } } }, true)
  assert.match(explicit.summary, /模型未启动/)
  assert.equal(explicit.code, 'HARNESS_UNAVAILABLE')
})

test('pending original request and accepted read error retain distinct, reconcilable receipts', () => {
  const pending = projectHarnessReceipt({ pending: { request_id: 'original', kind: 'submit', state: 'UNKNOWN' } }, false)
  assert.equal(pending.kind, 'PENDING')
  assert.equal(pending.requestId, 'original')
  assert.match(pending.summary, /避免重复提交/)
  const readError = projectHarnessReceipt({ error: new Error('read disconnected') }, true)
  assert.equal(readError.kind, 'READ_ERROR')
  assert.match(readError.summary, /已接收.*读取失败/)
  assert.equal(readError.message, 'read disconnected')
  const lastKnown = projectHarnessReceipt({ task: task('QUEUED'), error: new Error('refresh disconnected') }, true)
  assert.equal(lastKnown.kind, 'QUEUED')
  assert.equal(lastKnown.readError, 'refresh disconnected')
  assert.equal(projectHarnessReceipt({}), null)
})

test('an unresolved different request outranks an older Task and keeps its full identity', () => {
  const older = { ...task('COMPLETED'), request_id: 'old-request' }
  const pending = { request_id: 'new-request', kind: 'submit', state: 'UNKNOWN' }
  const view = projectHarnessReceipt({ task: older, pending, error: new Error('submit outcome unknown') }, false, 'submit')
  assert.equal(view.kind, 'PENDING')
  assert.equal(view.requestId, 'new-request')
  assert.equal(view.pendingKind, 'submit')
  assert.equal(view.pendingState, 'UNKNOWN')
  assert.equal(view.previousTaskId, ref.task_id)
  assert.doesNotMatch(view.summary, /已结束/)
})

test('operation failures are not called read failures; an accepted get failure is', () => {
  const submission = projectHarnessReceipt({ task: task(), error: new Error('submit rejected') }, false, 'submit')
  assert.equal(submission.kind, 'OPERATION_ERROR')
  assert.doesNotMatch(submission.summary, /读取失败/)
  const cancellation = projectHarnessReceipt({ task: task(), error: new Error('cancel rejected') }, false, 'cancel')
  assert.equal(cancellation.kind, 'OPERATION_ERROR')
  assert.match(cancellation.summary, /取消/)
  const read = projectHarnessReceipt({ error: new Error('get disconnected') }, true, 'submit')
  assert.equal(read.kind, 'READ_ERROR')
  assert.match(read.summary, /读取失败/)
})

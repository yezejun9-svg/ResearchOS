import test from 'node:test'
import assert from 'node:assert/strict'
import { projectHarnessProgress } from '../../apps/web/src/harness-progress.js'
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

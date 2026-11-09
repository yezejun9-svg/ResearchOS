import test from 'node:test'
import assert from 'node:assert/strict'
import { activityRows, composerSubmitKey, appendPrompt } from '../../../apps/web/src/activity.js'

test('activity is scoped to the current session, ordered and deduplicated', () => {
  const start = { event_id: 'e1', session_id: 'current', sequence: 1, kind: 'TOOL_STARTED', payload: { tool_call_id: 't1', tool_name: 'read_file', input_summary: 'README.md' } }
  const end = { event_id: 'e2', session_id: 'current', sequence: 2, kind: 'TOOL_RESULT', payload: { tool_call_id: 't1', outcome: 'SUCCEEDED', summary: '读取 12 行' } }
  const other = { ...end, event_id: 'secret', session_id: 'previous', sequence: 3 }
  const rows = activityRows([end, other, start, start], 'current')
  assert.deepEqual(rows.map(row => row.event.event_id), ['e2', 'e1'])
  assert.equal(rows[0].title, 'read_file')
  assert.match(rows[0].summary, /工具成功/)
  assert.doesNotMatch(rows[0].summary, /已验收/)
  assert.deepEqual(activityRows([start], null), [])
})

test('run completion and available artifacts never imply acceptance; unknown cost stays unknown', () => {
  const event = (id, kind, payload) => ({ event_id: id, session_id: 's', sequence: Number(id), kind, payload })
  const rows = activityRows([
    event('1', 'RUN_STATE', { status: 'SETTLED' }),
    event('2', 'ARTIFACT', { availability: 'AVAILABLE' }),
    event('3', 'USAGE', { cost_known: false, money: { amount: '0', currency: 'USD' } }),
    event('4', 'GOAL_STATE', { goal_id: 'g', revision: 2, status: 'VERIFYING' }),
  ], 's')
  assert.equal(rows.find(row => row.event.kind === 'RUN_STATE').title, '执行已结束')
  assert.match(rows.find(row => row.event.kind === 'ARTIFACT').summary, /另行核对/)
  assert.equal(rows.find(row => row.event.kind === 'USAGE').summary, '费用待结算')
  assert.equal(rows.find(row => row.event.kind === 'GOAL_STATE').title, '目标验收中')
})

test('composer sends on Enter while IME and Shift+Enter retain multiline composition', () => {
  assert.equal(composerSubmitKey({ key: 'Enter' }), true)
  assert.equal(composerSubmitKey({ key: 'Enter', ctrlKey: true }), true)
  assert.equal(composerSubmitKey({ key: 'Enter', shiftKey: true }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', isComposing: true }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', nativeEvent: { isComposing: true } }), false)
  assert.equal(composerSubmitKey({ key: 'Enter', nativeEvent: { keyCode: 229 } }), false)
})

test('exact uint64 event ordering preserves large values and all already read history', () => {
  const first = 9007199254740993n
  const events = Array.from({ length: 16 }, (_, i) => ({ event_id: `large-${i}`, session_id: 's', sequence: first + BigInt(i), kind: 'RUN_STATE', payload: { status: i === 0 ? 'FAILED' : 'RUNNING' } }))
  const rows = activityRows(events.reverse(), 's')
  assert.equal(rows.length, 16)
  assert.equal(rows[0].event.sequence, first + 15n)
  assert.equal(rows.at(-1).event.sequence, first)
  assert.equal(rows.at(-1).title, '执行失败')
})

test('a known exact decimal amount remains readable without numeric rounding', () => {
  const [row] = activityRows([{ event_id: 'money', session_id: 's', sequence: 1n, kind: 'USAGE', payload: { cost_known: true, money: { amount: { exact_decimal: '0.001200' }, currency: 'USD' } } }], 's')
  assert.equal(row.summary, '0.001200 USD')
})


test('starter suggestions append to an unsent draft without replacing user work', () => {
  const draft = '保留我的约束与长段说明。'.repeat(100)
  assert.equal(appendPrompt(draft, '检查当前改动'), `${draft}\n\n检查当前改动`)
  assert.equal(appendPrompt('', '检查当前改动'), '检查当前改动')
})


test('an invalidated goal explicitly requests revalidation', () => {
  const [row] = activityRows([{ event_id: 'revalidation', session_id: 's', sequence: 1, kind: 'GOAL_STATE', payload: { goal_id: 'g', status: 'NEEDS_REVALIDATION', revision: 3 } }], 's')
  assert.equal(row.title, '目标需重新验收')
  assert.equal(row.tone, 'neutral')
})

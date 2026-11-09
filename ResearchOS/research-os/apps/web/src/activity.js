import { integer, compare } from '../../desktop/main/lib/wire-values.mjs'
import { decimal, sameTask, harnessStatusLabel } from './harness.js'

const activityKinds = new Set(['TOOL_STARTED', 'TOOL_RESULT', 'RUN_STATE', 'GOAL_STATE', 'ARTIFACT', 'JUDGE_DECISION', 'ERROR', 'USAGE'])
const outcomes = { SUCCEEDED: '工具成功', FAILED: '工具失败', CANCELLED: '已取消', BLOCKED: '受阻', UNKNOWN: '结果待核对' }
const runStates = { QUEUED: '排队中', STARTING: '启动中', RUNNING: '执行中', CANCEL_REQUESTED: '正在取消', SETTLED: '执行已结束', FAILED: '执行失败', CANCELLED: '已取消', LOST: '连接丢失', RECONCILING: '恢复核对中' }
const goalStates = { DRAFT: '目标草稿', ACTIVE: '目标进行中', PAUSED: '目标已暂停', VERIFYING: '目标验收中', ACCEPTED: '目标已验收', NEEDS_REVALIDATION: '目标需重新验收', FAILED: '目标失败', CANCELLED: '目标已取消', BLOCKED: '目标受阻' }

export function activityRows(events, sessionId) {
  if (!sessionId) return []
  const seen = new Set(), tools = new Map()
  const ordered = events.filter(event => {
    if (event.session_id !== sessionId || !event.event_id || !integer(event.sequence) || seen.has(event.event_id)) return false
    seen.add(event.event_id)
    return true
  }).sort((a, b) => compare(a.sequence, b.sequence))
  return ordered.filter(event => activityKinds.has(event.kind)).map(event => {
    const payload = event.payload || {}
    if (event.kind === 'TOOL_STARTED') tools.set(payload.tool_call_id, payload.tool_name)
    let title, summary, tone = 'neutral'
    switch (event.kind) {
      case 'TOOL_STARTED': title = payload.tool_name || '调用工具'; summary = payload.input_summary || '工具调用已发起'; break
      case 'TOOL_RESULT':
        title = tools.get(payload.tool_call_id) || '工具结果'
        summary = `${outcomes[payload.outcome] || '结果待核对'}${payload.summary ? ` · ${payload.summary}` : ''}`
        tone = payload.outcome === 'FAILED' ? 'error' : payload.outcome === 'SUCCEEDED' ? 'success' : 'neutral'
        break
      case 'RUN_STATE': title = runStates[payload.status] || '运行状态待核对'; summary = payload.reason || '执行状态回执'; tone = payload.status === 'FAILED' ? 'error' : 'neutral'; break
      case 'GOAL_STATE': title = goalStates[payload.status] || '目标状态待核对'; summary = payload.goal_id ? `目标修订 ${payload.revision}` : '目标状态回执'; tone = payload.status === 'ACCEPTED' ? 'success' : 'neutral'; break
      case 'ARTIFACT': title = '产物回执'; summary = { AVAILABLE: '产物已可用，验收状态另行核对', SUPERSEDED: '产物已被新版本替代', REVOKED: '产物访问已撤销' }[payload.availability] || '产物状态待核对'; break
      case 'JUDGE_DECISION': title = '判断建议'; summary = payload.summary || '查看判断回执与用途资格'; break
      case 'ERROR': title = '需要处理'; summary = payload.message || payload.summary || '查看错误回执'; tone = 'error'; break
      case 'USAGE': title = '用量回执'; summary = payload.cost_known === true && payload.money != null ? `${payload.money.amount?.exact_decimal ?? payload.money.amount} ${payload.money.currency}` : '费用待结算'; break
    }
    return { event, title, summary, tone }
  }).reverse()
}

export function composerSubmitKey(event) {
  return event.key === 'Enter' && !event.shiftKey && !event.altKey && !event.isComposing && !event.nativeEvent?.isComposing && event.keyCode !== 229 && event.nativeEvent?.keyCode !== 229
}

export function appendPrompt(draft, prompt) {
  return draft.trim() ? `${draft}\n\n${prompt}` : prompt
}

export function harnessActivityRows(events, ref) {
  if (!ref) return []
  const seen = new Set()
  return events.filter(event => {
    if (!sameTask(event.task_ref, ref) || !event.event_id || !decimal(event.sequence, true) || seen.has(event.event_id)) return false
    seen.add(event.event_id)
    return true
  }).sort((a, b) => BigInt(a.sequence) < BigInt(b.sequence) ? -1 : BigInt(a.sequence) > BigInt(b.sequence) ? 1 : 0).map(event => {
    const value = event.payload || {}
    let title = '执行回执', summary = value.text || '', tone = 'neutral'
    if (event.kind === 'TOOL_EVENT') { title = value.tool?.name || '工具事件'; summary = `${value.tool?.phase || '待核对'} · ${value.tool?.summary || ''}`; if (value.tool?.phase === 'FAILED') tone = 'error' }
    else if (['TASK_QUEUED', 'RUN_STARTED', 'RUN_STATE', 'TASK_TERMINAL'].includes(event.kind)) { title = harnessStatusLabel(value.status); summary = value.error?.message || 'Host 持久化状态回执'; if (value.status === 'FAILED') tone = 'error' }
    else if (event.kind === 'ASSISTANT_MESSAGE') title = 'Codex 消息'
    else if (event.kind === 'LOG') title = '执行诊断'
    return { event, title, summary, tone }
  }).reverse()
}

import { decimal, sameTask } from './harness.js'

const terminalText = {
  COMPLETED: 'Task 执行已结束；结果仍需独立核对',
  FAILED: 'Task 执行失败；请查看失败回执',
  CANCELLED: 'Task 已取消',
  BLOCKED: 'Task 被阻止；请查看原因',
  UNKNOWN: 'Task 结果未知；请核对原请求，勿重复提交',
}

const sameRun = (left, right) => !!left && !!right &&
  left.run_id === right.run_id && left.epoch === right.epoch

// The Host Task is the receipt. An accepted submit ACK only confirms that a
// request was recorded; it must never override a later Task or read failure.
export function projectHarnessReceipt({ task = null, pending = null, error = null } = {}, acknowledged = false, errorContext = 'read') {
  const failure = task?.failure
  const message = typeof failure?.message === 'string' ? failure.message : ''
  const preparationFailed = /preparation failed before model launch|准备阶段失败.{0,20}模型未启动/i.test(message)
  const summaries = {
    QUEUED: '任务已记录，等待启动。',
    STARTING: '任务正在启动。',
    RUNNING: '任务正在执行。',
    CANCEL_REQUESTED: '已请求取消，等待原任务确认停止。',
    COMPLETED: '任务执行已结束；结果仍需核对。',
    FAILED: preparationFailed ? '准备阶段失败，模型未启动；没有自动重试。' : '任务执行失败；请查看 Host 返回的原因。',
    CANCELLED: '任务已取消。',
    BLOCKED: '任务已阻止；请查看原因。',
    UNKNOWN: '任务结果未知；请核对原请求，避免重复提交。',
  }
  const unresolved = pending && {
    kind: 'PENDING', summary: '原请求结果未确认；请核对原请求，避免重复提交。',
    requestId: pending.request_id || null, pendingKind: pending.kind || null, pendingState: pending.state || null,
    previousTaskId: task?.task_ref?.task_id || null,
  }
  if (unresolved && (!task || pending.request_id !== task.request_id)) return unresolved
  if (error && (errorContext === 'cancel' || !acknowledged && errorContext !== 'read')) return {
    kind: 'OPERATION_ERROR', summary: errorContext === 'cancel' ? '取消请求未确认；请核对当前任务。' : '提交请求未确认；请核对原请求后再操作。',
    message: error.message || String(error), code: error.code || null, previousTaskId: task?.task_ref?.task_id || null,
  }
  if (task) return { kind: task.status, summary: summaries[task.status] || '任务状态待核对。',
    message, code: failure?.code || null, taskId: task.task_ref?.task_id || null,
    revision: task.task_revision || null, runId: task.run?.run_id || null, epoch: task.run?.epoch || null,
    readError: error?.message || null }
  if (unresolved) return unresolved
  if (error) return { kind: 'READ_ERROR', summary: acknowledged ? '请求已接收，但当前任务读取失败；请刷新核对。' : '任务状态读取失败；请刷新核对。',
    message: error.message || String(error), code: error.code || null }
  if (acknowledged) return { kind: 'ACKNOWLEDGED', summary: '请求已接收，正在读取当前任务。' }
  return null
}

export function projectHarnessProgress(task, events = []) {
  if (!task) return { empty: true, stages: [], observedToolCount: 0 }
  const run = task.run
  const seen = new Set()
  const tools = (Array.isArray(events) ? events : []).filter(event => {
    if (event?.kind !== 'TOOL_EVENT' || !sameTask(event.task_ref, task.task_ref) ||
      !sameRun(event.run, run) || !event.event_id || !decimal(event.sequence, true) || seen.has(event.event_id)) return false
    seen.add(event.event_id)
    return true
  })
  const pendingCancel = task.status === 'CANCEL_REQUESTED'
  const terminal = terminalText[task.status]
  const runText = !run ? '尚未关联 Run' : pendingCancel ? '取消已请求，等待原 Run 结果' :
    task.status === 'UNKNOWN' ? 'Run 结果未知，需核对' :
    task.status === 'FAILED' ? 'Run 已失败' :
    task.status === 'COMPLETED' ? 'Run 已结束' :
    task.status === 'CANCELLED' ? 'Run 已取消' :
    task.status === 'BLOCKED' ? 'Run 已阻止' :
    task.status === 'QUEUED' ? 'Run 已关联，等待启动回执' : 'Run 已关联，执行状态见 Task 回执'
  return { empty: false, observedToolCount: tools.length, stages: [
    { key: 'submit', title: '提交', state: 'done', detail: 'Task 已由 Host 记录' },
    { key: 'run', title: '运行', state: !run ? 'waiting' : task.status === 'COMPLETED' ? 'observed' : terminal || pendingCancel ? 'unresolved' : 'active', detail: runText },
    { key: 'tools', title: '工具', state: tools.length ? 'observed' : 'waiting',
      detail: tools.length ? `当前事件窗口已观测 ${tools.length} 条工具事件` : '当前事件窗口未见工具事件；不代表此前从未使用' },
    { key: 'result', title: '结果', state: terminal ? (task.status === 'COMPLETED' ? 'observed' : 'unresolved') : 'waiting',
      detail: terminal || (pendingCancel ? '取消请求尚未形成终态' : '等待 Task 终态回执') },
  ] }
}

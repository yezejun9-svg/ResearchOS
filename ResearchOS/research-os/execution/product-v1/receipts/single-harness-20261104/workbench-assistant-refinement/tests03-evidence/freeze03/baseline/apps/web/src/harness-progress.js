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

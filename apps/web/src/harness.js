// Renderer projections only. The Go Host owns Tasks, Runs and capabilities.
export const HARNESS_CAPABILITIES = [
  ['readonly_turn', '只读任务'], ['event_stream', '执行事件'], ['cancel', '取消'],
  ['task_history', '任务历史'], ['request_lookup', '提交核对'], ['token_delta', '逐 token 输出'],
  ['write', '写入'], ['resume', '恢复执行'], ['pause', '暂停'],
  ['per_tool_approval', '逐工具授权'], ['file_diff', '文件差异'], ['file_list', '文件列表'],
  ['file_artifacts', '文件产物'], ['attachments', '附件'],
]

const STATES = {
  QUEUED: '已排队，尚未执行', STARTING: '启动中', RUNNING: '执行中',
  CANCEL_REQUESTED: '已请求取消，等待停止回执', COMPLETED: '执行已完成',
  FAILED: '执行失败', CANCELLED: '已取消', BLOCKED: '已阻止', UNKNOWN: '结果未知，需核对',
}
const TERMINAL = new Set(['COMPLETED', 'FAILED', 'CANCELLED', 'BLOCKED', 'UNKNOWN'])
const MAX = '9223372036854775807'
export const harnessStatusLabel = status => STATES[status] || '状态待核对'
export const hasHarnessCapability = (value, name) => value?.harness_id === 'codex' && value?.capabilities?.[name] === true
export const canSubmitHarness = value => value?.can_submit === true && hasHarnessCapability(value, 'readonly_turn')
const BLOCK_REASONS = {
  NOT_INSTALLED: '本机尚未找到 Codex CLI。',
  CONFIG_INHERITANCE_UNVERIFIED: '只读配置的隔离状态尚未确认。',
  AUTH_METADATA_REQUIRED: '登录状态尚未确认。',
  PERMISSION_PROFILE_UNVERIFIED: '只读权限配置尚未验证，暂不能提交。',
  CODEX_POLICY_IDENTITY_MISMATCH: '当前 Codex 策略与要求的只读配置不一致。',
}
export function harnessSubmissionBlockers(value) {
  if (!value || value.can_submit === true) return []
  const codes = Array.isArray(value.reason_codes) ? [...new Set(value.reason_codes.filter(code => typeof code === 'string'))] : []
  return codes.length ? codes.map(code => ({ code, message: BLOCK_REASONS[code] || '有一项提交条件尚未确认，请查看技术原因。' })) :
    [{ code: 'READINESS_UNCONFIRMED', message: 'Host 尚未确认可以提交只读任务。' }]
}
export function decimal(value, positive = false) {
  return typeof value === 'string' && /^(0|[1-9][0-9]{0,18})$/.test(value) &&
    (!positive || value !== '0') && (value.length < MAX.length || value.length === MAX.length && value <= MAX)
}
export function sameTask(left, right) {
  return !!left && !!right && left.project_id === right.project_id && left.task_id === right.task_id
}
const fail = () => { throw new Error('HARNESS_REPLY_MISMATCH') }
export function validateTaskIdentity(task, ref) {
  if (!sameTask(task?.task_ref, ref) || task.harness_id !== 'codex' || !decimal(task.task_revision, true) ||
      !Object.hasOwn(STATES, task.status) || task.terminal !== TERMINAL.has(task.status) ||
      !(task.run === null || typeof task.run?.run_id === 'string' && task.run.run_id && decimal(task.run.epoch, true))) fail()
  return task
}

// Apply a complete validated page before advancing its cursor. A new Run/epoch
// never discards the earlier Task history. Only an explicit Host reset does.
export function applyHarnessPage(state, page, ref) {
  if (!sameTask(page?.task_ref, ref) || !decimal(page.next_cursor) || !Array.isArray(page.events) ||
      page.events.length > 500 || typeof page.reset !== 'boolean' || typeof page.end !== 'boolean' ||
      typeof page.has_more !== 'boolean') fail()
  if (page.reset) {
    if (page.events.length || page.has_more || !page.snapshot) fail()
    const task = validateTaskIdentity(page.snapshot, ref)
    if (page.end !== task.terminal) fail()
    return { ...state, task, events: [], cursor: page.next_cursor, end: page.end }
  }
  if (page.snapshot !== null || !decimal(state.cursor) || BigInt(page.next_cursor) < BigInt(state.cursor)) fail()
  let sequence = 0n, task = state.task
  const known = new Map(state.events.map(event => [event.event_id, event]))
  const incoming = []
  for (const event of page.events) {
    if (!sameTask(event?.task_ref, ref) || typeof event.event_id !== 'string' || !event.event_id ||
        !decimal(event.sequence, true) || BigInt(event.sequence) <= sequence ||
        !(event.run === null || typeof event.run?.run_id === 'string' && event.run.run_id && decimal(event.run.epoch, true))) fail()
    sequence = BigInt(event.sequence)
    const previous = known.get(event.event_id)
    if (previous && JSON.stringify(previous) !== JSON.stringify(event)) fail()
    if (!previous && sequence <= BigInt(state.cursor)) fail()
    if (!previous) { incoming.push(event); known.set(event.event_id, event) }
    if (event.kind === 'TASK_TERMINAL' && sequence > BigInt(state.cursor)) task = validateTaskIdentity(event.payload?.task, ref)
  }
  if (sequence > BigInt(page.next_cursor) || !page.events.length && page.next_cursor !== state.cursor ||
      page.end && (page.has_more || !task?.terminal)) fail()
  return { ...state, task, events: [...state.events, ...incoming].slice(-500), cursor: page.next_cursor, end: page.end }
}

export function cancelIntent(task) {
  validateTaskIdentity(task, task?.task_ref)
  if (task.terminal) throw new Error('TASK_ALREADY_TERMINAL')
  return { task_id: task.task_ref.task_id, expected_task_revision: task.task_revision,
    expected_run_id: task.run?.run_id ?? null, expected_epoch: task.run?.epoch ?? null }
}

export function unwrapHarness(reply) {
  if (!reply?.ok) {
    const error = new Error(reply?.reason || 'HARNESS_UNAVAILABLE')
    error.code = reply?.reason
    error.outcome = reply?.outcome
    error.pending = reply?.pending || null
    throw error
  }
  return reply.data
}

// Shared by the real React workbench and pure bridge fixtures. No scheduler or
// task completion is implemented here; all snapshots are read from the Host.
export function createHarnessController(bridge, projectId) {
  let state = { loading: false, busy: false, capabilities: null, tasks: [], task: null,
    events: [], cursor: '0', end: false, pending: null, error: null }
  let generation = 0, disposed = false, polling = false
  const listeners = new Set()
  const publish = patch => { if (!disposed) { state = { ...state, ...patch }; for (const fn of listeners) fn() } }
  const current = token => !disposed && generation === token
  const call = async (name, body) => unwrapHarness(await bridge[name](body))
  const ref = id => ({ project_id: projectId, task_id: id })
  async function pending() { publish({ pending: await call('pending') }) }
  async function refreshTask(id, token) {
    const task = validateTaskIdentity(await call('get', { task_id: id }), ref(id))
    if (current(token)) publish({ task, tasks: [task, ...state.tasks.filter(item => !sameTask(item.task_ref, task.task_ref))] })
    return task
  }
  const controller = {
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn) },
    getSnapshot: () => state,
    dispose() { disposed = true; generation++; listeners.clear() },
    async load() {
      const token = ++generation
      publish({ loading: true, error: null })
      try {
        const [capabilities, list, outstanding] = await Promise.all([call('capabilities'), call('list', { cursor: '0', limit: 100 }), call('pending')])
        if (!current(token)) return
        for (const task of list.items) validateTaskIdentity(task, ref(task.task_ref.task_id))
        publish({ capabilities, tasks: list.items, pending: outstanding })
        if (state.task) { publish({ end: false }); await refreshTask(state.task.task_ref.task_id, token) }
      } catch (error) { if (current(token)) publish({ error }) }
      finally { if (current(token)) publish({ loading: false }) }
    },
    async select(id) {
      if (state.busy) return
      const token = ++generation
      publish({ busy: true, error: null, task: null, events: [], cursor: '0', end: false })
      try { await refreshTask(id, token) }
      catch (error) { if (current(token)) publish({ error }) }
      finally { if (current(token)) publish({ busy: false }) }
    },
    async submit(intent) {
      if (state.busy || state.pending || !canSubmitHarness(state.capabilities)) return false
      if (!intent.workspace_ref || typeof intent.prompt !== 'string' || !intent.prompt.trim() || new TextEncoder().encode(intent.prompt).length > 65536) return false
      const token = ++generation
      let accepted = false
      publish({ busy: true, error: null })
      try {
        const ack = await call('submit', intent)
        if (!current(token)) return false
        if (ack.status !== 'QUEUED' || ack.run !== null || ack.task_ref?.project_id !== projectId) fail()
        accepted = true
        publish({ task: null, events: [], cursor: '0', end: false })
        await refreshTask(ack.task_ref.task_id, token)
        return true
      } catch (error) { if (current(token)) publish({ error, pending: error.pending || state.pending }); return accepted }
      finally { if (current(token)) { try { await pending() } catch {} publish({ busy: false }) } }
    },
    async reconcile() {
      if (state.busy) return
      const token = ++generation
      publish({ busy: true, error: null })
      try {
        const value = await call('reconcile')
        if (!current(token)) return
        publish({ pending: value.pending })
        if (value.task) {
          const task = validateTaskIdentity(value.task, ref(value.task.task_ref.task_id))
          publish({ task, events: [], cursor: '0', end: false,
            tasks: [task, ...state.tasks.filter(item => !sameTask(item.task_ref, task.task_ref))] })
        }
      } catch (error) { if (current(token)) publish({ error }) }
      finally { if (current(token)) publish({ busy: false }) }
    },
    async cancel() {
      if (state.busy || state.pending || !hasHarnessCapability(state.capabilities, 'cancel') || !state.task || state.task.terminal) return
      const task = state.task, token = ++generation
      publish({ busy: true, error: null })
      try {
        const value = await call('cancel', cancelIntent(task))
        if (current(token)) publish({ task: validateTaskIdentity(value.task, task.task_ref) })
      } catch (error) {
        if (current(token)) {
          publish({ error })
          if (error.code === 'STATE_CONFLICT') { try { await refreshTask(task.task_ref.task_id, token) } catch {} }
        }
      } finally { if (current(token)) { try { await pending() } catch {} publish({ busy: false }) } }
    },
    async tick() {
      if (polling || state.busy || !state.task || state.end || !hasHarnessCapability(state.capabilities, 'event_stream')) return
      polling = true
      const token = generation, selected = state.task.task_ref
      try {
        for (let pageCount = 0; pageCount < 3; pageCount++) {
          const page = await call('events', { task_id: selected.task_id, cursor: state.cursor, limit: 100 })
          if (!current(token) || !sameTask(state.task?.task_ref, selected)) return
          publish(applyHarnessPage(state, page, selected))
          if (!page.has_more || page.end) break
        }
        if (current(token)) await refreshTask(selected.task_id, token)
      } catch (error) { if (current(token)) publish({ error }) }
      finally { polling = false }
    },
  }
  return controller
}

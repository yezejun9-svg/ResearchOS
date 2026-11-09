// View preferences and startup health only. Neither grants execution authority.
const THEME_KEY = 'researchos.theme'
const RECENT_KEY = 'researchos.recent-projects.v1'
const RECENT_LIMIT = 24

export function readTheme(storage) {
  try { return (storage || globalThis.localStorage).getItem(THEME_KEY) === 'light' ? 'light' : 'dark' }
  catch { return 'dark' }
}

export function saveTheme(theme, storage) {
  try { (storage || globalThis.localStorage).setItem(THEME_KEY, theme === 'light' ? 'light' : 'dark') }
  catch { /* A view preference must never prevent startup. */ }
}

export function readRecentProjects(storage) {
  try {
    const value = JSON.parse((storage || globalThis.localStorage).getItem(RECENT_KEY) || '[]')
    if (!Array.isArray(value)) return []
    const seen = new Set()
    return value.filter(row => {
      if (!row || typeof row.project_id !== 'string' || !row.project_id || row.project_id.length > 200 ||
          !Number.isSafeInteger(row.opened_at) || row.opened_at < 0 || seen.has(row.project_id)) return false
      seen.add(row.project_id); return true
    }).slice(0, RECENT_LIMIT).map(row => ({ project_id: row.project_id, opened_at: row.opened_at }))
  } catch { return [] }
}

export function rememberProject(projectId, storage, now = Date.now()) {
  if (typeof projectId !== 'string' || !projectId || projectId.length > 200 || !Number.isSafeInteger(now) || now < 0) return
  try {
    const target = storage || globalThis.localStorage
    const rows = [{ project_id: projectId, opened_at: now }, ...readRecentProjects(target).filter(row => row.project_id !== projectId)]
    target.setItem(RECENT_KEY, JSON.stringify(rows.slice(0, RECENT_LIMIT)))
  } catch { /* Only bounded UI preference IDs, never prompts, paths, or credentials. */ }
}

export function projectGroups(projects, recent) {
  const accessible = new Map()
  for (const row of projects || []) if (typeof row?.project_id === 'string' && row.project_id && !accessible.has(row.project_id)) accessible.set(row.project_id, row)
  const selected = new Set()
  const opened = []
  for (const row of recent || []) {
    const id = row?.project_id
    if (accessible.has(id) && !selected.has(id) && opened.length < 6) {
      selected.add(id); opened.push(accessible.get(id))
    }
  }
  return { recent: opened, other: [...accessible.values()].filter(row => !selected.has(row.project_id)) }
}

export function workspaceProjectPath(value) {
  return typeof value?.project_id === 'string' && value.project_id &&
    typeof value?.workspace?.authorized_workspace_ref === 'string' && value.workspace.authorized_workspace_ref
    ? `/p/${encodeURIComponent(value.project_id)}` : null
}

export function healthFromReply(reply) {
  return reply?.ok === true && reply.status === 'ready' && reply.scope === 'DEVELOPMENT_ONLY' && reply.database === 'sqlite'
    ? { state: 'ready', label: 'Host 已连接' }
    : { state: 'unavailable', label: 'Host 未连接' }
}

// A hung or late bridge read cannot keep the header green or overwrite a newer
// result. This monitor only observes health; protocol write barriers stay in IPC.
export function startHostHealthMonitor({ read, onChange, intervalMs = 15000, timeoutMs = 5000,
  schedule = setTimeout, cancel = clearTimeout }) {
  let stopped = false, generation = 0, nextTimer, deadlineTimer
  function check() {
    if (stopped) return
    const ticket = ++generation
    let settled = false
    const finish = value => {
      if (stopped || settled || ticket !== generation) return
      settled = true; cancel(deadlineTimer)
      onChange(value)
      nextTimer = schedule(check, intervalMs)
    }
    onChange({ state: 'checking', label: '正在检查 Host' })
    deadlineTimer = schedule(() => finish({ state: 'unavailable', label: 'Host 检查超时' }), timeoutMs)
    Promise.resolve().then(read).then(value => finish(healthFromReply(value)), () => finish({ state: 'unavailable', label: 'Host 未连接' }))
  }
  check()
  return () => { stopped = true; generation++; cancel(nextTimer); cancel(deadlineTimer) }
}

import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import tokens from '../../../spec/v2.0/ui/design-tokens.json'
import { createApi, classify, itemsOf } from './api'
import { useQueries, useProjectEvents } from './hooks'
import { Screen } from './screens'
import { useRoute } from './navigation'
import { AppShell } from './components/app-shell'
import { PairingGate, useDeviceSession } from './Pairing'
import { readTheme, saveTheme, rememberProject, startHostHealthMonitor } from './startup.js'
import './style.css'
import './workbench.css'

const nativeDesktop = !!window.researchos?.desktop?.context

function AuthGate({ onToken }) {
  const [value, setValue] = useState('')
  return <div className="auth-wrap"><div className="auth-card"><span className="brandmark">R</span><h1>ResearchOS</h1><p>输入本机已配置的访问令牌，打开研究工作台。令牌只保存在当前页面内存中，关闭页面即清除。</p><form onSubmit={event => { event.preventDefault(); if (value.trim()) onToken(value.trim()) }}><label htmlFor="access-token">访问令牌</label><input id="access-token" type="password" autoComplete="off" value={value} onChange={event => setValue(event.target.value)} required/><button className="primary" type="submit">打开工作台</button></form><small>令牌由本机受保护的凭据管理流程提供。</small></div></div>
}

function App() {
  const [token, setToken] = useState('')
  const deviceSession = useDeviceSession(setToken)
  const [theme, setTheme] = useState(() => readTheme())
  const [route, navigate] = useRoute()
  const [hostHealth, setHostHealth] = useState({ state: 'checking', label: '正在检查 Host' })
  useEffect(() => {
    if (!nativeDesktop) return
    return startHostHealthMonitor({ read: () => window.researchos.statusHealth({}), onChange: setHostHealth })
  }, [])
  const [drawer, setDrawer] = useState(null)
  const [compact, setCompact] = useState(() => matchMedia('(max-width: 767px)').matches)
  const [feedback, setFeedback] = useState(null)
  const [refresh, setRefresh] = useState(0)
  const drawerOpener = useRef(null)
  const api = useMemo(() => nativeDesktop || token ? createApi(() => token) : null, [token])
  const events = useProjectEvents(api, route.projectId)
  useEffect(() => { if (deviceSession.device && events.authExpired && !deviceSession.renewalPending) deviceSession.expire() }, [events.authExpired, deviceSession.device?.id, deviceSession.renewalPending])
  const shared = useQueries(api, route.projectId, route.projectId ? [{ op: 'getProjectProfile' }, { op: 'getProjectState' }, { op: 'getProgressProjection' }, { op: 'listMilestoneRelease' }, { op: 'listNotification' }] : [], refresh + events.refresh)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    Object.entries(tokens.themes[theme]).forEach(([name, value]) => document.documentElement.style.setProperty(`--${name.replaceAll('_', '-')}`, value))
    const size = { 'body-size': `${tokens.font.body_size_px}px`, 'body-line-height': tokens.font.body_line_height, 'title-size': `${tokens.font.title_size_px}px`, 'small-size': `${tokens.font.small_size_px}px`, 'header-height': `${tokens.layout.header_height_px}px`, 'nav-width': `${tokens.layout.nav_width_px}px`, 'progress-width': `${tokens.layout.progress_width_px}px`, 'mobile-target': `${tokens.layout.mobile_target_px}px`, 'control-radius': `${tokens.radius_px.control}px`, 'card-radius': `${tokens.radius_px.card}px`, 'panel-radius': `${tokens.radius_px.panel}px` }
    Object.entries(size).forEach(([name, value]) => document.documentElement.style.setProperty(`--${name}`, value))
    saveTheme(theme)
  }, [theme])
  useEffect(() => { setDrawer(null) }, [route.key])
  useEffect(() => { const media = matchMedia('(max-width: 767px)'); const changed = () => setCompact(media.matches); media.addEventListener('change', changed); return () => media.removeEventListener('change', changed) }, [])
  useEffect(() => { if (!drawer && drawerOpener.current?.isConnected) drawerOpener.current.focus() }, [drawer])
  useEffect(() => { if (drawer) document.querySelector(drawer === 'nav' ? '.sidebar.drawer-open .drawer-close' : drawer === 'rail' ? '.progress-rail.drawer-open .drawer-close' : '.notice-drawer .drawer-close')?.focus() }, [compact, drawer])
  useEffect(() => {
    const onKey = e => {
      if (e.key === 'Escape') setDrawer(null)
      if (e.key !== 'Tab' || !drawer) return
      const region = document.querySelector(drawer === 'nav' ? '.sidebar' : drawer === 'rail' ? '.progress-rail' : '.notice-drawer')
      const controls = [...(region?.querySelectorAll('a[href],button:not(:disabled),input,select,textarea,summary') || [])].filter(node => node.getClientRects().length)
      const first = controls[0], last = controls.at(-1)
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus() }
      if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus() }
    }
    addEventListener('keydown', onKey); return () => removeEventListener('keydown', onKey)
  }, [drawer])
  const projectId = route.projectId
  const state = shared.data.getProjectState
  const profile = shared.data.getProjectProfile
  useEffect(() => { if (projectId && profile) rememberProject(projectId) }, [projectId, profile])
  const connection = nativeDesktop ? hostHealth : { state: events.online ? 'ready' : 'unavailable', label: events.online ? '项目事件已连接' : '项目事件未连接' }
  const notifications = itemsOf(shared.data.listNotification)
  const unread = notifications.filter(item => item.status === 'UNREAD').length
  function openDrawer(name, event) { drawerOpener.current = event.currentTarget; setDrawer(name) }
  async function mutate(operation, options, message = '服务已保存') {
    if (projectId && !events.online && events.lastSync) { setFeedback({ kind: 'error', text: '连接已断开，写入未发送。请恢复连接后重试。' }); return null }
    try {
      const result = await api.call(operation, options)
      setFeedback({ kind: 'success', text: message })
      setRefresh(n => n + 1)
      return result
    } catch (error) {
      setFeedback({ kind: 'error', text: `${classify(error) === 'stale' ? '版本已变化，草稿仍在当前页面。' : ''}${error.message}${error.correlationId ? ` · 请求 ${error.correlationId}` : ''}` })
      throw error
    }
  }
  const navUrl = kind => {
    if (!projectId) return '/'
    if (kind === 'workbench') return `/p/${projectId}`
    if (kind === 'cycle') return state?.active_cycle_id ? `/p/${projectId}/cycles/${state.active_cycle_id}` : `/p/${projectId}/cycles`
    if (kind === 'release') return state?.latest_release_id ? `/p/${projectId}/releases/${state.latest_release_id}` : `/p/${projectId}/releases`
    if (kind === 'experiment') return `/p/${projectId}/experiments`
    return `/p/${projectId}/${kind}`
  }
  if (!nativeDesktop && !token && (location.pathname === '/pair' || deviceSession.error || location.hostname.endsWith('.trycloudflare.com'))) return <PairingGate sessionError={deviceSession.error} onSession={session => { deviceSession.accept(session); navigate(`/p/${session.device.project_ids[0]}`) }}/>
  if (!nativeDesktop && !token) return <AuthGate onToken={setToken}/>
  return <AppShell route={route} navigate={navigate} drawer={drawer} setDrawer={setDrawer} compact={compact}
    openDrawer={openDrawer} connection={connection} events={events} projectId={projectId} profile={profile} unread={unread}
    theme={theme} setTheme={setTheme} notifications={notifications} shared={shared} state={state}
    feedback={feedback} setFeedback={setFeedback} deviceSession={deviceSession} api={api}
    mutate={mutate} navUrl={navUrl}>
    <Screen key={route.key} route={route} api={api} token={token} navigate={navigate} shared={shared} events={events} refresh={refresh + events.refresh} mutate={mutate} onRefresh={() => setRefresh(n => n + 1)}/>
  </AppShell>
}

createRoot(document.getElementById('root')).render(<App />)

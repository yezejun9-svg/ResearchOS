import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import tokens from '../../../spec/v2.0/ui/design-tokens.json'
import { createApi, classify, etagOf, itemsOf } from './api'
import { useQueries, useProjectEvents } from './hooks'
import { Screen } from './screens'
import { PairingGate, useDeviceSession } from './Pairing'
import './style.css'

export const stages = [['discovery', '发现'], ['verification', '核验'], ['experiment', '实验'], ['review', '评审'], ['delivery', '交付'], ['follow_up', '跟踪']]
export const taskLabels = { DRAFT: '草稿', READY: '待执行', RUNNING: '执行中', EXECUTION_REPORTED: '结果已提交', VERIFYING: '验收中', ACCEPTED: '已验收', FAILED: '失败', BLOCKED: '受阻', CANCELLED: '已取消', NEEDS_REVALIDATION: '需重验', DEFERRED_NO_PROGRESS: '无进展延期' }
export const runLabels = { QUEUED: '排队', STARTING: '启动中', RUNNING: '运行中', CANCEL_REQUESTED: '取消请求中', SETTLED: '执行已结束', FAILED: '执行失败', CANCELLED: '已取消', LOST: '连接丢失', RECONCILING: '恢复对账中' }

const navigation = [['home', '工作台', 'workbench'], ['cycle', '研究周期', 'cycle'], ['release', '成果审查', 'release'], ['evidence', '来源证据', 'evidence'], ['experiment', '实验评测', 'experiment'], ['knowledge', '知识技能', 'knowledge'], ['team', '团队运行器', 'team'], ['resources', '费用资源', 'resources'], ['settings', '设置设备', 'settings']]

function routeOf(path) {
  const p = path.split('/').filter(Boolean).map(decodeURIComponent)
  if (!p.length) return { kind: 'projects', key: path }
  if (p[0] !== 'p' || !p[1]) return { kind: 'not-found', key: path }
  const projectId = p[1]
  if (p.length === 2) return { kind: 'workbench', projectId, key: path }
  const kind = { cycles: 'cycle', tasks: 'task', releases: 'release', evidence: 'evidence', experiments: 'experiment', knowledge: 'knowledge', team: 'team', resources: 'resources', settings: 'settings' }[p[2]]
  if (!kind || (['evidence', 'knowledge', 'team', 'resources', 'settings'].includes(kind) && p.length > 3)) return { kind: 'not-found', projectId, key: path }
  if (['cycle', 'task', 'release', 'experiment'].includes(kind) && !p[3]) return { kind: 'selection', section: kind, projectId, key: path }
  return { kind, projectId, id: p[3], key: path }
}

function useRoute() {
  const currentRoute = () => ({ ...routeOf(location.pathname), search: location.search })
  const [route, setRoute] = useState(currentRoute)
  useEffect(() => { const pop = () => setRoute(currentRoute()); addEventListener('popstate', pop); return () => removeEventListener('popstate', pop) }, [])
  const navigate = path => { const target = new URL(path, location.origin); if (target.pathname + target.search !== location.pathname + location.search) history.pushState(null, '', target); setRoute({ ...routeOf(target.pathname), search: target.search }); scrollTo(0, 0) }
  return [route, navigate]
}

export function Link({ to, navigate, children, ...props }) {
  return <a {...props} href={to} onClick={event => { props.onClick?.(event); if (!event.defaultPrevented && event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) { event.preventDefault(); navigate(to) } }}>{children}</a>
}

function Icon({ name }) {
  const paths = {
    home: <><path d="M3 10 12 3l9 7v10H3z"/><path d="M9 20v-6h6v6"/></>,
    cycle: <><path d="M20 7a8 8 0 0 0-14-2L4 7M4 3v4h4M4 17a8 8 0 0 0 14 2l2-2M16 17h4v4"/></>,
    release: <path d="M5 3h11l3 3v15H5zM8 10h8M8 14h8M8 18h5"/>,
    evidence: <path d="M4 4h16v16H4zM8 8h8M8 12h6M8 16h8"/>,
    experiment: <path d="M8 3h8M10 3v7l-5 9a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2l-5-9V3M8 16h8"/>,
    knowledge: <path d="M3 5c3-2 6-2 9 0 3-2 6-2 9 0v15c-3-2-6-2-9 0-3-2-6-2-9 0zM12 5v15"/>,
    team: <><circle cx="8" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M2 20c0-4 3-6 6-6s6 2 6 6M14 15c4-1 8 1 8 5"/></>,
    resources: <><circle cx="12" cy="12" r="9"/><path d="M15 8H10a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H9M12 5v3m0 8v3"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M19 5l-2 2M7 17l-2 2"/></>,
    menu: <path d="M3 6h18M3 12h18M3 18h18"/>, close: <path d="M5 5l14 14M19 5 5 19"/>,
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name] || paths.home}</svg>
}

function StageRail({ projection, state, releases, navigate, projectId, onClose }) {
  return <div className="rail-inner"><div className="rail-heading"><h2>阶段进度</h2><button className="icon-button drawer-close" aria-label="关闭进度" onClick={onClose}><Icon name="close"/></button></div>
    {projection ? <><p className="small-muted">计划版本 {projection.plan_revision} · 事件水位 {projection.as_of_event_sequence}</p>{projection.plan_change_note && <p className="small-muted">{projection.plan_change_note}</p>}<ol className="stage-list">{stages.map(([stage, label], index) => {
      const value = projection.stages?.find(row => row.stage === stage)
      return <li key={stage}><span className="stage-number">{index + 1}</span><span className="stage-title">{label}</span><span className="stage-count">{value ? `${value.accepted} / ${value.planned} 已验收` : '尚无计划'}</span>{value?.active > 0 && <span className="stage-extra">{value.active} 进行中</span>}{value?.pending_review > 0 && <span className="stage-extra">{value.pending_review} 待评审</span>}{value?.blocked > 0 && <span className="stage-extra warning">{value.blocked} 受阻</span>}</li>
    })}</ol></> : <p className="empty-inline">进度投影尚不可用，暂不显示百分比。</p>}
    <div className="rail-section"><h3>当前阻塞</h3><p>{state?.blocking_conflict_ids?.length ? `${state.blocking_conflict_ids.length} 项冲突待处理` : '无已记录的阻塞冲突'}</p></div>
    <div className="rail-section"><h3>最近已验收成果</h3>{itemsOf(releases).length ? itemsOf(releases).slice(-3).reverse().map(item => <Link className="rail-release" key={item.id} navigate={navigate} to={`/p/${projectId}/releases/${item.id}`}>{item.summary}<small>里程碑 {item.sequence}</small></Link>) : <p>尚无已验收成果</p>}</div>
  </div>
}

function NotificationDrawer({ notifications, projectId, navigate, mutate, onClose }) {
  const [busy, setBusy] = useState(null)
  async function read(notification) {
    if (notification.status === 'READ') return
    setBusy(notification.id)
    try { await mutate('markNotificationRead', { params: { projectId, id: notification.id }, etag: etagOf(notification), body: { reason: '用户在工作台已读通知' } }, '通知已标记为已读') }
    catch { /* App feedback shows the service error */ }
    finally { setBusy(null) }
  }
  return <div className="notice-inner"><div className="rail-heading"><h2>通知</h2><button className="icon-button drawer-close" aria-label="关闭通知" onClick={onClose}><Icon name="close"/></button></div>
    {notifications.length ? notifications.map(item => <div className="notice-row" key={item.id}><span className={`tag ${item.status === 'UNREAD' ? 'good' : ''}`}>{item.status === 'UNREAD' ? '未读' : '已读'}</span><p>{item.summary}</p><small>{new Date(item.created_at).toLocaleString()}</small><div className="button-row">{item.release_id && <Link to={`/p/${projectId}/releases/${item.release_id}`} navigate={navigate} onClick={onClose}>查看成果</Link>}{item.resource_request_id && <Link to={`/p/${projectId}/resources`} navigate={navigate} onClick={onClose}>查看资源</Link>}{item.status === 'UNREAD' && <button disabled={busy === item.id} onClick={() => read(item)}>标记已读</button>}</div></div>) : <p className="empty-state">没有项目通知。</p>}
  </div>
}

function AuthGate({ onToken }) {
  const [value, setValue] = useState('')
  return <div className="auth-wrap"><div className="auth-card"><span className="brandmark">R</span><h1>ResearchOS</h1><p>输入本机已配置的访问令牌，打开研究工作台。令牌只保存在当前页面内存中，关闭页面即清除。</p><form onSubmit={event => { event.preventDefault(); if (value.trim()) onToken(value.trim()) }}><label htmlFor="access-token">访问令牌</label><input id="access-token" type="password" autoComplete="off" value={value} onChange={event => setValue(event.target.value)} required/><button className="primary" type="submit">打开工作台</button></form><small>令牌由本机受保护的凭据管理流程提供。</small></div></div>
}

function App() {
  const [token, setToken] = useState('')
  const deviceSession = useDeviceSession(setToken)
  const [theme, setTheme] = useState(() => localStorage.getItem('researchos.theme') === 'dark' ? 'dark' : 'light')
  const [route, navigate] = useRoute()
  const [drawer, setDrawer] = useState(null)
  const [compact, setCompact] = useState(() => matchMedia('(max-width: 767px)').matches)
  const [feedback, setFeedback] = useState(null)
  const [refresh, setRefresh] = useState(0)
  const drawerOpener = useRef(null)
  const api = useMemo(() => token ? createApi(() => token) : null, [token])
  const events = useProjectEvents(api, route.projectId)
  const shared = useQueries(api, route.projectId, route.projectId ? [{ op: 'getProjectProfile' }, { op: 'getProjectState' }, { op: 'getProgressProjection' }, { op: 'listMilestoneRelease' }, { op: 'listNotification' }] : [], refresh + events.refresh)
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    Object.entries(tokens.themes[theme]).forEach(([name, value]) => document.documentElement.style.setProperty(`--${name.replaceAll('_', '-')}`, value))
    const size = { 'body-size': `${tokens.font.body_size_px}px`, 'body-line-height': tokens.font.body_line_height, 'title-size': `${tokens.font.title_size_px}px`, 'small-size': `${tokens.font.small_size_px}px`, 'header-height': `${tokens.layout.header_height_px}px`, 'nav-width': `${tokens.layout.nav_width_px}px`, 'progress-width': `${tokens.layout.progress_width_px}px`, 'mobile-target': `${tokens.layout.mobile_target_px}px`, 'control-radius': `${tokens.radius_px.control}px`, 'card-radius': `${tokens.radius_px.card}px`, 'panel-radius': `${tokens.radius_px.panel}px` }
    Object.entries(size).forEach(([name, value]) => document.documentElement.style.setProperty(`--${name}`, value))
    localStorage.setItem('researchos.theme', theme)
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
  if (!token && (location.pathname === '/pair' || deviceSession.error || location.hostname.endsWith('.trycloudflare.com'))) return <PairingGate sessionError={deviceSession.error} onSession={session => { deviceSession.accept(session); navigate(`/p/${session.device.project_ids[0]}`) }}/>
  if (!token) return <AuthGate onToken={setToken}/>
  return <>
    <header className="topbar" inert={!!drawer}><button className="icon-button menu-button" aria-label="打开导航" onClick={e => openDrawer('nav', e)}><Icon name="menu"/></button><Link to="/" navigate={navigate} className="brand"><span className="brandmark">R</span><span>ResearchOS</span></Link><span className="top-context">研究工作台</span><span className="top-spacer"/><span className={`connection-dot ${events.online ? '' : 'offline-dot'}`}/><span className="connection-text">{events.online ? '已连接' : '连接中断'}</span>{projectId && <button className="theme-button" aria-label={`打开通知，${unread} 条未读`} onClick={e => openDrawer('notice', e)}>通知{unread ? ` ${unread}` : ''}</button>}<button className="theme-button" onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')} aria-label={`切换为${theme === 'light' ? '深色' : '浅色'}主题`}>{theme === 'light' ? '深色' : '浅色'}</button><button className="icon-button progress-button" aria-label="打开阶段进度" onClick={e => openDrawer('rail', e)}><Icon name="cycle"/></button></header>
    {projectId && !events.online && <div className="connection-banner" role="status">连接已断开，状态可能过期。{events.lastSync ? `最后同步 ${events.lastSync.toLocaleString()}` : '尚未同步'}。</div>}
    {feedback && <div className={`feedback ${feedback.kind}`} role="status"><span>{feedback.text}</span><button aria-label="关闭提示" onClick={() => setFeedback(null)}><Icon name="close"/></button></div>}
    <div className={`drawer-overlay ${drawer ? 'visible' : ''}`} onClick={() => setDrawer(null)}/>
    <div className="app-grid"><nav className={`sidebar ${drawer === 'nav' ? 'drawer-open' : ''}`} aria-label="主导航" inert={(compact || !!drawer) && drawer !== 'nav'}><div className="sidebar-inner"><div className="sidebar-head"><span>项目空间</span><button className="icon-button drawer-close" aria-label="关闭导航" onClick={() => setDrawer(null)}><Icon name="close"/></button></div><Link to="/" navigate={navigate} className="project-switch">{profile?.name || '选择项目'}<small>{projectId ? '切换项目' : '项目入口'}</small></Link><div className="nav-group">{navigation.map(([icon, label, kind]) => <Link key={kind} to={navUrl(kind)} navigate={navigate} aria-label={label} className={`nav-link ${route.kind === kind ? 'active' : ''}`}><Icon name={icon}/><span>{label}</span></Link>)}</div><div className="sidebar-bottom"><span className="connection-dot"/> {events.online ? '已连接' : '等待连接'}<small>开发阶段 · 以服务回执为准</small></div></div></nav>
      <main id="main" className="main-area" tabIndex="-1" inert={!!drawer}><Screen key={route.key} route={route} api={api} navigate={navigate} shared={shared} events={events} refresh={refresh + events.refresh} mutate={mutate} onRefresh={() => setRefresh(n => n + 1)}/></main>
      <aside className={`progress-rail ${drawer === 'rail' ? 'drawer-open' : ''}`} aria-label="阶段进度" inert={(compact || !!drawer) && drawer !== 'rail'}><StageRail projection={shared.data.getProgressProjection} state={state} releases={shared.data.listMilestoneRelease} navigate={navigate} projectId={projectId} onClose={() => setDrawer(null)}/></aside></div>
    {drawer === 'notice' && <aside className="notice-drawer" aria-label="通知列表"><NotificationDrawer notifications={notifications} projectId={projectId} navigate={navigate} mutate={mutate} onClose={() => setDrawer(null)}/></aside>}
    {projectId && <nav className="bottom-nav" aria-label="手机主要导航" inert={!!drawer}>{[['home', '工作台', 'workbench'], ['cycle', '周期', 'cycle'], ['release', '成果', 'release'], ['resources', '资源', 'resources']].map(([icon, label, kind]) => <Link key={kind} to={navUrl(kind)} navigate={navigate} className={route.kind === kind ? 'active' : ''}><Icon name={icon}/><span>{label}</span></Link>)}</nav>}
  </>
}

createRoot(document.getElementById('root')).render(<App />)

import React, { useState } from 'react'
import { etagOf, itemsOf } from '../api'
import { Link, navigation, stages } from '../navigation'

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
    chat: <path d="M4 5h16v11H9l-5 4z M8 9h8M8 12h5"/>,
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

export function AppShell({ route, navigate, drawer, setDrawer, compact, openDrawer, connection, events, projectId, profile,
  unread, theme, setTheme, notifications, shared, state, feedback, setFeedback, deviceSession, api, mutate,
  navUrl, children }) {
  return <>
    <header className={`topbar ${route.kind === 'workbench' ? 'workbench-topbar' : ''} ${!projectId ? 'assistant-topbar' : ''}`} inert={!!drawer}>{projectId && <button className="icon-button menu-button" aria-label="打开导航" onClick={e => openDrawer('nav', e)}><Icon name="menu"/></button>}<Link to="/" navigate={navigate} className="brand"><span className="brandmark">R</span><span>ResearchOS</span></Link><span className="top-context">{projectId ? '项目工作台' : '本机 AI 工作空间'}</span>{!projectId && <nav className="home-navigation" aria-label="主导航"><Link to="/" navigate={navigate} aria-current="page">项目</Link></nav>}<span className="top-spacer"/><span className="host-connection" role="status" title="Host 连通状态；不代表 Harness 或模型能力已验证"><span className={`connection-dot ${connection.state === 'ready' ? '' : connection.state === 'checking' ? 'checking-dot' : 'offline-dot'}`}/><span className="connection-text">{connection.label}</span></span>{projectId && <button className="theme-button" aria-label={`打开通知，${unread} 条未读`} onClick={e => openDrawer('notice', e)}>通知{unread ? ` ${unread}` : ''}</button>}<button className="theme-button" onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')} aria-label={`切换为${theme === 'light' ? '深色' : '浅色'}主题`}>{theme === 'light' ? '深色' : '浅色'}</button>{projectId && <button className="icon-button progress-button" aria-label="打开阶段进展" onClick={e => openDrawer('rail', e)}><Icon name="cycle"/></button>}</header>
    {projectId && !events.online && <div className="connection-banner" role="status">连接已断开，状态可能过期。{events.lastSync ? `最后同步 ${events.lastSync.toLocaleString()}` : '尚未同步'}。</div>}
    {deviceSession.device && <div className="connection-banner" role="status">{(api?.deviceRole() || deviceSession.device.role) === 'READER' ? '此设备为只读监督；控制操作需要电脑显式授权。' : '此设备可控制已授权项目；设备和全局设置仍由电脑管理。'}</div>}
    {feedback && <div className={`feedback ${feedback.kind}`} role="status"><span>{feedback.text}</span><button aria-label="关闭提示" onClick={() => setFeedback(null)}><Icon name="close"/></button></div>}
    <div className={`drawer-overlay ${drawer ? 'visible' : ''}`} onClick={() => setDrawer(null)}/>
    <div className={`app-grid ${route.kind === 'workbench' ? 'workbench-route' : ''} ${!projectId ? 'assistant-route' : ''}`}>{projectId && <nav className={`sidebar ${drawer === 'nav' ? 'drawer-open' : ''}`} aria-label="主导航" inert={(compact || !!drawer) && drawer !== 'nav'}><div className="sidebar-inner"><div className="sidebar-head"><span>项目空间</span><button className="icon-button drawer-close" aria-label="关闭导航" onClick={() => setDrawer(null)}><Icon name="close"/></button></div><Link to="/" navigate={navigate} className="project-switch">{profile?.name || '选择项目'}<small>{projectId ? '切换项目' : '项目入口'}</small></Link><div className="nav-group">{navigation.map(([icon, label, kind]) => <Link key={kind} to={navUrl(kind)} navigate={navigate} aria-label={label} className={`nav-link ${route.kind === kind ? 'active' : ''}`}><Icon name={icon}/><span>{label}</span></Link>)}</div><div className="sidebar-bottom"><span className={`connection-dot ${events.online ? '' : 'offline-dot'}`}/> {events.online ? '已连接' : events.message || '连接中断'}<small>开发阶段 · 以服务回执为准</small></div></div></nav>}
      <main id="main" className="main-area" tabIndex="-1" inert={!!drawer}>{children}</main>
      {projectId && <aside className={`progress-rail ${drawer === 'rail' ? 'drawer-open' : ''}`} aria-label="阶段进度" inert={(compact || !!drawer) && drawer !== 'rail'}><StageRail projection={shared.data.getProgressProjection} state={state} releases={shared.data.listMilestoneRelease} navigate={navigate} projectId={projectId} onClose={() => setDrawer(null)}/></aside>}</div>
    {drawer === 'notice' && <aside className="notice-drawer" aria-label="通知列表"><NotificationDrawer notifications={notifications} projectId={projectId} navigate={navigate} mutate={mutate} onClose={() => setDrawer(null)}/></aside>}
    {projectId && <nav className="bottom-nav" aria-label="手机主要导航" inert={!!drawer}>{[['home', '工作台', 'workbench'], ['cycle', '周期', 'cycle'], ['release', '成果', 'release'], ['resources', '资源', 'resources']].map(([icon, label, kind]) => <Link key={kind} to={navUrl(kind)} navigate={navigate} className={route.kind === kind ? 'active' : ''}><Icon name={icon}/><span>{label}</span></Link>)}</nav>}
  </>
}

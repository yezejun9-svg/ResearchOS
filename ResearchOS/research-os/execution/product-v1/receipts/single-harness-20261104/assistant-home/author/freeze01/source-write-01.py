import hashlib, json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-assistant-home-20261104')
EVIDENCE = Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-assistant-startup-author')
SCOPE = json.loads(Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/assistant-home/scope.json').read_text(encoding='utf-8'))
sources = {}
for rel, expected in SCOPE['baseline_sha256'].items():
    p = ROOT / rel
    assert (not p.exists()) if expected == 'ABSENT_BEFORE' else hashlib.sha256(p.read_bytes()).hexdigest() == expected, rel
    if p.exists():
        sources[rel] = p.read_text(encoding='utf-8')
        target = EVIDENCE / 'baseline-source' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists(), target
        target.write_bytes(p.read_bytes())

startup = r'''// View preferences and startup health only. Neither grants execution authority.
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
    }).slice(0, RECENT_LIMIT)
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
    if (accessible.has(row.project_id) && !selected.has(row.project_id) && opened.length < 6) {
      selected.add(row.project_id); opened.push(accessible.get(row.project_id))
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
'''

main = sources['apps/web/src/main.jsx']
main = main.replace("import './style.css'", "import { readTheme, saveTheme, rememberProject, startHostHealthMonitor } from './startup.js'\nimport './style.css'")
main = main.replace("useState(() => localStorage.getItem('researchos.theme') === 'dark' ? 'dark' : 'light')", "useState(() => readTheme())")
main = main.replace("  const [route, navigate] = useRoute()", "  const [route, navigate] = useRoute()\n  const [hostHealth, setHostHealth] = useState({ state: 'checking', label: '正在检查 Host' })\n  useEffect(() => {\n    if (!nativeDesktop) return\n    return startHostHealthMonitor({ read: () => window.researchos.statusHealth({}), onChange: setHostHealth })\n  }, [])")
main = main.replace("localStorage.setItem('researchos.theme', theme)", "saveTheme(theme)")
main = main.replace("  const profile = shared.data.getProjectProfile", "  const profile = shared.data.getProjectProfile\n  useEffect(() => { if (projectId && profile) rememberProject(projectId) }, [projectId, profile])\n  const connection = nativeDesktop ? hostHealth : { state: events.online ? 'ready' : 'unavailable', label: events.online ? '项目事件已连接' : '项目事件未连接' }")
main = main.replace("openDrawer={openDrawer} events={events}", "openDrawer={openDrawer} connection={connection} events={events}")

screens = sources['apps/web/src/screens.jsx']
screens = screens.replace("import { Header, Section", "import { projectGroups, readRecentProjects } from './startup.js'\nimport { Header, Section")
needle = "  return <><Header title=\"项目入口\""
idx = screens.index(needle, screens.index('function Projects('))
screens = screens[:idx] + '''  if (window.researchos?.desktop) {
    const groups = projectGroups(projects, readRecentProjects())
    const projectRows = rows => <div className="assistant-projects">{rows.map(project => <Link key={project.project_id} className="assistant-project" to={`/p/${encodeURIComponent(project.project_id)}`} navigate={navigate}><span className="project-monogram" aria-hidden="true">{(project.name || 'P').slice(0, 1)}</span><span><strong>{project.name || '未命名项目'}</strong><small>{project.intent || '打开项目工作台'}</small></span><span className="project-open" aria-hidden="true">↗</span></Link>)}</div>
    return <div className="assistant-home">
      <section className="assistant-intro" aria-labelledby="assistant-title"><span className="assistant-eyebrow"><span aria-hidden="true">✳</span> YOUR LOCAL WORKSPACE</span><h1 id="assistant-title">把想法，<span>推进一步。</span></h1><p>从你的项目开始，和 Codex 理清下一步。<br/>对话、任务与每一步真实进展，都在一个工作台。</p></section>
      <NativeProjectEntry navigate={navigate} onRefresh={onRefresh}/>
      <section className="assistant-project-section" aria-label="项目"><div className="assistant-section-heading"><h2>{groups.recent.length ? '最近项目' : '可访问项目'}</h2><span>{state.data.listProjects ? `${projects.length} 个项目` : '读取项目中'}</span></div><StateNotice state={state} onRetry={onRefresh}/>
        {groups.recent.length ? <>{projectRows(groups.recent)}{groups.other.length > 0 && <details className="other-projects"><summary>其他可访问项目（{groups.other.length}）</summary>{projectRows(groups.other)}</details>}</> : groups.other.length ? projectRows(groups.other) : !state.loading && !state.errors.listProjects && <div className="assistant-empty"><span aria-hidden="true">⌁</span><p>你的下一个项目，从这里开始。</p><small>打开一个本地目录，它就会出现在这里。</small></div>}
      </section>
      <ol className="assistant-method" aria-label="使用流程"><li><span>01</span> 打开项目</li><li><span>02</span> 描述目标</li><li><span>03</span> 查看真实轨迹</li></ol>
      <p className="assistant-footnote">本机 Host 协调任务 · 具体能力以工作台实际状态为准</p>
    </div>
  }
''' + screens[idx:]

workbench = sources['apps/web/src/workbench.jsx']
workbench = workbench.replace("import { composerSubmitKey", "import { workspaceProjectPath } from './startup.js'\nimport { composerSubmitKey")
workbench = workbench.replace("if (!value.project_id || !value.workspace?.authorized_workspace_ref)", "if (!workspaceProjectPath(value))")
start = workbench.index('  return <Panel title="从本地目录开始">', workbench.index('export function NativeProjectEntry('))
end = workbench.index('\n}\n', start)
workbench = workbench[:start] + '''  return <section className="local-project-entry" aria-labelledby="local-project-title">
    <div className="local-project-main"><span className="local-project-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 6h7l2 2h9v11H3z"/><path d="M3 6V4h7l2 2"/></svg></span><div><h2 id="local-project-title">打开本地项目</h2><p>选择目录，连接你的工作空间。</p></div><button className="primary" disabled={busy} onClick={choose}>{busy ? '正在打开…' : '选择目录'} <span aria-hidden="true">↗</span></button></div>
    <details className="project-name-option"><summary>自定义项目名称</summary><label>显示名称<input value={name} onChange={event => setName(event.target.value)} placeholder="默认使用目录名称"/></label></details>
    <div className="local-project-note"><span>在本机登记目录并盘点文件，保留原内容。</span>{host && <span>已登记 {host.workspaces?.length || 0} 个工作区</span>}</div>
    <Failure error={hostError} retry={checkHost}/><Failure error={error}/>
    {result && <div className="project-open-result" role="status"><div><strong>项目已登记</strong><p className="break-all">{result.workspace.display_path}</p></div><button className="primary" onClick={() => navigate(workspaceProjectPath(result))}>打开工作台 <span aria-hidden="true">→</span></button></div>}
  </section>''' + workbench[end:]

shell = sources['apps/web/src/components/app-shell.jsx']
shell = shell.replace('openDrawer, events, projectId', 'openDrawer, connection, events, projectId')
start = shell.index('    <header className=')
end = shell.index('\n    {projectId && !events.online', start)
shell = shell[:start] + '''    <header className={`topbar ${route.kind === 'workbench' ? 'workbench-topbar' : ''} ${!projectId ? 'assistant-topbar' : ''}`} inert={!!drawer}>{projectId && <button className="icon-button menu-button" aria-label="打开导航" onClick={e => openDrawer('nav', e)}><Icon name="menu"/></button>}<Link to="/" navigate={navigate} className="brand"><span className="brandmark">R</span><span>ResearchOS</span></Link><span className="top-context">{projectId ? '项目工作台' : '本机 AI 工作空间'}</span>{!projectId && <nav className="home-navigation" aria-label="主导航"><Link to="/" navigate={navigate} aria-current="page">项目</Link></nav>}<span className="top-spacer"/><span className="host-connection" role="status" title="Host 连通状态；不代表 Harness 或模型能力已验证"><span className={`connection-dot ${connection.state === 'ready' ? '' : connection.state === 'checking' ? 'checking-dot' : 'offline-dot'}`}/><span className="connection-text">{connection.label}</span></span>{projectId && <button className="theme-button" aria-label={`打开通知，${unread} 条未读`} onClick={e => openDrawer('notice', e)}>通知{unread ? ` ${unread}` : ''}</button>}<button className="theme-button" onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')} aria-label={`切换为${theme === 'light' ? '深色' : '浅色'}主题`}>{theme === 'light' ? '深色' : '浅色'}</button>{projectId && <button className="icon-button progress-button" aria-label="打开阶段进展" onClick={e => openDrawer('rail', e)}><Icon name="cycle"/></button>}</header>''' + shell[end:]
shell = shell.replace("${route.kind === 'workbench' ? 'workbench-route' : ''}`}><nav", "${route.kind === 'workbench' ? 'workbench-route' : ''} ${!projectId ? 'assistant-route' : ''}`}>{projectId && <nav")
shell = shell.replace('</div></nav>\n      <main', '</div></nav>}\n      <main')
shell = shell.replace('      <aside className={`progress-rail', '      {projectId && <aside className={`progress-rail')
shell = shell.replace('onClose={() => setDrawer(null)}/></aside></div>', 'onClose={() => setDrawer(null)}/></aside>}</div>')

desktop = sources['apps/desktop/main/main.js']
idx = desktop.index('\nconst deps = {')
desktop = desktop[:idx] + '''
// Main-only status observation must not compete with a renderer presentation
// ticket. The private lane retains host/context and pending-write validation.
async function smokeNativeProbe(dependencies) {
  const reply = await ipc.callV2(dependencies, 'host.status', {}, ipc.AUTHORITY_READ);
  return { ok: reply.ok === true, protocol_status: reply.protocol_status || null, reason: reply.reason || null };
}
''' + desktop[idx:]
old = '''? await win.webContents.executeJavaScript(`window.researchos.v2['host.status']({}).then(r => ({
        ok: r.ok === true, protocol_status: r.protocol_status || null, reason: r.reason || null
      }))`)'''
assert desktop.count(old) == 1
desktop = desktop.replace(old, '? await smokeNativeProbe(v2Deps)')

css = sources['apps/web/src/style.css'].replace('var(--text,#18241d)', 'var(--text,#EDF3EE)').replace('var(--background,#f5f6f3)', 'var(--background,#111713)')
css += '''
/* The empty workspace has one real entry point. Project tooling begins inside
   a project; the landing does not simulate a conversation or execution. */
.host-connection{display:inline-flex;align-items:center;gap:5px}.checking-dot{background:var(--muted)}
.assistant-topbar{background:var(--background);border-bottom-color:transparent;padding:0 clamp(20px,4vw,64px);height:72px}.assistant-topbar .brandmark{background:var(--accent-soft);color:var(--accent);border:1px solid var(--border);border-radius:9px}.assistant-topbar .brand{font-size:16px}.assistant-topbar .top-context{font-size:11px}.home-navigation{margin-left:24px}.home-navigation a{font-size:12px;color:var(--text);padding:7px 12px;border-radius:7px;background:var(--subtle)}
.app-grid.assistant-route{display:block;min-height:calc(100vh - 72px)}.assistant-route .main-area{max-width:940px;padding:48px 36px 42px}.assistant-home{max-width:760px;margin:0 auto}.assistant-intro{margin-bottom:32px}.assistant-eyebrow{display:flex;align-items:center;gap:9px;font:10px/1.5 Consolas,monospace;letter-spacing:.16em;color:var(--muted);margin-bottom:18px}.assistant-eyebrow>span{font-size:22px;line-height:1;color:var(--accent)}.assistant-intro h1{font-size:clamp(30px,4vw,44px);font-weight:600;line-height:1.28;letter-spacing:-.045em;margin-bottom:16px}.assistant-intro h1>span{color:var(--accent)}.assistant-intro p{color:var(--muted);font-size:14px;line-height:1.8}
.local-project-entry{border:1px solid var(--border);border-radius:16px;background:var(--surface);padding:22px 24px;box-shadow:0 12px 40px #00000008}.local-project-main{display:flex;align-items:center;gap:15px}.local-project-icon{display:grid;place-items:center;width:44px;height:44px;flex:none;border-radius:11px;background:var(--accent-soft);color:var(--accent)}.local-project-icon svg{width:23px;height:23px}.local-project-main h2{font-size:16px;font-weight:600}.local-project-main p{font-size:12px;color:var(--muted);margin-top:3px}.local-project-main>button{margin-left:auto;white-space:nowrap;font-size:12px;min-height:38px;padding:7px 13px}.local-project-main>button>span{padding-left:14px}.project-name-option{margin:15px 0 0 59px;font-size:11px;color:var(--muted)}.project-name-option summary{cursor:pointer;width:fit-content}.project-name-option label{margin-top:12px;max-width:320px}.project-name-option input{width:100%}.local-project-note{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:10px;color:var(--muted);border-top:1px solid var(--border);padding-top:14px;margin-top:17px}.local-project-entry .state-notice{margin:14px 0 0;font-size:12px}.project-open-result{display:flex;align-items:center;gap:16px;border-top:1px solid var(--border);padding-top:18px;margin-top:18px}.project-open-result>div{min-width:0;flex:1}.project-open-result strong{font-size:13px;color:var(--accent)}.project-open-result p{font:11px/1.6 Consolas,monospace;color:var(--muted);margin-top:4px}.project-open-result button{flex:none;font-size:12px}
.assistant-project-section{margin-top:30px}.assistant-section-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}.assistant-section-heading h2{font-size:12px;font-weight:600}.assistant-section-heading>span{font-size:10px;color:var(--muted)}.assistant-projects{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;max-height:360px;overflow:auto}.assistant-project{display:flex;gap:12px;align-items:center;min-width:0;min-height:76px;padding:14px 15px;border:1px solid var(--border);border-radius:10px;color:var(--text);background:var(--surface)}.assistant-project:hover{background:var(--subtle);border-color:var(--muted);text-decoration:none}.project-monogram{display:grid;place-items:center;width:31px;height:31px;flex:none;border:1px solid var(--border);border-radius:7px;font:13px Consolas,monospace;color:var(--accent);background:var(--background)}.assistant-project>span:nth-child(2){min-width:0;flex:1}.assistant-project strong{display:block;font-size:12px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.assistant-project small{display:block;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}.project-open{color:var(--muted);font-size:14px}.other-projects{margin-top:12px}.other-projects summary{cursor:pointer;font-size:11px;color:var(--muted);padding:6px 0}.other-projects[open] summary{margin-bottom:8px}.assistant-empty{padding:22px 16px;text-align:center;border:1px dashed var(--border);border-radius:10px}.assistant-empty>span{display:block;font-size:23px;color:var(--accent);line-height:1.2;margin-bottom:7px}.assistant-empty p{font-size:12px;color:var(--muted)}.assistant-empty small{font-size:10px;display:block;margin-top:3px}
.assistant-method{list-style:none;display:flex;justify-content:center;gap:28px;padding:0;margin:30px 0 12px;color:var(--muted);font-size:10px}.assistant-method li+li{margin-top:0}.assistant-method span{font:10px Consolas,monospace;margin-right:7px;color:var(--accent)}.assistant-footnote{text-align:center;font-size:10px;color:var(--muted)}
@media(max-width:767px){.assistant-topbar{height:64px;padding:0 16px;gap:10px}.assistant-topbar .brand{font-size:14px}.assistant-topbar .brandmark{width:28px;height:28px}.assistant-topbar .connection-text{display:none}.home-navigation{margin-left:0}.home-navigation a{font-size:11px;padding:6px 8px}.assistant-route .main-area{padding:32px 20px}.assistant-intro{margin-bottom:26px}.assistant-intro h1{font-size:32px}.assistant-intro p{font-size:12px}.local-project-entry{padding:18px}.local-project-main{gap:11px;flex-wrap:wrap}.local-project-main h2{font-size:14px}.local-project-main p{font-size:11px}.local-project-main>button{min-height:44px}.local-project-icon{width:36px;height:36px}.project-name-option{margin-left:0}.assistant-projects{grid-template-columns:minmax(0,1fr)}.assistant-method{gap:16px;font-size:9px}.project-open-result{align-items:flex-start;flex-direction:column}.assistant-topbar .theme-button{min-width:44px}.assistant-home .assistant-project{display:flex}}
@media(max-width:390px){.assistant-topbar .brand span:last-child{display:inline}.assistant-topbar .top-context{display:none}.home-navigation{display:none}.local-project-main>button{width:100%;margin-top:5px}.assistant-method{gap:11px}.assistant-method span{margin-right:4px}}
'''

changed = {'apps/web/src/main.jsx':main, 'apps/web/src/screens.jsx':screens, 'apps/web/src/workbench.jsx':workbench,
           'apps/web/src/components/app-shell.jsx':shell, 'apps/web/src/style.css':css,
           'apps/web/src/startup.js':startup, 'apps/desktop/main/main.js':desktop}
assert set(changed) == set(SCOPE['production_paths'])
for rel, text in changed.items():
    assert text != sources.get(rel), rel
    draft = EVIDENCE / 'source-write-01' / rel
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(text, encoding='utf-8', newline='\n')
for rel in changed:
    (ROOT / rel).write_bytes((EVIDENCE / 'source-write-01' / rel).read_bytes())
print(json.dumps({'status':'SOURCE_WRITTEN','paths':{rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in changed}}, ensure_ascii=True))

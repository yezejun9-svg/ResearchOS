import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ApiError, classify, etagOf, itemsOf } from './api'
import { useQueries } from './hooks'
import { Link, taskLabels, runLabels } from './main'
import { ArtifactPreview } from './preview'
import { ProfileDraft } from './profile-draft'
import { DevicePanel } from './Pairing'
import { Continuity } from './continuity'
import { ResourceRecovery } from './resource-recovery.jsx'

const briefDate = raw => raw ? new Date(raw).toLocaleString() : '未记录'
const short = raw => raw ? String(raw).slice(0, 12) : '—'
function Header({ title, description, action }) { return <header className="page-heading"><div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header> }
function Section({ title, aside, children, className = '' }) { return <section className={`panel ${className}`}><div className="section-heading"><h2>{title}</h2>{aside}</div>{children}</section> }
function Tag({ value, type }) { return <span className={`tag ${type || (/失败|受阻|拒绝|限流|过期|PARTIAL|RATE_LIMITED/.test(String(value)) ? 'warning' : /验收|COMPLETE|CURRENT|IMPROVED/.test(String(value)) ? 'good' : '')}`}>{value ?? '未知'}</span> }
function Empty({ children }) { return <p className="empty-state">{children || '当前没有记录。'}</p> }
function StateNotice({ state, empty, onRetry }) {
  if (state.loading) return <div className="loading-state" role="status"><span className="loading-line"/><span className="loading-line short"/>正在读取已保存状态…</div>
  const entries = Object.entries(state.errors)
  if (entries.length) return <div className="state-notice" role="status">{entries.map(([name, error]) => <p key={name}><strong>{name}</strong>：{({ forbidden: '无权访问', missing: '记录不存在', stale: '版本已变化', limited: '请求被限流', unavailable: '服务能力尚未提供', offline: '连接中断', timeout: '请求超时，请重新读取' })[classify(error)] || '读取失败'}。{error?.correlationId && <small>请求 {error.correlationId}</small>}</p>)}{onRetry && <button onClick={onRetry}>重新读取</button>}</div>
  if (empty) return <Empty/>
  return null
}
function JsonDetails({ value, label = '查看原始字段' }) { return <details className="raw-details"><summary>{label}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details> }
function Table({ headers, rows }) { return <div className="table-wrap"><table><thead><tr>{headers.map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>)}</tbody></table></div> }
function refFor(value, kind) { return { entity_type: kind, id: value.id, revision: value.revision, content_hash: value.content_hash ?? null } }

function IdeaForm({ api, projectId, onCreated }) {
  const storageKey = `researchos:intent:${projectId}`
  const saved = useMemo(() => { try { return JSON.parse(localStorage.getItem(storageKey) || 'null') } catch { return null } }, [storageKey])
  const [open, setOpen] = useState(!!saved), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const [idea, setIdea] = useState(saved?.draft || '')
  const [conflict, setConflict] = useState(null)
  const stage = useRef(saved?.stage || null)
  function persist(draft = idea) { localStorage.setItem(storageKey, JSON.stringify({ draft, stage: stage.current })) }
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError(''); setConflict(null)
    try {
      if (!stage.current) stage.current = { idea, submission: crypto.randomUUID(), requirementKey: crypto.randomUUID(), acceptanceKey: crypto.randomUUID() }
      const staged = stage.current
      persist()
      if (!staged.requirement) {
        if (!staged.stateTag) { const state = await api.call('getProjectState', { params: { projectId } }); staged.stateTag = etagOf(state); persist() }
        staged.requirement = await api.call('createRequirement', { params: { projectId }, etag: staged.stateTag, key: staged.requirementKey, body: { requirement_key: `INTENT-${staged.submission}`, text: staged.idea, basis: 'USER_STATED', source_refs: [], rationale: '用户从工作台提交的原始想法', supersedes_id: null, acceptance_check_ids: [] } })
        persist()
      }
      await api.call('actOnRequirement', { params: { projectId, id: staged.requirement.id }, etag: etagOf(staged.requirement), key: staged.acceptanceKey, body: { action: 'ACCEPT', reason: '用户明确提交并确认此原始意图；授权先生成可审查规划提案', source_validation_refs: [] } })
      localStorage.removeItem(storageKey); stage.current = null; setOpen(false); setIdea(''); onCreated()
    } catch (cause) {
      if (classify(cause) === 'stale') {
        if (!stage.current?.requirement) { delete stage.current.stateTag; persist() }
        try { const current = await api.call('getProjectState', { params: { projectId } }); setConflict(current.revision) } catch { setConflict('暂不可读取') }
      }
      setError(cause.message)
    } finally { setBusy(false) }
  }
  return <><button className="primary" onClick={() => setOpen(v => !v)}>{open ? '收起新想法' : '提出新想法'}</button>{open && <form className="form-block" onSubmit={submit}><p>说出你希望推进的事。系统会保留原话，先生成可审查的规划；需要补充的业务问题和资源会显示在工作台。</p>{stage.current && <p className="callout">提交已保存。刷新或重试会继续同一份想法。</p>}<label>你希望推进什么？<textarea value={idea} onChange={e => { setIdea(e.target.value); persist(e.target.value) }} disabled={!!stage.current} required/></label>{error && <p className="form-error" role="alert">{error}。原话仍保留，可重试。</p>}{conflict !== null && <div className="state-notice"><strong>版本已变化，请核对原话后重试</strong><p>当前项目修订 {conflict}；本地原话和同一提交身份仍保留。</p></div>}<button type="submit" disabled={busy}>{busy ? '正在提交…' : conflict !== null ? '核对后重试' : stage.current ? '继续提交' : '确认原话并开始规划'}</button></form>}</>
}

function Projects({ api, navigate, refresh, onRefresh }) {
  const state = useQueries(api, null, [{ op: 'listProjects' }], refresh)
  const [name, setName] = useState(''), [intent, setIntent] = useState(''), [scope, setScope] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const projects = itemsOf(state.data.listProjects)
  async function create(e) { e.preventDefault(); setBusy(true); setError(''); try { const created = await api.call('createProject', { body: { name, intent, facts: [], accepted_scope: [scope], constraints: [], source_configs: [], source_document_refs: [], read_snapshot_ids: [] } }); onRefresh(); navigate(`/p/${created.project_id}`) } catch (cause) { setError(cause.message) } finally { setBusy(false) } }
  return <><Header title="项目入口" description="从一个项目的真实背景开始，逐步形成可验收的目标。"/><StateNotice state={state} onRetry={onRefresh}/><Section title="已有项目" aside={<span className="small-muted">{projects.length} 个可访问项目</span>}>{projects.length ? <div className="record-list">{projects.map(p => <Link key={p.project_id} className="record-row" to={`/p/${p.project_id}`} navigate={navigate}><strong>{p.name}</strong><span>{p.intent}</span><small>打开工作台 →</small></Link>)}</div> : !state.loading && <Empty>当前还没有可访问的项目。</Empty>}</Section><Section title="建立项目"><form className="form-grid" onSubmit={create}><label>项目名称<input value={name} onChange={e => setName(e.target.value)} required/></label><label>要解决的问题<input value={intent} onChange={e => setIntent(e.target.value)} required/></label><label className="full-row">首个明确范围<input value={scope} onChange={e => setScope(e.target.value)} required/></label>{error && <p className="form-error full-row" role="alert">{error}</p>}<button disabled={busy} type="submit" className="primary">{busy ? '正在创建…' : '创建项目'}</button></form></Section></>
}

function Workbench({ api, projectId, navigate, shared, refresh, onRefresh }) {
  const more = useQueries(api, projectId, [{ op: 'listGoal' }, { op: 'listTask' }, { op: 'listResearchCycle' }, { op: 'listResourceRequest' }], refresh)
  const state = shared.data.getProjectState, profile = shared.data.getProjectProfile
  const tasks = itemsOf(more.data.listTask), goals = itemsOf(more.data.listGoal), cycles = itemsOf(more.data.listResearchCycle)
  const planningTasks = tasks.filter(t => t.task_type === 'intent_planning')
  const businessTasks = tasks.filter(t => !['intent_planning', 'runtime_qualification'].includes(t.task_type))
  const active = cycles.find(c => c.id === state?.active_cycle_id) || cycles.at(-1)
  const release = itemsOf(shared.data.listMilestoneRelease).at(-1)
  return <><Header title={profile?.name || '研究工作台'} description="先看有效进展，再查看执行细节。" action={<IdeaForm key={projectId} api={api} projectId={projectId} onCreated={onRefresh}/>}/><StateNotice state={shared} onRetry={onRefresh}/><StateNotice state={more} onRetry={onRefresh}/><Section title="持续目标" className="goal-section">{goals.length ? goals.filter(g => g.status === 'ACTIVE' || g.status === 'DRAFT').slice(-2).map(goal => <div key={goal.id}><h3>{goal.title}</h3><p>{goal.original_intent}</p><div className="meta-line"><Tag value={goal.status}/><span>修订 {goal.revision}</span></div></div>) : <Empty>尚无目标。用右上角“提出新想法”开始规划。</Empty>}</Section><div className="summary-strip"><div><span>业务已验收</span><strong>{businessTasks.filter(t => t.status === 'ACCEPTED').length}</strong><small>业务任务 {businessTasks.length}</small><small>待执行 {businessTasks.filter(task => task.status === 'READY').length}</small></div><div><span>待评审</span><strong>{businessTasks.filter(t => ['EXECUTION_REPORTED', 'VERIFYING'].includes(t.status)).length}</strong><small>执行结果不算已验收</small></div><div><span>{state?.active_cycle_id ? '当前周期' : '最近周期'}</span><strong>{active ? active.status : '—'}</strong><small>{active ? briefDate(active.started_at) : '尚未开始'}</small></div></div><Section title="意图规划"><p className="small-muted">规划检查通过只表示提案可追溯、结构可检验，业务成果另行验收。</p>{planningTasks.length ? planningTasks.map(task => <Link key={task.id} className="record-row" to={`/p/${projectId}/tasks/${task.id}`} navigate={navigate}><strong>{goals.find(g => g.id === task.goal_id)?.original_intent || task.title}</strong><span>{task.status === 'ACCEPTED' ? '规划提案检查通过' : taskLabels[task.status] || task.status}</span><small>查看提案、执行与独立检查 →</small></Link>) : <Empty>提交一句想法即可开始。</Empty>}</Section><Section title="当前推进" aside={<span className="small-muted">按服务端任务状态</span>}>{tasks.length ? <div className="record-list">{tasks.slice(-8).reverse().map(task => <Link key={task.id} className="task-row" to={`/p/${projectId}/tasks/${task.id}`} navigate={navigate}><span><strong>{task.title}</strong><small>{task.stage} · {short(task.id)}</small></span><Tag value={taskLabels[task.status] || task.status}/></Link>)}</div> : <Empty>尚无任务。</Empty>}</Section><div className="two-column"><Section title="来源覆盖">{active?.source_coverage?.length ? active.source_coverage.map(c => <div className="coverage-row" key={c.source_id}><span>{short(c.source_id)}</span><Tag value={c.status}/><small>{c.gap_reason || `${c.record_count} 条记录`}</small></div>) : <Empty>尚无活动研究周期。</Empty>}</Section><Section title="最近成果">{release ? <Link to={`/p/${projectId}/releases/${release.id}`} navigate={navigate} className="feature-link"><strong>{release.summary}</strong><span>里程碑 {release.sequence} · {briefDate(release.created_at)}</span></Link> : <Empty>还没有已验收成果。执行结果提交后仍需独立验收。</Empty>}</Section></div><Section title="下一步">{itemsOf(more.data.listResourceRequest).filter(r => r.status !== 'RESOLVED').length ? <Link to={`/p/${projectId}/resources`} navigate={navigate}>查看待处理的资源请求 →</Link> : <p>查看当前任务、来源覆盖和待评审结果，按服务端回执推进。</p>}</Section></>
}

function Cycle({ route, api, navigate, refresh, onRefresh }) {
  const { projectId, id } = route
  const data = useQueries(api, projectId, [{ op: 'getResearchCycle', id }, { op: 'listEvidence' }, { op: 'listExperiment' }, { op: 'listDecisionReceipt' }, { op: 'listTask' }], refresh)
  const cycle = data.data.getResearchCycle
  const evidence = itemsOf(data.data.listEvidence), experiments = itemsOf(data.data.listExperiment), tasks = itemsOf(data.data.listTask)
  return <><Header title="研究周期" description={cycle ? `${briefDate(cycle.window_from)} 至 ${briefDate(cycle.window_to)}` : '从线索到结论，来源缺口会保留。'} action={cycle && <Tag value={cycle.status}/>}/><StateNotice state={data} onRetry={onRefresh}/>{cycle && <><Section title="来源覆盖" aside={<span className="small-muted">本轮范围 · 非全面扫描推断</span>}><div className="coverage-grid">{cycle.source_coverage?.map(c => <div className="coverage-card" key={c.source_id}><strong>{short(c.source_id)}</strong><Tag value={c.status}/><p>{c.gap_reason || `${c.record_count} 条持久记录`}</p><small>{briefDate(c.requested_from)} — {briefDate(c.requested_to)}</small></div>)}</div></Section><Section title="候选与核验">{cycle.candidate_evidence_ids?.length ? cycle.candidate_evidence_ids.map(id => { const ev = evidence.find(x => x.id === id); return <Link className="record-row" key={id} to={`/p/${projectId}/evidence?focus=${encodeURIComponent(id)}`} navigate={navigate}><strong>{ev?.canonical_url || short(id)}</strong><span>{ev?.verification_status || '未核验'} · {ev?.source_kind || '来源未知'}</span></Link> }) : <Empty>本轮尚无候选；无候选也可以形成合法结论。</Empty>}</Section><div className="two-column"><Section title="必需实验">{cycle.required_experiment_ids?.length ? cycle.required_experiment_ids.map(id => { const x = experiments.find(item => item.id === id); return <Link key={id} to={`/p/${projectId}/experiments/${id}`} navigate={navigate} className="record-row"><strong>{x?.hypothesis || short(id)}</strong><Tag value={x?.outcome || x?.status || '未加载'}/></Link> }) : <Empty>没有登记必需实验。</Empty>}</Section><Section title="后续任务">{cycle.follow_up_task_ids?.length ? cycle.follow_up_task_ids.map(id => <Link key={id} to={`/p/${projectId}/tasks/${id}`} navigate={navigate} className="record-row">{tasks.find(t => t.id === id)?.title || short(id)}</Link>) : <Empty>暂无后续任务。</Empty>}</Section></div><Section title="本轮结论"><p>{cycle.outcome_summary || '周期仍在进行；尚无关闭结论。'}</p><JsonDetails value={cycle} label="查看周期原始回执"/></Section></>}</>
}

function Task({ route, api, navigate, refresh, onRefresh, mutate }) {
  const { projectId, id } = route
  const data = useQueries(api, projectId, [{ op: 'getTask', id }, { op: 'listArtifact' }, { op: 'listEvents' }], refresh)
  const task = data.data.getTask
  const dependent = useQueries(api, projectId, task ? [
    ...(task.active_run_id ? [{ op: 'getRun', id: task.active_run_id }] : []),
    ...(task.acceptance_id ? [{ op: 'getAcceptanceReceipt', id: task.acceptance_id }] : []),
  ] : [], refresh)
  const [tab, setTab] = useState('summary'), [busy, setBusy] = useState(false)
  const run = dependent.data.getRun, acceptance = dependent.data.getAcceptanceReceipt
  const related = itemsOf(data.data.listArtifact).filter(a => task?.output_artifact_ids?.includes(a.id))
  async function action(op, body) { setBusy(true); try { const result = await mutate(op, { params: { projectId, id: op === 'cancelRun' ? run?.id : task.id }, etag: etagOf(op === 'cancelRun' ? run : task), body }, op === 'cancelRun' ? '取消请求已送达；等待执行器确认' : '任务状态已由服务更新'); if (result) onRefresh() } catch { /* feedback retains service error */ } finally { setBusy(false) } }
  return <><Header title={task?.title || '任务详情'} description={task ? `${task.stage} · ${task.task_type}` : '查看执行、产物和独立验收。'} action={task && <Tag value={taskLabels[task.status] || task.status}/>}/><StateNotice state={data} onRetry={onRefresh}/><StateNotice state={dependent} onRetry={onRefresh}/>{task && <><Section title="当前状态" aside={<div className="button-row">{['BLOCKED', 'DEFERRED_NO_PROGRESS'].includes(task.status) && <button disabled={busy} onClick={() => action('actOnTask', { action: 'RESUME', reason: '用户从工作台恢复任务' })}>恢复</button>}{['READY', 'RUNNING'].includes(task.status) && <button disabled={busy} onClick={() => action('actOnTask', { action: 'PAUSE', reason: '用户从工作台请求暂停' })}>暂停</button>}{run && !run.cancel_confirmed_at && !['CANCELLED', 'FAILED', 'SETTLED'].includes(run.status) && <button disabled={busy} onClick={() => action('cancelRun', { reason: '用户从工作台请求取消' })}>请求取消</button>}</div>}><p>{task.task_type === 'intent_planning' && task.status === 'ACCEPTED' ? '规划提案检查通过；业务目标是否完成须查看业务任务及成果验收。' : task.status === 'EXECUTION_REPORTED' ? '执行结果已经提交，仍需独立验收。' : task.status === 'VERIFYING' ? '检查正在进行，尚未计入已验收。' : task.status === 'ACCEPTED' ? '独立验收已通过。' : '以服务端状态为准，操作完成后等待回执。'}</p><div className="meta-line"><span>修订 {task.revision}</span><span>输入引用 {task.input_refs?.length || 0}</span>{run && <Tag value={runLabels[run.status] || run.status}/>}</div>{run?.status === 'CANCEL_REQUESTED' && <p className="warning">取消已请求，执行器尚未确认。</p>}</Section><div className="tabs" role="tablist" aria-label="任务详情标签" onKeyDown={event => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return
    const buttons = [...event.currentTarget.querySelectorAll('[role="tab"]')]
    const index = buttons.indexOf(document.activeElement)
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length
    event.preventDefault(); buttons[next].focus(); buttons[next].click()
  }}>{[['summary','摘要'],['process','过程'],['artifacts','产物'],['checks','检查']].map(([key,label]) => <button key={key} role="tab" tabIndex={tab === key ? 0 : -1} aria-selected={tab === key} className={tab === key ? 'selected' : ''} onClick={() => setTab(key)}>{label}</button>)}</div><div role="tabpanel" aria-label="任务详情内容" className="panel task-panel">{tab === 'summary' && <><p>{run?.execution_report || '尚无执行摘要。'}</p><JsonDetails value={task.input_refs} label="查看冻结输入引用"/></>}{tab === 'process' && <>{run ? <div className="key-grid"><span>运行器</span><strong>{short(run.runtime_id)}</strong><span>执行者</span><strong>{short(run.executor_principal_id)}</strong><span>开始</span><strong>{briefDate(run.started_at)}</strong><span>结束</span><strong>{briefDate(run.ended_at)}</strong></div> : <Empty>尚无活动运行。</Empty>}<EventList events={itemsOf(data.data.listEvents).filter(e => e.aggregate_ref?.id === task.id || e.aggregate_ref?.id === run?.id)}/></>}{tab === 'artifacts' && (related.length ? related.map(a => <ArtifactPreview key={a.id} artifact={a} api={api} projectId={projectId}/>) : <Empty>暂无任务产物。</Empty>)}{tab === 'checks' && (acceptance ? <><Tag value={acceptance.verdict}/><Table headers={['检查','结果','实际命令']} rows={(acceptance.checks || []).map(c => [c.check_id, c.status, c.command_key || '未登记'])}/><JsonDetails value={acceptance} label="查看独立验收回执"/></> : <Empty>尚无独立验收回执。</Empty>)}</div></>}</>
}

function EventList({ events }) { return events.length ? <ol className="event-list">{events.slice(-25).reverse().map(ev => <li key={ev.id}><time>{briefDate(ev.created_at)}</time><strong>{ev.event_type}</strong><details><summary>技术详情</summary><pre>{JSON.stringify(ev, null, 2)}</pre></details></li>)}</ol> : <Empty>当前没有关联事件。</Empty> }

function Release({ route, api, navigate, refresh, onRefresh, shared }) {
  const { projectId, id } = route
  const data = useQueries(api, projectId, [{ op: 'getMilestoneRelease', id }], refresh)
  const release = data.data.getMilestoneRelease
  const linked = useQueries(api, projectId, release ? [
    ...(release.acceptance_ids || []).map((item, index) => ({ op: 'getAcceptanceReceipt', id: item, as: `acceptance-${index}` })),
    ...(release.decision_ids || []).map((item, index) => ({ op: 'getDecisionReceipt', id: item, as: `decision-${index}` })),
    ...(release.artifact_refs || []).map((item, index) => ({ op: 'getArtifact', id: item.id, as: `artifact-${index}` })),
  ] : [], refresh)
  const releases = itemsOf(shared.data.listMilestoneRelease)
  return <><Header title="成果审查" description={release ? `里程碑 ${release.sequence} · ${briefDate(release.created_at)}` : '查看经过独立验收的成果与版本。'} action={<select aria-label="选择成果版本" value={id} onChange={e => navigate(`/p/${projectId}/releases/${e.target.value}`)}><option value={id}>当前成果 {short(id)}</option>{releases.filter(item => item.id !== id).map(item => <option key={item.id} value={item.id}>{item.sequence} · {item.summary}</option>)}</select>}/><StateNotice state={data} onRetry={onRefresh}/><StateNotice state={linked} onRetry={onRefresh}/>{release && <><Section title={release.summary} className="feature-panel"><div className="meta-line"><span>成果序号 {release.sequence}</span><span>产品版本 {release.software_version || '未发布软件版本'}</span><span>修订 {release.revision}</span></div><p>成果序号与产品语义版本分开记录；以下内容固定于本次回执。</p></Section><div className="two-column"><Section title="实际变化">{release.changes?.length ? <ul>{release.changes.map((x,i) => <li key={i}>{x}</li>)}</ul> : <Empty/>}</Section><Section title="仍需关注">{release.open_issues?.length ? <ul>{release.open_issues.map((x,i) => <li key={i}>{x}</li>)}</ul> : <Empty>无已记录的开放问题。</Empty>}</Section></div><Section title="独立验收">{release.acceptance_ids?.map((aid, index) => { const receipt = linked.data[`acceptance-${index}`]; return <div className="receipt-row" key={aid}><Tag value={receipt?.verdict || '读取中'}/><strong>{short(aid)}</strong><span>{receipt?.reason || '回执暂不可用'}</span>{receipt && <JsonDetails value={receipt} label="查看实际检查与命令"/>}</div> })}</Section><Section title="采用决定">{release.decision_ids?.length ? release.decision_ids.map((did,index) => <div key={did} className="receipt-row"><Tag value={linked.data[`decision-${index}`]?.decision || '读取中'}/><span>{linked.data[`decision-${index}`]?.reason || short(did)}</span></div>) : <Empty>没有关联采用决定。</Empty>}</Section><Section title="封存产物">{release.artifact_refs?.length ? release.artifact_refs.map((ref,index) => { const artifact = linked.data[`artifact-${index}`]; return artifact ? <ArtifactPreview key={ref.id} artifact={artifact} expectedRef={ref} api={api} projectId={projectId}/> : <p key={ref.id}>产物 {short(ref.id)} 暂不可访问</p> }) : <Empty>没有关联产物。</Empty>}</Section><Section title="下一步">{release.next_steps?.length ? <ul>{release.next_steps.map((x,i) => <li key={i}>{x}</li>)}</ul> : <Empty/>}</Section></>}</>
}

function Evidence({ route, api, projectId, navigate, refresh, onRefresh, shared }) {
  const data = useQueries(api, projectId, [{ op: 'listEvidence' }], refresh)
  const [query, setQuery] = useState(''), [source, setSource] = useState('ALL'), [validity, setValidity] = useState('ALL'), [search, setSearch] = useState(null)
  const [fromDate, setFromDate] = useState(''), [toDate, setToDate] = useState(''), [independence, setIndependence] = useState('ALL')
  const selected = new URLSearchParams(route.search).get('focus')
  function selectEvidence(id) {
    const query = new URLSearchParams(route.search)
    query.set('focus', id)
    navigate(`/p/${encodeURIComponent(projectId)}/evidence?${query}`)
  }
  const items = itemsOf(data.data.listEvidence)
  const filtered = items.filter(item => (source === 'ALL' || item.source_kind === source) && (validity === 'ALL' || item.validity === validity) && (independence === 'ALL' || item.independence_key === independence) && (!fromDate || item.retrieved_at.slice(0,10) >= fromDate) && (!toDate || item.retrieved_at.slice(0,10) <= toDate) && (!query || `${item.canonical_url || ''} ${item.claim}`.toLowerCase().includes(query.toLowerCase())))
  const snapshotIds = [...new Set(filtered.map(item => item.snapshot_artifact_ref?.id).filter(Boolean))]
  const detail = useQueries(api, projectId, selected ? [{ op: 'getEvidence', id: selected }] : [], refresh)
  async function searchServer(e) {
    e.preventDefault()
    try { const state = await api.call('getProjectState', { params: { projectId } }); const result = await api.call('searchEvidence', { params: { projectId }, body: { query, snapshot_ids: snapshotIds, limit: 20, expected_state_revision: state.revision } }); setSearch({ data: result }) }
    catch (error) { setSearch({ error }) }
  }
  const evidence = detail.data.getEvidence
  return <><Header title="来源证据" description="保留原文定位、抓取时间与独立来源关系。"/><StateNotice state={data} onRetry={onRefresh}/><Section title="筛选与检索"><form className="filter-row" onSubmit={searchServer}><label>检索词<input value={query} onChange={e => setQuery(e.target.value)} placeholder="URL或证据主张"/></label><label>来源<select value={source} onChange={e => setSource(e.target.value)}><option value="ALL">全部</option>{[...new Set(items.map(item => item.source_kind))].sort().map(x => <option key={x}>{x}</option>)}</select></label><label>有效性<select value={validity} onChange={e => setValidity(e.target.value)}><option value="ALL">全部</option>{['CURRENT','STALE','REVOKED'].map(x => <option key={x}>{x}</option>)}</select></label><label>抓取起日（UTC）<input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)}/></label><label>抓取止日（UTC）<input type="date" value={toDate} onChange={e => setToDate(e.target.value)}/></label><label>独立来源<select value={independence} onChange={e => setIndependence(e.target.value)}><option value="ALL">全部</option>{[...new Set(items.map(item => item.independence_key))].map(key => <option key={key} value={key}>{key.slice(-12)}</option>)}</select></label><button type="submit" disabled={!query.trim() || !snapshotIds.length}>服务端检索</button></form>{search?.error && <p className="form-error">检索失败：{search.error.message}</p>}{search?.data && <><p className="small-muted">服务端返回 {search.data.hits.length} 条检索结果；范围为本页筛选后的封存快照。</p>{search.data.warnings.map((warning,index) => <p key={index} className="warning">{warning}</p>)}<div className="record-list">{search.data.hits.map((hit,index) => <div className="record-row" key={index}><strong>{hit.locator}</strong><p>{hit.excerpt}</p><Tag value={hit.validity}/>{hit.evidence_id && <button onClick={() => selectEvidence(hit.evidence_id)}>定位证据</button>}</div>)}</div></>}</Section><div className="split-content"><Section title="证据列表" className="list-panel">{filtered.length ? <div className="record-list">{filtered.map(item => <button className={`record-row ${selected === item.id ? 'selected' : ''}`} key={item.id} onClick={() => selectEvidence(item.id)}><strong>{item.canonical_url || short(item.id)}</strong><span>{item.source_kind} · {briefDate(item.retrieved_at)}</span><Tag value={item.validity}/></button>)}</div> : <Empty>本页没有符合筛选条件的证据；来源受限应查看周期覆盖。</Empty>}</Section><Section title="原文与来源链">{selected ? <><StateNotice state={detail}/>{evidence && <><div className="meta-line"><Tag value={evidence.evidence_kind}/><Tag value={evidence.verification_status}/><Tag value={evidence.validity}/></div><p>{evidence.claim}</p><div className="key-grid"><span>原文 URL</span><strong className="break-all">{evidence.canonical_url || '未记录'}</strong><span>上游版本</span><strong>{evidence.upstream_revision || '未记录'}</strong><span>抓取时间</span><strong>{briefDate(evidence.retrieved_at)}</strong><span>源头</span><strong>{evidence.origin_evidence_id || '未建立独立源关系'}</strong></div>{evidence.snapshot_artifact_ref && <ArtifactFromRef api={api} projectId={projectId} ref={evidence.snapshot_artifact_ref} refresh={refresh}/>}<JsonDetails value={evidence} label="查看完整来源字段"/></>}</> : <Empty>选择一条证据查看原文和哈希。</Empty>}</Section></div></>
}

function ArtifactFromRef({ api, projectId, ref, refresh }) {
  const data = useQueries(api, projectId, [{ op: 'getArtifact', id: ref.id }], refresh)
  return <><StateNotice state={data}/>{data.data.getArtifact && <ArtifactPreview api={api} projectId={projectId} artifact={data.data.getArtifact} expectedRef={ref}/>}</>
}

function Experiment({ route, api, projectId, refresh, onRefresh }) {
  const data = useQueries(api, projectId, [{ op: 'getExperiment', id: route.id }, { op: 'listArtifact' }, { op: 'listQualification' }], refresh)
  const experiment = data.data.getExperiment
  const resultRefs = (experiment?.results || []).flatMap(result => result.evidence_refs || []).filter(ref => ref.entity_type === 'Artifact')
  const linked = itemsOf(data.data.listArtifact).filter(a => experiment?.run_ids?.includes(a.run_id) || resultRefs.some(ref => ref.id === a.id && ref.revision === a.revision && (!ref.content_hash || ref.content_hash === a.content_hash)))
  return <><Header title="实验与评测" description="在冻结条件下比较基线与候选；错误与弃权单独呈现。" action={experiment && <Tag value={experiment.outcome || experiment.status}/>}/><StateNotice state={data} onRetry={onRefresh}/>{experiment && <><Section title={experiment.hypothesis}><div className="key-grid"><span>预注册哈希</span><strong className="break-all mono">{experiment.preregistration_hash}</strong><span>测量模式</span><strong>{experiment.measurement_mode}</strong><span>冻结范围</span><strong>{experiment.scope}</strong><span>验收回执</span><strong>{experiment.acceptance_id || '尚无'}</strong></div></Section><Section title="基线与候选"><Table headers={['指标','基线','候选','结果']} rows={(experiment.results || []).map(r => [r.metric_id, r.baseline ?? '—', r.candidate ?? '—', <Tag value={r.status}/>])}/>{!experiment.results?.length && <Empty>尚无可核对的结果。</Empty>}{['NO_IMPROVEMENT','INCONCLUSIVE'].includes(experiment.outcome) && <p className="callout">无改善或证据不足是合法结果。稳定版本不会因此自动替换。</p>}</Section><div className="two-column"><Section title="评测资格">{itemsOf(data.data.listQualification).length ? itemsOf(data.data.listQualification).map(q => <p key={q.id}><Tag value={q.status}/> {q.scope?.provider} · {q.scope?.model_revision} · {q.measurement_mode}</p>) : <Empty>资格记录尚不可用；开发夹具不能替代正式资格。</Empty>}</Section><Section title="费用与完整性"><p>费用与完整性以关联评测报告为准；未提供报告时记为未知。</p><p>逐题正式留出内容不在工作台展示。</p></Section></div><Section title="关联产物">{linked.length ? linked.map(a => <ArtifactPreview key={a.id} api={api} projectId={projectId} artifact={a}/>) : <Empty>尚无可访问的报告产物。</Empty>}</Section></>}</>
}

function Knowledge({ api, projectId, navigate, refresh, onRefresh }) {
  const data = useQueries(api, projectId, [{ op: 'listSkillVersion' }], refresh)
  const [selected, setSelected] = useState(null)
  const detail = useQueries(api, projectId, selected ? [{ op: 'getSkillVersion', id: selected }] : [], refresh)
  const skill = detail.data.getSkillVersion
  return <><Header title="知识与技能" description="候选与稳定版本分开，资格和撤回条件可检查。"/><StateNotice state={data} onRetry={onRefresh}/><Section title="技能版本">{itemsOf(data.data.listSkillVersion).length ? itemsOf(data.data.listSkillVersion).map(item => <button className="record-row" key={item.id} onClick={() => setSelected(item.id)}><strong>{item.skill_name || short(item.id)} · {item.version}</strong><Tag value={item.status}/><span>{item.scope} · 修订 {item.revision}</span></button>) : <Empty>尚无技能版本；未实现的服务会显示明确错误。</Empty>}</Section>{selected && <Section title="版本详情"><StateNotice state={detail}/>{skill && <><div className="key-grid"><span>来源覆盖</span><strong>{skill.processed_source_ids.length} / {skill.expected_source_ids.length} 已处理</strong><span>失败来源</span><strong>{skill.failed_source_ids.length}</strong><span>待处理冲突</span><strong>{skill.conflict_ids.length}</strong><span>独立验收</span><strong>{skill.acceptance_id || '尚无回执'}</strong><span>回滚版本</span><strong>{skill.rollback_skill_id || '未登记'}</strong><span>许可</span><strong>{skill.license_expression || '未知'}</strong></div>{skill.experiment_id && <Link to={`/p/${projectId}/experiments/${skill.experiment_id}`} navigate={navigate}>查看关联实验</Link>}<ArtifactFromRef api={api} projectId={projectId} ref={skill.content_artifact_ref} refresh={refresh}/><JsonDetails value={skill}/></>}<p>晋升需独立验收回执与回滚版本；当前不提供绕过验收的快捷按钮。</p></Section>}</>
}

function Team({ api, projectId, refresh, onRefresh }) {
  const data = useQueries(api, projectId, [{ op: 'listRuntimeRegistration' }, { op: 'listRun' }, { op: 'listAgentMessage' }], refresh)
  const [selected, setSelected] = useState(null)
  const detail = useQueries(api, projectId, selected ? [{ op: 'getRuntimeRegistration', id: selected }] : [], refresh)
  return <><Header title="团队与运行器" description="区分已登记、探针、真实运行和独立资格。"/><StateNotice state={data} onRetry={onRefresh}/><Section title="运行器">{itemsOf(data.data.listRuntimeRegistration).length ? <Table headers={['名称','状态','健康检查','详情']} rows={itemsOf(data.data.listRuntimeRegistration).map(rt => [rt.name, <Tag value={rt.status}/>, briefDate(rt.health_checked_at), <button onClick={() => setSelected(rt.id)}>查看</button>])}/> : <Empty>尚未登记运行器；角色名称不代表在线员工。</Empty>}{selected && <><StateNotice state={detail}/>{detail.data.getRuntimeRegistration && <JsonDetails value={detail.data.getRuntimeRegistration} label="运行器资格与能力"/>}</>}</Section><div className="two-column"><Section title="当前执行">{itemsOf(data.data.listRun).length ? itemsOf(data.data.listRun).slice(-12).reverse().map(run => <div className="record-row" key={run.id}><strong>{short(run.task_id)}</strong><span>{short(run.executor_principal_id)}</span><Tag value={runLabels[run.status] || run.status}/></div>) : <Empty>没有运行中的任务。</Empty>}</Section><Section title="Agent 消息">{itemsOf(data.data.listAgentMessage).length ? itemsOf(data.data.listAgentMessage).slice(-10).reverse().map(m => <div className="record-row" key={m.id}><strong>{m.message_type}</strong><p>{m.body}</p><span>{briefDate(m.created_at)}</span></div>) : <Empty>没有消息记录。</Empty>}</Section></div></>
}

function Resources({ api, projectId, refresh, onRefresh, mutate }) {
  const data = useQueries(api, projectId, [{ op: 'getBudgetPolicy' }, { op: 'listBudgetLedgerEntry' }, { op: 'listResourceRequest' }], refresh)
  const policy = data.data.getBudgetPolicy, requests = itemsOf(data.data.listResourceRequest)
  const ledger = itemsOf(data.data.listBudgetLedgerEntry)
  const latestCosts = [...new Map(ledger.map(entry => [`${entry.run_id}:${entry.provider_request_id}`, entry])).values()]
  const [amount, setAmount] = useState(''), [currency, setCurrency] = useState('USD'), [mode, setMode] = useState('UNLIMITED_AMOUNT'), [enforcement, setEnforcement] = useState('STRICT'), [error, setError] = useState(''), [busy, setBusy] = useState(false)
  useEffect(() => { if (policy) { setMode(policy.mode); setEnforcement(policy.enforcement === 'ESTIMATED' ? 'ESTIMATED' : 'STRICT'); setAmount(policy.cap?.amount ?? ''); setCurrency(policy.cap?.currency ?? 'USD') } }, [policy?.id, policy?.revision])
  async function save(e) { e.preventDefault(); if (!policy) return; setBusy(true); setError(''); try { const body = { mode, cap: mode === 'CAPPED' ? { amount, currency } : null, enforcement: mode === 'CAPPED' ? enforcement : 'ACCOUNTING_ONLY', period: policy.period, timezone: policy.timezone, effective_from: policy.effective_from, unknown_cost_action: mode === 'CAPPED' && enforcement === 'STRICT' ? 'BLOCK' : 'ALLOW_AND_RECORD' }; await mutate('updateBudgetPolicy', { params: { projectId }, etag: etagOf(policy), body }, '金额策略已由服务保存'); onRefresh() } catch (cause) { setError(cause.message) } finally { setBusy(false) } }
  return <><Header title="费用与资源" description="已知、在途和未知费用分开看；未设上限不等于无限余额。"/><StateNotice state={data} onRetry={onRefresh}/><div className="summary-strip"><div><span>金额策略</span><strong>{policy?.mode === 'CAPPED' ? `${policy.cap?.amount} ${policy.cap?.currency}` : '未设上限'}</strong></div><div><span>账目记录</span><strong>{itemsOf(data.data.listBudgetLedgerEntry).length}</strong></div><div><span>待处理请求</span><strong>{requests.filter(x => x.status !== 'RESOLVED').length}</strong></div></div><Section title="修改项目上限">{policy ? <form className="form-grid" onSubmit={save}><label>策略<select value={mode} onChange={e => setMode(e.target.value)}><option value="UNLIMITED_AMOUNT">不设金额上限</option><option value="CAPPED">设定上限</option></select></label>{mode === 'CAPPED' && <><label>金额<input inputMode="decimal" value={amount} onChange={e => setAmount(e.target.value)} required/></label><label>币种<input value={currency} onChange={e => setCurrency(e.target.value.toUpperCase())} required/></label><label>执行方式<select value={enforcement} onChange={e => setEnforcement(e.target.value)}><option value="STRICT">严格上限</option><option value="ESTIMATED">按估算执行</option></select></label><p className="small-muted full-row">{enforcement === 'STRICT' ? '费用未知时阻止新执行；已有回执仍保留。' : '允许未知费用并记录；估算不能保证最终账单不超额。'}</p></>}{error && <p className="form-error full-row" role="alert">{error}。你的输入已保留。</p>}<button disabled={busy} type="submit">{busy ? '正在保存…' : '保存上限'}</button></form> : <Empty>金额策略尚未加载。</Empty>}</Section><Section title="账目"><p className="small-muted">本页账目：已结算 {latestCosts.filter(entry => ['COMMIT','RECONCILE'].includes(entry.operation)).length} 笔 · 在途预留 {latestCosts.filter(entry => entry.operation === 'RESERVE').length} 笔 · 未知 {latestCosts.filter(entry => entry.operation === 'UNKNOWN').length} 笔。金额与费用依据逐笔列出。</p><Table headers={['时间','操作','金额','费用依据']} rows={itemsOf(data.data.listBudgetLedgerEntry).map(entry => [briefDate(entry.occurred_at), entry.operation, entry.money?.amount != null ? `${entry.money.amount} ${entry.money.currency}` : '未知', entry.cost_basis])}/>{!itemsOf(data.data.listBudgetLedgerEntry).length && <Empty>尚无账目；未知费用不记为 0。</Empty>}</Section><Section title="资源请求">{requests.length ? requests.map(request => <div className="request-row" key={request.id}><div><h3>{request.summary}</h3><p>{request.requested_capability}</p><small style={{ overflowWrap: 'anywhere' }}>原因 {request.reason_code} · 状态 {request.status}</small><p>受阻任务 {request.blocked_task_ids.length} · 可继续任务 {request.continuable_task_ids.length} · 已保留产物 {request.completed_artifact_refs.length}</p><p>预计费用：{request.cost_known && request.estimated_cost ? `${request.estimated_cost.amount} ${request.estimated_cost.currency}` : '未知或待结算'}</p><p>恢复检查点：{request.resume_checkpoint_ref ? short(request.resume_checkpoint_ref.id) : '尚未登记'}</p></div><div><ResourceRecovery api={api} projectId={projectId} request={request} onRefresh={onRefresh}/><ResourceResolve api={api} projectId={projectId} request={request} onRefresh={onRefresh}/></div></div>) : <Empty>当前没有资源请求。</Empty>}</Section></>
}

function ResourceResolve({ api, projectId, request, onRefresh }) {
  const [open, setOpen] = useState(false), [reason, setReason] = useState(''), [kind, setKind] = useState('Artifact'), [referenceId, setReferenceId] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false)
  if (request.status === 'RESOLVED') return <Tag value="已解决"/>
  async function submit(e) { e.preventDefault(); setBusy(true); setError(''); try { const record = await api.call(kind === 'Artifact' ? 'getArtifact' : 'getEvidence', { params: { projectId, id: referenceId.trim() } }); await api.call('resolveResourceRequest', { params: { projectId, id: request.id }, etag: etagOf(request), body: { resolution_evidence_refs: [refFor(record, kind)], reason } }); setOpen(false); onRefresh() } catch (cause) { setError(cause.message) } finally { setBusy(false) } }
  return <div><button onClick={() => setOpen(v => !v)}>{open ? '取消' : '登记解决'}</button>{open && <form className="inline-form" onSubmit={submit}><label>解决依据<input value={reason} onChange={e => setReason(e.target.value)} required/></label><label>依据类型<select value={kind} onChange={e => setKind(e.target.value)}><option value="Artifact">封存产物</option><option value="Evidence">来源证据</option></select></label><label>依据 ID<input value={referenceId} onChange={e => setReferenceId(e.target.value)} required/></label><p className="small-muted">提交前会先读取并固定该依据的修订；服务最终核查是否足以解决请求。</p>{error && <p className="form-error">{error}</p>}<button disabled={busy}>提交服务核查</button></form>}</div>
}

function Settings({ api, projectId, refresh, onRefresh, mutate, shared }) {
  const data = useQueries(api, projectId, [{ op: 'getRunPolicy' }, { op: 'getProjectProfile' }, { op: 'listDevices' }], refresh)
  const policy = data.data.getRunPolicy, profile = data.data.getProjectProfile
  const [form, setForm] = useState({}), [error, setError] = useState(''), [busy, setBusy] = useState(false)
  useEffect(() => { if (policy) setForm({ max_concurrency: policy.max_concurrency, monitor_period_seconds: policy.monitor_period_seconds, timezone: policy.timezone }) }, [policy?.id, policy?.revision])
  async function save(e) { e.preventDefault(); setBusy(true); setError(''); try { const body = Object.fromEntries(['max_concurrency','max_queue','monitor_period_seconds','first_lookback_seconds','max_active_cycles_per_project','coalesce_missed_triggers','same_failure_retry_limit','no_progress_iteration_limit','heartbeat_seconds','lease_seconds','log_retention_days','timezone'].map(k => [k, form[k] ?? policy[k]])); for (const k of ['max_concurrency','monitor_period_seconds']) body[k] = Number(body[k]); await mutate('updateRunPolicy', { params: { projectId }, etag: etagOf(policy), body }, '运行策略已保存'); onRefresh() } catch (cause) { setError(cause.message) } finally { setBusy(false) } }

  return <><Header title="设置与设备" description="管理运行策略、来源声明与可撤销设备。"/><StateNotice state={data} onRetry={onRefresh}/><Section title="研究与运行策略">{policy ? <form className="form-grid" onSubmit={save}><label>并发上限<input type="number" min="1" value={form.max_concurrency ?? ''} onChange={e => setForm({ ...form, max_concurrency: e.target.value })}/></label><label>研究周期（秒）<input type="number" min="60" value={form.monitor_period_seconds ?? ''} onChange={e => setForm({ ...form, monitor_period_seconds: e.target.value })}/></label><label>时区<input value={form.timezone ?? ''} onChange={e => setForm({ ...form, timezone: e.target.value })}/></label>{error && <p className="form-error full-row">{error}</p>}<button disabled={busy}>保存运行策略</button></form> : <Empty>运行策略尚不可用。</Empty>}</Section><Section title="项目背景候选"><ProfileDraft api={api} projectId={projectId} profile={profile}/></Section><Section title="来源配置">{profile?.source_configs?.length ? <Table headers={['类型','范围','启用','必需']} rows={profile.source_configs.map(c => [c.kind, c.query, c.enabled ? '是' : '否', c.required ? '是' : '否'])}/> : <Empty>尚无来源配置。</Empty>}<p className="small-muted">凭据不返回前端；配置凭据需使用受保护的服务入口，当前无公开设置操作。</p></Section><Section title="设备"><DevicePanel api={api} projectId={projectId} devices={data.data.listDevices} onRefresh={onRefresh}/></Section></>
}

function Selection({ route, api, projectId, navigate, refresh, onRefresh }) {
  const map = { cycle: ['listResearchCycle','研究周期','cycles'], task: ['listTask','任务','tasks'], release: ['listMilestoneRelease','成果','releases'], experiment: ['listExperiment','实验','experiments'] }
  const [op,title,path] = map[route.section]
  const data = useQueries(api, projectId, [{ op }], refresh)
  return <><Header title={`选择${title}`} description="从已保存的记录进入详情；地址可直接打开。"/><StateNotice state={data} onRetry={onRefresh}/><Section title={title}>{itemsOf(data.data[op]).length ? itemsOf(data.data[op]).map(item => <Link key={item.id} className="record-row" to={`/p/${projectId}/${path}/${item.id}`} navigate={navigate}><strong>{item.title || item.summary || item.hypothesis || `${title} ${short(item.id)}`}</strong><Tag value={item.status || item.outcome || '已记录'}/><small>{briefDate(item.created_at)}</small></Link>) : <Empty>目前没有可打开的记录。</Empty>}</Section></>
}

export function Screen(props) {
  const { route, api, navigate, shared, refresh, onRefresh, mutate, token } = props
  const common = { route, api, navigate, shared, refresh, onRefresh, mutate, projectId: route.projectId }
  switch (route.kind) {
    case 'projects': return <Projects {...common}/>
    case 'workbench': return <Workbench {...common}/>
    case 'continuity': return <Continuity token={token} projectId={route.projectId} shared={shared}/>
    case 'cycle': return <Cycle {...common}/>
    case 'task': return <Task {...common}/>
    case 'release': return <Release {...common}/>
    case 'evidence': return <Evidence {...common}/>
    case 'experiment': return <Experiment {...common}/>
    case 'knowledge': return <Knowledge {...common}/>
    case 'team': return <Team {...common}/>
    case 'resources': return <Resources {...common}/>
    case 'settings': return <Settings {...common}/>
    case 'selection': return <Selection {...common}/>
    default: return <><Header title="页面不存在" description="检查地址，或返回项目入口。"/><Link to="/" navigate={navigate}>返回项目入口</Link></>
  }
}

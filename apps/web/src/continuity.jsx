import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createV2Client, METHODS } from './v2client'

const short = raw => raw ? String(raw).slice(0, 12) : '—'
const when = raw => raw ? new Date(raw).toLocaleString() : '未记录'
const list = value => Array.isArray(value) ? value : Array.isArray(value?.items) ? value.items : []
function Header({ title, description, action }) { return <header className="page-heading"><div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header> }
function Section({ title, aside, children, className = '' }) { return <section className={`panel ${className}`}><div className="section-heading"><h2>{title}</h2>{aside}</div>{children}</section> }
function Empty({ children }) { return <p className="empty-state">{children || '当前没有记录。'}</p> }
function Tag({ value }) { return <span className="tag">{value ?? '未知'}</span> }
function JsonDetails({ value, label = '查看原始回执' }) { return <details className="raw-details"><summary>{label}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details> }

// Every control that sends a protocol command is a Producer tagged with the method it produces. The tag is the
// machine-readable half of the card's "所有按钮有生产者": a browser run can ask for one control per frozen method
// and watch that command actually leave the page, which a restyled button cannot fake.
function Producer({ method, children, ...rest }) { return <button type="button" data-producer={method} {...rest}>{children}</button> }

const EVENT_LABELS = {
  MESSAGE: '消息', TOOL_STARTED: '工具开始', TOOL_RESULT: '工具结果', JUDGE_DECISION: '裁判判定', RUN_STATE: '运行状态',
  GOAL_STATE: '目标状态', ARTIFACT: '产物', USAGE: '用量', CHECKPOINT: '检查点', CLIENT_HANDOFF: '客户端接续',
  BOOTSTRAP_STATE: '引导状态', PERMISSION_REQUIRED: '等待授权', PERMISSION_RESOLVED: '授权已处理', ERROR: '错误',
}
const DELIVERY_LABELS = { NORMAL: '正常排队', STEER: '插队引导', FOLLOW_UP: '追加后续' }

function statusLine(status) {
  if (status.kind === 'COMPLETED' || status.kind === 'ACKNOWLEDGED') return null
  if (status.kind === 'IN_PROGRESS') return '主机回答 IN_PROGRESS：命令已受理，仍在执行'
  if (status.kind === 'LOCAL_REFUSED') return `本机已拒发：${status.reason}（命令未离开浏览器）`
  if (status.kind === 'TRANSPORT_UNAVAILABLE') return `主机未应答：${status.detail}`
  if (status.kind === 'MALFORMED_REPLY' || status.kind === 'UNKNOWN_STATUS') return `回执无法解析：${status.detail || status.status}`
  if (status.kind === 'REJECTED') return `主机拒绝：${status.error_code || '未给出原因'}`
  if (status.kind === 'NOT_IMPLEMENTED') return '主机回答 NOT_IMPLEMENTED：该能力尚未由本机服务提供'
  return `未预期状态：${status.kind}`
}

export function Continuity({ token, projectId, shared }) {
  const [notices, setNotices] = useState([])
  const [snapshot, setSnapshot] = useState(null)
  const [events, setEvents] = useState([])
  const [watermark, setWatermark] = useState(0)
  const [sessions, setSessions] = useState([])
  const [bindings, setBindings] = useState([])
  const [tree, setTree] = useState([])
  const [diff, setDiff] = useState(null)
  const [diffBase, setDiffBase] = useState('INDEX')
  const [base, setBase] = useState(null)
  const [draft, setDraft] = useState('')
  const [dirty, setDirty] = useState(false)
  const [models, setModels] = useState(null)
  const [probe, setProbe] = useState(null)
  const [report, setReport] = useState(null)
  const [busy, setBusy] = useState(null)
  const [chat, setChat] = useState('')
  const [form, setForm] = useState({ workspacePath: '', displayName: '', modelRef: '', objective: '', targetClient: '', handoffMode: 'WHEN_SETTLED', delivery: 'NORMAL', attachment: '' })
  const draftKey = `researchos:v2draft:${projectId}`
  const seen = useRef(new Set())
  const workspaceRef = bindings[0]?.authorized_workspace_ref || ''

  const client = useMemo(() => createV2Client({
    identity: { clientId: 'desktop-renderer', credential: token },
    state: { projectId },
    fetcher: async env => {
      const response = await fetch(env.path, { method: env.verb, headers: env.headers, body: JSON.stringify(env.payload), cache: 'no-store' })
      let body = null
      try { body = await response.json() } catch { body = null }
      return { status: response.status, body: body == null ? '' : body }
    },
    onStatus: (status, method) => {
      const line = statusLine(status)
      if (line) setNotices(old => [{ method, line, at: new Date().toISOString() }, ...old].slice(0, 20))
      // A refused or unresolved reply never re-baselines the screen: the revision and content hash the next write
      // will carry stay the ones the host last reported, so a conflict cannot be papered over here.
      if (!line && status.revision !== null && status.revision !== undefined) client.adopt({ expectedRevision: status.revision })
    },
  }), [token, projectId])

  function applySnapshot(next) {
    if (!next) return
    client.adopt({ projectId: next.project_id, sessionId: next.session_id, expectedRevision: next.revision, writerEpoch: next.writer?.epoch })
    setSnapshot(next)
    setWatermark(Number(next.event_sequence) || 0)
    const fromTranscript = list(next.messages).map((message, index) => ({
      event_id: message.message_id, kind: 'MESSAGE', sequence: -(index + 1), payload: message,
    }))
    setEvents(fromTranscript)
    seen.current = new Set(fromTranscript.map(e => e.event_id))
  }

  function appendEvents(page) {
    const fresh = (page.events || []).filter(event => event?.event_id && !seen.current.has(event.event_id))
    fresh.forEach(event => seen.current.add(event.event_id))
    if (fresh.length) setEvents(old => [...old, ...fresh].slice(-200))
    const high = Number(page.high_watermark ?? page.next_sequence) || 0
    if (high > 0) setWatermark(old => Math.max(old, high))
  }

  async function run(method, payload, overrides = {}) {
    setBusy(method)
    try {
      const result = await client.send(method, payload, overrides)
      const settled = result.kind === 'COMPLETED' || result.kind === 'ACKNOWLEDGED'
      if (settled && result.result) {
        const value = result.result
        // Three methods answer with the snapshot itself rather than wrapping it, so both shapes have to be adopted:
        // a screen that only read the wrapped form would sit at "未接入" forever after session.get.
        const bare = value.session_id && value.revision !== undefined && value.event_sequence !== undefined
        if (value.snapshot || bare) applySnapshot(value.snapshot || value)
        else if (method === 'session.list') setSessions(list(value))
        else if (method === 'workspace.list') setBindings(list(value))
        else if (value.entries) setTree(value.entries)
        else if (value.events) appendEvents(value)
        else if (value.content_hash !== undefined) setBase(value)
        else if (value.files) setDiff(value)
        else if (value.artifact_ref) setForm(old => ({ ...old, attachment: value.artifact_ref.id || old.attachment }))
        if (value.session_id && !value.snapshot) client.adopt({ sessionId: value.session_id })
      }
      setReport({ method, kind: result.kind, error_code: result.error_code || null, result: result.result || null })
      return result
    } finally { setBusy(null) }
  }

  // Recovery is a cursor read, never a resend: reconnect, tab-return and remount all ask session.events from the
  // watermark the host already reported, so no send, control or write is replayed on the way back.
  function resync() { return run('session.events', { after_sequence: watermark, limit: 200 }) }
  useEffect(() => {
    const visible = () => { if (snapshot && document.visibilityState === 'visible' && navigator.onLine) resync() }
    const online = () => { if (snapshot) resync() }
    addEventListener('online', online)
    document.addEventListener('visibilitychange', visible)
    return () => { removeEventListener('online', online); document.removeEventListener('visibilitychange', visible) }
  }, [snapshot, watermark])

  useEffect(() => {
    let saved = null
    try { saved = JSON.parse(localStorage.getItem(draftKey) || 'null') } catch { localStorage.removeItem(draftKey) }
    if (saved && typeof saved.text === 'string') { setBase(saved.read || null); setDraft(saved.text); setDirty(true) }
  }, [draftKey])

  function keepDraft(read, text) {
    localStorage.setItem(draftKey, JSON.stringify({ text, read }))
  }
  useEffect(() => {
    if (!dirty) return
    const warn = event => { event.preventDefault(); event.returnValue = '' }
    addEventListener('beforeunload', warn)
    return () => removeEventListener('beforeunload', warn)
  }, [dirty])

  // Switching sessions would drop the editor, so it asks first; the draft stays on disk either way.
  function openSession(id) {
    if (dirty && !window.confirm('当前文件有未保存草稿。切换会话只保留草稿在本地，不会发送它。继续？')) return
    client.adopt({ sessionId: id })
    return run('session.get', {})
  }

  const prompts = snapshot?.pending_permissions || []
  const writer = snapshot?.writer
  const hasEpoch = writer?.epoch !== undefined && writer?.epoch !== null
  const hasSession = !!snapshot?.session_id
  const hasRun = !!snapshot?.active_run_id
  const sealedRefs = list(shared?.data?.listMilestoneRelease).flatMap(release => list(release?.artifact_refs).map(ref => ({ ...ref, release: release?.summary || short(release?.id) })))

  return <>
    <Header title="对话与接续" description="同一会话可由 CLI 与工作台先后接入；序号、修订与写者纪元都取自本机服务回执。"
      action={<Tag value={snapshot ? (snapshot.run_status || snapshot.goal_status || '已接入') : '未接入'}/>} />

    <Section title="本机、工作区与会话" aside={<div className="button-row">
      <Producer method="host.status" disabled={!!busy} onClick={() => run('host.status', {})}>读取主机状态</Producer>
      <Producer method="workspace.list" disabled={!!busy} onClick={() => run('workspace.list', {})}>列出工作区</Producer>
      <Producer method="session.list" disabled={!!busy} onClick={() => run('session.list', { cursor: null, limit: 50 })}>列出会话</Producer>
    </div>}>
      <div className="key-grid">
        <span>客户端身份</span><strong>desktop-renderer</strong>
        <span>会话</span><strong>{short(snapshot?.session_id)}</strong>
        <span>修订</span><strong>{snapshot?.revision ?? '未接入'}</strong>
        <span>写者纪元</span><strong>{writer?.epoch ?? '无写者'}</strong>
        <span>事件水位</span><strong>{watermark}</strong>
        <span>活动运行</span><strong>{short(snapshot?.active_run_id)}</strong>
      </div>
      {snapshot?.resume_requires_explicit_user && <p className="callout">该会话要求用户显式恢复；在未按下“恢复”之前服务端不会自行继续。</p>}
      <div className="form-grid">
        <label>工作区绝对路径<input value={form.workspacePath} onChange={e => setForm({ ...form, workspacePath: e.target.value })} placeholder="C:/work/research"/></label>
        <label>工作区名称<input value={form.displayName} onChange={e => setForm({ ...form, displayName: e.target.value })} placeholder="我的研究目录"/></label>
        <label>模型配置引用<input value={form.modelRef} onChange={e => setForm({ ...form, modelRef: e.target.value })} placeholder="default"/></label>
        <label className="full-row">目标描述<textarea value={form.objective} onChange={e => setForm({ ...form, objective: e.target.value })} placeholder="希望推进的目标；先存草稿，独立验收后才算完成"/></label>
      </div>
      <div className="button-row">
        <Producer method="workspace.register" disabled={!!busy || !form.workspacePath} onClick={() => run('workspace.register', { selection_ref: form.workspacePath, display_name: form.displayName || form.workspacePath, requested_access: 'READ_WRITE' })}>登记工作区</Producer>
        <Producer method="project.bootstrap" disabled={!!busy || !form.workspacePath} onClick={() => run('project.bootstrap', { authorized_workspace_ref: form.workspacePath, display_name: form.displayName || '新的研究项目' }, { expectedRevision: 0, writerEpoch: 1 })}>建立项目与首个会话</Producer>
        <Producer method="session.create" disabled={!!busy || !workspaceRef} onClick={() => run('session.create', { workspace_ref: workspaceRef, model_config_ref: form.modelRef || 'default', title: form.displayName || '未命名会话' })}>新建会话</Producer>
        <Producer method="goal.start" disabled={!!busy || !form.objective} onClick={() => run('goal.start', { objective: form.objective, contract_artifact_ids: form.attachment ? [form.attachment] : [], start_as_draft: true })}>把目标存为草稿</Producer>
      </div>
      {bindings.length ? <p className="small-muted">已授权工作区 {bindings.length} 个，当前使用 {short(workspaceRef)}。</p> : <Empty>尚未登记工作区。</Empty>}
    </Section>

    <Section title="模型目录与配置" aside={<Tag value={models ? `${list(models).length} 个模型` : '未读取'}/>} >
      <div className="button-row">
        <Producer method="provider.models" disabled={!!busy} onClick={() => run('provider.models', { provider_id: 'default', refresh: true, allow_network: false, cursor: null, limit: 50 }).then(result => { if (result.kind === 'COMPLETED') setModels(result.result) })}>刷新模型目录</Producer>
        <Producer method="provider.probe" disabled={!!busy} onClick={() => run('provider.probe', { model_config_ref: form.modelRef || 'default', allow_network: false, max_output_tokens: 64, timeout_ms: 5000 }).then(result => { if (result.kind === 'COMPLETED') setProbe(result.result) })}>离线探测模型</Producer>
        <Producer method="host.configure" disabled={!!busy || !hasSession || !hasEpoch} onClick={() => run('host.configure', { config_revision: snapshot?.revision || 1, provider_id: 'default', base_url: 'http://127.0.0.1:0', model_id: form.modelRef || 'default', credential_ref: null })}>切换模型</Producer>
      </div>
      {!hasEpoch && <p className="small-muted">切换模型需要写者纪元；当前没有已接入的写者，故本按钮不会发送。</p>}
      {models && <p className="small-muted">目录：{list(models).map(item => item.model_id || item.id).slice(0, 8).join('、') || '空'}</p>}
      {probe && <p className="small-muted">探测：{JSON.stringify(probe).slice(0, 160)}</p>}
    </Section>

    <Section title="接入、交接与接续" aside={<span className="small-muted">CLI 与工作台共用同一会话</span>}>
      <div className="form-grid">
        <label>对端客户端 ID<input value={form.targetClient} onChange={e => setForm({ ...form, targetClient: e.target.value })} placeholder="例如 cli-本机"/></label>
        <label>交接方式<select value={form.handoffMode} onChange={e => setForm({ ...form, handoffMode: e.target.value })}><option value="WHEN_SETTLED">本轮结束后交接</option><option value="PAUSE_THEN_TRANSFER">先暂停再交接</option></select></label>
      </div>
      <div className="button-row">
        <Producer method="session.attach" data-mode="read" disabled={!!busy || !hasSession || !hasEpoch} onClick={() => run('session.attach', { after_sequence: watermark, request_write_owner: false })}>只读接入</Producer>
        <Producer method="session.attach" data-mode="claim" disabled={!!busy || !hasSession} onClick={() => run('session.attach', { after_sequence: watermark, request_write_owner: true }, { writerEpoch: undefined })}>接管写入</Producer>
        <Producer method="session.handoff" disabled={!!busy || !hasSession || !form.targetClient} onClick={() => run('session.handoff', { target_client_id: form.targetClient, handoff_mode: form.handoffMode })}>交接给另一台设备</Producer>
        <Producer method="session.update" disabled={!!busy || !hasSession} onClick={() => run('session.update', { action: 'ARCHIVE', title: null })}>归档当前会话</Producer>
      </div>
      {sessions.length ? <div className="record-list">{sessions.slice(0, 8).map(item => <Producer key={item.session_id} method="session.get" className="record-row" disabled={!!busy} onClick={() => openSession(item.session_id)}>
        <strong>{item.title || short(item.session_id)}</strong><span>{item.run_status || item.goal_status || '未运行'} · 修订 {item.revision} · 事件 {item.event_sequence}</span></Producer>)}</div> : <Empty>尚未列出会话；按“列出会话”读取本机记录。</Empty>}
      {!hasEpoch && hasSession && <p className="small-muted">只读接入需要携带观察到的写者纪元；无写者时请先“接管写入”。</p>}
    </Section>

    <Section title="对话、工具与队列" className="conversation-panel">
      {events.length ? <ol className="event-list">{events.slice(-25).reverse().map(event => <li key={event.event_id}><time>#{event.sequence}</time><strong>{EVENT_LABELS[event.kind] || event.kind}</strong><details><summary>技术详情</summary><pre>{JSON.stringify(event, null, 2)}</pre></details></li>)}</ol> : <Empty>暂无消息与事件。</Empty>}
      <div className="form-block">
        <label>发送给该会话<textarea aria-label="对话输入" value={chat} onChange={e => setChat(e.target.value)} placeholder="输入一条消息；附件只能来自候选产物"/></label>
        <label>投递方式<select aria-label="投递方式" value={form.delivery} onChange={e => setForm({ ...form, delivery: e.target.value })}>{Object.entries(DELIVERY_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>附件候选 ID<input value={form.attachment} onChange={e => setForm({ ...form, attachment: e.target.value })} placeholder="由“登记为附件”或封存产物候选填入"/></label>
        <div className="button-row">
          <Producer method="session.send" disabled={!!busy || !hasSession || !chat.trim()} onClick={() => run('session.send', { text: chat, attachment_artifact_ids: form.attachment ? [form.attachment] : [], delivery: form.delivery }).then(result => { if (!statusLine(result)) setChat('') })}>发送</Producer>
          <Producer method="session.events" disabled={!!busy || !hasSession} onClick={resync}>按游标读取事件</Producer>
          <Producer method="session.control" data-action="PAUSE" disabled={!!busy || !hasRun} onClick={() => run('session.control', { action: 'PAUSE', target_id: snapshot.active_run_id, reason: '用户在工作台请求暂停' })}>暂停</Producer>
          <Producer method="session.control" data-action="RESUME" disabled={!!busy || !hasRun} onClick={() => run('session.control', { action: 'RESUME', target_id: snapshot.active_run_id, reason: '用户在工作台请求恢复' })}>恢复</Producer>
          <Producer method="session.control" data-action="CANCEL" disabled={!!busy || !hasRun} onClick={() => run('session.control', { action: 'CANCEL', target_id: snapshot.active_run_id, reason: '用户在工作台请求取消' })}>取消</Producer>
        </div>
      </div>
      <p className="small-muted">队列与在途以回执为准：{(snapshot?.pending_command_ids || []).length} 条命令仍在途；队列位见最近一次发送回执。</p>
    </Section>

    <Section title="待授权的权限请求" aside={<span className="small-muted">{prompts.length} 项</span>}>
      {prompts.length ? prompts.map(prompt => <div className="request-row" key={prompt.action_digest}>
        <div><h3>{prompt.request?.summary || short(prompt.request?.id)}</h3><p>{prompt.action_scope?.tool_name || prompt.request?.requested_capability || '未给出能力'}</p>
          <small>任务 {short(prompt.task_id)} · 运行 {short(prompt.run_id)} · 动作摘要 {short(prompt.action_digest)}</small>
          {!prompt.policy_allows_user_decision && <p className="callout">策略不允许在此由用户决定；本按钮不发送。</p>}</div>
        <div className="button-row">
          {list(prompt.allowed_responses).includes('ALLOW_ONCE') && <Producer method="permission.respond" data-decision="ALLOW_ONCE" disabled={!!busy || !prompt.policy_allows_user_decision} onClick={() => run('permission.respond', { resource_request_id: prompt.request.id, resource_request_revision: prompt.request.revision, action_digest: prompt.action_digest, decision: 'ALLOW_ONCE', reason: '用户在工作台允许本次执行' })}>本次允许</Producer>}
          {list(prompt.allowed_responses).includes('DENY') && <Producer method="permission.respond" data-decision="DENY" disabled={!!busy || !prompt.policy_allows_user_decision} onClick={() => run('permission.respond', { resource_request_id: prompt.request.id, resource_request_revision: prompt.request.revision, action_digest: prompt.action_digest, decision: 'DENY', reason: '用户在工作台拒绝本次执行' })}>拒绝</Producer>}
        </div>
      </div>) : <Empty>当前没有等待响应的权限请求。</Empty>}
    </Section>

    <Section title="文件树、Diff 与保存" aside={<div className="button-row">
      <Producer method="workspace.tree" disabled={!!busy || !workspaceRef} onClick={() => run('workspace.tree', { workspace_ref: workspaceRef, relative_path: null, cursor: null, limit: 200 })}>读取文件树</Producer>
      <label>比较基准<select aria-label="比较基准" value={diffBase} onChange={e => setDiffBase(e.target.value)}><option value="INDEX">暂存区</option><option value="HEAD">上次提交</option></select></label>
      <Producer method="workspace.diff" disabled={!!busy || !workspaceRef} onClick={() => run('workspace.diff', { workspace_ref: workspaceRef, base: diffBase, relative_path: null, max_bytes: 65536 })}>生成 Diff</Producer>
      <Producer method="artifact.import" disabled={!!busy || !base?.relative_path} onClick={() => run('artifact.import', { workspace_ref: base.workspace_ref || workspaceRef, relative_path: base.relative_path, expected_content_hash: base.content_hash || null, purpose: 'ATTACHMENT' })}>把当前文件登记为附件</Producer>
    </div>}>
      <div className="two-column">
        <div>{tree.length ? <div className="record-list">{tree.slice(0, 40).map(entry => <Producer key={entry.relative_path} method="workspace.read" className="record-row" disabled={!!busy || !entry.readable || !workspaceRef}
          onClick={() => run('workspace.read', { workspace_ref: workspaceRef, relative_path: entry.relative_path, max_bytes: 262144 }).then(result => { if (result.kind === 'COMPLETED') { setDraft(''); setDirty(false) } })}>
          <strong>{entry.name}</strong><span>{entry.kind}{entry.readable ? '' : ` · ${entry.reason_code || '不可读'}`}</span><small>{entry.byte_size ?? '—'} 字节 · {short(entry.content_hash)}</small></Producer>)}</div> : <Empty>尚未读取文件树。</Empty>}</div>
        <div>{diff ? <><p className="small-muted">基准 {diff.base} · 版本 {short(diff.base_revision)} · {diff.total_files} 个文件{diff.truncated ? '（已截断）' : ''}</p>
          <ul className="event-list">{list(diff.files).map(file => <li key={file.relative_path}><time>{file.status}</time><strong>{file.relative_path}</strong><details><summary>{file.binary ? '二进制差异' : '查看补丁'}</summary><pre>{file.patch || '无补丁文本'}</pre></details></li>)}</ul></> : <Empty>尚无差异。</Empty>}
          {sealedRefs.length ? <><h3>封存产物</h3><div className="record-list">{sealedRefs.slice(0, 6).map(ref => <button type="button" key={`${ref.id}-${ref.revision}`} className="record-row" onClick={() => setForm(old => ({ ...old, attachment: ref.id }))}>
            <strong>{ref.release}</strong><span>{short(ref.id)} · 修订 {ref.revision} · {short(ref.content_hash)}</span><small>只能作为候选附件引用；封存内容不可在此改写或验收</small></button>)}</div></> : null}</div>
      </div>
      {base && <div className="form-block">
        <p className="small-muted">基线 {base.relative_path} · 哈希 {short(base.content_hash)} · 可写：{base.editable ? '是' : `否（${base.encoding || '未知编码'}）`}</p>
        <label>编辑文件<textarea rows="8" aria-label="文件编辑" value={draft} disabled={!base.editable} onChange={e => { setDraft(e.target.value); setDirty(true); keepDraft(base, e.target.value) }}/></label>
        <div className="button-row">
          <Producer method="workspace.write" disabled={!!busy || !base.editable || !hasSession} onClick={() => run('workspace.write', { workspace_ref: base.workspace_ref || workspaceRef, relative_path: base.relative_path, task_id: snapshot?.active_run_id || '', expected_content_hash: base.content_hash || null, text: draft, create_if_missing: false }).then(result => { if (!statusLine(result)) { setDirty(false); localStorage.removeItem(draftKey) } })}>按基线哈希保存</Producer>
          <Producer method="workspace.read" data-role="rebase" disabled={!!busy} onClick={() => run('workspace.read', { workspace_ref: base.workspace_ref || workspaceRef, relative_path: base.relative_path, max_bytes: 262144 }).then(result => { if (!statusLine(result)) { setDirty(false); localStorage.removeItem(draftKey) } })}>放弃草稿并重读基线</Producer>
        </div>
        {dirty && <p className="callout">草稿尚未发送；保存只会带上你读到的基线哈希，服务端内容已变化时应拒绝而不是覆盖。</p>}
      </div>}
    </Section>

    <Section title="本机拒发与最近回执">
      {notices.length ? <ul className="event-list">{notices.map((notice, index) => <li key={`${notice.at}-${index}`}><time>{when(notice.at)}</time><strong>{notice.method}</strong><details><summary>技术详情</summary><pre>{notice.line}</pre></details></li>)}</ul> : <Empty>本轮没有本机拒发或主机拒绝。</Empty>}
      {report && <JsonDetails value={report} label={`最近一次 ${report.method} 回执`}/>}
      <p className="small-muted">冻结协议共 {METHODS.length} 个方法；本面板为每个方法至少提供一个生产者，未满足前置条件时按钮禁用而不发送。</p>
    </Section>
  </>
}

import React, { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { integer, previous, display } from '../../desktop/main/lib/wire-values.mjs'
import { ArtifactPreview } from './preview.jsx'
import { SessionContinuation } from './session-continuation.jsx'

const rows = value => Array.isArray(value) ? value : value?.items || value?.sessions || value?.workspaces || []
const labels = { USER: '你', ASSISTANT: 'Agent', SYSTEM: '系统' }
const settled = value => value?.completed === true && (value?.protocol_status || value?.kind) === 'COMPLETED'
const sameConfiguration = (value, request) => !!value?.model_config_ref &&
  ['config_revision', 'provider_id', 'base_url', 'model_id', 'credential_ref'].every(key => value[key] === request[key])
// The shell owns the command lifetime. This observable renderer snapshot holds
// only the public payload and terminal result across route unmounts.
const modelConfigurationPending = new Map()
const modelConfigurationListeners = new Map()
const modelPending = projectId => modelConfigurationPending.get(projectId) || null
function updateModelPending(projectId, value) {
  if (value) modelConfigurationPending.set(projectId, value)
  else modelConfigurationPending.delete(projectId)
  for (const listener of modelConfigurationListeners.get(projectId) || []) listener()
}
function subscribeModelPending(projectId, listener) {
  let listeners = modelConfigurationListeners.get(projectId)
  if (!listeners) { listeners = new Set(); modelConfigurationListeners.set(projectId, listeners) }
  listeners.add(listener)
  return () => { listeners.delete(listener); if (!listeners.size) modelConfigurationListeners.delete(projectId) }
}
function unwrap(reply) {
  if (!reply?.ok || !settled(reply)) {
    const code = reply?.error_code || reply?.reason || reply?.protocol_status || '主机尚未完成请求'
    const detail = typeof reply?.error === 'string' ? reply.error : reply?.error?.message
    const error = new Error(detail ? `${code}：${detail}` : code)
    error.code = reply?.error_code || reply?.reason || reply?.protocol_status
    error.reply = reply
    throw error
  }
  return reply.result
}
function Panel({ title, children, aside }) { return <section className="panel"><div className="section-heading"><h2>{title}</h2>{aside}</div>{children}</section> }
function Failure({ error, retry }) { return error && <div className="state-notice" role="alert"><p>{error.message}。输入仍保留，请核对当前状态。</p>{retry && <button onClick={retry}>重新读取</button>}</div> }

export function NativeModelConfiguration({ projectId, initialHost, onConfigured }) {
  const pending = useSyncExternalStore(listener => subscribeModelPending(projectId, listener), () => modelPending(projectId), () => null)
  const [host, setHost] = useState(initialHost || null)
  const [form, setForm] = useState(() => modelPending(projectId)?.form || { provider_id: '', base_url: '', model_id: '', credential_ref: '' })
  const [busy, setBusy] = useState(false), [error, setError] = useState(null), [notice, setNotice] = useState('')
  const live = useRef(true)
  useEffect(() => { live.current = true; return () => { live.current = false } }, [])
  useEffect(() => { if (initialHost) setHost(initialHost) }, [initialHost])
  async function readHost() {
    if (!live.current) throw new Error('页面已切换')
    const selected = await window.researchos.desktop.selectProject(projectId)
    if (!selected?.ok) throw new Error(selected?.reason || '项目选择失败')
    if (!live.current) throw new Error('页面已切换')
    const reply = await window.researchos.v2['host.status']({})
    const value = { ...unwrap(reply), localHostOrigin: reply?.local_host_origin }
    if (!Number.isSafeInteger(value?.config_revision) || value.config_revision < 0) throw new Error('主机未返回有效的配置修订')
    if (!/^[a-f0-9]{64}$/.test(value.localHostOrigin || '')) throw new Error('主机未返回可信的本地身份')
    if (!live.current) throw new Error('页面已切换')
    setHost(value)
    return value
  }
  useEffect(() => { readHost().catch(setError) }, [projectId])
  async function reconcile(entry) {
    if (!entry?.outcome) return
    if (entry.reconciling) return entry.reconciling
    entry.reconciling = (async () => {
      if (!live.current || modelPending(projectId) !== entry) return
      const reply = entry.outcome
      if (reply?.dispatch_state === 'NOT_SENT') {
        // This attempt never reached HTTP. It has no original-host effect to
        // reconcile, even if another project's command owns the shell barrier.
        updateModelPending(projectId, null)
        setError((() => { try { unwrap(reply) } catch (cause) { return cause } })() || new Error(reply?.reason || '本地请求未发送'))
        return
      }
      const refreshed = await readHost()
      if (!entry.origin || refreshed.localHostOrigin !== entry.origin || reply?.local_host_origin !== entry.origin) {
        throw new Error('主机已切换；原配置只能在原主机核对，当前主机不可证明保存结果')
      }
      if ((reply?.ok && settled(reply)) || reply?.reason === 'STALE_RESPONSE') {
        const saved = reply?.reason === 'STALE_RESPONSE' ? reply.local_terminal_result : unwrap(reply)
        if (!sameConfiguration(saved, entry.payload)) throw new Error('原配置回执缺少完整的配置身份；请核对原主机状态')
        if (!refreshed.model_configurations?.some(item => sameConfiguration(item, entry.payload) && item.model_config_ref === saved.model_config_ref)) {
          throw new Error('原主机状态尚未列出同一配置；请刷新核对')
        }
        if (!live.current || modelPending(projectId) !== entry) return
        updateModelPending(projectId, null)
        onConfigured?.(refreshed, saved)
        setNotice(`配置已保存（修订 ${saved.config_revision}）。运行时资格尚未确认，创建会话或发送消息仍以服务端检查为准。`)
      } else {
        const reason = reply?.reason || reply?.error_code
        if (!live.current || modelPending(projectId) !== entry) return
        updateModelPending(projectId, null)
        setError((() => { try { unwrap(reply) } catch (cause) { return cause } })() || new Error(reason || '主机拒绝配置'))
      }
    })()
    try { await entry.reconciling }
    finally { entry.reconciling = null }
  }
  useEffect(() => { if (pending?.outcome) reconcile(pending).catch(setError) }, [pending, projectId])
  async function submit(event) {
    event.preventDefault(); if (busy) return
    setBusy(true); setError(null); setNotice('')
    try {
      const remembered = modelPending(projectId)
      if (remembered?.outcome) { await reconcile(remembered); return }
      if (!remembered && (!form.provider_id.trim() || !form.model_id.trim() || !form.base_url.trim())) {
        throw new Error('提供方 ID、模型 ID 和 API 基础地址不能为空')
      }
      const current = remembered ? null : await readHost()
      const request = remembered?.payload || {
        config_revision: current.config_revision + 1,
        provider_id: form.provider_id.trim(), base_url: form.base_url.trim(), model_id: form.model_id.trim(),
        credential_ref: form.credential_ref.trim() || null,
      }
      if (!live.current) return
      if (!remembered) updateModelPending(projectId, { payload: request, form: { ...form }, origin: current.localHostOrigin, outcome: null })
      const reply = await window.researchos.v2['host.configure'](request)
      const entry = modelPending(projectId)
      if (entry?.payload !== request) return
      if (reply?.ok && !settled(reply)) {
        if (reply.local_host_origin && reply.local_host_origin !== entry.origin) updateModelPending(projectId, { ...entry, origin: reply.local_host_origin })
        if (live.current) setNotice('主机已接收配置命令，尚未确认保存。请用同一请求继续查询结果。')
        return
      }
      // Only a trusted shell terminal response or pre-HTTP fact ends this
      // intent. Every other failure remains an uncertain replay.
      if (settled(reply) || reply?.protocol_status === 'REJECTED' || reply?.reason === 'STALE_RESPONSE' || reply?.dispatch_state === 'NOT_SENT' || (!remembered && reply?.reason === 'COMMAND_PENDING')) {
        const terminal = { ...entry, origin: reply?.local_host_origin || null, outcome: reply }
        updateModelPending(projectId, terminal)
        if (live.current) await reconcile(terminal)
      } else if (live.current) unwrap(reply)
    } catch (cause) {
      if (live.current) { setError(cause); if (modelPending(projectId)?.outcome?.ok) setNotice('主机已返回配置成功；状态刷新尚未确认，请重新读取。') }
    } finally { if (live.current) setBusy(false) }
  }
  return <Panel title="模型配置" aside={<button type="button" disabled={busy} onClick={() => readHost().then(() => setError(null)).catch(setError)}>刷新主机状态</button>}>
    <p>配置保存到本地主机。空凭据引用适用于无凭据的本地模型；远程服务须使用主机已有的受保护凭据引用。</p>
    {host && <p className="small-muted">当前配置修订 {host.config_revision} · 已保存 {host.model_configurations?.length || 0} 条配置</p>}
    <Failure error={error}/>
    <form className="form-grid" onSubmit={submit}>
      <label>提供方 ID<input value={form.provider_id} disabled={busy || !!pending} onChange={event => setForm({ ...form, provider_id: event.target.value })} placeholder="例如 ollama" required/></label>
      <label>模型 ID<input value={form.model_id} disabled={busy || !!pending} onChange={event => setForm({ ...form, model_id: event.target.value })} placeholder="例如 qwen3:4b-instruct" required/></label>
      <label className="full-row">API 基础地址<input type="url" value={form.base_url} disabled={busy || !!pending} onChange={event => setForm({ ...form, base_url: event.target.value })} placeholder="http://127.0.0.1:11434/v1" required/></label>
      <label className="full-row">受保护凭据引用（本地模型留空）<input value={form.credential_ref} disabled={busy || !!pending} onChange={event => setForm({ ...form, credential_ref: event.target.value })} autoComplete="off" placeholder="留空时提交 null"/></label>
      <button className="primary" type="submit" disabled={busy}>{busy ? '正在核对主机修订…' : pending?.outcome ? '核对原配置结果' : pending ? '继续同一配置命令' : '保存模型配置'}</button>
    </form>
    {notice && <p role="status">{notice}</p>}
    {!!host?.model_configurations?.length && <div className="record-list">{host.model_configurations.map(item => <div className="record-row" key={item.model_config_ref}><strong>{item.provider_id} · {item.model_id}</strong><small>配置修订 {item.config_revision} · {item.verified_at ? '提供方已探测' : '提供方未探测'} · 运行时资格未由此确认</small></div>)}</div>}
  </Panel>
}

export function NativeProjectEntry({ navigate, onRefresh }) {
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [host, setHost] = useState(null), [hostError, setHostError] = useState(null)
  async function checkHost() {
    try { setHost(unwrap(await window.researchos.v2['host.status']({}))); setHostError(null) }
    catch (cause) { setHostError(cause) }
  }
  useEffect(() => { checkHost() }, [])
  async function choose() {
    setBusy(true); setError(null)
    try {
      const reply = await window.researchos.desktop.chooseWorkspace({ display_name: name.trim() })
      if (!reply?.ok) throw new Error(reply?.reason || reply?.error_code || '项目初始化未完成')
      const value = reply.result || reply
      if (!value.project_id || !value.workspace?.authorized_workspace_ref) throw new Error('主机没有返回完整的项目与工作区引用')
      setResult(value); onRefresh()
    } catch (cause) { setError(cause) }
    finally { setBusy(false) }
  }
  return <Panel title="从本地目录开始"><p>选择项目目录后，主机会登记授权范围并盘点已有文件。已有项目会接续原身份。</p>
    <Failure error={hostError} retry={checkHost}/>{host && <p className="small-muted">本地主机已连接 · {host.workspaces?.length || 0} 个已登记工作区</p>}
    <label>项目显示名称<input value={name} onChange={event => setName(event.target.value)} placeholder="留空时使用目录名称"/></label>
    <div className="button-row"><button className="primary" disabled={busy} onClick={choose}>{busy ? '等待目录选择与本地盘点…' : '选择本地项目目录'}</button></div>
    <Failure error={error}/>{result && <div role="status"><p>本地盘点已保存。接下来可在项目工作台配置模型；配置保存后仍须由服务端验证运行资格。</p><p className="break-all">{result.workspace.display_path}</p><button onClick={() => navigate(`/p/${result.project_id}`)}>配置模型并打开工作台</button></div>}
  </Panel>
}

export function DesktopQualification({ projectId, sessionId }) {
  const [state, setState] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState('')
  const lifetime = useRef(0)
  useEffect(() => {
    const generation = ++lifetime.current
    setState(null); setError(null); setNotice('')
    const bridge = window.researchos?.desktop
    if (!bridge?.qualificationCurrent) return
    bridge.qualificationCurrent().then(reply => {
      if (lifetime.current !== generation) return
      if (reply?.ok) setState(reply)
      else setError(new Error(reply?.reason || '托管资格状态不可用'))
    }).catch(cause => { if (lifetime.current === generation) setError(cause) })
    return () => { lifetime.current++ }
  }, [projectId, sessionId])
  if (!window.researchos?.desktop?.qualificationCurrent) return null
  async function action(label, method) {
    if (busy) return
    const generation = lifetime.current
    setBusy(label); setError(null); setNotice('')
    try {
      const reply = await window.researchos.desktop[method]()
      if (generation !== lifetime.current) return
      if (!reply?.ok) throw new Error(reply?.reason || '托管资格操作失败')
      setState(reply)
      setNotice(method === 'qualificationPrepare' ? '准备完成；模型调用尚未开始。请核对后明确确认。' :
        method === 'qualificationConfirm' ? '确认调用已结束；下方状态来自原请求的当前复核。' : '已复核原请求的当前状态。')
    } catch (cause) { if (generation === lifetime.current) setError(cause) }
    finally { if (generation === lifetime.current) setBusy('') }
  }
  const pending = state?.state === 'AWAITING_CONFIRMATION' && !state?.consumed &&
    Date.parse(state?.expires_at) > Date.now()
  return <Panel title="本地模型运行资格">
    <p>先打开会话并取得写入权，再准备当前会话的模型资格确认。准备阶段不会调用模型。</p>
    <p className="small-muted">确认后最多调用模型 1 次，工具 0 个，用途仅为 mu_turn（600 秒）；费用依据 UNKNOWN，金额无法预估。确认可能消耗一次性请求，失败或超时后请用“复核原请求”查询，不要重复确认。</p>
    {state?.model && <p>当前待确认模型：{state.model.provider_id} · {state.model.model_id}</p>}
    {state?.request_id && <p className="break-all">原请求：{state.request_id}；有效至 {state.expires_at || '未知'}</p>}
    <p role="status">{state?.state === 'QUALIFIED_PURPOSE_AUTHORIZED' ?
      '最近一次复核显示用途授权；实际使用时服务端再次检查，请按需复核原请求。' :
      state?.state === 'CONTEXT_CHANGED_PENDING' ? '项目或会话已变更，原请求保留，当前不可确认。' :
      state?.state || '正在读取托管状态'}{state?.reason ? ` · ${state.reason}` : ''}</p>
    <div className="button-row">
      <button disabled={!!busy || !state?.available || !sessionId ||
        (!!state?.request_id && !(state?.state === 'EXPIRED' && !state?.consumed))}
        onClick={() => action('准备', 'qualificationPrepare')}>准备当前会话</button>
      <button className="primary" disabled={!!busy || !state?.available || !pending} onClick={() => {
        if (window.confirm('确认进行最多 1 次本地模型资格调用？费用依据 UNKNOWN，金额无法预估；此请求只能确认一次。')) action('确认', 'qualificationConfirm')
      }}>明确确认一次调用</button>
      <button disabled={!!busy || !state?.available || !state?.request_id} onClick={() => action('复核', 'qualificationStatus')}>复核原请求</button>
    </div>
    {busy && <p role="status">{busy}中…</p>}{notice && <p role="status">{notice}</p>}
    <Failure error={error} />
  </Panel>
}

export function NativeWorkbench({ projectId, profile, api, navigate, shared, onRefresh }) {
  const [state, setState] = useState({ loading: true, sessions: [], host: null, snapshot: null, events: [], error: null })
  const [busy, setBusy] = useState('')
  const [draft, setDraft] = useState('')
  const [delivery, setDelivery] = useState('NORMAL')
  const [model, setModel] = useState('')
  const [workspace, setWorkspace] = useState('')
  const [title, setTitle] = useState('')
  const [attachment, setAttachment] = useState('')
  const [selectedFile, setSelectedFile] = useState('')
  const [fileDirty, setFileDirty] = useState(false)
  const [notice, setNotice] = useState('')
  const current = useRef({ projectId, generation: 0, snapshot: null, busy: false })
  const [online, setOnline] = useState(navigator.onLine)
  const composer = useRef(null)
  function active(generation) { return current.current.projectId === projectId && current.current.generation === generation }
  function adopt(snapshot) {
    if (!snapshot || snapshot.project_id !== projectId) throw new Error('会话与当前项目不一致')
    if (current.current.snapshot?.session_id !== snapshot.session_id) current.current.eventSequence = previous(snapshot.earliest_event_sequence)
    current.current.snapshot = snapshot
    setState(old => ({ ...old, snapshot, error: null }))
  }
  async function readSnapshot(generation = current.current.generation) {
    const value = unwrap(await window.researchos.v2['session.get']({}))
    if (active(generation)) adopt(value)
    return value
  }
  async function load() {
    const generation = ++current.current.generation
    current.current.projectId = projectId
    setState(old => ({ ...old, loading: true, error: null }))
    try {
      const selected = await window.researchos.desktop.selectProject(projectId)
      if (!selected?.ok) throw new Error(selected?.reason || '项目选择失败')
      const host = unwrap(await window.researchos.v2['host.status']({}))
      if (active(generation)) setState(old => ({ ...old, host }))
      const sessions = unwrap(await window.researchos.v2['session.list']({ cursor: null, limit: 100 }))
      const context = await window.researchos.desktop.context()
      if (!active(generation)) return
      const values = rows(sessions)
      setState(old => ({ ...old, host, sessions: values, nextCursor: sessions.next_cursor, loading: false, error: null }))
      setModel(old => old || host?.model_configurations?.[0]?.model_config_ref || '')
      setWorkspace(old => old || host?.workspaces?.find(item => item.project_id === projectId && item.status === 'ACTIVE')?.authorized_workspace_ref || '')
      if (context.project_id === projectId && context.session_id) {
        const opened = unwrap(await window.researchos.desktop.openSession(context.session_id))
        if (active(generation)) { adopt(opened); current.current.eventSequence = previous(opened.earliest_event_sequence) }
      }
    } catch (error) { if (active(generation)) setState(old => ({ ...old, loading: false, error })) }
  }
  useEffect(() => {
    current.current = { projectId, generation: current.current.generation + 1, snapshot: null, busy: false }
    setState({ loading: true, sessions: [], host: null, snapshot: null, events: [], error: null })
    load()
    const changed = () => setOnline(navigator.onLine)
    addEventListener('online', changed); addEventListener('offline', changed)
    return () => { current.current.generation++; removeEventListener('online', changed); removeEventListener('offline', changed) }
  }, [projectId])
  useEffect(() => {
    let stopped = false, polling = false
    const tick = async () => {
      const snapshot = current.current.snapshot
      if (stopped || polling || current.current.busy || !navigator.onLine || !snapshot) return
      const generation = current.current.generation
      polling = true
      try {
        const page = unwrap(await window.researchos.v2['session.events']({ after_sequence: current.current.eventSequence ?? snapshot.event_sequence, limit: 200 }))
        if (stopped || !active(generation)) return
        if (integer(page.next_sequence)) current.current.eventSequence = page.next_sequence
        if (page.events?.length) {
          setState(old => {
            const seen = new Set(old.events.map(item => item.event_id))
            return { ...old, events: [...old.events, ...page.events.filter(item => !seen.has(item.event_id))].slice(-500) }
          })
          await readSnapshot(generation)
        }
      } catch (error) {
        if (stopped || !active(generation)) return
        if (['CURSOR_EXPIRED', 'CURSOR_INVALID'].includes(error.code)) { try { const fresh = await readSnapshot(generation); if (active(generation)) current.current.eventSequence = previous(fresh.earliest_event_sequence) } catch (cause) { if (active(generation)) setState(old => ({ ...old, error: cause })) } }
        else setState(old => ({ ...old, error }))
      } finally { polling = false }
    }
    const timer = setInterval(tick, 1200)
    const visible = () => { if (document.visibilityState === 'visible') tick() }
    addEventListener('online', tick); document.addEventListener('visibilitychange', visible)
    return () => { stopped = true; clearInterval(timer); removeEventListener('online', tick); document.removeEventListener('visibilitychange', visible) }
  }, [projectId])
  async function command(label, action) {
    if (current.current.busy) return
    current.current.generation++; current.current.busy = true; setBusy(label); setNotice('')
    try { await action(); setState(old => ({ ...old, error: null })) }
    catch (error) { setState(old => ({ ...old, error })) }
    finally { current.current.busy = false; setBusy('') }
  }
  async function open(sessionId) {
    if (fileDirty && !confirm('文件有未保存草稿，切换会话会丢弃当前文件草稿。继续？')) return
    if (draft && !confirm('当前消息尚未发送，切换会话后会保留在输入框。继续？')) return
    await command('打开会话', async () => { adopt(unwrap(await window.researchos.desktop.openSession(sessionId))); setState(old => ({ ...old, events: [] })) })
  }
  async function moreSessions() {
    await command('读取更多会话', async () => {
      const page = unwrap(await window.researchos.v2['session.list']({ cursor: state.nextCursor, limit: 100 }))
      setState(old => ({ ...old, sessions: [...new Map([...old.sessions, ...rows(page)].map(item => [item.session_id, item])).values()], nextCursor: page.next_cursor }))
    })
  }
  async function create() {
    if (fileDirty && !confirm('文件有未保存草稿，新建会话会丢弃当前文件草稿。继续？')) return
    await command('创建会话', async () => {
      const value = unwrap(await window.researchos.v2['session.create']({ workspace_ref: workspace, model_config_ref: model, title: title.trim() || '新会话' }))
      adopt(unwrap(await window.researchos.desktop.openSession(value.session_id)))
      setState(old => ({ ...old, sessions: [value, ...old.sessions.filter(item => item.session_id !== value.session_id)], events: [] }))
    })
  }
  const snapshot = state.snapshot
  const writer = snapshot?.writer?.client_id === state.host?.client_id && Date.parse(snapshot?.writer?.expires_at) > Date.now()
  const disabled = !!busy || !online
  const tools = state.events.filter(event => ['TOOL_STARTED', 'TOOL_RESULT', 'ERROR', 'USAGE', 'ARTIFACT', 'JUDGE_DECISION'].includes(event.kind))
  return <>
    <header className="page-heading"><div><h1>{profile?.name || '会话工作台'}</h1><p>消息、工具结果和成果保留在当前项目中。</p></div><button disabled={!!busy} onClick={load}>刷新会话</button></header>
    <Failure error={state.error} retry={load}/>
    {Object.values(shared?.errors || {}).map((error, index) => <Failure key={index} error={new Error(`部分项目资料尚未读取：${error.message}`)} retry={() => { onRefresh(); load() }}/>) }
    {!online && <p className="connection-banner" role="status">已离线，显示最后读取的会话；重新连接后核对最新状态。</p>}
    {state.loading && <div className="loading-state" role="status" aria-busy="true">正在读取本机会话…</div>}
    {!state.loading && state.host && !state.host.model_configurations?.length && <NativeModelConfiguration projectId={projectId} initialHost={state.host} onConfigured={(host, configured) => { setState(old => ({ ...old, host })); setModel(configured.model_config_ref); setNotice(`配置已保存（修订 ${configured.config_revision}）；运行时资格仍待验证。`) }} />}
    <DesktopQualification key={`${projectId}:${state.snapshot?.session_id || ''}`} projectId={projectId} sessionId={state.snapshot?.session_id || null}/>
    <div className="session-layout">
      <Panel title="项目会话"><ul className="session-picker">{state.sessions.map(item => <li key={item.session_id}><button aria-current={snapshot?.session_id === item.session_id ? 'page' : undefined} disabled={disabled} onClick={() => open(item.session_id)}>{item.title || '未命名会话'}<small>{item.run_status || (item.archived_at ? '已归档' : '等待消息')}</small></button></li>)}</ul>
        {state.nextCursor && <button disabled={disabled} onClick={moreSessions}>加载更多会话</button>}
        {!state.sessions.length && !state.loading && <p className="empty-state">{state.error ? '会话列表尚未读取，请恢复连接或权限后重试。' : '还没有会话，选择已配置模型后开始。'}</p>}
        <details><summary>新建会话</summary><label>名称<input value={title} onChange={event => setTitle(event.target.value)}/></label>
          <label>工作区<select value={workspace} onChange={event => setWorkspace(event.target.value)}><option value="">选择已授权目录</option>{(state.host?.workspaces || []).filter(item => item.project_id === projectId && item.status === 'ACTIVE').map(item => <option key={item.authorized_workspace_ref} value={item.authorized_workspace_ref}>{item.display_name}</option>)}</select></label>
          <label>模型<select value={model} onChange={event => setModel(event.target.value)}><option value="">选择配置记录（资格未确认）</option>{(state.host?.model_configurations || []).map(item => <option key={item.model_config_ref} value={item.model_config_ref}>{item.provider_id} · {item.model_id}</option>)}</select></label>
          {!state.host?.model_configurations?.length ? <p>还没有模型配置，请先使用上方表单或项目设置保存。</p> : <p className="small-muted">配置记录不代表运行时已具备资格；创建会话时由服务端检查。</p>}<button disabled={disabled || !workspace || !model} onClick={create}>创建会话</button></details>
      </Panel>
      <div className="session-center"><Panel title={snapshot?.title || '开始协作'} aside={snapshot && <span className="tag">{snapshot.run_status || '等待消息'}</span>}>
        {snapshot ? <><div className="button-row"><button disabled={disabled || writer} onClick={() => command('接管写入', async () => { unwrap(await window.researchos.v2['session.attach']({ after_sequence: snapshot.event_sequence, request_write_owner: true })); await readSnapshot(); composer.current?.focus() })}>{writer ? '当前可写' : '在此继续'}</button>
          {['PAUSE', 'RESUME', 'CANCEL'].map((action, index) => <button key={action} disabled={disabled || !writer || (action !== 'RESUME' && !snapshot.active_run_id)} onClick={() => command(action, async () => { unwrap(await window.researchos.v2['session.control']({ action, target_id: action === 'RESUME' ? snapshot.session_id : snapshot.active_run_id, reason: '用户从桌面会话操作' })); await readSnapshot() })}>{['暂停', '恢复', '取消'][index]}</button>)}</div>
          {snapshot.resume_requires_explicit_user && <p className="callout">会话等待明确恢复。查看上次结果后再继续。</p>}
          <div className="conversation-transcript" aria-label="会话记录">{(snapshot.messages || []).map(message => <article className={`conversation-message role-${message.role.toLowerCase()}`} key={message.message_id}><h3>{labels[message.role] || message.role}</h3><div className="message-text">{(message.parts || []).map(part => part.text).join('')}</div>{!message.complete && <small>正在接收…</small>}</article>)}{!snapshot.messages?.length && <p className="empty-state">发送第一条消息，说明希望完成的事。</p>}</div>
          {snapshot.has_earlier_messages && <div><p>这里只显示最近记录，可读取已封存的完整会话记录。</p>{snapshot.transcript_artifact_ref ? <BoundArtifact reference={snapshot.transcript_artifact_ref} api={api} projectId={projectId} label="读取完整会话记录"/> : <p role="status">完整记录尚未封存，请刷新后重试。</p>}</div>}
          {snapshot.pending_command_ids?.length > 0 && <p role="status">{snapshot.pending_command_ids.length} 条命令等待处理。</p>}
          <form className="session-composer" onSubmit={event => { event.preventDefault(); command('发送消息', async () => { unwrap(await window.researchos.v2['session.send']({ text: draft, attachment_artifact_ids: attachment ? [attachment] : [], delivery })); setDraft(''); setAttachment(''); await readSnapshot(); setNotice('消息已接收，等待运行结果。') }) }}>
            <label>发送给 Agent<textarea ref={composer} aria-label="会话消息" value={draft} onChange={event => setDraft(event.target.value)} placeholder="说明目标、约束或要修改的文件…" required/></label>
            <div className="composer-controls"><label>投递方式<select value={delivery} onChange={event => setDelivery(event.target.value)}><option value="NORMAL">正常消息</option><option value="STEER">引导当前执行</option><option value="FOLLOW_UP">追加后续</option></select></label><button className="primary" type="submit" disabled={disabled || !writer || !draft.trim()}>发送</button></div>
            {attachment && <p>已附加受控产物：<span className="break-all">{attachment}</span><button type="button" onClick={() => setAttachment('')}>移除附件</button></p>}
            {!writer && <p className="small-muted">当前为只读，请先选择“在此继续”。</p>}
          </form>
        </> : <p className="empty-state">打开已有会话，或选择工作区和模型创建会话。</p>}
        <p className="small-muted" role="status" aria-live="polite">{busy ? `${busy}…` : notice}</p>
      </Panel>
      {snapshot?.project_id === projectId && <SessionContinuation key={`${projectId}:${snapshot.session_id}:${snapshot.goal_id || ''}:${snapshot.revision}`} api={api} projectId={projectId} snapshot={snapshot} navigate={navigate}/>}
      {tools.length > 0 && <Panel title="工具与结果"><ol className="event-list">{tools.map(event => <li key={event.event_id}><strong>{event.kind === 'TOOL_STARTED' ? '开始工具' : event.kind === 'TOOL_RESULT' ? '工具结果' : event.kind}</strong><span>{event.payload?.tool_name || event.payload?.summary || event.payload?.message || ''}</span><details><summary>查看完整回执</summary><pre>{display(event.payload)}</pre></details></li>)}</ol></Panel>}
      {(snapshot?.pending_permissions || []).map(prompt => <PermissionDecision key={prompt.request.id} prompt={prompt} api={api} projectId={projectId} disabled={disabled || !writer} respond={decision => command('处理授权', async () => { unwrap(await window.researchos.v2['permission.respond']({ resource_request_id: prompt.request.id, resource_request_revision: prompt.request.revision, action_digest: prompt.action_digest, decision, reason: '用户在桌面明确选择' })); await readSnapshot() })}/>)}
      </div>
    </div>
    {snapshot && <WorkspaceFiles snapshot={snapshot} api={api} projectId={projectId} writer={writer} disabled={disabled} command={command} readSnapshot={readSnapshot} setAttachment={setAttachment} selectedFile={selectedFile} setSelectedFile={setSelectedFile} setFileDirty={setFileDirty}/>}
  </>
}

function BoundArtifact({ reference, api, projectId, label = '读取引用产物', onVerified }) {
  const [artifact, setArtifact] = useState(null), [error, setError] = useState(null)
  const controller = useRef(null)
  useEffect(() => { controller.current?.abort(); setArtifact(null); setError(null); return () => controller.current?.abort() }, [projectId, reference.id, reference.revision, reference.content_hash])
  async function read() {
    controller.current?.abort(); const active = new AbortController(); controller.current = active
    try {
      const value = await api.call('getArtifact', { params: { projectId, id: reference.id }, signal: active.signal })
      if (value.revision !== reference.revision || value.content_hash !== reference.content_hash) throw new Error('产物版本与会话固定引用不一致，请刷新会话')
      if (!active.signal.aborted) { setArtifact(value); setError(null) }
    } catch (cause) { if (!active.signal.aborted) setError(cause) }
  }
  return <div><button onClick={read}>{label}</button><Failure error={error} retry={read}/>{artifact && <ArtifactPreview artifact={artifact} expectedRef={reference} api={api} projectId={projectId} onVerified={onVerified}/>}</div>
}

function PermissionDecision({ prompt, api, projectId, disabled, respond }) {
  const scope = prompt.action_scope
  const [reviewed, setReviewed] = useState(false), [now, setNow] = useState(Date.now())
  useEffect(() => { setReviewed(false) }, [prompt.action_digest, scope.arguments_artifact_ref.content_hash])
  useEffect(() => { const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer) }, [])
  const expired = !Number.isFinite(Date.parse(scope.expires_at)) || now >= Date.parse(scope.expires_at)
  return <Panel title="工具等待授权"><p>{prompt.request.summary}</p>
    <dl><dt>工具</dt><dd>{scope.tool_name}</dd><dt>工作区</dt><dd className="break-all">{scope.workspace_ref}</dd><dt>允许路径</dt><dd>{scope.allowed_relative_paths.length ? scope.allowed_relative_paths.join('、') : '没有文件路径授权'}</dd><dt>有效期</dt><dd>{new Date(scope.expires_at).toLocaleString()}</dd></dl>
    <p>授权仅对本次动作生效一次。请先预览冻结参数，再决定是否允许。</p>
    <BoundArtifact reference={scope.arguments_artifact_ref} api={api} projectId={projectId} label="查看本次工具参数" onVerified={({ content_hash, text }) => setReviewed(content_hash === scope.arguments_artifact_ref.content_hash && text != null)}/>
    <details><summary>动作范围与输入版本</summary><pre>{display(scope)}</pre></details>
    {!prompt.policy_allows_user_decision && <p role="status">当前策略不允许用户授权此动作，请先处理策略限制。</p>}
    {expired && <p role="status">本次授权请求已过期，请刷新原任务状态。</p>}
    {prompt.allowed_responses.filter(decision => decision !== 'ALLOW_ONCE' || prompt.policy_allows_user_decision).map(decision => <button key={decision} disabled={disabled || expired || !prompt.policy_allows_user_decision || (decision === 'ALLOW_ONCE' && !reviewed)} onClick={() => respond(decision)}>{decision === 'DENY' ? '拒绝' : '允许本次'}</button>)}
  </Panel>
}

function WorkspaceFiles({ snapshot, api, projectId, writer, disabled, command, readSnapshot, setAttachment, selectedFile, setSelectedFile, setFileDirty }) {
  const [entries, setEntries] = useState([]), [directory, setDirectory] = useState(''), [cursor, setCursor] = useState(null)
  const [base, setBase] = useState(null), [text, setText] = useState(''), [diff, setDiff] = useState(null), [diffBase, setDiffBase] = useState('HEAD')
  const [tasks, setTasks] = useState([]), [task, setTask] = useState(''), [conflict, setConflict] = useState(null)
  const [taskError, setTaskError] = useState(null), [taskRefresh, setTaskRefresh] = useState(0)
  const dirty = !!base && base.text !== text
  useEffect(() => { setFileDirty(dirty); return () => setFileDirty(false) }, [dirty, setFileDirty])
  useEffect(() => { setEntries([]); setDirectory(''); setCursor(null); setBase(null); setText(''); setDiff(null); setConflict(null); setSelectedFile(''); setTask('') }, [snapshot.session_id])
  useEffect(() => {
    const controller = new AbortController()
    api.call('listTask', { params: { projectId }, signal: controller.signal }).then(value => { if (!controller.signal.aborted) { setTasks(rows(value).filter(item => item.task_type === 'mu_turn' && item.goal_id === snapshot.goal_id && ['DRAFT', 'READY', 'BLOCKED', 'NEEDS_REVALIDATION'].includes(item.status))); setTaskError(null) } }).catch(error => { if (!controller.signal.aborted) { setTasks([]); setTaskError(error) } })
    return () => controller.abort()
  }, [api, projectId, snapshot.session_id, snapshot.active_run_id, snapshot.revision, taskRefresh])
  async function tree(path, append = false) {
    await command('读取目录', async () => { const value = unwrap(await window.researchos.v2['workspace.tree']({ workspace_ref: snapshot.workspace_ref, relative_path: path || '.', cursor: append ? cursor : null, limit: 100 })); setEntries(old => append ? [...old, ...value.entries] : value.entries); setCursor(value.next_cursor); setDirectory(path) })
  }
  async function open(path) {
    if (dirty && !confirm('文件有未保存草稿，打开其他文件会丢弃当前草稿。继续？')) return
    await command('读取文件', async () => { const value = unwrap(await window.researchos.v2['workspace.read']({ workspace_ref: snapshot.workspace_ref, relative_path: path, max_bytes: 1048576 })); setBase(value); setText(value.text); setSelectedFile(path); setConflict(null) })
  }
  return <Panel title="工作区文件与差异" aside={<button disabled={disabled} onClick={() => tree('')}>读取文件树</button>}>
    <div className="workspace-layout"><div><p className="small-muted break-all">{directory || '项目根目录'}</p>{directory && <button disabled={disabled} onClick={() => tree(directory.split('/').slice(0, -1).join('/'))}>上级目录</button>}<ul className="file-list">{entries.map(item => <li key={item.relative_path}><button disabled={disabled || !item.readable} onClick={() => item.kind === 'DIRECTORY' ? tree(item.relative_path) : open(item.relative_path)}>{item.name || item.relative_path}{item.kind === 'DIRECTORY' ? ' /' : ''}</button>{!item.readable && <small>{({ CONTENT_TOO_LARGE: '超过读取上限', UNSUPPORTED_CONTENT: '不支持预览', PATH_OUT_OF_SCOPE: '不在授权范围', FORBIDDEN: '无读取权限' })[item.reason_code] || '不可读取'}</small>}</li>)}</ul>{cursor && <button disabled={disabled} onClick={() => tree(directory, true)}>加载更多文件</button>}</div>
    <div><label>差异基线<select value={diffBase} onChange={event => setDiffBase(event.target.value)}><option value="HEAD">Git HEAD</option><option value="INDEX">Git 暂存区</option></select></label><button disabled={disabled} onClick={() => command('读取差异', async () => setDiff(unwrap(await window.researchos.v2['workspace.diff']({ workspace_ref: snapshot.workspace_ref, base: diffBase, relative_path: selectedFile || null, max_bytes: 1048576 }))))}>查看差异</button>
      {diff && <><p>{diff.base} · {diff.files?.length || 0} / {diff.total_files} 个文件{diff.truncated ? ' · 内容超限，已截断' : ''}</p><pre className="preview-text">{display(diff.files)}</pre>{diff.full_diff_artifact_ref && <BoundArtifact reference={diff.full_diff_artifact_ref} api={api} projectId={projectId} label="读取完整差异"/>}</>}
      {base && <><h3 className="break-all">{base.relative_path}</h3><label>文件草稿<textarea className="file-editor" value={text} onChange={event => setText(event.target.value)} readOnly={!base.editable || !writer}/></label>
        <label>关联任务<select value={task} onChange={event => setTask(event.target.value)}><option value="">选择已有可编辑任务</option>{tasks.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
        <Failure error={taskError} retry={() => setTaskRefresh(value => value + 1)}/>
        <div className="button-row"><button disabled={disabled || !writer || !task || !base.editable || !dirty || !!conflict} onClick={() => command('保存文件草稿', async () => { try { unwrap(await window.researchos.v2['workspace.write']({ workspace_ref: snapshot.workspace_ref, relative_path: base.relative_path, task_id: task, expected_content_hash: base.content_hash, text, create_if_missing: false })); const next = unwrap(await window.researchos.v2['workspace.read']({ workspace_ref: snapshot.workspace_ref, relative_path: base.relative_path, max_bytes: 1048576 })); setBase(next); setText(next.text); await readSnapshot() } catch (error) { if (/CONFLICT|STALE|HASH|REVISION|EXTERNAL_WRITE_RACE/.test(error.code || '')) setConflict(error.message); throw error } })}>保存草稿</button>
        <button disabled={disabled || !writer || dirty} onClick={() => command('附加文件', async () => { const value = unwrap(await window.researchos.v2['artifact.import']({ workspace_ref: snapshot.workspace_ref, relative_path: base.relative_path, expected_content_hash: base.content_hash, purpose: 'ATTACHMENT' })); setAttachment(value.artifact_ref.id); await readSnapshot() })}>附加到消息</button></div>
        {!task && <p className="small-muted">选择已有任务后才能保存；封存产物不可原地编辑。</p>}
        {conflict && <div className="state-notice" role="alert"><p>外部版本已改变，当前草稿仍保留。请复制需要保留的内容，重新读取并手工合并。</p><button disabled={disabled} onClick={() => open(base.relative_path)}>核对外部版本</button></div>}
      </>}
    </div></div>
  </Panel>
}

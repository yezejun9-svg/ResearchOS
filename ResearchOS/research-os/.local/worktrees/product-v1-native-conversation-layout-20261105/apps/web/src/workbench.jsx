import React, { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { integer, previous, display } from '../../desktop/main/lib/wire-values.mjs'
import { ArtifactPreview } from './preview.jsx'
import { SessionContinuation } from './session-continuation.jsx'
import { WorkbenchLayout } from './components/workbench-layout.jsx'
import { ActivityRail } from './components/activity-rail.jsx'
import { workspaceProjectPath } from './startup.js'
import { composerSubmitKey, appendPrompt } from './activity.js'
import { HARNESS_CAPABILITIES, canSubmitHarness, hasHarnessCapability, harnessStatusLabel, createHarnessController } from './harness.js'

const rows = value => Array.isArray(value) ? value : value?.items || value?.sessions || value?.workspaces || []
const labels = { USER: '你', ASSISTANT: 'Agent', SYSTEM: '系统' }
const sessionStates = { WAITING: '等待消息', QUEUED: '排队中', STARTING: '启动中', RUNNING: '执行中', PAUSED: '已暂停', SETTLED: '执行已结束', COMPLETED: '已结束', FAILED: '执行失败', CANCELLED: '已取消', RECONCILING: '恢复核对中' }
const configurationStates = { NOT_REQUESTED: '尚未发起请求', AWAITING_CONFIRMATION: '等待明确确认', AWAITING_CODING_CONFIRMATION: '等待明确确认', QUALIFIED_PURPOSE_AUTHORIZED: '用途授权已核对', CODING_CONFIGURED: '编码配置已保存，运行资格待核对', HOST_UNAVAILABLE: '本机主机不可核对', CONTEXT_CHANGED_PENDING: '会话已变化，需复核原请求', EXPIRED: '原请求已过期', CURRENT_RECHECK_REQUIRED: '当前状态待复核', FAILED: '未通过', REGISTERED: '已登记，资格待核对' }
const statusLabel = (value, dictionary, fallback) => value ? dictionary[value] || '状态待核对' : fallback
const settled = value => value?.completed === true && (value?.protocol_status || value?.kind) === 'COMPLETED'
const sameConfiguration = (value, request) => !!value?.model_config_ref &&
  ['config_revision', 'provider_id', 'base_url', 'model_id', 'credential_ref'].every(key => value[key] === request[key])
// The shell owns the command lifetime. This observable renderer snapshot holds
// only the public payload and terminal result across route unmounts.
const modelConfigurationPending = new Map()
const modelConfigurationListeners = new Map()
// A committed private result can arrive through CONFIRM or original STATUS.
// Successful V2 adoption survives a component remount; failed reads remain retryable.
const codingReconciliations = new Map()
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
function Panel({ title, children, aside, className = '' }) { return <section className={`panel ${className}`}><div className="section-heading"><h2>{title}</h2>{aside}</div>{children}</section> }
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
      if (!workspaceProjectPath(value)) throw new Error('主机没有返回完整的项目与工作区引用')
      setResult(value); onRefresh()
    } catch (cause) { setError(cause) }
    finally { setBusy(false) }
  }
  return <section className="local-project-entry" aria-labelledby="local-project-title">
    <div className="local-project-main"><span className="local-project-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 6h7l2 2h9v11H3z"/><path d="M3 6V4h7l2 2"/></svg></span><div><h2 id="local-project-title">打开本地项目</h2><p>选择目录，连接你的工作空间。</p></div><button className="primary" disabled={busy} onClick={choose}>{busy ? '正在打开…' : '选择目录'} <span aria-hidden="true">↗</span></button></div>
    <details className="project-name-option"><summary>自定义项目名称</summary><label>显示名称<input value={name} onChange={event => setName(event.target.value)} placeholder="默认使用目录名称"/></label></details>
    <div className="local-project-note"><span>在本机登记目录并盘点文件，保留原内容。</span>{host && <span>已登记 {host.workspaces?.length || 0} 个工作区</span>}</div>
    <Failure error={hostError} retry={checkHost}/><Failure error={error}/>
    {result && <div className="project-open-result" role="status"><div><strong>项目已登记</strong><p className="break-all">{result.workspace.display_path}</p></div><button className="primary" onClick={() => navigate(workspaceProjectPath(result))}>打开工作台 <span aria-hidden="true">→</span></button></div>}
  </section>
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
      setNotice(!reply.available ? '操作后本机主机身份无法确认；原请求仅保留为历史，请恢复主机后复核。' :
        reply.status_scope === 'ORIGINAL_REQUEST_HISTORY' ? '已复核原请求历史状态；该结果不代表当前模型或写入权已获用途授权。' :
        method === 'qualificationPrepare' ? '准备完成；模型调用尚未开始。请核对后明确确认。' :
        method === 'qualificationConfirm' ? '确认调用已结束；下方状态来自原请求的当前复核。' : '已复核原请求的当前状态。')
    } catch (cause) {
      if (generation !== lifetime.current) return
      setError(cause)
      setState(old => old && ({ ...old, available: false, authorized: false,
        state: 'CURRENT_RECHECK_REQUIRED', reason: cause?.message || 'CURRENT_RECHECK_REQUIRED' }))
      try {
        const current = await window.researchos.desktop.qualificationCurrent()
        if (generation === lifetime.current && current?.ok) setState(current)
      } catch { /* Keep the non-authoritative state until a later refresh. */ }
    }
    finally { if (generation === lifetime.current) setBusy('') }
  }
  const pending = state?.state === 'AWAITING_CONFIRMATION' && !state?.consumed &&
    Date.parse(state?.expires_at) > Date.now()
  return <Panel title="本地模型运行资格">
    <p>{!sessionId ? '尚未打开会话，请先选择或创建会话。' : state && !state.available ? '当前资格请求不可操作，请查看状态并复核原请求。' : '当前会话可准备模型资格请求；准备阶段不会调用模型。'}</p>
    <p className="small-muted">明确确认后最多调用本地模型 1 次；费用未知。</p>
    <details className="raw-details"><summary>查看用途、限制与失败后的处理</summary><p>工具调用 0 次，用途仅为 mu_turn（600 秒）。金额无法预估。确认可能消耗一次性请求；失败或超时后请复核原请求，不要重复确认。</p></details>
    {state?.model && <p>当前待确认模型：{state.model.provider_id} · {state.model.model_id}</p>}
    {state?.request_id && <p className="break-all">原请求：{state.request_id}；有效至 {state.expires_at || '未知'}</p>}
    {state?.previous_request_id && <p className="break-all small-muted">已退役的过期原请求：{state.previous_request_id}；过期于 {state.previous_expires_at || '未知'}。该记录仅供审计，不代表当前资格。</p>}
    <p role="status">{state?.status_scope === 'ORIGINAL_REQUEST_HISTORY' ?
      `原请求历史状态：${state.original_state}；${state.original_checked_at ? `复核于 ${state.original_checked_at}` : '尚需复核'}。当前模型或写入权的用途授权须另行核对。` :
      state?.authorized ?
      '最近一次复核显示用途授权；实际使用时服务端再次检查，请按需复核原请求。' :
      state?.state === 'QUALIFIED_PURPOSE_AUTHORIZED' ? '保留上次用途授权结果；当前授权尚未确认，请复核原请求。' :
      state?.state === 'HOST_UNAVAILABLE' ? '本机主机身份已变化或无法确认；旧请求仅作历史记录，当前不可用。' :
      state?.state === 'CONTEXT_CHANGED_PENDING' ? '项目或会话已变更，原请求保留，当前不可确认。' :
      statusLabel(state?.state, configurationStates, '正在读取资格状态')}{state?.reason ? ` · ${state.reason}` : ''}</p>
    {state?.state && <details className="raw-details"><summary>原始状态</summary><code>{state.state}</code></details>}
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

export function DesktopCodingAuthorization({ projectId, sessionId, onConfigured }) {
  const [state, setState] = useState(null)
  const [toolchain, setToolchain] = useState('')
  const [vendor, setVendor] = useState('')
  const [readPaths, setReadPaths] = useState('go.mod\npkg/value.go\npkg/value_test.go')
  const [writePaths, setWritePaths] = useState('pkg/value.go')
  const [checkPaths, setCheckPaths] = useState('go.mod\npkg/value.go\npkg/value_test.go')
  const [checkId, setCheckId] = useState('go-check')
  const [checkPackage, setCheckPackage] = useState('./pkg')
  const [testPattern, setTestPattern] = useState('^TestValue$')
  const [limits, setLimits] = useState({ max_read_bytes: 8192, max_write_bytes: 8192,
    max_tool_calls: 8, max_output_tokens: 2048, timeout_seconds: 90,
    process_limit: 32, memory_mib: 1024, max_text_bytes: 4096 })
  const [busy, setBusy] = useState('')
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState('')
  const lifetime = useRef(0)
  useEffect(() => {
    const generation = ++lifetime.current
    setState(null); setToolchain(''); setVendor(''); setError(null); setNotice('')
    window.researchos?.desktop?.codingCurrent?.().then(reply => {
      if (generation !== lifetime.current) return
      if (reply?.ok) setState(reply)
      else setError(new Error(reply?.reason || '编码授权状态不可用'))
    }).catch(cause => { if (generation === lifetime.current) setError(cause) })
    return () => { lifetime.current++ }
  }, [projectId, sessionId])
  if (!window.researchos?.desktop?.codingCurrent) return null
  const lines = value => value.split(/\r?\n/).map(item => item.trim()).filter(Boolean)
  async function reconcile(reply, generation) {
    if (reply.state !== 'CODING_CONFIGURED' || !reply.available ||
        !reply.commit_key || !reply.model_config_ref || !onConfigured) return
    const key = reply.commit_key
    const existing = codingReconciliations.get(key)
    if (existing) { await existing; return }
    const work = (async () => {
      if (generation !== lifetime.current) throw new Error('编码配置会话已切换，请复核原请求')
      await onConfigured(reply)
    })()
    codingReconciliations.set(key, work)
    try { await work }
    catch (cause) { if (codingReconciliations.get(key) === work) codingReconciliations.delete(key); throw cause }
  }
  async function action(label, method, body) {
    if (busy) return
    const generation = lifetime.current
    setBusy(label); setError(null); setNotice('')
    try {
      const reply = await window.researchos.desktop[method](body)
      if (generation !== lifetime.current) return
      if (!reply?.ok) throw new Error(reply?.reason || '编码授权操作失败')
      setState(reply)
      if (reply.state === 'CODING_CONFIGURED') {
        await reconcile(reply, generation)
        setNotice('编码配置已保存；运行时仍是 REGISTERED，模型资格与代码检查均尚未执行。')
      } else setNotice(method === 'codingPrepare' ? '冻结完成；配置尚未写入，也未调用模型。请核对摘要后明确确认。' :
        method === 'codingStatus' ? '已复核原请求；复核不会重试确认。' : '')
    } catch (cause) {
      if (generation !== lifetime.current) return
      setError(cause)
      setState(old => old && ({ ...old, available: false, state: 'CURRENT_RECHECK_REQUIRED' }))
      try { const current = await window.researchos.desktop.codingCurrent()
        if (generation === lifetime.current && current?.ok) setState(current) } catch { /* Explicit later status remains available. */ }
    } finally { if (generation === lifetime.current) setBusy('') }
  }
  async function pick(kind) {
    if (busy) return
    const generation = lifetime.current
    setBusy('选择目录'); setError(null)
    try {
      const reply = await window.researchos.desktop[kind === 'toolchain' ? 'codingPickToolchain' : 'codingPickVendor']()
      if (generation !== lifetime.current) return
      if (!reply?.ok) throw new Error(reply?.reason || '目录选择失败')
      if (reply.selected) (kind === 'toolchain' ? setToolchain : setVendor)(reply.name || '已选择')
    } catch (cause) { if (generation === lifetime.current) setError(cause) }
    finally { if (generation === lifetime.current) setBusy('') }
  }
  const setLimit = key => event => setLimits(old => ({ ...old, [key]: Number(event.target.value) }))
  const intent = () => ({ read_paths: lines(readPaths), write_paths: lines(writePaths),
    max_read_bytes: limits.max_read_bytes, max_write_bytes: limits.max_write_bytes,
    max_tool_calls: limits.max_tool_calls, max_output_tokens: limits.max_output_tokens,
    checks: [{ id: checkId.trim(), package: checkPackage.trim(), test_pattern: testPattern.trim(),
      source_paths: lines(checkPaths), timeout_seconds: limits.timeout_seconds,
      process_limit: limits.process_limit, memory_mib: limits.memory_mib, max_text_bytes: limits.max_text_bytes }] })
  const prepared = state?.state === 'AWAITING_CODING_CONFIRMATION' && !state.consumed &&
    Date.parse(state.expires_at) > Date.now()
  return <Panel title="显式工作区编码授权">
    <p>选择当前会话的可读、可写相对文件和离线 Go 检查。准备只冻结文件与检查计划；明确确认才写入新的模型配置，期间模型调用为 0。</p>
    <details className="setup-disclosure"><summary>编辑授权范围与离线检查</summary>
    <div className="button-row"><button disabled={!!busy || !sessionId} onClick={() => pick('toolchain')}>选择 Go 工具链目录</button>
      <span>{toolchain || '尚未选择'}</span><button disabled={!!busy || !sessionId} onClick={() => pick('vendor')}>选择离线 vendor（可选）</button><span>{vendor || '未选择'}</span></div>
    <label>可读相对路径（每行一个）<textarea value={readPaths} onChange={event => setReadPaths(event.target.value)}/></label>
    <label>可写相对路径（须包含在可读路径中）<textarea value={writePaths} onChange={event => setWritePaths(event.target.value)}/></label>
    <div className="field-grid"><label>单文件读取上限（字节）<input type="number" value={limits.max_read_bytes} onChange={setLimit('max_read_bytes')}/></label>
      <label>单文件写入上限（字节）<input type="number" value={limits.max_write_bytes} onChange={setLimit('max_write_bytes')}/></label>
      <label>工具调用上限<input type="number" value={limits.max_tool_calls} onChange={setLimit('max_tool_calls')}/></label>
      <label>模型输出 token 上限<input type="number" value={limits.max_output_tokens} onChange={setLimit('max_output_tokens')}/></label></div>
    <h3>离线 Go 检查</h3>
    <div className="field-grid"><label>检查 ID<input value={checkId} onChange={event => setCheckId(event.target.value)}/></label>
      <label>包路径<input value={checkPackage} onChange={event => setCheckPackage(event.target.value)}/></label>
      <label>测试选择器（^…$）<input value={testPattern} onChange={event => setTestPattern(event.target.value)}/></label></div>
    <label>检查源文件相对路径（每行一个）<textarea value={checkPaths} onChange={event => setCheckPaths(event.target.value)}/></label>
    <div className="field-grid"><label>检查超时（秒）<input type="number" value={limits.timeout_seconds} onChange={setLimit('timeout_seconds')}/></label>
      <label>进程上限<input type="number" value={limits.process_limit} onChange={setLimit('process_limit')}/></label>
      <label>内存上限（MiB）<input type="number" value={limits.memory_mib} onChange={setLimit('memory_mib')}/></label>
      <label>输出上限（字节）<input type="number" value={limits.max_text_bytes} onChange={setLimit('max_text_bytes')}/></label></div>
    </details>
    {state?.scope && <div><h3>本次冻结摘要</h3><p>可读：{state.scope.read_paths.join('、')}；可写：{state.scope.write_paths.join('、')}</p>
      <p>检查：{state.scope.checks.map(check => `${check.id} ${check.package} ${check.test_pattern}（${check.source_paths.join('、')}）`).join('；')}</p>
      <p>限制：读取 {state.scope.max_read_bytes} 字节/文件，写入 {state.scope.max_write_bytes} 字节/文件，
        工具最多 {state.scope.max_tool_calls} 次，模型输出最多 {state.scope.max_output_tokens} token。</p>
      {state.scope.checks.map(check => <p key={check.id}>检查 {check.id}：超时 {check.timeout_seconds} 秒，
        最多 {check.process_limit} 个进程、{check.memory_mib} MiB 内存、{check.max_text_bytes} 字节输出；
        Go 工具链{check.toolchain_selected ? '已选' : '未选'}，离线 vendor {check.vendor_selected ? '已选' : '未选'}。</p>)}
      <p>最多 8 次普通模型调用；资格验证最多 1 次模型调用、0 次工具调用。当前模型调用：{state.model_calls}。</p>
      <p>截止：{state.expires_at || '未知'}；冻结检查摘要：{state.frozen_checks?.map(check => check.id).join('、') || '无'}。</p></div>}
    <p role="status">{statusLabel(state?.state, configurationStates, '正在读取编码授权状态')}{state?.reason ? ` · ${state.reason}` : ''}</p>
    {state?.state && <details className="raw-details"><summary>原始状态</summary><code>{state.state}</code></details>}
    <div className="button-row"><button disabled={!!busy || !state?.available || !sessionId || !toolchain ||
      (!!state?.scope && !(state?.state === 'EXPIRED' && !state?.consumed))}
      onClick={() => action('准备', 'codingPrepare', intent())}>准备并冻结</button>
      <button className="primary" disabled={!!busy || !state?.available || !prepared}
        onClick={() => action('确认', 'codingConfirm')}>明确确认配置</button>
      <button disabled={!!busy || !state?.available || !state?.scope} onClick={() => action('复核', 'codingStatus')}>复核原请求</button></div>
    {busy && <p role="status">{busy}中…</p>}{notice && <p role="status">{notice}</p>}<Failure error={error}/>
  </Panel>
}

export function NativeWorkbench(props) {
  const [harness, setHarness] = useState('codex')
  const [codexDraft, setCodexDraft] = useState(''), [muDraft, setMuDraft] = useState('')
  const [guard, setGuard] = useState({})
  function choose(value) {
    if (guard.busy) return
    if (guard.fileDirty && !confirm('文件有未保存草稿，切换 Harness 会关闭文件编辑。继续吗？')) return
    if (guard.active && !confirm('当前任务仍由 Host 执行，切换 Harness 不会取消它。继续吗？')) return
    setHarness(value)
  }
  return <><div className="button-row composer-context"><label>Harness <select aria-label="Harness" value={harness} disabled={guard.busy} onChange={event => choose(event.target.value)}><option value="codex">Codex CLI · 只读任务</option><option value="mu">Mu · 原有模型会话</option></select></label><small>各 Harness 的登录、模型与能力分别核对；草稿在本页保留。</small></div>
    {harness === 'codex' ? <NativeHarnessWorkbench {...props} draft={codexDraft} setDraft={setCodexDraft} onGuardChange={setGuard}/> :
      <NativeMuWorkbench {...props} draft={muDraft} setDraft={setMuDraft} onGuardChange={setGuard}/>}</>
}

function NativeHarnessWorkbench({ projectId, profile, navigate, shared, draft, setDraft, onGuardChange }) {
  const [state, setState] = useState({ loading: true, busy: false, tasks: [], task: null, events: [], capabilities: null, pending: null })
  const [workspaces, setWorkspaces] = useState([]), [workspace, setWorkspace] = useState('')
  const [hostError, setHostError] = useState(null), [notice, setNotice] = useState('')
  const [online, setOnline] = useState(navigator.onLine)
  const controller = useRef(null), composer = useRef(null)
  const draftVersion = useRef(0), draftScope = useRef({ projectId, workspace })
  if (draftScope.current.projectId !== projectId || draftScope.current.workspace !== workspace) {
    draftVersion.current++
    draftScope.current = { projectId, workspace }
  }
  function editDraft(value) {
    draftVersion.current++
    setDraft(value)
  }
  useEffect(() => {
    let stopped = false
    const control = createHarnessController(window.researchos.harness, projectId)
    controller.current = control
    const unsubscribe = control.subscribe(() => { if (!stopped) setState(control.getSnapshot()) })
    async function load() {
      try {
        const selected = await window.researchos.desktop.selectProject(projectId)
        if (!selected?.ok) throw new Error(selected?.reason || 'PROJECT_NOT_SELECTED')
        if (stopped) return
        try {
          const host = unwrap(await window.researchos.v2['host.status']({}))
          if (stopped) return
          const values = (host.workspaces || []).filter(item => item.project_id === projectId && item.status === 'ACTIVE')
          setWorkspaces(values)
          setWorkspace(old => values.some(item => item.authorized_workspace_ref === old) ? old : values[0]?.authorized_workspace_ref || '')
          setHostError(null)
        } catch (error) { if (!stopped) setHostError(error) }
        if (!stopped) await control.load()
      } catch (error) { if (!stopped) { setHostError(error); setState(old => ({ ...old, loading: false })) } }
    }
    load()
    const changed = () => setOnline(navigator.onLine)
    const tick = () => { if (navigator.onLine) control.tick() }
    const visible = () => { if (document.visibilityState === 'visible') tick() }
    const timer = setInterval(tick, 1200)
    addEventListener('online', changed); addEventListener('offline', changed); addEventListener('online', tick)
    document.addEventListener('visibilitychange', visible)
    return () => { stopped = true; draftVersion.current++; if (controller.current === control) controller.current = null; unsubscribe(); control.dispose(); clearInterval(timer); removeEventListener('online', changed); removeEventListener('offline', changed); removeEventListener('online', tick); document.removeEventListener('visibilitychange', visible) }
  }, [projectId])
  useEffect(() => { onGuardChange({ busy: state.busy, fileDirty: false, active: !!state.task && !state.task.terminal }) }, [state.busy, state.task, onGuardChange])
  const capabilities = state.capabilities, task = state.task
  const disabled = state.busy || state.loading || !online
  const canSend = !disabled && !state.pending && !!workspace && !!draft.trim() && canSubmitHarness(capabilities)
  const assistant = state.events.filter(event => event.kind === 'ASSISTANT_MESSAGE' && typeof event.payload?.text === 'string')
  async function send(event) {
    event.preventDefault()
    if (!canSend) return
    const control = controller.current, submittedVersion = draftVersion.current
    if (!control) return
    setNotice('')
    if (await control.submit({ workspace_ref: workspace, prompt: draft })) {
      if (controller.current !== control) return
      if (draftVersion.current === submittedVersion) setDraft('')
      setNotice('任务已接收，等待真实运行回执。')
    }
  }
  return <><header className="page-heading workbench-heading"><div><span className="workbench-eyebrow">RESEARCH / WORKSPACE</span><h1>{profile?.name || '项目工作台'}</h1><p>通过本机 Codex 执行一次只读临时任务，查看真实执行回执。</p></div><button disabled={disabled} onClick={() => controller.current.load()}>刷新任务</button></header>
    <Failure error={hostError}/><Failure error={state.error}/>
    {!online && <p className="connection-banner" role="status">当前离线。保留已读任务；恢复连接后核对状态，不会重新提交。</p>}
    {state.pending && <div className="state-notice" role="status"><p>原{state.pending.kind === 'cancel' ? '取消' : '提交'}请求需核对：{state.pending.request_id}。不会自动重发或创建新任务。</p><button disabled={disabled} onClick={() => controller.current.reconcile()}>只读核对原请求</button></div>}
    <WorkbenchLayout hasSession={!!task} sessions={<Panel title="Codex 任务"><ul className="session-picker">{state.tasks.map(item => <li key={item.task_ref.task_id}><button disabled={disabled} aria-current={task?.task_ref.task_id === item.task_ref.task_id ? 'page' : undefined} onClick={() => { if (!draft || confirm('当前草稿会保留在输入框。切换查看此任务？')) controller.current.select(item.task_ref.task_id) }}>{item.prompt.slice(0, 80) || item.task_ref.task_id}<small>{harnessStatusLabel(item.status)}</small></button></li>)}</ul>{!state.tasks.length && <p className="empty-state">{state.loading ? '正在读取真实任务…' : '尚无任务。选择授权工作区后输入目标。'}</p>}<label>工作区<select aria-label="Codex 工作区" value={workspace} disabled={disabled} onChange={event => setWorkspace(event.target.value)}><option value="">选择已授权目录</option>{workspaces.map(item => <option key={item.authorized_workspace_ref} value={item.authorized_workspace_ref}>{item.display_name}</option>)}</select></label>{!workspaces.length && <p>请先从项目入口选择并授权工作区；不需要 provider 模型配置。</p>}</Panel>}
      conversation={<div className="session-center"><Panel className="conversation-canvas" title="Codex · 只读任务" aside={<span className="tag">{task ? harnessStatusLabel(task.status) : '等待输入'}</span>}>
        <div className="button-row session-run-controls"><button disabled={disabled || !!state.pending || !task || task.terminal || !hasHarnessCapability(capabilities, 'cancel')} onClick={() => controller.current.cancel()}>取消当前任务</button><button disabled title="当前 Harness 不支持暂停">暂停</button><button disabled title="当前 Harness 不支持恢复执行">恢复执行</button></div>
        <div className="conversation-transcript" aria-label="Codex 任务记录">{task ? <><article className="conversation-message role-user"><h3>你</h3><div className="message-text">{task.prompt}</div></article>{assistant.map(event => <article className="conversation-message role-assistant" key={event.event_id}><h3>Codex</h3><div className="message-text">{event.payload.text}</div></article>)}{task.result?.assistant_text && !assistant.some(event => event.payload.text === task.result.assistant_text) && <article className="conversation-message role-assistant"><h3>Codex</h3><div className="message-text">{task.result.assistant_text}</div></article>}{task.failure && <p role="status">{task.failure.code}：{task.failure.message}</p>}<p className="small-muted">Task {task.task_ref.task_id} · 修订 {task.task_revision}{task.run ? ` · Run ${task.run.run_id} · epoch ${task.run.epoch}` : ' · 尚无 Run'}。执行状态不代表业务验收。</p></> : <ConversationWelcome setDraft={editDraft} composer={composer}/>}</div>
        <form className="session-composer" onSubmit={send}><div className="composer-context"><span className="composer-prompt">researchos &gt;</span><span>Codex CLI</span><span>模型由 Codex 配置决定</span><span>workspace-read · ephemeral</span></div><textarea ref={composer} aria-label="Codex 任务输入" value={draft} onChange={event => editDraft(event.target.value)} onKeyDown={event => { if (composerSubmitKey(event)) { event.preventDefault(); if (canSend) event.currentTarget.form.requestSubmit() } }} placeholder="输入一次只读任务，例如：检查项目结构并解释主要入口。" required/><div className="composer-controls"><small>Enter 发送 · Shift+Enter 换行</small><button className="primary" type="submit" disabled={!canSend}>提交只读任务</button></div>{notice && <p role="status">{notice}</p>}</form>
      </Panel></div>}
      context={<><Panel title="Codex 状态与能力">{capabilities ? <><p>安装：{capabilities.installation.present ? capabilities.installation.version || '已发现' : '未发现'} · 登录：{({ UNPROBED: '未探测', LOGGED_IN: '已登录', LOGGED_OUT: '未登录', ERROR: '探测失败' })[capabilities.authentication.state]}</p><p>执行验证：{capabilities.verification.execution} · 只读范围验证：{capabilities.verification.workspace_read_scope} · 取消验证：{capabilities.verification.cancellation}</p><p>平台策略管理；只读边界{capabilities.security_scope.enforcement_verified ? '已由 Host 标记验证' : '未验证'}。登录与执行验证分别记录。</p><div className="record-list">{HARNESS_CAPABILITIES.map(([key, label]) => <div className="record-row" key={key}><span>{label}</span><span>{hasHarnessCapability(capabilities, key) ? '已实现' : '不支持'}</span></div>)}</div>{!capabilities.can_submit && <p role="status">暂不能提交：{capabilities.reason_codes.join('、')}</p>}</> : <p>{state.loading ? '正在读取 Host 能力…' : '能力尚未读取；操作保持禁用。'}</p>}</Panel><ActivityRail events={state.events} harnessTask={task} projection={shared?.data?.getProgressProjection} projectState={shared?.data?.getProjectState} releases={shared?.data?.listMilestoneRelease} projectId={projectId} navigate={navigate}/><details className="inspector-disclosure"><summary>文件、产物与授权</summary><p>此 Harness 首版未提供文件列表、diff、文件产物、附件或逐工具授权能力，相关操作不可用。</p><button disabled>读取文件差异</button><button disabled>写入文件</button><button disabled>批准工具</button></details></>}/>
  </>
}

function NativeMuWorkbench({ projectId, profile, api, navigate, shared, onRefresh, draft, setDraft, onGuardChange }) {
  const [state, setState] = useState({ loading: true, sessions: [], host: null, snapshot: null, events: [], error: null })
  const [busy, setBusy] = useState('')
  const [delivery, setDelivery] = useState('NORMAL')
  const [model, setModel] = useState('')
  const [workspace, setWorkspace] = useState('')
  const [title, setTitle] = useState('')
  const [attachment, setAttachment] = useState('')
  const [selectedFile, setSelectedFile] = useState('')
  const [fileDirty, setFileDirty] = useState(false)
  useEffect(() => { onGuardChange({ busy: !!busy, fileDirty, active: !!state.snapshot?.active_run_id && !['SETTLED', 'COMPLETED', 'FAILED', 'CANCELLED'].includes(state.snapshot?.run_status) }) }, [busy, fileDirty, state.snapshot, onGuardChange])
  const [notice, setNotice] = useState('')
  const current = useRef({ projectId, generation: 0, snapshot: null, busy: false })
  const [online, setOnline] = useState(navigator.onLine)
  const composer = useRef(null)
  function active(generation) { return current.current.projectId === projectId && current.current.generation === generation }
  function adopt(snapshot) {
    if (!snapshot || snapshot.project_id !== projectId) throw new Error('会话与当前项目不一致')
    if (current.current.snapshot?.session_id !== snapshot.session_id) current.current.eventSequence = previous(snapshot.earliest_event_sequence)
    current.current.snapshot = snapshot
    setState(old => ({ ...old, snapshot, events: old.snapshot?.session_id === snapshot.session_id ? old.events : [], error: null }))
  }
  async function readSnapshot(generation = current.current.generation) {
    const value = unwrap(await window.researchos.v2['session.get']({}))
    if (active(generation)) adopt(value)
    return value
  }
  async function reconcileCodingCommit(commit) {
    const generation = current.current.generation
    const originalSession = current.current.snapshot?.session_id
    if (!originalSession || commit.runtime_status !== 'REGISTERED') throw new Error('原会话不可用，请复核编码配置')
    const before = await window.researchos.desktop.context()
    if (!active(generation) || before.project_id !== projectId || before.session_id !== originalSession)
      throw new Error('编码配置会话已切换，请复核原请求')
    const host = unwrap(await window.researchos.v2['host.status']({}))
    const snapshot = unwrap(await window.researchos.v2['session.get']({}))
    const after = await window.researchos.desktop.context()
    const currentCoding = await window.researchos.desktop.codingCurrent()
    if (!active(generation) || current.current.snapshot?.session_id !== originalSession ||
        after.project_id !== projectId || after.session_id !== originalSession ||
        snapshot.project_id !== projectId || snapshot.session_id !== originalSession ||
        !currentCoding?.ok || !currentCoding.available || currentCoding.commit_key !== commit.commit_key ||
        !host.model_configurations?.some(item => item.model_config_ref === commit.model_config_ref &&
          item.config_revision === commit.config_revision))
      throw new Error('编码配置已保存，但原会话读取尚未核对；请复核原请求')
    setState(old => ({ ...old, host, snapshot, error: null }))
    current.current.snapshot = snapshot
    setModel(commit.model_config_ref)
    setNotice(`编码配置已保存（修订 ${commit.config_revision}）；运行时资格仍待验证。`)
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
            return { ...old, events: [...old.events, ...page.events.filter(item => item.session_id === snapshot.session_id && !seen.has(item.event_id))].slice(-500) }
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
  const selectedModel = state.host?.model_configurations?.find(item => item.model_config_ref === (snapshot?.model_config_ref || model))
  const selectedWorkspace = state.host?.workspaces?.find(item => item.authorized_workspace_ref === (snapshot?.workspace_ref || workspace))
  return <>
    <header className="page-heading workbench-heading"><div><span className="workbench-eyebrow">RESEARCH / WORKSPACE</span><h1>{profile?.name || '会话工作台'}</h1><p>把想法交给 Agent，让每一次迭代都有据可查。</p></div><button className="workbench-refresh" disabled={!!busy} onClick={load}>刷新会话</button></header>
    <Failure error={state.error} retry={load}/>
    {Object.values(shared?.errors || {}).map((error, index) => <Failure key={index} error={new Error(`部分项目资料尚未读取：${error.message}`)} retry={() => { onRefresh(); load() }}/>) }
    {!online && <p className="connection-banner" role="status">已离线，显示最后读取的会话；重新连接后核对最新状态。</p>}
    {state.loading && <div className="loading-state" role="status" aria-busy="true">正在读取本机会话…</div>}
    {!state.loading && state.host && !state.host.model_configurations?.length && <NativeModelConfiguration projectId={projectId} initialHost={state.host} onConfigured={(host, configured) => { setState(old => ({ ...old, host })); setModel(configured.model_config_ref); setNotice(`配置已保存（修订 ${configured.config_revision}）；运行时资格仍待验证。`) }} />}
    <WorkbenchLayout hasSession={!!snapshot} sessions={<>
      <Panel title="项目会话"><ul className="session-picker">{state.sessions.map(item => <li key={item.session_id}><button aria-current={snapshot?.session_id === item.session_id ? 'page' : undefined} disabled={disabled} onClick={() => open(item.session_id)}>{item.title || '未命名会话'}<small title={item.run_status ? `原始状态：${item.run_status}` : undefined}>{item.archived_at ? '已归档' : statusLabel(item.run_status, sessionStates, '等待消息')}</small></button></li>)}</ul>
        {state.nextCursor && <button disabled={disabled} onClick={moreSessions}>加载更多会话</button>}
        {!state.sessions.length && !state.loading && <p className="empty-state">{state.error ? '会话列表尚未读取，请恢复连接或权限后重试。' : '还没有会话，选择已配置模型后开始。'}</p>}
        <details><summary>新建会话</summary><label>名称<input value={title} onChange={event => setTitle(event.target.value)}/></label>
          <label>工作区<select value={workspace} onChange={event => setWorkspace(event.target.value)}><option value="">选择已授权目录</option>{(state.host?.workspaces || []).filter(item => item.project_id === projectId && item.status === 'ACTIVE').map(item => <option key={item.authorized_workspace_ref} value={item.authorized_workspace_ref}>{item.display_name}</option>)}</select></label>
          <label>模型<select value={model} onChange={event => setModel(event.target.value)}><option value="">选择配置记录（资格未确认）</option>{(state.host?.model_configurations || []).map(item => <option key={item.model_config_ref} value={item.model_config_ref}>{item.provider_id} · {item.model_id}</option>)}</select></label>
          {!state.host?.model_configurations?.length ? <p>还没有模型配置，请先使用上方表单或项目设置保存。</p> : <p className="small-muted">配置记录不代表运行时已具备资格；创建会话时由服务端检查。</p>}<button disabled={disabled || !workspace || !model} onClick={create}>创建会话</button></details>
      </Panel>
    </>} conversation={<div className="session-center"><Panel className="conversation-canvas" title={snapshot?.title || '开始协作'} aside={snapshot && <span className="tag" title={snapshot.run_status ? `原始状态：${snapshot.run_status}` : undefined}>{statusLabel(snapshot.run_status, sessionStates, '等待消息')}</span>}>
        {snapshot ? <><div className="button-row session-run-controls">{writer ? <span className="tag good" role="status">当前可写</span> : <button disabled={disabled} onClick={() => command('接管写入', async () => { unwrap(await window.researchos.v2['session.attach']({ after_sequence: snapshot.event_sequence, request_write_owner: true })); await readSnapshot(); composer.current?.focus() })}>在此继续</button>}
          {['PAUSE', 'RESUME', 'CANCEL'].map((action, index) => <button key={action} disabled={disabled || !writer || (action !== 'RESUME' && !snapshot.active_run_id)} onClick={() => command(action, async () => { unwrap(await window.researchos.v2['session.control']({ action, target_id: action === 'RESUME' ? snapshot.session_id : snapshot.active_run_id, reason: '用户从桌面会话操作' })); await readSnapshot() })}>{['暂停', '恢复', '取消'][index]}</button>)}</div>
          {snapshot.resume_requires_explicit_user && <p className="callout">会话等待明确恢复。查看上次结果后再继续。</p>}
          <div className="conversation-transcript" aria-label="会话记录">{(snapshot.messages || []).map(message => <article className={`conversation-message role-${message.role.toLowerCase()}`} key={message.message_id}><h3>{labels[message.role] || message.role}</h3><div className="message-text">{(message.parts || []).map(part => part.text).join('')}</div>{!message.complete && <small>正在接收…</small>}</article>)}{!snapshot.messages?.length && <ConversationWelcome setDraft={setDraft} composer={composer}/>}</div>
          {snapshot.has_earlier_messages && <div><p>这里只显示最近记录，可读取已封存的完整会话记录。</p>{snapshot.transcript_artifact_ref ? <BoundArtifact reference={snapshot.transcript_artifact_ref} api={api} projectId={projectId} label="读取完整会话记录"/> : <p role="status">完整记录尚未封存，请刷新后重试。</p>}</div>}
          {snapshot.pending_command_ids?.length > 0 && <p role="status">{snapshot.pending_command_ids.length} 条命令等待处理。</p>}
        </> : <div className="conversation-transcript"><ConversationWelcome setDraft={setDraft} composer={composer}/></div>}
          <form className="session-composer" onSubmit={event => { event.preventDefault(); if (disabled || !snapshot || !writer || !draft.trim()) return; command('发送消息', async () => { unwrap(await window.researchos.v2['session.send']({ text: draft, attachment_artifact_ids: attachment ? [attachment] : [], delivery })); setDraft(''); setAttachment(''); await readSnapshot(); setNotice('消息已接收，等待运行结果。') }) }}>
            <div className="composer-context"><span className="composer-prompt">researchos &gt;</span><span title={selectedModel?.model_id}>{selectedModel?.model_id || '尚未选择模型'}</span>{selectedWorkspace?.display_name && <span title={selectedWorkspace.display_name}>{selectedWorkspace.display_name}</span>}</div>
            <label className="composer-message-label"><span className="visually-hidden">发送给 Agent</span><textarea ref={composer} aria-label="会话消息" value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (composerSubmitKey(event)) { event.preventDefault(); if (!disabled && snapshot && writer && draft.trim()) event.currentTarget.form.requestSubmit() } }} placeholder="描述目标、提出问题，或告诉 Agent 下一步做什么…" required/></label>
            <div className="composer-controls"><label><span className="visually-hidden">投递方式</span><select aria-label="投递方式" value={delivery} onChange={event => setDelivery(event.target.value)}><option value="NORMAL">正常消息</option><option value="STEER">引导当前执行</option><option value="FOLLOW_UP">追加后续</option></select></label><small className="composer-shortcut">Enter 发送 · Shift+Enter 换行</small><button className="primary" type="submit" disabled={disabled || !snapshot || !writer || !draft.trim()}>发送</button></div>
            {attachment && <p>已附加受控产物：<span className="break-all">{attachment}</span><button type="button" onClick={() => setAttachment('')}>移除附件</button></p>}
            {(!snapshot || !writer) && <p className="composer-access-note">{snapshot ? '当前为只读，请先选择“在此继续”。' : '在上方选择或创建会话；输入内容会保留。'}</p>}
          </form>
        <p className="small-muted" role="status" aria-live="polite">{busy ? `${busy}…` : notice}</p>
      </Panel>
      {(snapshot?.pending_permissions || []).map(prompt => <PermissionDecision key={prompt.request.id} prompt={prompt} api={api} projectId={projectId} disabled={disabled || !writer} respond={decision => command('处理授权', async () => { unwrap(await window.researchos.v2['permission.respond']({ resource_request_id: prompt.request.id, resource_request_revision: prompt.request.revision, action_digest: prompt.action_digest, decision, reason: '用户在桌面明确选择' })); await readSnapshot() })}/>)}
      </div>} context={<>
      <ActivityRail events={state.events} snapshot={snapshot} projection={shared?.data?.getProgressProjection} projectState={shared?.data?.getProjectState} releases={shared?.data?.listMilestoneRelease} projectId={projectId} navigate={navigate}/>
      {snapshot?.project_id === projectId && <details className="inspector-disclosure"><summary>目标与双端接续</summary><SessionContinuation key={`${projectId}:${snapshot.session_id}:${snapshot.goal_id || ''}:${snapshot.revision}`} api={api} projectId={projectId} snapshot={snapshot} navigate={navigate}/></details>}
      {snapshot && <details className="inspector-disclosure"><summary>工作区文件与差异</summary><WorkspaceFiles snapshot={snapshot} api={api} projectId={projectId} writer={writer} disabled={disabled} command={command} readSnapshot={readSnapshot} setAttachment={setAttachment} selectedFile={selectedFile} setSelectedFile={setSelectedFile} setFileDirty={setFileDirty}/></details>}
      <details className="inspector-disclosure"><summary>模型运行资格</summary><DesktopQualification key={`${projectId}:${state.snapshot?.session_id || ''}`} projectId={projectId} sessionId={state.snapshot?.session_id || null}/></details>
      <details className="inspector-disclosure"><summary>工作区与编码授权</summary><DesktopCodingAuthorization key={`coding:${projectId}:${state.snapshot?.session_id || ''}`} projectId={projectId}
        sessionId={state.snapshot?.session_id || null} onConfigured={reconcileCodingCommit}/></details>
    </>}/>
  </>
}

function ConversationWelcome({ setDraft, composer }) {
  return <div className="conversation-welcome"><span className="workbench-eyebrow">YOUR NEXT ITERATION</span><h2>让想法，开始迭代。</h2><p>从当前项目出发，一起研究、构建和验证。</p><div className="conversation-starters">{['梳理项目现状与下一步', '检查当前改动并运行必要测试', '继续尚未完成的工作'].map(text => <button type="button" key={text} onClick={() => { setDraft(previous => appendPrompt(previous, text)); composer.current?.focus() }}>{text}</button>)}</div></div>
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

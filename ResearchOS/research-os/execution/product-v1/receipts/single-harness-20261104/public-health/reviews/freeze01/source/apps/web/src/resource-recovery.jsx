import React, { useState } from 'react'
import { itemsOf } from './api'
import { recoverResource } from './resource-recovery.js'

export function ResourceRecovery({ api, projectId, request, onRefresh }) {
  const [open, setOpen] = useState(false), [runtimes, setRuntimes] = useState([])
  const [runtimeId, setRuntimeId] = useState(''), [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [result, setResult] = useState('')
  if (!['OPEN', 'ACKNOWLEDGED'].includes(request.status) || !request.blocked_task_ids?.length) return null
  async function show() {
    setOpen(true); setError(''); setBusy(true)
    try { setRuntimes(itemsOf(await api.call('listRuntimeRegistration', { params: { projectId } }))) }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  async function recover(e) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const resolved = await recoverResource(api, projectId, request, runtimeId, reason)
      setResult(`请求 ${resolved.id} 已解决，宿主已安排从原检查点恢复。任务仍须独立验收。`)
      setOpen(false); onRefresh()
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  return <div>
    <button onClick={show} disabled={busy}>选择已授权运行器恢复</button>
    {result && <p role="status">{result}</p>}
    {open && <form className="inline-form" onSubmit={recover}>
      <label>替代运行器<select required value={runtimeId} onChange={e => setRuntimeId(e.target.value)}>
        <option value="">请选择</option>{runtimes.map(r => <option key={r.id} value={r.id}>{r.name} · {r.status} · {r.measurement_mode}</option>)}
      </select></label>
      <label>恢复原因<input required value={reason} onChange={e => setReason(e.target.value)}/></label>
      <p className="small-muted">宿主将重新检查同用途资格、账户授权和原运行的副作用。缺少任何条件都会保留原请求。</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button disabled={busy || !runtimeId || !reason.trim()}>{busy ? '正在核查…' : '核查并恢复'}</button>
      <button type="button" disabled={busy} onClick={() => setOpen(false)}>取消</button>
    </form>}
  </div>
}

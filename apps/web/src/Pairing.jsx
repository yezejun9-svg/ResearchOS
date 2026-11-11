import React, { useEffect, useRef, useState } from 'react'
import { createApi, etagOf, itemsOf } from './api'

const proofApi = createApi(() => '')
export function useDeviceSession(onToken) {
  const current = useRef(null), pending = useRef(null)
  const [device, setDevice] = useState(null), [error, setError] = useState(''), [renewalPending, setRenewalPending] = useState(false)
  function accept(session) { current.current = session; pending.current = null; setRenewalPending(false); setDevice(session.device); setError(''); onToken(session.access_token) }
  function expire() {
    // Rotation invalidates the old access token before its response arrives.
    // Keep the same refresh attempt until its outcome is known.
    if (pending.current) return
    current.current = null; setRenewalPending(false); setDevice(null); setError('设备会话已过期或被撤销，请在电脑重新配对。'); onToken('')
  }
  useEffect(() => {
    let busy = false, closed = false
    async function renew() {
      const session = current.current
      if (!session || busy || !navigator.onLine || Date.parse(session.access_expires_at) - Date.now() > 60000) return
      busy = true
      pending.current ||= { key: crypto.randomUUID(), body: { refresh_token: session.refresh_token } }
      setRenewalPending(true)
      try { const next = await proofApi.call('refreshDeviceSession', pending.current); if (!closed && current.current === session) accept(next) }
      catch (cause) { if (!closed && current.current === session && [401, 403, 409].includes(cause.status)) { pending.current = null; expire() } }
      finally { busy = false }
    }
    const timer = setInterval(renew, 5000)
    addEventListener('online', renew); document.addEventListener('visibilitychange', renew)
    return () => { closed = true; clearInterval(timer); removeEventListener('online', renew); document.removeEventListener('visibilitychange', renew) }
  }, [])
  return { device, error, renewalPending, accept, expire }
}

function takeChallenge() {
  const fragment = location.hash.slice(1)
  if (location.pathname !== '/pair' || !fragment) return null
  history.replaceState(null, '', location.pathname)
  const split = fragment.split('.')
  return split.length === 2 && /^[a-f0-9]{32}$/.test(split[0]) && /^[a-f0-9]{64}$/.test(split[1]) ? { challenge_id: split[0], pairing_token: split[1] } : null
}

export function PairingGate({ onSession, sessionError }) {
  const [challenge] = useState(takeChallenge), [label, setLabel] = useState('我的手机'), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const attempt = useRef(null)
  async function pair(event) {
    event.preventDefault(); setBusy(true); setError('')
    attempt.current ||= { key: crypto.randomUUID(), body: { ...challenge, device_label: label } }
    try { const session = await proofApi.call('redeemDevicePairing', attempt.current); onSession(session) }
    catch (cause) { setError([401, 409].includes(cause.status) ? '此配对链接已使用、过期或不可重试，请在电脑生成新链接。' : '配对未完成，请检查网络后重试。') }
    finally { setBusy(false) }
  }
  return <div className="auth-wrap"><div className="auth-card"><span className="brandmark">R</span><h1>连接研究电脑</h1><p>用电脑“设置与设备”生成的一次性链接连接。默认只能查看指定项目，电脑可随时撤销。</p>{sessionError && <p role="alert" className="form-error">{sessionError}</p>}{challenge ? <form onSubmit={pair}><label htmlFor="device-label">设备名称</label><input id="device-label" value={label} maxLength={100} onChange={e => { setLabel(e.target.value); attempt.current = null }} disabled={busy} required/><button className="primary" disabled={busy}>{busy ? '正在配对…' : '配对并打开工作台'}</button></form> : <p role="status">请从电脑复制新的配对链接，再在此浏览器打开。</p>}{error && <p role="alert" className="form-error">{error}</p>}<small>会话仅保存在当前页面内存；关闭或刷新页面需要重新配对。网络恢复后会自动对账，不重发控制操作。</small></div></div>
}

export function DevicePanel({ api, projectId, devices, onRefresh }) {
  const [label, setLabel] = useState('我的手机'), [origin, setOrigin] = useState(location.origin), [challenge, setChallenge] = useState(null), [message, setMessage] = useState(''), [busy, setBusy] = useState(false)
  const attempt = useRef(null)
  useEffect(() => { if (!challenge) return; const timer = setTimeout(() => setChallenge(null), Math.max(0, Date.parse(challenge.expires_at) - Date.now())); return () => clearTimeout(timer) }, [challenge])
  async function create(event) {
    event.preventDefault(); setBusy(true); setMessage('')
    try {
      const target = new URL(origin)
      if (target.origin !== origin || (target.protocol !== 'https:' && target.origin !== location.origin)) throw new Error('请填写已审核的完整 HTTPS 入口地址，不含路径。')
      attempt.current ||= { key: crypto.randomUUID(), body: { label, project_ids: [projectId], expires_in_seconds: 300 } }
      const result = await api.call('createDevicePairing', attempt.current)
      setChallenge({ ...result, origin }); attempt.current = null; setMessage('配对链接有效期五分钟，只能使用一次。')
    } catch (cause) { setMessage(cause.message) } finally { setBusy(false) }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(`${challenge.origin}/pair#${challenge.challenge_id}.${challenge.pairing_token}`); setMessage('链接已复制，请仅发给要配对的设备。') }
    catch { setMessage('浏览器未允许剪贴板，请授予此页面剪贴板权限后重试。') }
  }
  async function change(device, operation) {
    setBusy(true); setMessage('')
    try { await api.call(operation, { params: { device_id: device.id }, etag: etagOf(device), body: operation === 'revokeDevice' ? { reason: '用户撤销手机' } : { role: device.role === 'READER' ? 'OWNER' : 'READER', project_ids: device.project_ids, reason: '用户显式调整手机控制权限' } }); onRefresh(); setMessage('设备权限已由服务保存。') }
    catch (cause) { setMessage(cause.message) } finally { setBusy(false) }
  }
  return <div>{itemsOf(devices).map(device => <div className="request-row" key={device.id}><div><strong>{device.label}</strong><p>{device.status === 'REVOKED' ? '已撤销' : device.role === 'READER' ? '只读监督' : '可控制指定项目'}</p></div>{device.status === 'ACTIVE' && <div className="button-row"><button disabled={busy} onClick={() => change(device, 'updateDeviceGrants')}>{device.role === 'READER' ? '允许项目控制' : '改为只读'}</button><button disabled={busy} onClick={() => change(device, 'revokeDevice')}>撤销设备</button></div>}</div>)}<form className="form-grid" onSubmit={create}><label>设备名称<input value={label} maxLength={100} onChange={e => { setLabel(e.target.value); attempt.current = null }} required/></label><label>已审核的手机入口<input type="url" value={origin} onChange={e => setOrigin(e.target.value)} required/></label><button disabled={busy}>生成只读配对链接</button></form>{challenge && <button onClick={copy}>复制配对链接</button>}{message && <p role="status">{message}</p>}<p className="small-muted">新设备仅能查看本项目。允许控制会授予本项目操作权限；配对和全局设置仍由电脑管理。入口尚未审核启用时，请保持本机访问。</p></div>
}

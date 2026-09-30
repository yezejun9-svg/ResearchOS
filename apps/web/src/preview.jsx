import React, { useEffect, useRef, useState } from 'react'

const LIMIT = 5 * 1024 * 1024
const textKinds = /^(text\/|application\/(json|xml|javascript|x-ndjson))/i
const htmlCsp = "default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:; form-action 'none'; base-uri 'none'"

export function ArtifactPreview({ artifact, expectedRef, api, projectId }) {
  const [state, setState] = useState({ status: 'idle' })
  const [downloadError, setDownloadError] = useState('')
  const active = useRef(null)
  const media = (artifact.media_type || 'application/octet-stream').split(';')[0].toLowerCase()
  const size = Number(artifact.byte_size || 0)
  useEffect(() => () => { if (state.url) URL.revokeObjectURL(state.url) }, [state.url])
  useEffect(() => { active.current?.abort(); setState({ status: 'idle' }); setDownloadError(''); return () => active.current?.abort() }, [projectId, artifact.id, artifact.revision, artifact.content_hash, expectedRef?.revision, expectedRef?.content_hash])
  async function load() {
    if (size > LIMIT) { setState({ status: 'oversize' }); return }
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setState({ status: 'loading' })
    try {
      if (expectedRef && (expectedRef.id !== artifact.id || expectedRef.revision !== artifact.revision)) throw new Error('产物修订与固定引用不一致')
      const { blob } = await api.call('getArtifactContent', { params: { projectId, id: artifact.id }, raw: true, signal: controller.signal })
      if (controller.signal.aborted) return
      if (blob.size > LIMIT) { setState({ status: 'oversize' }); return }
      const bytes = await blob.arrayBuffer()
      const digest = await crypto.subtle.digest('SHA-256', bytes)
      if (controller.signal.aborted) return
      const hash = `sha256:${Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('')}`
      if (hash !== artifact.content_hash || (expectedRef?.content_hash && hash !== expectedRef.content_hash)) throw new Error('内容哈希与封存记录不一致')
      const object = new Blob([bytes], { type: media })
      const text = textKinds.test(media) ? await object.text() : null
      if (controller.signal.aborted) return
      setState({ status: 'ready', text, url: URL.createObjectURL(object) })
    } catch (error) { if (!controller.signal.aborted) setState({ status: 'error', message: error.message }) }
  }
  async function download() {
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setDownloadError('')
    try {
      if (expectedRef && (expectedRef.id !== artifact.id || expectedRef.revision !== artifact.revision)) throw new Error('产物修订与固定引用不一致')
      const { blob } = await api.call('getArtifactContent', { params: { projectId, id: artifact.id }, raw: true, signal: controller.signal })
      if (controller.signal.aborted) return
      const bytes = await blob.arrayBuffer()
      const digest = await crypto.subtle.digest('SHA-256', bytes)
      if (controller.signal.aborted) return
      const hash = `sha256:${Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('')}`
      if (hash !== artifact.content_hash || (expectedRef?.content_hash && hash !== expectedRef.content_hash)) throw new Error('下载内容哈希与封存记录不一致')
      const url = URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' }))
      const link = document.createElement('a')
      link.href = url; link.download = `artifact-${artifact.id}`; document.body.appendChild(link); link.click(); link.remove()
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (error) { if (!controller.signal.aborted) setDownloadError(error.message) }
  }
  return <article className="artifact-preview"><div className="artifact-head"><div><strong>{artifact.kind || '产物'}</strong><small>修订 {artifact.revision} · {artifact.validity} · {artifact.evidence_kind} · {artifact.measurement_mode} · 验收状态见关联回执</small><small className="break-all">{artifact.content_hash}</small><small>{media} · {size ? `${Math.ceil(size / 1024)} KiB` : '大小未知'} · {artifact.access_class}</small></div><button onClick={load} disabled={state.status === 'loading'}>{state.status === 'idle' ? '受控预览' : '重新读取'}</button></div>
    {state.status === 'loading' && <p role="status">正在读取并核对哈希…</p>}
    {state.status === 'oversize' && <p className="warning">超过 5 MiB 行内上限；可下载后在受信任的本地应用查看。</p>}
    {state.status === 'error' && <p className="form-error" role="alert">预览失败：{state.message}</p>}
    {(state.status === 'oversize' || state.status === 'error') && <button onClick={download}>受控下载</button>}
    {downloadError && <p className="form-error" role="alert">下载失败：{downloadError}</p>}
    {state.status === 'ready' && <>
      {media === 'text/html' ? <iframe className="preview-frame" title="无脚本 HTML 预览" sandbox="" referrerPolicy="no-referrer" srcDoc={`<meta http-equiv="Content-Security-Policy" content="${htmlCsp}">${state.text}`}/> :
       media.startsWith('image/') ? <img className="preview-image" src={state.url} alt="产物图片预览" onError={() => setState({ status: 'error', message: '图片无法渲染，可下载已封存内容' })}/> :
       media === 'application/pdf' ? <iframe className="preview-frame" title="PDF 预览" sandbox="" src={state.url}/> :
       media === 'text/markdown' ? <MarkdownPreview text={state.text || ''}/> :
       state.text != null ? <pre className="preview-text">{media === 'application/json' ? prettyJson(state.text) : state.text}</pre> : <p>此格式不支持行内预览。</p>}
      <a href={state.url} download={`artifact-${artifact.id}`}>下载已核对的内容</a>
    </>}
  </article>
}
function prettyJson(value) { try { return JSON.stringify(JSON.parse(value), null, 2) } catch { return value } }

function MarkdownPreview({ text }) {
  let code = false
  return <div className="preview-markdown">{text.split(/\r?\n/).map((line, index) => {
    if (line.startsWith('```')) { code = !code; return null }
    if (code) return <pre key={index}>{line}</pre>
    const heading = /^(#{1,4})\s+(.+)$/.exec(line)
    if (heading) return <p key={index} className={`md-heading md-h${heading[1].length}`}>{heading[2]}</p>
    if (/^\s*[-*+]\s+/.test(line)) return <p key={index} className="md-list">{line.replace(/^\s*[-*+]\s+/, '')}</p>
    return <p key={index}>{line || '\u00a0'}</p>
  })}</div>
}

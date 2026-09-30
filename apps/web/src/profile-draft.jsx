import React, { useState } from 'react'
import { classify, etagOf } from './api'

const ref = (value, entity_type) => ({ entity_type, id: value.id, revision: value.revision, content_hash: value.content_hash ?? null })

export function ProfileDraft({ api, projectId, profile }) {
  const [base, setBase] = useState(null)
  const [draft, setDraft] = useState('')
  const [conflict, setConflict] = useState(null)
  const [merged, setMerged] = useState('')
  const [saved, setSaved] = useState([])
  const [proposal, setProposal] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function seal(text, label) {
    const principal = api.principalId()
    if (!principal) throw new Error('服务尚未提供当前身份，草稿仍保留')
    const body = new Blob([JSON.stringify(text)], { type: 'application/json' })
    const upload = await api.call('uploadContent', { params: { projectId }, body })
    const state = await api.call('getProjectState', { params: { projectId } })
    const artifact = await api.call('sealArtifact', { params: { projectId }, etag: etagOf(state), body: {
      run_id: null, kind: 'REPORT', evidence_kind: 'GENERATED', measurement_mode: 'FIXTURE',
      content_hash: upload.content_hash, storage_key: upload.storage_key, byte_size: upload.byte_size,
      media_type: 'application/json', input_refs: [], source_refs: [], produced_by: principal, access_class: 'PROJECT',
    } })
    setSaved(old => [...old.filter(item => item.artifact.id !== artifact.id), { label, artifact }])
    return artifact
  }

  async function submit(merge = false) {
    setBusy(true); setError('')
    const target = merge ? conflict.current : base
    try {
      // Preserve both sides before publishing a deliberately edited merge candidate.
      if (merge) {
        await seal(draft, '原本地草稿')
        await seal(conflict.current.intent, '外部版本')
      }
      const artifact = await seal(merge ? merged : draft, merge ? '合并候选' : '本地候选')
      const state = await api.call('getProjectState', { params: { projectId } })
      const result = await api.call('createChangeProposal', { params: { projectId }, etag: etagOf(state), body: {
        title: merge ? '合并项目背景草稿' : '修订项目背景', reason: '用户编辑 ProjectProfile.intent，封存候选等待独立重验',
        base_state_revision: state.revision,
        edits: [{ target_ref: ref(target, 'ProjectProfile'), field: 'intent', proposed_value_artifact_ref: ref(artifact, 'Artifact'), reason: '用户明确提交的候选文本' }],
        migration_steps: [], test_check_ids: ['context.inputs-frozen', 'context.impact-exact', 'context.authority-independent'],
        rollback_steps: ['提交引用原项目背景的新候选，由独立验收后恢复'],
      } })
      setProposal(result); setConflict(null)
    } catch (cause) {
      setError(cause.status === 403 ? '当前身份没有候选封存权限。草稿仍保留，可导出并交由获授权的执行者封存。' : cause.message)
      if (classify(cause) === 'stale') {
        try {
          const current = await api.call('getProjectProfile', { params: { projectId } })
          setConflict({ current }); setMerged('')
        } catch { setError('版本冲突且外部版本读取失败；本地草稿仍保留，请恢复连接后重新提交。') }
      }
    } finally { setBusy(false) }
  }

  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify({ projectId, base, draft, external: conflict?.current ?? null, merged, candidates: saved }, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a'); link.href = url; link.download = 'researchos-background-drafts.json'; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return <div className="profile-draft">
    <p>编辑项目背景（ProjectProfile.intent）。提交后生成独立封存的 JSON 候选和 ChangeProposal，仍需独立验收；已有产物保持只读。</p>
    {!base ? <button disabled={!profile} onClick={() => { setBase(profile); setDraft(profile.intent) }}>编辑项目背景草稿</button> : <>
      <p className="small-muted">冻结编辑基线：{base.id} · 修订 {base.revision}</p>
      <label>本地背景草稿<textarea value={draft} onChange={event => setDraft(event.target.value)} disabled={busy || !!conflict || !!proposal}/></label>
      {conflict && <div className="state-notice" role="status"><strong>背景版本冲突，请保留双方并显式合并</strong>
        <label>外部背景版本<textarea readOnly value={conflict.current.intent}/></label>
        <p>外部修订 {conflict.current.revision}；不会自动更新旧草稿的基线后重试。</p>
        <label>人工合并后的背景<textarea value={merged} onChange={event => setMerged(event.target.value)} disabled={busy}/></label>
        <button disabled={busy || !merged.trim()} onClick={() => submit(true)}>保存双方并提交合并候选</button>
      </div>}
      {!conflict && !proposal && <button disabled={busy || !draft.trim()} onClick={() => submit()}>封存候选并请求重验</button>}
      <button onClick={download}>导出保留的草稿</button>
      {proposal && <p role="status">候选已提交，等待独立验收。ChangeProposal：<span className="break-all">{proposal.id}</span> · {proposal.status}</p>}
      {saved.length > 0 && <details open><summary>已保存的双方候选</summary>{saved.map(item => <p key={item.artifact.id} className="break-all">{item.label} · {item.artifact.id} · {item.artifact.content_hash}</p>)}</details>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {busy && <p role="status">正在保存候选…</p>}
    </>}
  </div>
}

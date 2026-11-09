import { etagOf } from './api.js'

const ref = (o, kind) => ({ entity_type: kind, id: o.id, revision: o.revision, content_hash: kind === 'Artifact' ? o.content_hash : o.receipt_hash ?? null })

// A sealed instruction goes through the same existing resource-resolution
// transaction as the CLI. The server rechecks the purpose grant and all inputs.
export async function recoverResource(api, projectId, request, runtimeId, reason) {
  const params = { projectId }
  const current = await api.call('getResourceRequest', { params: { ...params, id: request.id } })
  if (current.revision !== request.revision) throw new Error('请求已变化，请重新读取后再恢复')
  if (!['OPEN', 'ACKNOWLEDGED'].includes(current.status)) throw new Error('请求已经关闭')
  const runtime = await api.call('getRuntimeRegistration', { params: { ...params, id: runtimeId } })
  const replacements = [], input_refs = [ref(current, 'ResourceRequest'), ref(runtime, 'RuntimeRegistration')]
  for (const id of current.blocked_task_ids) {
    const task = await api.call('getTask', { params: { ...params, id } })
    if (!task.active_run_id) throw new Error('该任务尚无可恢复运行，请先处理原资源条件')
    const run = await api.call('getRun', { params: { ...params, id: task.active_run_id } })
    replacements.push({ task_ref: ref(task, 'Task'), run_ref: ref(run, 'Run'), runtime_ref: ref(runtime, 'RuntimeRegistration') })
    input_refs.push(ref(task, 'Task'), ref(run, 'Run'))
  }
  if (!replacements.length) throw new Error('该请求没有受阻运行')
  const raw = new Blob([JSON.stringify({ schema: 'researchos.resource-recovery.v1', action: 'SWITCH_RUNTIME', resource_request_ref: ref(current, 'ResourceRequest'), replacements })], { type: 'application/json' })
  const key = crypto.randomUUID()
  const uploaded = await api.call('uploadContent', { params, body: raw, key: `${key}-content` })
  const state = await api.call('getProjectState', { params })
  const principal = api.principalId()
  if (!principal) throw new Error('当前主体未通过宿主鉴别')
  const artifact = await api.call('sealArtifact', { params, etag: etagOf(state), key: `${key}-artifact`, body: {
    run_id: null, kind: 'REPORT', evidence_kind: 'GENERATED', measurement_mode: runtime.measurement_mode,
    content_hash: uploaded.content_hash, storage_key: uploaded.storage_key, media_type: 'application/vnd.researchos.resource-recovery+json', byte_size: raw.size,
    input_refs, source_refs: [], produced_by: principal, access_class: 'PROJECT'
  } })
  return api.call('resolveResourceRequest', { params: { ...params, id: request.id }, etag: etagOf(current), key: `${key}-resolve`, body: {
    resolution_evidence_refs: [ref(artifact, 'Artifact')], reason
  } })
}

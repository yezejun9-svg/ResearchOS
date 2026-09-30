import { useEffect, useState } from 'react'

export function useQueries(api, projectId, requests, revision = 0) {
  const key = JSON.stringify(requests)
  const scope = JSON.stringify([projectId, key])
  const [result, setResult] = useState({ api, scope, loading: true, data: {}, errors: {} })
  useEffect(() => {
    if (!api || !requests.length) { setResult({ api, scope, loading: false, data: {}, errors: {} }); return }
    const controller = new AbortController()
    setResult(old => ({ api, scope, loading: true, data: old.api === api && old.scope === scope ? old.data : {}, errors: {} }))
    Promise.allSettled(requests.map(({ op, id, params, query }) => api.call(op, { params: { projectId, id, ...params }, query, signal: controller.signal }))).then(values => {
      if (controller.signal.aborted) return
      const data = {}, errors = {}
      values.forEach((value, index) => {
        const name = requests[index].as || requests[index].op
        if (value.status === 'fulfilled') data[name] = value.value
        else errors[name] = value.reason
      })
      setResult(old => {
        if (old.api === api && old.scope === scope) {
          for (const [name, value] of Object.entries(data)) {
            const previous = old.data[name]
            if (value?.id && previous?.id === value.id && previous.project_id === value.project_id &&
              ['revision', 'plan_revision', 'as_of_event_sequence'].some(field =>
                Number.isSafeInteger(value[field]) && Number.isSafeInteger(previous[field]) && value[field] < previous[field])) data[name] = previous
          }
        }
        return { api, scope, loading: false, data, errors }
      })
    })
    return () => controller.abort()
  }, [api, projectId, key, revision])
  return result.api === api && result.scope === scope ? result : { loading: true, data: {}, errors: {} }
}

export function useProjectEvents(api, projectId) {
  const [status, setStatus] = useState({ api: null, projectId: null, online: false, lastSync: null, sequence: null, refresh: 0, message: null })
  useEffect(() => {
    if (!api || !projectId) return
    const controller = new AbortController()
    let sequence = null
    let transport = null
    const seen = new Set()
    setStatus({ api, projectId, online: false, lastSync: null, sequence: null, refresh: 0, message: '正在同步快照' })
    const reset = async () => {
      const progress = await api.call('getProgressProjection', { params: { projectId }, signal: controller.signal })
      if (controller.signal.aborted) return
      sequence = Number(progress.as_of_event_sequence)
      seen.clear()
      setStatus(old => ({ ...old, api, projectId, online: true, authExpired: false, lastSync: new Date(), sequence, refresh: old.refresh + 1, message: null }))
    }
    const loop = async () => {
      while (!controller.signal.aborted) {
        if (!navigator.onLine) { await new Promise(resolve => setTimeout(resolve, 1000)); continue }
        const abortTransport = () => transport?.abort()
        try {
          if (sequence === null) await reset()
          if (controller.signal.aborted) break
          transport = new AbortController()
          controller.signal.addEventListener('abort', abortTransport, { once: true })
          let gap = false
          await api.stream(projectId, sequence, event => {
            if (controller.signal.aborted || event.project_id !== projectId || !event.id || seen.has(event.id)) return
            const next = Number(event.sequence)
            if (!Number.isSafeInteger(next) || next <= sequence) return
            if (next !== sequence + 1) { gap = true; return }
            seen.add(event.id)
            if (seen.size > 512) seen.clear()
            sequence = next
            setStatus(old => ({ ...old, online: true, authExpired: false, lastSync: new Date(), sequence, refresh: old.refresh + 1 }))
          }, transport.signal, () => gap, () => {
            if (!controller.signal.aborted) setStatus(old => ({ ...old, online: true, authExpired: false, lastSync: new Date(), message: null, refresh: old.refresh + 1 }))
          })
          if (gap) sequence = null
        } catch (error) {
          if (controller.signal.aborted) break
          if (error.status === 410 || error.code === 'EVENT_GAP') sequence = null
          setStatus(old => ({ ...old, online: false, authExpired: error.status === 401, message: error.status === 410 ? '事件游标过期，正在重取快照' : error.message }))
          await new Promise(resolve => setTimeout(resolve, 2200))
        } finally { controller.signal.removeEventListener('abort', abortTransport) }
      }
    }
    loop()
    const off = () => { transport?.abort(); setStatus(old => ({ ...old, online: false, message: '网络已断开' })) }
    const on = () => setStatus(old => ({ ...old, message: '正在重新连接' }))
    addEventListener('offline', off); addEventListener('online', on)
    return () => { controller.abort(); removeEventListener('offline', off); removeEventListener('online', on) }
  }, [api, projectId])
  return status.api === api && status.projectId === projectId ? status : { api, projectId, online: false, lastSync: null, sequence: null, refresh: 0, message: '正在同步快照' }
}

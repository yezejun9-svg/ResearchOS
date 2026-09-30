import { useEffect, useState } from 'react'

export function useQueries(api, projectId, requests, revision = 0) {
  const key = JSON.stringify(requests)
  const scope = JSON.stringify([projectId, key, revision])
  const [result, setResult] = useState({ scope, loading: true, data: {}, errors: {} })
  useEffect(() => {
    if (!api || !requests.length) { setResult({ scope, loading: false, data: {}, errors: {} }); return }
    const controller = new AbortController()
    setResult({ scope, loading: true, data: {}, errors: {} })
    Promise.allSettled(requests.map(({ op, id, params, query }) => api.call(op, { params: { projectId, id, ...params }, query, signal: controller.signal }))).then(values => {
      if (controller.signal.aborted) return
      const data = {}, errors = {}
      values.forEach((value, index) => {
        const name = requests[index].as || requests[index].op
        if (value.status === 'fulfilled') data[name] = value.value
        else errors[name] = value.reason
      })
      setResult({ scope, loading: false, data, errors })
    })
    return () => controller.abort()
  }, [api, projectId, key, revision])
  return result.scope === scope ? result : { loading: true, data: {}, errors: {} }
}

export function useProjectEvents(api, projectId) {
  const [status, setStatus] = useState({ projectId: null, online: false, lastSync: null, sequence: null, refresh: 0, message: null })
  useEffect(() => {
    if (!api || !projectId) return
    const controller = new AbortController()
    let sequence = null
    const seen = new Set()
    setStatus({ projectId, online: false, lastSync: null, sequence: null, refresh: 0, message: '正在同步快照' })
    const reset = async () => {
      const progress = await api.call('getProgressProjection', { params: { projectId }, signal: controller.signal })
      sequence = Number(progress.as_of_event_sequence)
      seen.clear()
      setStatus(old => ({ ...old, projectId, online: true, lastSync: new Date(), sequence, refresh: old.refresh + 1, message: null }))
    }
    const loop = async () => {
      while (!controller.signal.aborted) {
        try {
          if (sequence === null) await reset()
          let gap = false
          await api.stream(projectId, sequence, event => {
            if (seen.has(event.id)) return
            const next = Number(event.sequence)
            if (!Number.isSafeInteger(next) || next <= sequence) return
            if (next !== sequence + 1) { gap = true; return }
            seen.add(event.id)
            if (seen.size > 512) seen.clear()
            sequence = next
            setStatus(old => ({ ...old, online: true, lastSync: new Date(), sequence, refresh: old.refresh + 1 }))
          }, controller.signal, () => gap)
          if (gap) sequence = null
        } catch (error) {
          if (controller.signal.aborted) break
          if (error.status === 410 || error.code === 'EVENT_GAP') sequence = null
          setStatus(old => ({ ...old, online: false, message: error.status === 410 ? '事件游标过期，正在重取快照' : error.message }))
          await new Promise(resolve => setTimeout(resolve, 2200))
        }
      }
    }
    loop()
    const off = () => setStatus(old => ({ ...old, online: false, message: '网络已断开' }))
    const on = () => setStatus(old => ({ ...old, message: '正在重新连接' }))
    addEventListener('offline', off); addEventListener('online', on)
    return () => { controller.abort(); removeEventListener('offline', off); removeEventListener('online', on) }
  }, [api, projectId])
  return status.projectId === projectId ? status : { projectId, online: false, lastSync: null, sequence: null, refresh: 0, message: '正在同步快照' }
}

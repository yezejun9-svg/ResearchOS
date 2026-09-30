import { operations } from './operations.js'

export class ApiError extends Error {
  constructor(status, detail, operation) {
    super(detail?.message || `HTTP ${status}`)
    this.status = status
    this.code = detail?.code || 'HTTP_ERROR'
    this.correlationId = detail?.correlation_id || null
    this.operation = operation
  }
}

function pathFor(pattern, params) {
  return pattern.replace(/\{([^}]+)\}/g, (_, key) => {
    const value = params[key] ?? (key === 'project_id' ? params.projectId : key === 'object_id' ? params.id : undefined)
    if (value == null || value === '') throw new Error(`缺少路径参数 ${key}`)
    return encodeURIComponent(String(value))
  })
}

export function createApi(getToken) {
  async function call(operation, { params = {}, query, body, signal, etag, key, raw = false } = {}) {
    const spec = operations[operation]
    if (!spec) throw new Error(`未知操作 ${operation}`)
    const url = new URL(pathFor(spec.path, params), window.location.origin)
    if (query) Object.entries(query).forEach(([name, value]) => { if (value != null && value !== '') url.searchParams.set(name, String(value)) })
    const headers = { Authorization: `Bearer ${getToken()}`, Accept: raw ? '*/*' : 'application/json' }
    if (body != null) headers['Content-Type'] = 'application/json'
    if (etag) headers['If-Match'] = etag
    if (spec.method !== 'GET') headers['Idempotency-Key'] = key || crypto.randomUUID()
    const response = await fetch(url, { method: spec.method, headers, body: body == null ? undefined : JSON.stringify(body), signal, cache: 'no-store' })
    if (!response.ok) {
      let detail
      try { detail = await response.json() } catch { detail = null }
      throw new ApiError(response.status, detail, operation)
    }
    if (raw) return { blob: await response.blob(), headers: response.headers, status: response.status }
    return response.status === 204 ? null : response.json()
  }
  async function stream(projectId, afterSequence, onEvent, signal, shouldStop = () => false) {
    const url = new URL(pathFor(operations.streamEvents.path, { projectId }), window.location.origin)
    const headers = { Authorization: `Bearer ${getToken()}`, Accept: 'text/event-stream' }
    if (afterSequence != null) headers['Last-Event-ID'] = String(afterSequence)
    const response = await fetch(url, { headers, signal, cache: 'no-store' })
    if (!response.ok) {
      let detail
      try { detail = await response.json() } catch { detail = null }
      throw new ApiError(response.status, detail, 'streamEvents')
    }
    if (!response.body) throw new Error('事件流不可用')
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    try {
      while (!signal.aborted) {
        const { done, value } = await reader.read()
        if (done) throw new Error('事件流已断开')
        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
        let end
        while ((end = buffer.indexOf('\n\n')) >= 0) {
          const frame = buffer.slice(0, end)
          buffer = buffer.slice(end + 2)
          if (!frame || frame.startsWith(':')) continue
          const lines = frame.split('\n')
          const data = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
          if (!data) continue
          let event
          try { event = JSON.parse(data) } catch { continue }
          onEvent(event)
          if (shouldStop()) throw new ApiError(409, { code: 'EVENT_GAP', message: '事件序号出现缺口' }, 'streamEvents')
        }
      }
    } finally {
      try { await reader.cancel() } catch { /* response already aborted */ }
      reader.releaseLock()
    }
  }
  return { call, stream }
}

export function classify(error) {
  if (error?.name === 'AbortError') return 'aborted'
  if (error?.status === 401) return 'auth'
  if (error?.status === 403) return 'forbidden'
  if (error?.status === 404) return 'missing'
  if (error?.status === 409 || error?.status === 412) return 'stale'
  if (error?.status === 429) return 'limited'
  if (error?.status === 503) return 'unavailable'
  if (!navigator.onLine || error instanceof TypeError) return 'offline'
  return 'error'
}

export function etagOf(object) { return object?.revision ? `"r${object.revision}"` : undefined }
export function itemsOf(page) { return Array.isArray(page?.items) ? page.items : Array.isArray(page) ? page : [] }

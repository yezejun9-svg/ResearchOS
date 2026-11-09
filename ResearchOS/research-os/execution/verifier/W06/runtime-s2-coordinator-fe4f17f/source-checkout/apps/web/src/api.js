import { operations } from './operations.js'

let remoteTransport
async function transportMode() {
  remoteTransport ||= fetch('/remote-info', { cache: 'no-store', signal: AbortSignal.timeout(5000) }).then(response => response.ok && response.headers.get('Content-Type')?.includes('application/json') ? response.json() : null).then(info => info?.events === 'poll' ? 'poll' : 'sse').catch(() => { remoteTransport = null; return location.hostname.endsWith('.trycloudflare.com') ? 'poll' : 'sse' })
  return remoteTransport
}

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
  let principalId = null
  let deviceRole = null
  async function call(operation, { params = {}, query, body, signal, etag, key, raw = false } = {}) {
    const spec = operations[operation]
    if (!spec) throw new Error(`未知操作 ${operation}`)
    const url = new URL(pathFor(spec.path, params), window.location.origin)
    if (query) Object.entries(query).forEach(([name, value]) => { if (value != null && value !== '') url.searchParams.set(name, String(value)) })
    const headers = { Authorization: `Bearer ${getToken()}`, Accept: raw ? '*/*' : 'application/json' }
    if (body != null) headers['Content-Type'] = body instanceof Blob ? 'application/octet-stream' : 'application/json'
    if (etag) headers['If-Match'] = etag
    if (spec.method !== 'GET') headers['Idempotency-Key'] = key || crypto.randomUUID()
    const controller = new AbortController()
    const abort = () => controller.abort(signal.reason)
    if (signal?.aborted) abort()
    else signal?.addEventListener('abort', abort, { once: true })
    let timedOut = false
    const timer = setTimeout(() => { timedOut = true; controller.abort() }, 30000)
    try {
      const response = await fetch(url, { method: spec.method, headers, body: body == null ? undefined : body instanceof Blob ? body : JSON.stringify(body), signal: controller.signal, cache: 'no-store' })
      principalId = response.headers.get('X-ResearchOS-Principal-ID') || principalId
      deviceRole = response.headers.get('X-ResearchOS-Device-Role') || deviceRole
      if (!response.ok) {
        let detail
        try { detail = await response.json() } catch (error) { if (controller.signal.aborted) throw error; detail = null }
        throw new ApiError(response.status, detail, operation)
      }
      if (raw) return { blob: await response.blob(), headers: response.headers, status: response.status }
      return response.status === 204 ? null : await response.json()
    } catch (error) {
      if (timedOut && !signal?.aborted) throw new ApiError(408, { code: 'REQUEST_TIMEOUT', message: '请求超过 30 秒未完成，请检查连接后重试。' }, operation)
      throw error
    } finally {
      clearTimeout(timer)
      signal?.removeEventListener('abort', abort)
    }
  }
  async function stream(projectId, afterSequence, onEvent, signal, shouldStop = () => false, onOpen = () => {}) {
    if (await transportMode() === 'poll') {
      let position = afterSequence ?? 0
      while (!signal.aborted) {
        let cursor = null
        do {
          const page = await call('listEvents', { params: { projectId }, query: { after_sequence: position, limit: 100, cursor }, signal })
          for (const event of page.items || []) {
            onEvent(event)
            if (shouldStop()) throw new ApiError(409, { code: 'EVENT_GAP', message: '事件序号出现缺口' }, 'listEvents')
          }
          cursor = page.next_cursor
          if (!cursor) position = Math.max(position, Number(page.snapshot_event_sequence) || position)
        } while (cursor && !signal.aborted)
        onOpen()
        await new Promise(resolve => { if (signal.aborted) { resolve(); return }; const done = () => { clearTimeout(timer); signal.removeEventListener('abort', done); resolve() }; const timer = setTimeout(done, 2000); signal.addEventListener('abort', done, { once: true }) })
      }
      return
    }
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
    onOpen()
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
  return { call, stream, principalId: () => principalId, deviceRole: () => deviceRole }
}

export function classify(error) {
  if (error?.name === 'AbortError') return 'aborted'
  if (error?.code === 'REQUEST_TIMEOUT') return 'timeout'
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

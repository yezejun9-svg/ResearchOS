'use strict';

const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { PassThrough, Readable } = require('node:stream');

const APP_ORIGIN = 'ros-app://desktop';
const MAX_REQUEST = 8 * 1024 * 1024;
const MAX_RESPONSE = 16 * 1024 * 1024;
const MAX_STREAM = 16 * 1024 * 1024;
const REQUEST_HEADERS = ['accept', 'content-type', 'if-match', 'idempotency-key', 'last-event-id'];
const RESPONSE_HEADERS = ['content-type', 'etag', 'x-researchos-principal-id', 'x-researchos-device-role'];
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };
const CSP = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; object-src 'none'; frame-src 'self' blob: about:; base-uri 'none'; form-action 'self'";

function routeTable(spec) {
  const routes = [];
  for (const [pattern, operations] of Object.entries(spec.paths || {})) {
    if (!pattern.startsWith('/v1/')) continue;
    const escaped = pattern.split('/').map(part => part.startsWith('{') && part.endsWith('}')
      ? '[A-Za-z0-9._~-]{1,256}' : part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('/');
    for (const method of ['get', 'post', 'put', 'patch', 'delete']) {
      if (operations[method]) routes.push({ method: method.toUpperCase(), pattern, test: new RegExp('^' + escaped + '$') });
    }
  }
  return routes;
}

function allowedRoute(routes, method, pathname) {
  if (!['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].includes(method) ||
      /%(?:2f|5c|00|2e)/i.test(pathname) || pathname.includes('\\') || pathname.includes('//')) return false;
  return routes.some(route => route.method === method && route.test.test(pathname));
}

function copyHeaders(input, names) {
  const out = {};
  for (const name of names) {
    const value = input.get ? input.get(name) : input[name];
    if (typeof value === 'string' && value.length <= 4096 && !/[\r\n]/.test(value)) out[name] = value;
  }
  return out;
}

async function boundedBody(request) {
  if (request.method === 'GET' || request.method === 'HEAD') return Buffer.alloc(0);
  const length = Number(request.headers.get('content-length'));
  if (Number.isFinite(length) && length > MAX_REQUEST) throw Error('REQUEST_TOO_LARGE');
  if (!request.body) return Buffer.alloc(0);
  const parts = [];
  let total = 0;
  for await (const chunk of request.body) {
    const part = Buffer.from(chunk);
    total += part.length;
    if (total > MAX_REQUEST) throw Error('REQUEST_TOO_LARGE');
    parts.push(part);
  }
  return Buffer.concat(parts, total);
}

function requestCore(target, method, headers, body, signal) {
  return new Promise((resolve, reject) => {
    const req = http.request(target, { method, agent: false, timeout: target.pathname.endsWith('/events/stream') ? 0 : 30000,
      headers: { ...headers, 'content-length': body.length } }, res => {
      res.once('close', () => signal?.removeEventListener('abort', abort));
      resolve({ req, res });
    });
    const abort = () => req.destroy(Error('REQUEST_ABORTED'));
    signal?.addEventListener('abort', abort, { once: true });
    req.on('error', error => { signal?.removeEventListener('abort', abort); reject(error); });
    req.on('timeout', () => req.destroy(Error('CORE_TIMEOUT')));
    req.end(body);
  });
}

function responseFromCore(res, isStream) {
  if (res.statusCode >= 300 && res.statusCode < 400) {
    res.resume();
    return new Response('UPSTREAM_REDIRECT_REFUSED', { status: 502 });
  }
  const headers = copyHeaders(res.headers, RESPONSE_HEADERS);
  headers['cache-control'] = 'no-store';
  if (res.statusCode === 204 || res.statusCode === 205) {
    res.resume();
    return new Response(null, { status: res.statusCode, headers });
  }
  const sink = new PassThrough();
  let seen = 0;
  res.on('data', chunk => {
    seen += chunk.length;
    if (seen > (isStream ? MAX_STREAM : MAX_RESPONSE)) {
      res.destroy(Error('RESPONSE_TOO_LARGE'));
      sink.destroy(Error('RESPONSE_TOO_LARGE'));
      return;
    }
    if (!sink.write(chunk)) res.pause();
  });
  sink.on('drain', () => res.resume());
  sink.on('close', () => { if (!res.destroyed) res.destroy(); });
  res.on('end', () => sink.end());
  res.on('error', error => sink.destroy(error));
  res.on('close', () => { if (!res.complete) sink.destroy(Error('CORE_STREAM_CLOSED')); });
  return new Response(Readable.toWeb(sink), { status: res.statusCode, headers });
}

function staticResponse(dist, pathname) {
  let decoded;
  try { decoded = decodeURIComponent(pathname); } catch { return new Response('Bad path', { status: 400 }); }
  if (decoded.includes('\\') || decoded.includes('\0') || decoded.split('/').includes('..')) return new Response('Bad path', { status: 400 });
  const root = path.resolve(dist);
  const target = path.resolve(root, '.' + decoded);
  if (target !== root && !target.startsWith(root + path.sep)) return new Response('Bad path', { status: 400 });
  let file = target;
  try {
    if (!fs.statSync(file).isFile()) file = '';
  } catch { file = ''; }
  if (!file) {
    if (path.extname(decoded)) return new Response('Asset not found', { status: 404 });
    file = path.join(root, 'index.html');
  }
  try {
    const realRoot = fs.realpathSync(root);
    const realFile = fs.realpathSync(file);
    if (!realFile.startsWith(realRoot + path.sep) || !fs.statSync(realFile).isFile()) return new Response('Asset not allowed', { status: 403 });
    if (fs.statSync(realFile).size > MAX_RESPONSE) return new Response('Asset too large', { status: 413 });
    const bytes = fs.readFileSync(realFile);
    return new Response(bytes, { status: 200, headers: { 'content-type': MIME[path.extname(file)] || 'application/octet-stream', 'content-security-policy': CSP, 'x-content-type-options': 'nosniff', 'cache-control': 'no-store' } });
  } catch { return new Response('Web build unavailable', { status: 503 }); }
}

function createAppProtocol({ dist, routes, ensureCore, credentialFor }) {
  return async request => {
    const url = new URL(request.url);
    if (url.protocol !== 'ros-app:' || url.hostname !== 'desktop' || url.port || url.username || url.password || url.hash) return new Response('Forbidden origin', { status: 403 });
    if (!url.pathname.startsWith('/v1/')) {
      if (request.method !== 'GET') return new Response('Method not allowed', { status: 405 });
      return staticResponse(dist, url.pathname);
    }
    if (!allowedRoute(routes, request.method, url.pathname)) return new Response('Route not allowed', { status: 404 });
    let body;
    try { body = await boundedBody(request); } catch { return new Response('Request too large', { status: 413 }); }
    const started = await ensureCore();
    if (!started.discovery) return new Response('Host unavailable', { status: 503 });
    const target = new URL(url.pathname + url.search, started.discovery.url);
    if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(target.hostname)) return new Response('Nonlocal host', { status: 502 });
    const headers = copyHeaders(request.headers, REQUEST_HEADERS);
    let credential;
    try { credential = await credentialFor(started.discovery); }
    catch { return new Response('Host credential unavailable', { status: 503 }); }
    const isStream = url.pathname.endsWith('/events/stream');
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const { res } = await requestCore(target, request.method, { ...headers, authorization: 'Bearer ' + credential }, body, request.signal);
        if (res.statusCode === 401 && attempt === 0) {
          res.resume();
          const renewed = await credentialFor(started.discovery, true);
          if (request.method !== 'GET') {
            return Response.json({ code: 'AUTH_REFRESHED_RETRY_REQUIRED',
              message: '身份已刷新。请先核对操作结果，再决定是否重新提交。' }, { status: 401 });
          }
          credential = renewed;
          continue;
        }
        return responseFromCore(res, isStream);
      } catch { return new Response('Host request failed', { status: 502 }); }
    }
    return new Response('Host authentication failed', { status: 401 });
  };
}

module.exports = { APP_ORIGIN, MAX_REQUEST, MAX_RESPONSE, routeTable, allowedRoute, boundedBody, staticResponse, createAppProtocol };

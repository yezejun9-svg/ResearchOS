// W13-01 host and client routing for the ResearchOS desktop shell.
//
// This module is deliberately Electron-free and dependency-free so its behaviour can be exercised by a
// plain node process (tests/ui/check drives it with a fake core and a fake spawn). It carries the two
// properties the card's negatives name: a first-run user must never be told to open a terminal or copy an
// owner token, and a provider call that did not succeed must never be rendered as a success. Every decision
// here is a pure function of its injected dependencies, so a check can prove the branch is reachable instead
// of asserting a shape.
'use strict';

const fs = require('node:fs');
const http = require('node:http');

// The four native clients the card names, each with the methods the first-run flow needs. A client with no
// entry here is a hole in the workbench, so the route table is the assertion target rather than prose.
const ROUTES = {
  status: { health: ['GET', '/healthz'], host: ['GET', '/host/status'] },
  workspace: { list: ['GET', '/workspaces'], register: ['POST', '/workspaces'], pick_directory: ['POST', '/workspaces/pick'] },
  session: { list: ['GET', '/sessions'], create: ['POST', '/sessions'], send: ['POST', '/sessions/send'] },
  provider: { models: ['GET', '/provider/models'], configure: ['POST', '/provider/configure'], probe: ['POST', '/provider/probe'] },
};

const CLIENTS = Object.keys(ROUTES).sort();

// Discovery of the existing Go control host: the same file the thin main already reads. No second scheduler.
function readDiscovery(fsImpl, file) {
  try {
    const d = JSON.parse(fsImpl.readFileSync(file, 'utf8'));
    if (!d || typeof d.url !== 'string' || !d.url) return { ok: false, reason: 'DISCOVERY_MALFORMED', detail: String(d && d.url) };
    return { ok: true, discovery: d };
  } catch (e) {
    return { ok: false, reason: 'DISCOVERY_ABSENT', detail: String(e.code || e.message || e) };
  }
}

function probe(httpImpl, url, pathName, timeoutMs) {
  return new Promise((resolve) => {
    const t0 = Date.now();
    const req = httpImpl.get(url + pathName, { timeout: timeoutMs || 4000, agent: false }, (res) => {
      let body = '';
      res.on('data', (c) => { body += c; });
      res.on('end', () => resolve({ status: res.statusCode, body, ms: Date.now() - t0 }));
    });
    req.on('error', (e) => resolve({ status: 0, error: String(e.code || e.message || e), ms: Date.now() - t0 }));
    req.on('timeout', () => { req.destroy(); resolve({ status: 0, error: 'TIMEOUT', ms: Date.now() - t0 }); });
  });
}

// Start the local core only when it is genuinely not reachable, and never ask the user to do it by hand.
// launched/attempt_spawns are returned so a check can prove the branch taken, not the branch intended.
async function ensureCore(deps) {
  const { fsImpl, httpImpl, spawnImpl, discoveryFile, coreArgv, retries, waitMs } = deps;
  const attempts = [];
  let disc = readDiscovery(fsImpl, discoveryFile);
  if (disc.ok) {
    const p = await probe(httpImpl, disc.discovery.url, ROUTES.status.health[1], waitMs);
    attempts.push({ phase: 'probe_existing', status: p.status });
    if (p.status === 200) {
      return { health: 'UP', launched: false, spawns: 0, discovery: disc.discovery, attempts };
    }
  }
  if (deps.requireLaunchDisabled) {
    return { health: disc.ok ? 'DOWN_NO_LAUNCH' : 'NOT_FOUND_NO_LAUNCH', launched: false, spawns: 0, discovery: disc.ok ? disc.discovery : null, attempts };
  }
  const spawned = spawnImpl(coreArgv[0], coreArgv.slice(1));
  let launched = { ok: !!spawned, pid: spawned && spawned.pid };
  attempts.push({ phase: 'spawn', ok: launched.ok });
  const out = { health: 'LAUNCH_FAILED', launched: launched.ok, spawns: launched.ok ? 1 : 0, discovery: null, attempts, launch_error: launched.ok ? null : 'spawn returned nothing' };
  if (!launched.ok) return out;
  const tries = retries === undefined ? 6 : retries;
  for (let i = 0; i < tries; i++) {
    await deps.sleep(waitMs || 400);
    const d2 = readDiscovery(fsImpl, discoveryFile);
    if (!d2.ok) { attempts.push({ phase: 'await_discovery', status: 0, reason: d2.reason }); continue; }
    const p = await probe(httpImpl, d2.discovery.url, ROUTES.status.health[1], waitMs);
    attempts.push({ phase: 'probe_after_launch', status: p.status });
    if (p.status === 200) {
      return { health: 'UP', launched: true, spawns: 1, discovery: d2.discovery, attempts };
    }
  }
  return { health: 'UP_AFTER_RETRIES_FAILED', launched: true, spawns: 1, discovery: null, attempts };
}

// The principal is read from the local store the host already owns. A value is never pasted into a request
// body and never returned to the renderer, which is what makes "copy the owner token" impossible rather than
// merely discouraged.
function principalFor(fsImpl, storeFile) {
  try {
    const raw = JSON.parse(fsImpl.readFileSync(storeFile, 'utf8'));
    if (!raw || typeof raw.principal_id !== 'string' || !raw.principal_id) return { ok: false, reason: 'PRINCIPAL_STORE_MALFORMED' };
    return { ok: true, principal_id: raw.principal_id };
  } catch (e) {
    return { ok: false, reason: 'PRINCIPAL_STORE_ABSENT', detail: String(e.code || e.message || e) };
  }
}

function requestFor(client, method, body, principal) {
  const routes = ROUTES[client];
  if (!routes) return { ok: false, reason: 'UNKNOWN_CLIENT', client };
  const r = routes[method];
  if (!r) return { ok: false, reason: 'UNKNOWN_METHOD', client, method };
  // The payload carries only what the host needs; a token field is structurally impossible here because no
  // dependency injects one, and the principal travels as a header the caller cannot override.
  const payload = Object.assign({}, body || {});
  delete payload.token;
  delete payload.owner_token;
  return { ok: true, verb: r[0], path: r[1], payload, headers: { 'X-ResearchOS-Principal': principal } };
}

// A provider result is a success only when the host says it is. Anything else is surfaced as a failure with
// the host reason kept, because a shell that paints a degraded probe green is the cards second negative.
function classifyProvider(result) {
  if (!result || typeof result !== 'object') return { ok: false, reason: 'NO_REPLY' };
  if (result.error) return { ok: false, reason: 'TRANSPORT', detail: String(result.error) };
  const st = result.status;
  if (st === 'OK' && result.degraded !== true) return { ok: true, reason: 'OK' };
  if (st === 'OK' && result.degraded === true) return { ok: false, reason: 'DEGRADED_NOT_SUCCESS' };
  if (st === 'AUTH_REQUIRED') return { ok: false, reason: 'AUTH_REQUIRED' };
  if (st === 'RATE_LIMITED') return { ok: false, reason: 'RATE_LIMITED' };
  if (st === 'UNSUPPORTED') return { ok: false, reason: 'UNSUPPORTED_MODEL' };
  return { ok: false, reason: 'PROVIDER_' + String(st || 'UNKNOWN') };
}

function emptyState(projects) {
  const n = Array.isArray(projects) ? projects.length : 0;
  if (n > 0) return { kind: 'HAS_PROJECTS', count: n, actions: ['open', 'new_session'] };
  return { kind: 'FIRST_RUN', count: 0, actions: ['pick_directory', 'configure_provider', 'new_session'], requires_terminal: false, requires_token_copy: false };
}

module.exports = { ROUTES, CLIENTS, readDiscovery, probe, ensureCore, principalFor, requestFor, classifyProvider, emptyState };

// W13-01 IPC surface: one registration function that turns the routed clients in host.js into real
// desktop-prototype channels, and the single source of truth for what the preload bridge may expose.
//
// It takes ipcMain and its collaborators as arguments instead of requiring electron, so the check program can
// register the whole surface against a recorder and prove which channels exist, whether the core is started
// on demand, and that a provider that did not succeed is reported as a failure rather than painted green.
'use strict';

const host = require('./host.js');

// The names the renderer may call. The preload file is checked against this list by tests/ui/check, so a
// channel added here without a bridge entry, or a bridge entry added without a handler, fails the suite.
const BRIDGE = [
  'statusHealth', 'statusHost',
  'workspaceList', 'workspaceRegister', 'workspacePickDirectory',
  'sessionList', 'sessionCreate', 'sessionSend',
  'providerModels', 'providerConfigure', 'providerProbe',
];

// method -> bridge name, mirroring ROUTES so one table drives both
const CHANNELS = {
  statusHealth: ['status', 'health'], statusHost: ['status', 'host'],
  workspaceList: ['workspace', 'list'], workspaceRegister: ['workspace', 'register'],
  workspacePickDirectory: ['workspace', 'pick_directory'],
  sessionList: ['session', 'list'], sessionCreate: ['session', 'create'], sessionSend: ['session', 'send'],
  providerModels: ['provider', 'models'], providerConfigure: ['provider', 'configure'],
  providerProbe: ['provider', 'probe'],
};

// Every client call begins by making sure a core is reachable, because the card promises install-and-run:
// the shell starts the local control host itself rather than telling the user to open a terminal.
async function callCore(deps, client, method, body) {
  const started = await host.ensureCore(deps);
  if (!started.discovery) {
    return { ok: false, reason: started.health, launched: started.launched, attempts: started.attempts.length };
  }
  const principal = host.principalFor(deps.fsImpl, deps.principalFile);
  if (!principal.ok) return { ok: false, reason: principal.reason, detail: principal.detail || null };
  const req = host.requestFor(client, method, body, principal.principal_id);
  if (!req.ok) return { ok: false, reason: req.reason, client, method };
  const reply = await deps.transport(req.verb, started.discovery.url + req.path, req.payload, req.headers);
  if (client === 'provider' && method === 'probe') {
    const cls = host.classifyProvider(reply);
    return Object.assign({}, reply, cls);
  }
  if (reply && (reply.error || reply.status === 'ERROR')) {
    return Object.assign({ ok: false, reason: 'HOST_ERROR' }, reply);
  }
  return Object.assign({ ok: true }, reply);
}

function register(ipcMain, deps) {
  const registered = [];
  Object.keys(CHANNELS).forEach((name) => {
    const route = CHANNELS[name];
    ipcMain.handle('ros:' + name, async (_event, body) => callCore(deps, route[0], route[1], body));
    registered.push(name);
  });
  return registered;
}

module.exports = { BRIDGE, CHANNELS, callCore, register };

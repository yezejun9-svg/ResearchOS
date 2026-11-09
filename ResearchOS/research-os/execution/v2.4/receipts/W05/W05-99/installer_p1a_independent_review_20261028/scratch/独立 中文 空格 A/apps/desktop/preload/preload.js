// Constrained preload: exposes exactly the bridge channels named in main/lib/ipc.js, one function each.
// No generic invoke, no require, no fs/shell/http surface, and no path by which a token could be pasted in:
// the principal is read from the local store inside the main process and never crosses this boundary.
//
// W13-02 adds the client-protocol surface as a nested `v2` namespace keyed by the published method names. It is a
// second list rather than a merged one because the accepted W13-01 surface is measured as exactly eleven flat
// channels; the method names below are compared against main/lib/ipc.js's V2_METHODS by this card's check, so a
// channel added here without a handler, or a handler with no bridge, fails by name.
const { contextBridge, ipcRenderer } = require('electron');

const CHANNELS = ['statusHealth', 'statusHost',
  'workspaceList', 'workspaceRegister', 'workspacePickDirectory',
  'sessionList', 'sessionCreate', 'sessionSend',
  'providerModels', 'providerConfigure', 'providerProbe'];

// The frozen local_protocol.methods list, spelled exactly as the protocol spells it.
const V2_METHODS = ['artifact.import', 'goal.start', 'host.configure', 'host.status', 'permission.respond',
  'project.bootstrap', 'provider.models', 'provider.probe', 'session.attach', 'session.control', 'session.create',
  'session.events', 'session.get', 'session.handoff', 'session.list', 'session.send', 'session.update',
  'workspace.diff', 'workspace.list', 'workspace.read', 'workspace.register', 'workspace.tree', 'workspace.write'];

const api = {};
for (const name of CHANNELS) {
  api[name] = (body) => ipcRenderer.invoke('ros:' + name, body);
}

const v2api = {};
for (const method of V2_METHODS) {
  v2api[method] = (body) => ipcRenderer.invoke('ros:v2:' + method, body);
}
api.v2 = Object.freeze(v2api);
api.desktop = Object.freeze({
  context: () => ipcRenderer.invoke('ros:desktop:context'),
  selectProject: (projectId) => ipcRenderer.invoke('ros:desktop:selectProject', { project_id: projectId }),
  openSession: (sessionId) => ipcRenderer.invoke('ros:desktop:openSession', { session_id: sessionId }),
  readArtifact: (ref) => ipcRenderer.invoke('ros:desktop:readArtifact', ref),
  chooseWorkspace: (body) => ipcRenderer.invoke('ros:desktop:chooseWorkspace', body),
  qualificationCurrent: () => ipcRenderer.invoke('ros:desktop:qualification:current'),
  qualificationPrepare: () => ipcRenderer.invoke('ros:desktop:qualification:prepare'),
  qualificationConfirm: () => ipcRenderer.invoke('ros:desktop:qualification:confirm'),
  qualificationStatus: () => ipcRenderer.invoke('ros:desktop:qualification:status'),
  codingCurrent: () => ipcRenderer.invoke('ros:desktop:coding:current'),
  codingPickToolchain: () => ipcRenderer.invoke('ros:desktop:coding:pickToolchain'),
  codingPickVendor: () => ipcRenderer.invoke('ros:desktop:coding:pickVendor'),
  codingPrepare: (intent) => ipcRenderer.invoke('ros:desktop:coding:prepare', intent),
  codingConfirm: () => ipcRenderer.invoke('ros:desktop:coding:confirm'),
  codingStatus: () => ipcRenderer.invoke('ros:desktop:coding:status'),
});

contextBridge.exposeInMainWorld('researchos', Object.freeze(api));

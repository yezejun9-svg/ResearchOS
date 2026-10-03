// Constrained preload: exposes exactly the bridge channels named in main/lib/ipc.js, one function each.
// No generic invoke, no require, no fs/shell/http surface, and no path by which a token could be pasted in:
// the principal is read from the local store inside the main process and never crosses this boundary.
const { contextBridge, ipcRenderer } = require('electron');

const CHANNELS = ['statusHealth', 'statusHost',
  'workspaceList', 'workspaceRegister', 'workspacePickDirectory',
  'sessionList', 'sessionCreate', 'sessionSend',
  'providerModels', 'providerConfigure', 'providerProbe'];

const api = {};
for (const name of CHANNELS) {
  api[name] = (body) => ipcRenderer.invoke('ros:' + name, body);
}

contextBridge.exposeInMainWorld('researchos', Object.freeze(api));

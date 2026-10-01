// Constrained preload: exposes ONLY the host-status read. No generic fs/shell/http surface.
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('researchos', {
  hostStatus: () => ipcRenderer.invoke('ros:host-status'),
});

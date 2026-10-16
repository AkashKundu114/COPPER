const { contextBridge, ipcRenderer } = require("electron");


const ALLOWED_INVOKE_CHANNELS = [
  "quick-bar-hide",
  "quick-bar-resize",
  "quick-bar-focus-main",
  "get-backend-status",
  "start-backend",
  "stop-backend",
  "get-accessibility-status",
  "get-activation-status",
  "activate-local-gpu",
  "activate-owner-code",
  "get-system-info",
  "run-setup-wizard",
];

const copperAPI = {
  invoke: (channel, ...args) => {
    if (ALLOWED_INVOKE_CHANNELS.includes(channel)) {
      return ipcRenderer.invoke(channel, ...args);
    }
    return Promise.reject(new Error(`Unauthorized IPC channel: ${channel}`));
  },
  hideQuickBar: () => ipcRenderer.invoke("quick-bar-hide"),
  resizeQuickBar: (height) => {
    const clampedHeight = Math.min(Math.max(Number(height) || 72, 72), 600);
    return ipcRenderer.invoke("quick-bar-resize", clampedHeight);
  },
  focusMain: () => ipcRenderer.invoke("quick-bar-focus-main"),
  getBackendStatus: () => ipcRenderer.invoke("get-backend-status"),
  startBackend: () => ipcRenderer.invoke("start-backend"),
  stopBackend: () => ipcRenderer.invoke("stop-backend"),
  getAccessibilityStatus: () => ipcRenderer.invoke("get-accessibility-status"),
};


contextBridge.exposeInMainWorld("copperAPI", copperAPI);


contextBridge.exposeInMainWorld("ipcRenderer", {
  invoke: (channel, ...args) => copperAPI.invoke(channel, ...args),
});

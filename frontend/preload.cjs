const { contextBridge, ipcRenderer } = require("electron");

/**
 * COPPER Electron Secure Preload Script
 * 
 * Enforces Context Isolation and Principle of Least Privilege:
 * - Exposes only an explicit whitelist of validated IPC invocations to the renderer.
 * - Prevents raw Node.js execution or arbitrary child process spawning in the browser context.
 */

const ALLOWED_INVOKE_CHANNELS = [
  "quick-bar-hide",
  "quick-bar-resize",
  "quick-bar-focus-main",
  "get-backend-status",
  "start-backend",
  "stop-backend",
  "get-accessibility-status",
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

// Expose secure API to window.copperAPI
contextBridge.exposeInMainWorld("copperAPI", copperAPI);

// Expose sanitized fallback for window.ipcRenderer
contextBridge.exposeInMainWorld("ipcRenderer", {
  invoke: (channel, ...args) => copperAPI.invoke(channel, ...args),
});

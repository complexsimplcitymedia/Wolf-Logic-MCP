import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuration
  getConfig: (key: string) => ipcRenderer.invoke('get-config', key),
  setConfig: (key: string, value: any) => ipcRenderer.invoke('set-config', key, value),
  getAllConfig: () => ipcRenderer.invoke('get-all-config'),
  
  // System info
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  
  // Dependencies
  installDependencies: () => ipcRenderer.invoke('install-dependencies'),
  
  // Health check
  healthCheck: (serverUrl: string) => ipcRenderer.invoke('health-check', serverUrl),
  
  // Event listeners
  onNavigateTo: (callback: (page: string) => void) => {
    ipcRenderer.on('navigate-to', (event, page) => callback(page));
  },
  
  onShowAbout: (callback: () => void) => {
    ipcRenderer.on('show-about', () => callback());
  },
  
  onUpdateAvailable: (callback: () => void) => {
    ipcRenderer.on('update-available', () => callback());
  },
  
  onUpdateDownloaded: (callback: () => void) => {
    ipcRenderer.on('update-downloaded', () => callback());
  }
});

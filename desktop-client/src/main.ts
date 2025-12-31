import { app, BrowserWindow, ipcMain, Menu, shell } from 'electron';
import { autoUpdater } from 'electron-updater';
import Store from 'electron-store';
import * as path from 'path';
import * as os from 'os';

// Initialize configuration store
const store = new Store({
  defaults: {
    serverUrl: 'http://100.110.82.181:8002',
    authentikUrl: 'http://100.110.82.181:9001',
    apiKey: '',
    username: '',
    windowBounds: { width: 1200, height: 800 }
  }
});

let mainWindow: BrowserWindow | null = null;

function createWindow(): void {
  const bounds = store.get('windowBounds') as { width: number; height: number };
  
  mainWindow = new BrowserWindow({
    width: bounds.width,
    height: bounds.height,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    title: 'Wolf Logic MCP'
  });

  // Load the app
  if (app.isPackaged) {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  } else {
    // In development, you might want to load from a dev server
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // Save window bounds on close
  mainWindow.on('close', () => {
    if (mainWindow) {
      store.set('windowBounds', mainWindow.getBounds());
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  createMenu();
}

function createMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('navigate-to', 'settings');
            }
          }
        },
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            await shell.openExternal('https://github.com/complexsimplcitymedia/Wolf-Logic-MCP');
          }
        },
        {
          label: 'About',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('show-about');
            }
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC Handlers for configuration
ipcMain.handle('get-config', (event, key: string) => {
  return store.get(key);
});

ipcMain.handle('set-config', (event, key: string, value: any) => {
  store.set(key, value);
  return true;
});

ipcMain.handle('get-all-config', () => {
  return store.store;
});

ipcMain.handle('get-system-info', () => {
  return {
    platform: process.platform,
    arch: process.arch,
    version: app.getVersion(),
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node,
    osVersion: os.release(),
    hostname: os.hostname()
  };
});

// Check for updates
function checkForUpdates(): void {
  if (!app.isPackaged) {
    console.log('Skipping auto-update in development');
    return;
  }

  autoUpdater.checkForUpdatesAndNotify();

  autoUpdater.on('update-available', () => {
    if (mainWindow) {
      mainWindow.webContents.send('update-available');
    }
  });

  autoUpdater.on('update-downloaded', () => {
    if (mainWindow) {
      mainWindow.webContents.send('update-downloaded');
    }
  });
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();
  checkForUpdates();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle install dependencies request
ipcMain.handle('install-dependencies', async () => {
  // This would trigger a separate process to install Python, Ollama, etc.
  // For now, return a placeholder
  return {
    success: true,
    message: 'Dependency installation requires elevated privileges. Please run the installer script.'
  };
});

// Health check
ipcMain.handle('health-check', async (event, serverUrl: string) => {
  try {
    // In a real implementation, use node-fetch or similar to check server health
    return {
      success: true,
      status: 'Server connection not yet implemented',
      serverUrl
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
});

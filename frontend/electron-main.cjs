const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

let mainWindow = null;
let backendProcess = null;

function getPythonExecutable(rootDir) {
  const candidates = [
    path.join(rootDir, ".venv", "Scripts", "python.exe"),
    path.join(rootDir, "venv", "Scripts", "python.exe"),
    path.join(rootDir, ".venv", "bin", "python"),
    path.join(rootDir, "venv", "bin", "python"),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return "python";
}

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

function configureAutoStart() {
  if (process.platform === "win32") {
    app.setLoginItemSettings({
      openAtLogin: true,
      openAsHidden: false,
      path: process.execPath,
      args: ["--autostart"],
    });
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 860,
    minWidth: 1024,
    minHeight: 700,
    show: false,
    backgroundColor: "#020617",
    autoHideMenuBar: true,
    titleBarStyle: "hidden",
    titleBarOverlay: {
      color: "rgba(0,0,0,0)",
      symbolColor: "#8B8D93",
      height: 56,
    },
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webviewTag: false,
      spellcheck: false,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (
      url.startsWith("http://localhost") ||
      url.startsWith("http://127.0.0.1")
    ) {
      mainWindow.loadURL(url);
    }
    return { action: "deny" };
  });

  mainWindow.webContents.on("will-navigate", (event, url) => {
    const isLocal =
      url.startsWith("http://localhost") ||
      url.startsWith("http://127.0.0.1") ||
      url.startsWith("file://");
    if (!isLocal) {
      event.preventDefault(); // Block external URL navigation completely
    }
  });

  const isDev = process.env.NODE_ENV === "development" || !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
  } else {
    mainWindow.loadFile(path.join(__dirname, "dist", "index.html"));
  }

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

const net = require("net");

function isPortOpen(port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(400);
    socket.on("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("timeout", () => {
      socket.destroy();
      resolve(false);
    });
    socket.on("error", () => {
      socket.destroy();
      resolve(false);
    });
    socket.connect(port, "127.0.0.1");
  });
}

async function startBackend() {
  const open = await isPortOpen(8000);
  if (open) return true;

  const rootDir = path.resolve(__dirname, "..");

  try {
    const pythonExec = getPythonExecutable(rootDir);

    backendProcess = spawn(
      pythonExec,
      [
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
      ],
      {
        cwd: rootDir,
        detached: true,
        stdio: "ignore",
        shell: false,
      },
    );
    backendProcess.on("error", (err) => {
      console.error("Backend process error:", err);
      backendProcess = null;
    });
    backendProcess.on("exit", () => {
      backendProcess = null;
    });
    backendProcess.unref();
    return true;
  } catch (err) {
    console.error("Failed to spawn background backend process:", err);
    return false;
  }
}

async function stopBackend() {
  if (backendProcess) {
    try {
      if (process.platform === "win32") {
        spawn("taskkill", ["/pid", backendProcess.pid, "/f", "/t"]);
      } else {
        backendProcess.kill();
      }
    } catch (err) {
      console.error("Failed to stop backend:", err);
    }
    backendProcess = null;
  }

  if (process.platform === "win32") {
    try {
      const { execSync } = require("child_process");
      const cmd = `powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"`;
      execSync(cmd, { stdio: "ignore" });
    } catch {}
  }
  return true;
}

ipcMain.handle("get-backend-status", async () => {
  if (backendProcess !== null && !backendProcess.killed) return true;
  return await isPortOpen(8000);
});

ipcMain.handle("start-backend", async () => await startBackend());
ipcMain.handle("stop-backend", async () => await stopBackend());

app.whenReady().then(() => {
  configureAutoStart();
  createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("will-quit", () => {
  stopBackend();
});

app.on("window-all-closed", function () {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

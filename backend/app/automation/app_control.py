import os
import subprocess
import platform
from typing import Optional
from app.core.logger import logger

OS = platform.system()

APP_MAP = {
    "browser": {
        "Windows": ["chrome", "msedge", "firefox"],
        "Linux": ["google-chrome", "firefox", "chromium-browser"],
        "Darwin": ["open -a 'Google Chrome'", "open -a Firefox"],
    },
    "terminal": {
        "Windows": ["wt", "cmd", "powershell"],
        "Linux": ["gnome-terminal", "xterm", "konsole"],
        "Darwin": ["open -a Terminal"],
    },
    "editor": {
        "Windows": ["code", "notepad++", "notepad"],
        "Linux": ["code", "gedit", "nano"],
        "Darwin": ["open -a 'Visual Studio Code'"],
    },
    "file_manager": {
        "Windows": ["explorer"],
        "Linux": ["nautilus", "thunar", "dolphin"],
        "Darwin": ["open -a Finder"],
    },
}


async def launch_app(app_name: str, args: list[str] = None) -> bool:
    try:
        cmd = [app_name] + (args or [])
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Launched app: {app_name}")
        return True
    except FileNotFoundError:
        logger.warning(f"App not found: {app_name}")
        return False
    except Exception as e:
        logger.error(f"Launch app error: {e}")
        return False


async def launch_by_category(category: str, args: list[str] = None) -> bool:
    candidates = APP_MAP.get(category, {}).get(OS, [])
    for app in candidates:
        if await launch_app(app, args):
            return True
    logger.warning(f"No app found for category '{category}' on {OS}")
    return False


async def launch_url(url: str) -> bool:
    try:
        import webbrowser
        webbrowser.open(url)
        logger.info(f"Opened URL: {url}")
        return True
    except Exception as e:
        logger.error(f"Launch URL error: {e}")
        return False


async def focus_window(title: str) -> bool:
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title)
        if windows:
            windows[0].activate()
            return True
        return False
    except Exception as e:
        logger.error(f"Focus window error: {e}")
        return False


async def close_window(title: str) -> bool:
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title)
        if windows:
            windows[0].close()
            return True
        return False
    except Exception as e:
        logger.error(f"Close window error: {e}")
        return False


async def list_open_windows() -> list[str]:
    try:
        import pygetwindow as gw
        return [w.title for w in gw.getAllWindows() if w.title.strip()]
    except Exception:
        return []

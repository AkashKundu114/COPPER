import asyncio
import ctypes
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import psutil

from app.core.logger import logger


@dataclass
class ActivityEntry:
    timestamp: datetime
    app_name: str
    window_title: str
    duration_seconds: float = 5.0


@dataclass
class ActivitySession:
    app_name: str
    window_title: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float


class ContextWatcher:
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.poll_interval = 5.0
        self.buffer_size = 2000
        self.buffer: List[ActivityEntry] = []
        self._unflushed: List[ActivityEntry] = []

        self.db_path = os.path.join(os.path.dirname(__file__), "ambient_history.db")
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        app_name TEXT,
                        window_title TEXT,
                        duration_seconds REAL
                    )
                """
                )
        except Exception as e:
            logger.error(f"Failed to initialize ContextWatcher DB: {e}")

    def start(self):
        if not self.is_running:
            self.is_running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._watch_loop())
                logger.info("Context Watcher started.")
            except RuntimeError:
                logger.warning("Context Watcher could not start: no running event loop.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self._task:
                self._task.cancel()
            self._flush_to_db()
            logger.info("Context Watcher stopped.")

    def get_current_context(self) -> Optional[ActivityEntry]:
        try:
            if os.name != "nt":
                return None

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            window_title = buf.value

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            try:
                process = psutil.Process(pid.value)
                app_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown"

            return ActivityEntry(
                timestamp=datetime.now(),
                app_name=app_name,
                window_title=window_title,
                duration_seconds=self.poll_interval,
            )
        except Exception as e:
            logger.debug(f"Context watcher platform error: {e}")
            return None

    async def _watch_loop(self):
        flush_interval = 60
        last_flush = time.time()

        while self.is_running:
            try:
                entry = self.get_current_context()
                if entry:
                    self.buffer.append(entry)
                    self._unflushed.append(entry)
                    if len(self.buffer) > self.buffer_size:
                        self.buffer.pop(0)

                now = time.time()
                if now - last_flush > flush_interval:
                    self._flush_to_db()
                    last_flush = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Context watcher loop error: {e}")

            await asyncio.sleep(self.poll_interval)

    def _flush_to_db(self):
        if not self._unflushed:
            return

        entries = self._unflushed[:]
        self._unflushed.clear()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "INSERT INTO activity_log (timestamp, app_name, window_title, duration_seconds) VALUES (?, ?, ?, ?)",
                    [(e.timestamp.isoformat(), e.app_name, e.window_title, e.duration_seconds) for e in entries],
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to flush ContextWatcher DB: {e}")
            self._unflushed.extend(entries)

    def get_timeline(self, hours: int = 24) -> List[ActivityEntry]:
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.buffer if e.timestamp >= cutoff]

    def get_sessions(self, hours: int = 24) -> List[ActivitySession]:
        entries = self.get_timeline(hours)
        if not entries:
            return []

        sessions = []
        current_app = entries[0].app_name
        session_start = entries[0].timestamp
        last_time = entries[0].timestamp
        titles_in_session = [entries[0].window_title]

        gap_threshold = timedelta(seconds=30)

        for i in range(1, len(entries)):
            e = entries[i]

            if (e.timestamp - last_time > gap_threshold) or (e.app_name != current_app):
                end_time = last_time + timedelta(seconds=self.poll_interval)
                duration_mins = (end_time - session_start).total_seconds() / 60.0

                most_common_title = max(set(titles_in_session), key=titles_in_session.count)

                sessions.append(
                    ActivitySession(
                        app_name=current_app,
                        window_title=most_common_title,
                        start_time=session_start,
                        end_time=end_time,
                        duration_minutes=duration_mins,
                    )
                )

                current_app = e.app_name
                session_start = e.timestamp
                titles_in_session = [e.window_title]
            else:
                titles_in_session.append(e.window_title)

            last_time = e.timestamp

        end_time = last_time + timedelta(seconds=self.poll_interval)
        duration_mins = (end_time - session_start).total_seconds() / 60.0
        most_common_title = max(set(titles_in_session), key=titles_in_session.count)
        sessions.append(
            ActivitySession(
                app_name=current_app,
                window_title=most_common_title,
                start_time=session_start,
                end_time=end_time,
                duration_minutes=duration_mins,
            )
        )

        return sessions

    def get_app_usage_stats(self, hours: int = 24) -> Dict[str, float]:
        sessions = self.get_sessions(hours)
        stats: Dict[str, float] = {}
        for s in sessions:
            stats[s.app_name] = stats.get(s.app_name, 0.0) + s.duration_minutes
        return stats


context_watcher = ContextWatcher()

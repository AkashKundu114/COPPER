import asyncio
import ctypes
import json
import re
import sys
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Optional

from app.core.logger import logger


@dataclass
class ClipboardEntry:
    id: str
    timestamp: datetime
    content: str
    content_type: str
    content_preview: str
    processed: bool = False
    processing_result: Optional[dict] = None


class ClipboardMonitor:
    def __init__(self):
        self.history: Deque[ClipboardEntry] = deque(maxlen=200)
        self.is_running = False
        self._task = None
        self._last_sequence_number = 0
        self.is_windows = sys.platform == "win32"

    def detect_type(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "plain_text"

        # URL
        if re.match(r"^(https?://|www\.)[^\s/$.?#].[^\s]*$", text, re.IGNORECASE) or \
           re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?$", text):
            return "url"

        # Error Message
        error_keywords = ["error", "exception", "traceback", "failed", "stack trace", "fatal"]
        lower_text = text.lower()
        if any(kw in lower_text for kw in error_keywords) and \
           ("line " in lower_text or "file " in lower_text or " at " in lower_text):
            return "error_message"

        # Email
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", text):
            return "email"
        if "From:" in text and "To:" in text and "Subject:" in text:
            return "email"

        # JSON
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                json.loads(text)
                return "json"
            except ValueError:
                pass

        # File Path
        if re.match(r"^[a-zA-Z]:\\[^*|\"<>?]*$", text) or \
           re.match(r"^/[a-zA-Z0-9_.-]+(/[a-zA-Z0-9_.-]+)*$", text):
            return "file_path"

        # Code
        code_patterns = [
            r"def\s+\w+\s*\(", r"class\s+\w+", r"function\s+\w+\s*\(",
            r"import\s+[\w\.]+", r"#include\s+<.*>", r"console\.log",
            r"=>", r"public\s+class", r"func\s+\w+\s*\("
        ]
        if any(re.search(pattern, text) for pattern in code_patterns) or \
           ("{" in text and "}" in text and ";" in text):
            return "code"

        return "plain_text"

    def _get_clipboard_text(self) -> str:
        if not self.is_windows:
            return ""

        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            user32.OpenClipboard(0)

            # CF_UNICODETEXT = 13
            if user32.IsClipboardFormatAvailable(13):
                handle = user32.GetClipboardData(13)
                if handle:
                    ptr = kernel32.GlobalLock(handle)
                    text = ctypes.c_wchar_p(ptr).value
                    kernel32.GlobalUnlock(handle)
                    user32.CloseClipboard()
                    return text or ""
            user32.CloseClipboard()
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
        return ""

    async def _monitor_loop(self):
        if not self.is_windows:
            logger.info("Clipboard monitor is only supported on Windows")
            return

        user32 = ctypes.windll.user32

        logger.info("Starting clipboard monitor")
        while self.is_running:
            try:
                # Check sequence number to see if clipboard changed
                seq_num = user32.GetClipboardSequenceNumber()

                if seq_num != self._last_sequence_number and self._last_sequence_number != 0:
                    text = self._get_clipboard_text()

                    if text:
                        entry = ClipboardEntry(
                            id=uuid.uuid4().hex,
                            timestamp=datetime.utcnow(),
                            content=text,
                            content_type=self.detect_type(text),
                            content_preview=text[:200]
                        )
                        self.history.appendleft(entry)
                        logger.debug(f"New clipboard entry detected: {entry.content_type}")

                self._last_sequence_number = seq_num
            except Exception as e:
                logger.error(f"Error in clipboard monitor loop: {e}")

            await asyncio.sleep(1.0)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._monitor_loop())

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None


clipboard_monitor = ClipboardMonitor()

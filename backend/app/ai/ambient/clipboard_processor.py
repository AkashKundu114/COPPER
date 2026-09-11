import json
import os
import re
from urllib.parse import urlparse

from app.ai.ambient.clipboard_monitor import ClipboardEntry
from app.core.logger import logger


class ClipboardProcessor:
    def process_entry(self, entry: ClipboardEntry) -> dict:
        content = entry.content.strip()
        analysis = {}
        suggested_actions = []

        try:
            if entry.content_type == "url":
                if not content.startswith("http"):
                    content = "https://" + content
                parsed = urlparse(content)
                domain = parsed.netloc
                path_parts = [p for p in parsed.path.split("/") if p]
                title_guess = path_parts[-1].replace("-", " ").title() if path_parts else domain

                analysis = {
                    "domain": domain,
                    "title_guess": title_guess,
                    "tags": ["reference"]
                }
                suggested_actions = ["Open in browser", "Save to bookmarks", "Summarize page"]

            elif entry.content_type == "code":
                lines = content.splitlines()
                lang = "unknown"
                if re.search(r"def\s+\w+\s*\(|import\s+[\w\.]+", content):
                    lang = "Python"
                elif re.search(r"console\.log|=>|function\s+\w+\s*\(", content):
                    lang = "JavaScript/TypeScript"
                elif re.search(r"public\s+class|System\.out\.println", content):
                    lang = "Java"
                elif re.search(r"#include\s+<.*>|std::", content):
                    lang = "C++"
                elif re.search(r"func\s+\w+\s*\(", content):
                    lang = "Go"
                elif re.search(r"fn\s+\w+\s*\(|let\s+mut", content):
                    lang = "Rust"

                is_function = "def " in content or "function " in content or "func " in content or "fn " in content
                is_class = "class " in content

                analysis = {
                    "language": lang,
                    "line_count": len(lines),
                    "is_function": is_function,
                    "is_class": is_class,
                    "is_snippet": not (is_function or is_class)
                }
                suggested_actions = ["Analyze code", "Find bugs", "Explain code"]

            elif entry.content_type == "error_message":
                error_type = "unknown"
                match = re.search(r"([A-Za-z]+Error|[A-Za-z]+Exception)", content)
                if match:
                    error_type = match.group(1)

                file_ref = None
                file_match = re.search(r"File\s+\"([^\"]+)\",\s+line\s+(\d+)", content)
                if file_match:
                    file_ref = f"{file_match.group(1)}:{file_match.group(2)}"

                analysis = {
                    "error_type": error_type,
                    "file_reference": file_ref
                }
                suggested_actions = ["Search for fix", "Explain error", "Debug"]

            elif entry.content_type == "json":
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        analysis = {
                            "type": "object",
                            "top_level_keys": list(data.keys()),
                            "key_count": len(data.keys())
                        }
                    elif isinstance(data, list):
                        analysis = {
                            "type": "array",
                            "length": len(data)
                        }
                    else:
                        analysis = {"type": type(data).__name__}
                except Exception:
                    analysis = {"error": "Invalid JSON"}

                suggested_actions = ["Format JSON", "Extract fields"]

            elif entry.content_type == "email":
                sender_match = re.search(r"From:\s*([^\n]+)", content)
                subject_match = re.search(r"Subject:\s*([^\n]+)", content)

                analysis = {
                    "sender": sender_match.group(1).strip() if sender_match else None,
                    "subject": subject_match.group(1).strip() if subject_match else None
                }
                suggested_actions = ["Draft reply", "Summarize email", "Extract action items"]

            elif entry.content_type == "file_path":
                # Remove quotes if present
                path = content.strip("\"'")
                exists = os.path.exists(path)

                analysis = {
                    "path": path,
                    "exists": exists
                }
                if exists:
                    analysis["is_file"] = os.path.isfile(path)
                    analysis["is_dir"] = os.path.isdir(path)
                    if os.path.isfile(path):
                        analysis["size_bytes"] = os.path.getsize(path)
                        _, ext = os.path.splitext(path)
                        analysis["extension"] = ext

                suggested_actions = ["Open file", "Show in explorer", "Read contents"]

            else:  # plain_text
                words = len(content.split())
                sentences = len(re.split(r'[.!?]+', content)) - 1
                is_question = "?" in content

                analysis = {
                    "word_count": words,
                    "sentence_count": sentences,
                    "is_question": is_question
                }
                suggested_actions = ["Summarize", "Translate", "Answer question" if is_question else "Rewrite"]

        except Exception as e:
            logger.error(f"Error processing clipboard entry {entry.id}: {e}")
            analysis = {"error": str(e)}

        # Check cognitive load state to protect deep focus flow
        from app.ai.ambient.cognitive_load import cognitive_load_detector, CognitiveState
        is_deep_focus = cognitive_load_detector.current_state == CognitiveState.DEEP_FOCUS

        result = {
            "type": entry.content_type,
            "analysis": analysis,
            "suggested_actions": suggested_actions,
            "suppressed_for_focus": is_deep_focus,
            "notifications_suppressed": is_deep_focus,
        }

        entry.processed = True
        entry.processing_result = result
        if is_deep_focus:
            logger.info(f"[ClipboardProcessor] Cognitive load is DEEP_FOCUS. Suppressed toast notifications for entry {entry.id}")
        return result


clipboard_processor = ClipboardProcessor()

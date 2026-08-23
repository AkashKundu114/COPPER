import csv
import io
import json
from pathlib import Path
from typing import Any

from app.ai.memory.memory_manager import memory_manager
from app.core.document_indexer import chunk_text
from app.core.logger import logger


class DocumentService:
    """
    Robust Document Parser, Extractor, and Reader Service for C.O.P.P.E.R.
    Supports PDF (with multi-page extraction), CSV/TSV tables, JSON, Markdown, Code, and Text.
    """

    SUPPORTED_EXTENSIONS = {
        "pdf": "PDF Document",
        "txt": "Plain Text",
        "md": "Markdown Document",
        "csv": "Comma-Separated Values",
        "tsv": "Tab-Separated Values",
        "json": "JSON Data",
        "py": "Python Source",
        "js": "JavaScript Source",
        "ts": "TypeScript Source",
        "tsx": "React TypeScript Source",
        "jsx": "React JavaScript Source",
        "html": "HTML Document",
        "css": "CSS Stylesheet",
        "sql": "SQL Database Script",
        "yaml": "YAML Configuration",
        "yml": "YAML Configuration",
        "xml": "XML Data",
        "log": "System Log",
        "env": "Environment Config",
        "sh": "Shell Script",
        "bat": "Batch Script",
        "ps1": "PowerShell Script",
        "rs": "Rust Source",
        "go": "Go Source",
        "java": "Java Source",
        "c": "C Source",
        "cpp": "C++ Source",
        "h": "C/C++ Header",
        "hpp": "C++ Header",
    }

    def format_file_size(self, size_bytes: int) -> str:
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        if size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes} B"

    async def parse_document(self, file_bytes: bytes, filename: str, index_to_memory: bool = True) -> dict[str, Any]:
        ext = Path(filename).suffix.lstrip(".").lower()
        size_bytes = len(file_bytes)
        size_formatted = self.format_file_size(size_bytes)
        file_category = self.SUPPORTED_EXTENSIONS.get(ext, f".{ext.upper()} File")

        pages: list[dict[str, Any]] = []
        full_text = ""
        structured_data: Any = None
        error_msg: str | None = None

        if ext == "pdf":
            pages, full_text, error_msg = self._parse_pdf(file_bytes)
        elif ext in ["csv", "tsv"]:
            delimiter = "," if ext == "csv" else "\t"
            pages, full_text, structured_data, error_msg = self._parse_delimited(file_bytes, delimiter)
        elif ext == "json":
            pages, full_text, structured_data, error_msg = self._parse_json(file_bytes)
        else:
            pages, full_text, error_msg = self._parse_text(file_bytes)

        lines = full_text.splitlines()
        words = full_text.split()
        word_count = len(words)
        char_count = len(full_text)
        estimated_tokens = max(1, int(char_count / 4))

        preview_lines = lines[:100]
        preview_text = "\n".join(preview_lines)
        if len(lines) > 100:
            preview_text += f"\n\n[... {len(lines) - 100} more lines in full document ({size_formatted}) ...]"

        indexed_chunks = 0
        if index_to_memory and full_text.strip():
            try:
                chunks = chunk_text(full_text)
                for i, chunk in enumerate(chunks):
                    await memory_manager.save_document(
                        content=chunk,
                        source=filename,
                        metadata={
                            "filename": filename,
                            "extension": ext,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "word_count": word_count,
                        },
                    )
                indexed_chunks = len(chunks)
                logger.info(f"Indexed uploaded document '{filename}' ({indexed_chunks} chunks)")
            except Exception as e:
                logger.warning(f"Failed to vector-index document '{filename}': {e}")

        return {
            "filename": filename,
            "extension": ext,
            "category": file_category,
            "size_bytes": size_bytes,
            "size_formatted": size_formatted,
            "page_count": len(pages),
            "line_count": len(lines),
            "word_count": word_count,
            "char_count": char_count,
            "estimated_tokens": estimated_tokens,
            "indexed_chunks": indexed_chunks,
            "pages": pages,
            "full_text": full_text,
            "preview_text": preview_text,
            "structured_data": structured_data,
            "error": error_msg,
            "status": "success" if not error_msg else "partial",
        }

    def _parse_pdf(self, file_bytes: bytes) -> tuple[list[dict[str, Any]], str, str | None]:
        pages = []
        full_text_parts = []
        error = None

        try:
            import pypdf

            stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(stream)
            total_pages = len(reader.pages)

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                clean_text = page_text.strip()
                page_words = len(clean_text.split())
                pages.append(
                    {
                        "page_number": idx + 1,
                        "text": clean_text,
                        "word_count": page_words,
                        "char_count": len(clean_text),
                    }
                )
                if clean_text:
                    full_text_parts.append(f"--- [Page {idx + 1} of {total_pages}] ---\n{clean_text}")

            full_text = "\n\n".join(full_text_parts)
            return pages, full_text, None
        except Exception as e:
            logger.warning(f"pypdf failed to parse PDF: {e}")
            error = str(e)

        try:
            import pymupdf

            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            total_pages = len(doc)
            pages = []
            full_text_parts = []

            for idx, page in enumerate(doc):
                text = page.get_text() or ""
                clean_text = text.strip()
                pages.append(
                    {
                        "page_number": idx + 1,
                        "text": clean_text,
                        "word_count": len(clean_text.split()),
                        "char_count": len(clean_text),
                    }
                )
                if clean_text:
                    full_text_parts.append(f"--- [Page {idx + 1} of {total_pages}] ---\n{clean_text}")

            full_text = "\n\n".join(full_text_parts)
            return pages, full_text, None
        except Exception as e2:
            logger.error(f"pymupdf also failed on PDF: {e2}")
            return [], "", f"Could not parse PDF: {error or e2}"

    def _parse_delimited(
        self, file_bytes: bytes, delimiter: str = ","
    ) -> tuple[list[dict[str, Any]], str, Any, str | None]:
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            rows = list(reader)
            if not rows:
                return [], "", {"headers": [], "rows": [], "total_rows": 0}, None

            headers = rows[0]
            data_rows = rows[1:]
            preview_rows = data_rows[:50]

            structured = {
                "headers": headers,
                "preview_rows": preview_rows,
                "total_rows": len(data_rows),
                "column_count": len(headers),
            }

            pages = [
                {
                    "page_number": 1,
                    "text": text,
                    "word_count": len(text.split()),
                    "char_count": len(text),
                }
            ]
            return pages, text, structured, None
        except Exception as e:
            logger.error(f"CSV/TSV parse error: {e}")
            return [], "", None, str(e)

    def _parse_json(self, file_bytes: bytes) -> tuple[list[dict[str, Any]], str, Any, str | None]:
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            parsed_json = json.loads(text)
            formatted_text = json.dumps(parsed_json, indent=2)

            top_level_keys = list(parsed_json.keys()) if isinstance(parsed_json, dict) else []
            item_count = len(parsed_json) if isinstance(parsed_json, (dict, list)) else 1

            structured = {
                "is_array": isinstance(parsed_json, list),
                "is_object": isinstance(parsed_json, dict),
                "top_level_keys": top_level_keys[:30],
                "item_count": item_count,
            }

            pages = [
                {
                    "page_number": 1,
                    "text": formatted_text,
                    "word_count": len(formatted_text.split()),
                    "char_count": len(formatted_text),
                }
            ]
            return pages, formatted_text, structured, None
        except Exception as e:
            text = file_bytes.decode("utf-8", errors="replace")
            return (
                [{"page_number": 1, "text": text, "word_count": len(text.split()), "char_count": len(text)}],
                text,
                None,
                f"Invalid JSON: {e}",
            )

    def _parse_text(self, file_bytes: bytes) -> tuple[list[dict[str, Any]], str, str | None]:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("latin-1")
            except Exception as e:
                return [], "", f"Could not decode text file: {e}"

        pages = [
            {
                "page_number": 1,
                "text": text,
                "word_count": len(text.split()),
                "char_count": len(text),
            }
        ]
        return pages, text, None


document_service = DocumentService()

import os
from pathlib import Path

from app.ai.memory.memory_manager import memory_manager
from app.core.logger import logger

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

async def index_file(filepath: str):
    ext = Path(filepath).suffix.lower()
    text = ""
    try:
        if ext in [".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".html"]:
            with open(filepath, encoding="utf-8") as f:
                text = f.read()
        elif ext == ".pdf":
            try:
                import pypdf

                with open(filepath, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except ImportError:
                logger.error("pypdf not installed, cannot index PDF.")
                return
        else:
            return 

        if not text.strip():
            return

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            await memory_manager.save_document(
                content=chunk,
                source=filepath,
                metadata={"chunk_index": i, "total_chunks": len(chunks), "filename": Path(filepath).name},
            )
        logger.info(f"Indexed {filepath} ({len(chunks)} chunks)")

    except Exception as e:
        logger.error(f"Failed to index {filepath}: {e}")

async def index_directory(directory_path: str, extensions: list[str] = None):
    if not extensions:
        extensions = [".txt", ".md", ".pdf"]

    logger.info(f"Starting index of directory: {directory_path}")
    count = 0
    for root, _, files in os.walk(directory_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                await index_file(filepath)
                count += 1
    logger.info(f"Finished indexing {count} files in {directory_path}")
    return count

import os
import shutil
import glob
from pathlib import Path
from typing import Optional
from app.core.logger import logger


async def list_directory(path: str, pattern: str = "*") -> list[dict]:
    try:
        p = Path(path)
        if not p.exists():
            return []
        entries = []
        for item in p.glob(pattern):
            stat = item.stat()
            entries.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size_bytes": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
            })
        return sorted(entries, key=lambda x: (not x["is_dir"], x["name"].lower()))
    except Exception as e:
        logger.error(f"List directory error: {e}")
        return []


async def create_directory(path: str) -> bool:
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Create directory error: {e}")
        return False


async def copy_file(src: str, dst: str) -> bool:
    try:
        shutil.copy2(src, dst)
        logger.info(f"Copied {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"Copy file error: {e}")
        return False


async def move_file(src: str, dst: str) -> bool:
    try:
        shutil.move(src, dst)
        logger.info(f"Moved {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"Move file error: {e}")
        return False


async def delete_file(path: str, safe: bool = True) -> bool:
    try:
        p = Path(path)
        if safe:
            # Move to temp trash instead of permanent delete
            import tempfile
            trash = Path(tempfile.gettempdir()) / "copper_trash"
            trash.mkdir(exist_ok=True)
            shutil.move(path, trash / p.name)
            logger.info(f"Moved to trash: {path}")
        else:
            if p.is_dir():
                shutil.rmtree(path)
            else:
                p.unlink()
            logger.info(f"Deleted: {path}")
        return True
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return False


async def rename_file(path: str, new_name: str) -> bool:
    try:
        p = Path(path)
        new_path = p.parent / new_name
        p.rename(new_path)
        logger.info(f"Renamed {path} -> {new_path}")
        return True
    except Exception as e:
        logger.error(f"Rename file error: {e}")
        return False


async def search_files(directory: str, pattern: str, recursive: bool = True) -> list[str]:
    try:
        p = Path(directory)
        if recursive:
            matches = list(p.rglob(pattern))
        else:
            matches = list(p.glob(pattern))
        return [str(m) for m in matches[:100]]
    except Exception as e:
        logger.error(f"Search files error: {e}")
        return []


async def read_text_file(path: str) -> Optional[str]:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Read file error: {e}")
        return None


async def write_text_file(path: str, content: str) -> bool:
    try:
        Path(path).write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"Write file error: {e}")
        return False


async def get_file_info(path: str) -> Optional[dict]:
    try:
        p = Path(path)
        if not p.exists():
            return None
        stat = p.stat()
        return {
            "name": p.name,
            "path": str(p.resolve()),
            "extension": p.suffix,
            "size_bytes": stat.st_size,
            "is_dir": p.is_dir(),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }
    except Exception as e:
        logger.error(f"Get file info error: {e}")
        return None

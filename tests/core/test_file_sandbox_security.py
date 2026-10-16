import tempfile
from pathlib import Path

import pytest

from app.ai.ambient.code_review_agent import _sanitize_git_ref
from app.ai.tools.builtin.file_tools import (
    file_list,
    file_read,
    file_search,
    file_write,
    validate_safe_path,
)


def test_validate_safe_path_blocks_secrets_and_traversal():
    safe, p, err = validate_safe_path(".env")
    assert safe is False
    assert "sensitive credential" in err.lower() or "denied" in err.lower()

    safe, p, err = validate_safe_path("~/.ssh/id_rsa")
    assert safe is False
    assert "access denied" in err.lower()

    safe, p, err = validate_safe_path("C:/Windows/System32/cmd.exe")
    assert safe is False
    assert "protected system directory" in err.lower() or "outside permitted" in err.lower()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "safe_notes.txt"
        safe, p, err = validate_safe_path(tmp_file, allow_nonexistent=True)
        assert safe is True
        assert p is not None
        assert err is None


@pytest.mark.asyncio
async def test_file_read_and_write_sandbox_confinement():
    res_read = await file_read(path="C:/Windows/win.ini")
    assert res_read["status"] == "error"
    assert "access denied" in res_read["error"].lower()

    res_write = await file_write(path="C:/Windows/System32/evil.bat", content="malicious")
    assert res_write["status"] == "error"
    assert "access denied" in res_write["error"].lower()

    res_list = await file_list(directory="C:/Windows")
    assert res_list["status"] == "error"
    assert "access denied" in res_list["error"].lower()

    res_search = await file_search(query="secret", directory="C:/Windows")
    assert res_search["status"] == "error"
    assert "access denied" in res_search["error"].lower()


def test_sanitize_git_ref_prevents_flag_injection():
    with pytest.raises(ValueError, match="Invalid git reference"):
        _sanitize_git_ref("--output=/tmp/evil")

    with pytest.raises(ValueError, match="Invalid git reference"):
        _sanitize_git_ref("-o")

    with pytest.raises(ValueError, match="Invalid git reference format"):
        _sanitize_git_ref("main; rm -rf /")

    with pytest.raises(ValueError, match="Invalid git reference format"):
        _sanitize_git_ref("feature/$(whoami)")

    assert _sanitize_git_ref("main") == "main"
    assert _sanitize_git_ref("feat/voice-v3") == "feat/voice-v3"
    assert _sanitize_git_ref("HEAD~1") == "HEAD~1"
    assert _sanitize_git_ref("e6c38cd") == "e6c38cd"

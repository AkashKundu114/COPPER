import os
import tempfile
from pathlib import Path
import pytest

from app.ai.tools.builtin.file_tools import file_list, file_read, file_write
from app.ai.tools.builtin.shell_tools import python_execute, shell_execute
from app.ai.tools.builtin.memory_tools import memory_query, memory_store
from app.ai.tools.builtin.calendar_tools import calendar_create, reminder_set
from app.ai.tools.builtin.web_tools import web_search


@pytest.mark.asyncio
async def test_file_tools_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_artifact.txt"

        # 1. Write
        write_res = await file_write(path=str(test_file), content="Hello COPPER tool execution!")
        assert write_res["status"] == "success"
        assert write_res["bytes_written"] > 0

        # 2. Read
        read_res = await file_read(path=str(test_file))
        assert read_res["status"] == "success"
        assert "Hello COPPER tool execution!" in read_res["content"]

        # 3. List
        list_res = await file_list(directory=tmpdir, pattern="*.txt")
        assert list_res["status"] == "success"
        assert list_res["total_matches"] == 1
        assert list_res["entries"][0]["name"] == "test_artifact.txt"


@pytest.mark.asyncio
async def test_python_execute_sandbox():
    code = "x = 40 + 2\nprint(f'Answer={x}')"
    res = await python_execute(code=code, timeout=5)
    assert res["status"] == "success"
    assert "Answer=42" in res["stdout"]
    assert res["exit_code"] == 0


@pytest.mark.asyncio
async def test_shell_execute():
    cmd = "Write-Output 'PowerShell Hello'"
    res = await shell_execute(command=cmd, timeout=5)
    assert res["status"] == "success"
    assert "PowerShell Hello" in res["output"]


@pytest.mark.asyncio
async def test_memory_tools():
    # Store
    store_res = await memory_store(content="User prefers Python over JavaScript", memory_type="preference", confidence=0.95)
    assert store_res["status"] == "success"
    assert "memory_id" in store_res

    # Query
    query_res = await memory_query(query="Python preference", limit=3)
    assert query_res["status"] == "success"
    assert isinstance(query_res["memories"], list)


@pytest.mark.asyncio
async def test_calendar_and_reminder_tools():
    # Calendar create
    cal_res = await calendar_create(title="Architecture Sync", datetime="tomorrow 2pm", duration_minutes=45)
    assert cal_res["status"] == "success"
    assert "evt_" in cal_res["event_id"]

    # Reminder set
    rem_res = await reminder_set(time="15 minutes", message="Check build pipeline", priority="high")
    assert rem_res["status"] == "success"
    assert "rem_" in rem_res["reminder_id"]


@pytest.mark.asyncio
async def test_web_search_resilience():
    res = await web_search(query="Python asyncio documentation", num_results=2)
    assert res["status"] in ["success", "partial"]
    assert "query" in res

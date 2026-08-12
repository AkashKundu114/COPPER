import pytest
from app.core.self_healing import resilient_call, ResilientResult

@pytest.mark.asyncio
async def test_resilient_primary_success():
    async def primary():
        return "success"
    
    result = await resilient_call(primary)
    assert result.success is True
    assert result.result == "success"
    assert len(result.attempts) == 1
    assert result.attempts[0].succeeded is True

@pytest.mark.asyncio
async def test_resilient_primary_retry_success():
    call_count = 0
    async def primary():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Transient error")
        return "success"
    
    result = await resilient_call(primary, retries=1, retry_delay_s=0.01)
    assert result.success is True
    assert result.result == "success"
    assert len(result.attempts) == 2
    assert result.attempts[0].succeeded is False
    assert result.attempts[1].succeeded is True

@pytest.mark.asyncio
async def test_resilient_fallback_success():
    async def primary():
        raise ValueError("Primary failed")
    
    async def fallback():
        return "fallback_success"
    
    result = await resilient_call(primary, fallbacks=[fallback], retries=0)
    assert result.success is True
    assert result.result == "fallback_success"
    assert len(result.attempts) == 2
    assert result.attempts[0].succeeded is False
    assert result.attempts[1].succeeded is True

@pytest.mark.asyncio
async def test_resilient_total_failure():
    async def primary():
        raise ValueError("Primary failed")
    
    async def fallback():
        raise ValueError("Fallback failed")
    
    result = await resilient_call(primary, fallbacks=[fallback], retries=0)
    assert result.success is False
    assert result.result is None
    assert len(result.attempts) == 2
    assert "Fallback failed" in result.final_error

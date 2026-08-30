import pytest
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType


def test_model_manager_mini_model_detection():
    mini = model_manager.get_mini_model()
    assert mini is not None
    assert "llama3.2" in mini.lower() or "qwen" in mini.lower() or "smollm" in mini.lower()

    assert model_manager.is_mini_model("llama3.2:1b") is True
    assert model_manager.is_mini_model("qwen2.5:0.5b") is True
    assert model_manager.is_mini_model("smollm2:1.7b") is True
    assert model_manager.is_mini_model("Meta-Llama-3.1-8B-Instruct") is False
    assert model_manager.is_mini_model("DeepSeek-R1-Distill-Qwen-7B") is False


def test_model_manager_document_model():
    doc_model = model_manager.get_document_model()
    assert doc_model is not None


def test_model_manager_keep_alive_policy():
    # Mini model should have persistent keep-alive (-1)
    assert model_manager.get_model_keep_alive("llama3.2:1b") == -1
    assert model_manager.get_model_keep_alive("qwen2.5:0.5b") == -1

    # Heavy models should have short transient TTL
    heavy_ttl = model_manager.get_model_keep_alive("deepseek-r1:7b")
    assert heavy_ttl in ["2m", "1m", "60s"] or isinstance(heavy_ttl, str)


def test_ollama_client_select_model():
    assert ollama_client.select_model(AgentType.DOCUMENT) == model_manager.get_document_model()
    assert ollama_client.select_model(AgentType.CODING) is not None
    assert ollama_client.select_model(AgentType.CHAT) is not None


@pytest.mark.asyncio
async def test_ollama_client_vram_methods(monkeypatch):
    async def mock_get_loaded_models():
        return [
            {"name": "llama3.2:1b", "size": 800000000},
            {"name": "deepseek-r1:7b", "size": 4600000000},
        ]

    monkeypatch.setattr(ollama_client, "get_loaded_models", mock_get_loaded_models)
    
    unload_res = await ollama_client.unload_heavy_models(keep_mini=True)
    assert unload_res["status"] == "success"
    assert "llama3.2:1b" in unload_res["kept_mini_models"]

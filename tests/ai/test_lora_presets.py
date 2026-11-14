"""Tests for specialized Llama 3.1 & Qwen 2.5 Coder LoRA fine-tuning presets."""

import json
from pathlib import Path
from scripts.train_qlora import MODEL_PRESETS, generate_ollama_modelfile


def test_preset_definitions():
    assert "llama3.1" in MODEL_PRESETS
    assert "qwen2.5-coder" in MODEL_PRESETS

    llama = MODEL_PRESETS["llama3.1"]
    assert "unsloth/Meta-Llama-3.1" in llama["unsloth_model"]
    assert llama["ollama_base"] == "llama3.1:8b"
    assert "q_proj" in llama["targets"]
    assert "gate_proj" in llama["targets"]

    qwen = MODEL_PRESETS["qwen2.5-coder"]
    assert "unsloth/Qwen2.5-Coder" in qwen["unsloth_model"]
    assert qwen["ollama_base"] == "qwen2.5-coder:7b"
    assert "q_proj" in qwen["targets"]
    assert "gate_proj" in qwen["targets"]


def test_ollama_modelfile_generation(tmp_path: Path):
    modelfile = generate_ollama_modelfile(
        output_dir=tmp_path,
        ollama_base="llama3.1:8b",
        stop_tokens=["<|eot_id|>", "<|end_header_id|>"],
    )

    assert modelfile.exists()
    content = modelfile.read_text(encoding="utf-8")
    assert "FROM llama3.1:8b" in content
    assert "ADAPTER ./adapter_model.bin" in content
    assert 'PARAMETER stop "<|eot_id|>"' in content
    assert 'PARAMETER stop "<|end_header_id|>"' in content

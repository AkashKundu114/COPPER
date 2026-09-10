from pathlib import Path
from PIL import Image

from app.ai.image.diffusion_engine import LocalDiffusionEngine


def test_diffusion_engine_init(tmp_path):
    engine = LocalDiffusionEngine(
        model_path=str(tmp_path / "model.safetensors"),
        output_dir=str(tmp_path / "generated"),
        device="cpu",
    )
    assert engine.default_steps == 1
    assert engine.default_width == 512
    assert engine.default_height == 512
    assert engine.target_device == "cpu"
    assert engine.resolve_device() == "cpu"


def test_diffusion_engine_status(tmp_path):
    engine = LocalDiffusionEngine(
        model_path=str(tmp_path / "model.safetensors"),
        output_dir=str(tmp_path / "generated"),
    )
    status = engine.get_status()
    assert "model_path" in status
    assert "model_exists" in status
    assert status["offline_only"] is True
    assert "pipeline_loaded" in status
    assert status["pipeline_loaded"] is False


def test_offline_fallback_generation(tmp_path):
    engine = LocalDiffusionEngine(
        model_path=str(tmp_path / "non_existent.safetensors"),
        output_dir=str(tmp_path / "generated"),
        device="cpu",
    )
    prompt = "cyberpunk copper mechanical owl perched on gear"
    res = engine.generate(prompt=prompt, width=256, height=256, steps=1)

    assert res["status"] == "fallback"
    assert res["engine"] == "procedural_canvas"
    assert res["prompt"] == prompt
    assert res["width"] == 256
    assert res["height"] == 256
    assert res["offline"] is True
    assert res["url"].startswith("/generated/copper_sd_")

    # Verify PNG file was generated and is valid image
    generated_file = Path(res["file_path"])
    assert generated_file.exists()
    assert generated_file.is_file()

    with Image.open(generated_file) as img:
        assert img.format == "PNG"
        assert img.size == (256, 256)


def test_engine_unload():
    engine = LocalDiffusionEngine()
    # Unload on uninitialized engine should return False cleanly
    assert engine.unload() is False

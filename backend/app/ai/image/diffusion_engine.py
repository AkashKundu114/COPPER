"""
C.O.P.P.E.R. Local Diffusion Engine (PICASSO Studio)
100% Offline Stable Diffusion Pipeline utilizing local SD-Turbo weights.
Supports GPU acceleration (CUDA fp16) on RTX 5060, CPU fallback, lazy loading,
and clean VRAM release.
"""

import gc
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings

logger = logging.getLogger("copper.image.diffusion")


class LocalDiffusionEngine:
    def __init__(
        self,
        model_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        device: Optional[str] = None,
        default_steps: int = 1,
        default_width: int = 512,
        default_height: int = 512,
    ):
        self.model_path = Path(model_path or settings.IMAGE_MODEL_PATH)
        self.output_dir = Path(output_dir or settings.IMAGE_OUTPUT_DIR)
        self.target_device = device or getattr(settings, "IMAGE_DEVICE", "auto")
        self.default_steps = default_steps or getattr(settings, "IMAGE_INFERENCE_STEPS", 1)
        self.default_width = default_width or getattr(settings, "IMAGE_WIDTH", 512)
        self.default_height = default_height or getattr(settings, "IMAGE_HEIGHT", 512)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._pipeline = None
        self._loaded_device: Optional[str] = None

    def is_model_available(self) -> bool:
        """Check if local SD-Turbo weights exist on disk."""
        return self.model_path.exists() and self.model_path.is_file()

    def is_torch_available(self) -> bool:
        """Check if PyTorch is installed."""
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            return False

    def is_cuda_available(self) -> bool:
        """Check if CUDA GPU acceleration is available."""
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def resolve_device(self) -> str:
        """Resolve the target execution device (cuda or cpu)."""
        target = self.target_device.lower()
        if target == "cuda":
            return "cuda" if self.is_cuda_available() else "cpu"
        elif target == "cpu":
            return "cpu"
        else:  # "auto"
            return "cuda" if self.is_cuda_available() else "cpu"

    def load_pipeline(self) -> Any:
        """
        Lazy load Stable Diffusion pipeline from local SD-Turbo safetensors.
        Keeps VRAM footprint optimized with float16 on CUDA.
        """
        if self._pipeline is not None:
            return self._pipeline

        if not self.is_model_available():
            raise FileNotFoundError(f"SD-Turbo model weights not found at: {self.model_path}")

        try:
            import torch
            from diffusers import AutoPipelineForText2Image

            device = self.resolve_device()
            dtype = torch.float16 if device == "cuda" else torch.float32

            logger.info(
                f"[PICASSO] Loading SD-Turbo from {self.model_path.name} on {device.upper()} ({dtype})..."
            )

            pipeline = AutoPipelineForText2Image.from_single_file(
                str(self.model_path),
                torch_dtype=dtype,
                local_files_only=True,
                load_safety_checker=False,
            )

            pipeline = pipeline.to(device)
            # Enable memory optimization if available on CUDA
            if device == "cuda" and hasattr(pipeline, "enable_vae_tiling"):
                try:
                    pipeline.enable_vae_tiling()
                except Exception:
                    pass

            self._pipeline = pipeline
            self._loaded_device = device
            logger.info("[PICASSO] SD-Turbo pipeline successfully initialized in memory.")
            return self._pipeline

        except Exception as e:
            logger.warning(f"[PICASSO] Could not initialize diffusers pipeline: {e}")
            raise

    def unload(self) -> bool:
        """
        Explicitly unload pipeline and release GPU VRAM back to system/LLM models.
        """
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            self._loaded_device = None

            if self.is_torch_available():
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            gc.collect()
            logger.info("[PICASSO] Diffusion pipeline unloaded; VRAM/RAM reclaimed.")
            return True
        return False

    def generate(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Generate image locally.
        Uses local SD-Turbo if diffusers and weights are available.
        Otherwise falls back to an offline high-fidelity aesthetic procedural canvas.
        """
        prompt = prompt.strip() if prompt else "a futuristic copper machine"
        width = width or self.default_width
        height = height or self.default_height
        steps = steps or self.default_steps

        # Generate unique local file name
        timestamp = int(time.time())
        token = uuid.uuid4().hex[:6]
        file_name = f"copper_sd_{timestamp}_{token}.png"
        file_path = self.output_dir / file_name

        start_time = time.time()
        device_used = "offline-procedural"
        engine_used = "procedural_canvas"
        status = "fallback"

        # Attempt local Stable Diffusion inference
        if self.is_model_available() and self.is_torch_available():
            try:
                import torch

                pipe = self.load_pipeline()
                device = self._loaded_device or self.resolve_device()
                generator = None
                if seed is not None:
                    generator = torch.Generator(device=device).manual_seed(seed)

                # SD-Turbo is adversarial distilled: guidance_scale=0.0 is optimal for 1-step
                guidance_scale = 0.0 if steps <= 1 else 1.5

                with torch.inference_mode():
                    output = pipe(
                        prompt=prompt,
                        width=width,
                        height=height,
                        num_inference_steps=steps,
                        guidance_scale=guidance_scale,
                        generator=generator,
                    )
                    image = output.images[0]
                    image.save(str(file_path), format="PNG")

                engine_used = "sd_turbo_local"
                device_used = device
                status = "success"
                logger.info(
                    f"[PICASSO] Successfully rendered local SD-Turbo image in {time.time() - start_time:.2f}s: {file_name}"
                )

            except Exception as e:
                logger.warning(
                    f"[PICASSO] Local SD inference encountered error: {e}. Activating offline canvas fallback."
                )
                self._generate_fallback_image(prompt, width, height, file_path)
        else:
            # Model weights or diffusers runtime not active: create offline aesthetic canvas
            self._generate_fallback_image(prompt, width, height, file_path)

        duration = time.time() - start_time
        url = f"/generated/{file_name}"

        return {
            "status": status,
            "engine": engine_used,
            "prompt": prompt,
            "file_name": file_name,
            "file_path": str(file_path),
            "url": url,
            "width": width,
            "height": height,
            "steps": steps,
            "device": device_used,
            "duration_seconds": round(duration, 3),
            "offline": True,
        }

    def _generate_fallback_image(
        self, prompt: str, width: int, height: int, output_file: Path
    ) -> None:
        """
        Generate a high-contrast dark cyberpunk procedural canvas as an offline fallback.
        Ensures 100% offline uptime and visual feedback even if torch/diffusers is not loaded.
        """
        # Create dark background
        img = Image.new("RGB", (width, height), color=(10, 15, 26))
        draw = ImageDraw.Draw(img)

        # Draw subtle grid lines
        grid_step = 32
        for x in range(0, width, grid_step):
            draw.line([(x, 0), (x, height)], fill=(18, 26, 44), width=1)
        for y in range(0, height, grid_step):
            draw.line([(0, y), (width, y)], fill=(18, 26, 44), width=1)

        # Draw border in copper tone
        border_color = (249, 115, 22)  # Copper Orange #f97316
        draw.rectangle([(8, 8), (width - 9, height - 9)], outline=border_color, width=2)
        draw.rectangle([(12, 12), (width - 13, height - 13)], outline=(40, 50, 70), width=1)

        # Header banner
        draw.rectangle([(16, 16), (width - 17, 56)], fill=(20, 30, 50))
        draw.text(
            (26, 26),
            "🎨 C.O.P.P.E.R. PICASSO STUDIO (100% OFFLINE)",
            fill=border_color,
        )

        # Status badge
        draw.rectangle([(width - 160, 24), (width - 24, 48)], fill=(15, 23, 42), outline=(51, 65, 85))
        draw.text((width - 150, 28), "SD-TURBO READY", fill=(148, 163, 184))

        # Central Visual Block / Placeholder frame
        center_box = [(40, 76), (width - 40, height - 110)]
        draw.rectangle(center_box, fill=(13, 19, 34), outline=(51, 65, 85), width=1)

        # Stylized crosshairs in center box
        cx = width // 2
        cy = (76 + height - 110) // 2
        draw.line([(cx - 40, cy), (cx + 40, cy)], fill=(249, 115, 22), width=1)
        draw.line([(cx, cy - 40), (cx, cy + 40)], fill=(249, 115, 22), width=1)
        draw.ellipse([(cx - 20, cy - 20), (cx + 20, cy + 20)], outline=(251, 146, 60), width=1)

        # Prompt text wrapping
        max_chars = 48
        words = prompt.split()
        lines = []
        cur_line = []
        for w in words:
            if sum(len(x) for x in cur_line) + len(cur_line) + len(w) > max_chars:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        # Draw prompt title
        prompt_y = cy + 50
        draw.text((cx, prompt_y), "PROMPT SPECIFICATION:", fill=(148, 163, 184), anchor="mm")
        prompt_y += 24
        for line in lines[:3]:  # max 3 lines
            draw.text((cx, prompt_y), f'"{line}"', fill=(241, 245, 249), anchor="mm")
            prompt_y += 20

        # Footer
        footer_text = f"Local SD-Turbo Model: {self.model_path.name} | Offline Safe Mode"
        draw.text((20, height - 36), footer_text, fill=(100, 116, 139))
        draw.text(
            (width - 20, height - 36),
            f"{width}x{height} PNG",
            fill=(100, 116, 139),
            anchor="ra",
        )

        img.save(str(output_file), format="PNG")

    def get_status(self) -> dict[str, Any]:
        """Return diagnostic status of the local diffusion engine."""
        return {
            "model_path": str(self.model_path),
            "model_exists": self.is_model_available(),
            "model_size_mb": (
                round(self.model_path.stat().st_size / (1024 * 1024), 2)
                if self.is_model_available()
                else 0
            ),
            "torch_available": self.is_torch_available(),
            "cuda_available": self.is_cuda_available(),
            "target_device": self.target_device,
            "resolved_device": self.resolve_device(),
            "pipeline_loaded": self._pipeline is not None,
            "output_dir": str(self.output_dir),
            "offline_only": getattr(settings, "IMAGE_OFFLINE_ONLY", True),
        }


diffusion_engine = LocalDiffusionEngine()

"""Quantization-Aware VRAM Estimator & Footprint Calculator.

Computes exact VRAM footprints for quantized local models (Q2_K through FP16)
to optimize resident memory allocation under COPPER's 8GB VRAM constraint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class QuantizationType(str, Enum):
    FP16 = "fp16"
    Q8_0 = "q8_0"
    Q6_K = "q6_k"
    Q5_K_M = "q5_k_m"
    Q4_K_M = "q4_k_m"
    Q4_0 = "q4_0"
    Q3_K_M = "q3_k_m"
    Q2_K = "q2_k"
    DEFAULT = "q4_k_m"


# Effective bits per weight for GGUF/AWQ quantizations
BITS_PER_WEIGHT: dict[QuantizationType, float] = {
    QuantizationType.FP16: 16.0,
    QuantizationType.Q8_0: 8.5,
    QuantizationType.Q6_K: 6.6,
    QuantizationType.Q5_K_M: 5.5,
    QuantizationType.Q4_K_M: 4.5,
    QuantizationType.Q4_0: 4.5,
    QuantizationType.Q3_K_M: 3.4,
    QuantizationType.Q2_K: 2.6,
}

# Base parameter counts in billions for common architectures
KNOWN_BASE_PARAMS: dict[str, float] = {
    "0.5b": 0.49,
    "1.5b": 1.54,
    "1.7b": 1.71,
    "2b": 2.10,
    "3b": 3.09,
    "7b": 7.24,
    "8b": 8.03,
    "12b": 12.24,
    "14b": 14.77,
    "32b": 32.50,
}


@dataclass(frozen=True)
class ModelFootprint:
    model_tag: str
    base_params_billion: float
    quantization: QuantizationType
    weights_vram_gb: float
    kv_cache_vram_gb: float
    total_vram_gb: float
    fits_8gb_vram: bool


class QuantizationVRAMEstimator:
    """Calculates realistic VRAM footprints for local LLM instances."""

    def __init__(self, context_length: int = 4096):
        self.context_length = context_length

    def parse_model_tag(self, model_tag: str) -> tuple[float, QuantizationType]:
        """Parses model tag to extract parameter size (in B) and quantization level."""
        tag = model_tag.lower().strip()

        # 1. Detect quantization
        detected_quant = QuantizationType.DEFAULT
        for q in QuantizationType:
            if q.value in tag:
                detected_quant = q
                break

        # 2. Detect parameter size
        detected_params = 7.0  # default assumption
        # Check explicit patterns like ":14b", "-7b", "3b"
        param_match = re.search(r"(\d+(?:\.\d+)?)b\b", tag)
        if param_match:
            detected_params = float(param_match.group(1))
        else:
            for k, v in KNOWN_BASE_PARAMS.items():
                if k in tag:
                    detected_params = v
                    break

        return detected_params, detected_quant

    def estimate_vram(
        self,
        model_tag: str,
        context_length: int | None = None,
        batch_size: int = 1,
    ) -> ModelFootprint:
        """Estimates total VRAM required including weights and KV cache."""
        ctx_len = context_length or self.context_length
        base_params, quant = self.parse_model_tag(model_tag)

        # 1. Model Weights Footprint (Calibrated to Empirical GGUF Model Sizes)
        # In GGUF, 4-bit quantized weights occupy ~0.40 GB per billion active parameters
        bits = BITS_PER_WEIGHT.get(quant, 4.5)
        scale_ratio = bits / 4.5
        weights_gb = (base_params * 0.40) * scale_ratio

        # 2. KV Cache Footprint (scaled for standard context length)
        kv_cache_gb = (base_params / 7.0) * (ctx_len / 4096.0) * 0.40 * batch_size

        # 3. CUDA Runtime & PyTorch/Ollama Context Overhead (~0.25 GB)
        overhead_gb = 0.25

        total_gb = round(weights_gb + kv_cache_gb + overhead_gb, 2)
        fits_8gb = total_gb <= 8.0

        return ModelFootprint(
            model_tag=model_tag,
            base_params_billion=base_params,
            quantization=quant,
            weights_vram_gb=round(weights_gb, 2),
            kv_cache_vram_gb=round(kv_cache_gb, 2),
            total_vram_gb=total_gb,
            fits_8gb_vram=fits_8gb,
        )


quantization_vram_estimator = QuantizationVRAMEstimator()

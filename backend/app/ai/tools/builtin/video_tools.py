import asyncio
import os
import shutil
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger

OPENMONTAGE_PIPELINES = {
    "screen-demo": {
        "name": "Screen Demo Walkthrough",
        "aspect_ratio": "16:9",
        "description": "Step-by-step software walkthrough highlighting UI elements, terminal commands, and workflow transitions.",
        "pacing_sec_per_scene": 5.0,
    },
    "animated-explainer": {
        "name": "Animated Concept Explainer",
        "aspect_ratio": "16:9",
        "description": "Educational narrative explaining complex technical or scientific ideas with diagrams and text callouts.",
        "pacing_sec_per_scene": 4.0,
    },
    "clip-factory": {
        "name": "Short-Form Reel / Clip",
        "aspect_ratio": "9:16",
        "description": "High-velocity vertical video tailored for mobile viewing, featuring rapid cuts and dynamic captions.",
        "pacing_sec_per_scene": 2.5,
    },
    "documentary-montage": {
        "name": "Documentary Montage",
        "aspect_ratio": "16:9",
        "description": "Cinematic visual montage paired with deep neural voice narration and atmospheric pacing.",
        "pacing_sec_per_scene": 6.0,
    },
    "podcast-repurpose": {
        "name": "Audiogram & Podcast Clip",
        "aspect_ratio": "1:1",
        "description": "Waveform-reactive audiogram video generated from speech audio clips and key quote cards.",
        "pacing_sec_per_scene": 4.0,
    },
}


@tool_registry.tool(
    name="video_pipeline_list",
    description="List all available OpenMontage agentic video production pipelines and their format specifications.",
    parameters={
        "type": "object",
        "properties": {},
    },
    return_description="List of video production pipelines.",
    guardian_level=0,
)
async def video_pipeline_list() -> dict[str, Any]:
    return {
        "status": "success",
        "total_pipelines": len(OPENMONTAGE_PIPELINES),
        "pipelines": OPENMONTAGE_PIPELINES,
    }


@tool_registry.tool(
    name="video_create_slideshow",
    description="Render a video slideshow from an image sequence and optional audio narration track using local FFmpeg.",
    parameters={
        "type": "object",
        "properties": {
            "image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered list of image file paths for slides.",
            },
            "output_path": {
                "type": "string",
                "description": "Destination file path for the rendered MP4 video.",
            },
            "seconds_per_image": {
                "type": "number",
                "description": "Display duration per image in seconds (default: 4.0).",
            },
            "audio_path": {
                "type": "string",
                "description": "Optional background audio or neural speech narration track (WAV/MP3).",
            },
            "pipeline": {
                "type": "string",
                "description": "Optional OpenMontage pipeline preset (e.g. 'screen-demo', 'clip-factory').",
            },
        },
        "required": ["image_paths", "output_path"],
    },
    return_description="Render status and output video path.",
    guardian_level=1,
)
async def video_create_slideshow(
    image_paths: list[str],
    output_path: str,
    seconds_per_image: float | None = None,
    audio_path: str | None = None,
    pipeline: str | None = None,
) -> dict[str, Any]:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return {
            "status": "error",
            "error": "FFmpeg executable not found on system PATH. Install ffmpeg to enable local video production.",
        }

    # Determine pacing from pipeline if specified
    if pipeline and pipeline in OPENMONTAGE_PIPELINES and seconds_per_image is None:
        duration_per_img = OPENMONTAGE_PIPELINES[pipeline]["pacing_sec_per_scene"]
    else:
        duration_per_img = seconds_per_image if seconds_per_image is not None else 4.0

    valid_images = [Path(p).resolve() for p in image_paths if Path(p).exists()]
    if not valid_images:
        return {"status": "error", "error": "None of the specified image paths exist."}

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    concat_txt = out_file.parent / f"concat_{out_file.stem}.txt"
    try:
        with open(concat_txt, "w", encoding="utf-8") as f:
            for img in valid_images:
                escaped = str(img).replace("\\", "/")
                f.write(f"file '{escaped}'\n")
                f.write(f"duration {duration_per_img}\n")
            escaped_last = str(valid_images[-1]).replace("\\", "/")
            f.write(f"file '{escaped_last}'\n")

        cmd = [
            ffmpeg_bin,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
        ]

        if audio_path and Path(audio_path).exists():
            cmd.extend(["-i", str(Path(audio_path).resolve()), "-shortest"])

        cmd.extend([
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
            "-c:v", "libx264",
            "-r", "24",
            "-movflags", "+faststart",
            str(out_file),
        ])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            return {
                "status": "error",
                "error": f"FFmpeg render failed: {stderr.decode('utf-8', errors='replace')[-500:]}",
            }

        return {
            "status": "success",
            "output_video": str(out_file),
            "pipeline": pipeline or "custom",
            "size_bytes": out_file.stat().st_size,
            "slides_count": len(valid_images),
            "estimated_duration_sec": len(valid_images) * duration_per_img,
        }
    except Exception as e:
        logger.error(f"video_create_slideshow error: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        if concat_txt.exists():
            try:
                concat_txt.unlink()
            except OSError:
                pass


@tool_registry.tool(
    name="video_probe",
    description="Inspect media file metadata (duration, resolution, codecs) via FFprobe.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the video or audio file to inspect.",
            }
        },
        "required": ["file_path"],
    },
    return_description="Media stream metadata and container information.",
    guardian_level=0,
)
async def video_probe(file_path: str) -> dict[str, Any]:
    ffprobe_bin = shutil.which("ffprobe")
    if not ffprobe_bin:
        return {"status": "warning", "message": "ffprobe executable not found on system PATH."}

    p = Path(file_path).resolve()
    if not p.exists():
        return {"status": "error", "error": f"File does not exist: {file_path}"}

    try:
        proc = await asyncio.create_subprocess_exec(
            ffprobe_bin,
            "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=codec_name,codec_type,width,height",
            "-of", "json",
            str(p),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        import json
        data = json.loads(stdout.decode("utf-8", errors="replace"))
        return {"status": "success", "file": str(p), "metadata": data}
    except Exception as e:
        return {"status": "error", "error": str(e)}

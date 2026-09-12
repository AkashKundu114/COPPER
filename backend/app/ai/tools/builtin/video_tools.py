import asyncio
import os
import shutil
from pathlib import Path
from typing import Any

from app.ai.tools.registry import tool_registry
from app.core.logger import logger


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
        },
        "required": ["image_paths", "output_path"],
    },
    return_description="Render status and output video path.",
    guardian_level=1,
)
async def video_create_slideshow(
    image_paths: list[str],
    output_path: str,
    seconds_per_image: float = 4.0,
    audio_path: str | None = None,
) -> dict[str, Any]:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return {
            "status": "error",
            "error": "FFmpeg executable not found on system PATH. Install ffmpeg to enable local video production.",
        }

    # Validate image paths
    valid_images = [Path(p).resolve() for p in image_paths if Path(p).exists()]
    if not valid_images:
        return {"status": "error", "error": "None of the specified image paths exist."}

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Build concat demuxer file
    concat_txt = out_file.parent / f"concat_{out_file.stem}.txt"
    try:
        with open(concat_txt, "w", encoding="utf-8") as f:
            for img in valid_images:
                escaped = str(img).replace("\\", "/")
                f.write(f"file '{escaped}'\n")
                f.write(f"duration {seconds_per_image}\n")
            # Concat demuxer requirement: repeat last file without duration
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

        # Encode with H.264 & AAC, scale to even dimensions for compatibility
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
            "size_bytes": out_file.stat().st_size,
            "slides_count": len(valid_images),
            "estimated_duration_sec": len(valid_images) * seconds_per_image,
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

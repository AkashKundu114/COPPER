"""
C.O.P.P.E.R. Audio Model Setup & Downloader
Provides helper routines to inspect or fetch Whisper & Piper models for offline STT/TTS.
"""

from pathlib import Path
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WHISPER_DIR = ROOT_DIR / "ai-models" / "audio" / "whisper"
TTS_DIR = ROOT_DIR / "ai-models" / "audio" / "tts"

def setup_audio_models():
    print("=" * 66)
    print("         C.O.P.P.E.R. OFFLINE AUDIO PIPELINE SETUP")
    print("=" * 66)

    WHISPER_DIR.mkdir(parents=True, exist_ok=True)
    TTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[*] Whisper STT Model Directory: {WHISPER_DIR}")
    whisper_models = list(WHISPER_DIR.glob("*"))
    print(f"[+] Found {len(whisper_models)} STT model file(s)")
    for wm in whisper_models:
        print(f"    - {wm.name} ({wm.stat().st_size / (1024*1024):.2f} MB)")

    print(f"\n[*] Piper TTS Voices Directory:   {TTS_DIR}")
    tts_models = list(TTS_DIR.glob("*"))
    print(f"[+] Found {len(tts_models)} TTS voice file(s)")
    for tm in tts_models:
        print(f"    - {tm.name} ({tm.stat().st_size / (1024*1024):.2f} MB)")

    print("\n[+] Audio model directories configured and ready.")
    print("=" * 66)

if __name__ == "__main__":
    setup_audio_models()

import pytest
import io
import wave
import struct
import math


def generate_test_tone(duration=0.2, freq=440.0, rate=16000, channels=1):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        total_samples = int(duration * rate)
        frames = bytearray()
        for i in range(total_samples):
            val = int(math.sin(2.0 * math.pi * freq * (i / rate)) * 16384)
            for _ in range(channels):
                frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return buf.getvalue()


def test_tone_generator_16khz_mono():
    wav = generate_test_tone(duration=0.1, freq=440.0, rate=16000, channels=1)
    assert len(wav) > 44
    with io.BytesIO(wav) as bio:
        with wave.open(bio, "rb") as wf:
            assert wf.getframerate() == 16000
            assert wf.getnchannels() == 1


def test_tone_generator_22khz_mono():
    wav = generate_test_tone(duration=0.1, freq=880.0, rate=22050, channels=1)
    with io.BytesIO(wav) as bio:
        with wave.open(bio, "rb") as wf:
            assert wf.getframerate() == 22050


def test_tone_generator_44khz_stereo():
    wav = generate_test_tone(duration=0.1, freq=440.0, rate=44100, channels=2)
    with io.BytesIO(wav) as bio:
        with wave.open(bio, "rb") as wf:
            assert wf.getframerate() == 44100
            assert wf.getnchannels() == 2


def test_tone_generator_48khz():
    wav = generate_test_tone(duration=0.05, freq=1000.0, rate=48000, channels=1)
    with io.BytesIO(wav) as bio:
        with wave.open(bio, "rb") as wf:
            assert wf.getframerate() == 48000


def test_pcm_chunk_slicing():
    wav = generate_test_tone(duration=0.4, freq=440.0, rate=16000, channels=1)
    # Header is 44 bytes, audio frames start after byte 44
    pcm_data = wav[44:]
    chunk_size = 1024
    chunks = [pcm_data[i:i + chunk_size] for i in range(0, len(pcm_data), chunk_size)]
    assert len(chunks) > 1
    assert sum(len(c) for c in chunks) == len(pcm_data)


def test_silence_threshold_detection():
    # Detect silence from raw PCM bytes
    silence = b"\x00\x00" * 1000
    values = struct.unpack(f"<{len(silence)//2}h", silence)
    max_amplitude = max(abs(v) for v in values)
    assert max_amplitude == 0


def test_active_signal_amplitude():
    wav = generate_test_tone(duration=0.1, freq=440.0, rate=16000, channels=1)
    pcm_data = wav[44:]
    values = struct.unpack(f"<{len(pcm_data)//2}h", pcm_data)
    max_amplitude = max(abs(v) for v in values)
    assert max_amplitude > 10000

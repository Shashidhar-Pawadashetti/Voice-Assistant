"""Audio test fixture generator producing synthetic WAV and invalid test byte streams."""

import io
import math
import struct
import wave


def make_test_wav(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
    channels: int = 1,
    frequency: float = 440.0,
) -> bytes:
    """Generate in-memory valid PCM 16-bit WAV bytes."""
    num_samples = int(duration_seconds * sample_rate)
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        samples = []
        for i in range(num_samples):
            val = int(32767.0 * 0.2 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            sample_bytes = struct.pack("<h", val)
            if channels == 2:
                sample_bytes = sample_bytes * 2
            samples.append(sample_bytes)

        wav_file.writeframes(b"".join(samples))

    return buffer.getvalue()


def make_corrupt_wav() -> bytes:
    """Generate corrupt WAV with RIFF header but truncated data."""
    return b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"


def make_fake_ogg() -> bytes:
    """Generate minimal Ogg signature bytes for container detection tests."""
    return b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x1e" + b"\x00" * 40


def make_fake_webm() -> bytes:
    """Generate minimal WebM EBML signature bytes for container detection tests."""
    return b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01\x42\xf7\x81\x01\x42\xf2\x81\x04\x42\xf3\x81\x08" + b"\x00" * 40

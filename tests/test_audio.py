import math
import struct
import wave
from pathlib import Path

import pytest

from omni.audio import AUDIO_FORMATS, convert_audio, extract_audio
from omni.errors import ConversionError


def make_wav(path: Path, seconds=1.0, rate=44100):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(int(seconds * rate)):
            v = int(12000 * math.sin(2 * math.pi * 440 * i / rate))
            frames += struct.pack("<h", v)
        w.writeframes(bytes(frames))


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def test_formats_defined():
    assert {"mp3", "wav", "flac", "ogg", "opus", "m4a", "wma"} == set(AUDIO_FORMATS)


def test_wav_to_mp3(tmp_path):
    src = tmp_path / "in.wav"
    make_wav(src)
    dst = tmp_path / "out.mp3"
    convert_audio(src, dst)
    assert dst.stat().st_size > 1000


def test_mp3_to_wav_duration(tmp_path):
    src = tmp_path / "in.wav"
    make_wav(src)
    convert_audio(src, tmp_path / "mid.mp3")
    dst = tmp_path / "back.wav"
    convert_audio(tmp_path / "mid.mp3", dst)
    assert abs(wav_duration(dst) - 1.0) < 0.05


def test_wav_to_flac_roundtrip(tmp_path):
    src = tmp_path / "in.wav"
    make_wav(src)
    convert_audio(src, tmp_path / "mid.flac")
    convert_audio(tmp_path / "mid.flac", tmp_path / "back.wav")
    assert abs(wav_duration(tmp_path / "back.wav") - 1.0) < 0.05


def test_opus_bitrate_override(tmp_path):
    src = tmp_path / "in.wav"
    make_wav(src)
    convert_audio(src, tmp_path / "out.opus", bitrate_k=64)
    assert (tmp_path / "out.opus").stat().st_size > 1000


def test_missing_source_raises(tmp_path):
    with pytest.raises(ConversionError):
        convert_audio(tmp_path / "nope.wav", tmp_path / "x.mp3")

from pathlib import Path

import pytest

from omni.errors import ConversionError
from omni.ffmpeg import run_ffmpeg
from omni.video import VIDEO_FORMATS, convert_video, extract_audio, extract_frames


def make_mp4(path: Path, seconds=2):
    run_ffmpeg(
        [
            "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=320x240:rate=15",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(path),
        ]
    )
    return path


def test_formats_defined():
    assert {"mp4", "avi", "mkv", "mov", "webm", "gif"} == set(VIDEO_FORMATS)


def test_mp4_to_webm_and_back(tmp_path):
    src = make_mp4(tmp_path / "in.mp4")
    convert_video(src, tmp_path / "mid.webm")
    assert (tmp_path / "mid.webm").stat().st_size > 1000
    convert_video(tmp_path / "mid.webm", tmp_path / "back.mp4")
    assert (tmp_path / "back.mp4").stat().st_size > 1000


def test_mp4_to_gif(tmp_path):
    src = make_mp4(tmp_path / "in.mp4")
    convert_video(src, tmp_path / "out.gif")
    assert (tmp_path / "out.gif").stat().st_size > 1000


def test_extract_frames(tmp_path):
    src = make_mp4(tmp_path / "in.mp4", seconds=3)
    out_dir = tmp_path / "frames"
    files = extract_frames(src, out_dir, fps=1.0)
    assert len(files) >= 2
    assert all(p.suffix == ".png" for p in files)


def test_extract_audio_from_video(tmp_path):
    src = tmp_path / "in.mp4"
    run_ffmpeg(
        [
            "-f", "lavfi", "-i", f"testsrc=duration=1:size=160x120:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
            str(src),
        ]
    )
    dst = tmp_path / "sound.wav"
    extract_audio(src, dst)
    assert dst.stat().st_size > 1000


def test_missing_source_raises(tmp_path):
    with pytest.raises(ConversionError):
        convert_video(tmp_path / "nope.mp4", tmp_path / "x.avi")
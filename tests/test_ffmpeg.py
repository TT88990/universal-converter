import pytest

from omni.errors import ConversionError
from omni.ffmpeg import ffmpeg_exe, has_ffmpeg, run_ffmpeg


def test_has_ffmpeg_true():
    assert has_ffmpeg() is True


def test_ffmpeg_exe_returns_string():
    assert isinstance(ffmpeg_exe(), str)
    assert ffmpeg_exe().lower().endswith(".exe")


def test_run_ffmpeg_version_ok():
    run_ffmpeg(["-version"])


def test_run_ffmpeg_failure_raises():
    with pytest.raises(ConversionError):
        run_ffmpeg(["-i", "no_such_file_abc.mp3", "-f", "mp3", "out.mp3"])
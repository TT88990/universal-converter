import subprocess

from omni.errors import ConversionError


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - env dependent
        raise ConversionError(
            "ffmpeg binary not found. Reinstall the app or the imageio-ffmpeg package."
        ) from exc


def has_ffmpeg() -> bool:
    try:
        ffmpeg_exe()
        return True
    except ConversionError:
        return False


def run_ffmpeg(args: list[str]) -> None:
    cmd = [ffmpeg_exe(), "-hide_banner", "-nostdin", "-y"] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-5:])
        raise ConversionError(f"ffmpeg failed: {tail}")
from pathlib import Path

from omni.audio import extract_audio as _extract_audio
from omni.errors import ConversionError
from omni.ffmpeg import run_ffmpeg

VIDEO_FORMATS = {
    "mp4": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "avi": ["-c:v", "mpeg4", "-c:a", "mp3"],
    "mkv": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "mov": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "webm": ["-c:v", "libvpx-vp9", "-c:a", "libopus", "-b:v", "1M"],
    "gif": ["-vf", "fps=15,scale=480:-1:flags=lanczos", "-f", "gif"],
}


def convert_video(src: str | Path, dst: str | Path) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    ext = dst_path.suffix.lower().lstrip(".")
    params = VIDEO_FORMATS.get(ext)
    if params is None:
        raise ConversionError(f"Unsupported video format .{ext}")
    try:
        run_ffmpeg(["-i", str(src_path), *params, str(dst_path)])
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Video conversion failed: {exc}") from exc


def extract_frames(src: str | Path, out_dir: str | Path, fps: float = 1.0) -> list[Path]:
    src_path = Path(src)
    out_path = Path(out_dir)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    out_path.mkdir(parents=True, exist_ok=True)
    pattern = out_path / "frame_%04d.png"
    try:
        run_ffmpeg(["-i", str(src_path), "-vf", f"fps={fps}", str(pattern)])
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Frame extraction failed: {exc}") from exc
    return sorted(out_path.glob("frame_*.png"))


def extract_audio(src: str | Path, dst: str | Path) -> None:
    _extract_audio(src, dst)
from pathlib import Path

from omni.errors import ConversionError
from omni.ffmpeg import run_ffmpeg

AUDIO_FORMATS = {
    "mp3": ["-c:a", "libmp3lame", "-b:a", "192k"],
    "wav": ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
    "opus": ["-c:a", "libopus", "-b:a", "128k"],
    "m4a": ["-c:a", "aac", "-b:a", "192k"],
    "wma": ["-c:a", "wmav2", "-b:a", "192k"],
}


def _params(ext: str, bitrate_k: int | None) -> list[str]:
    base = AUDIO_FORMATS.get(ext)
    if base is None:
        raise ConversionError(f"Unsupported audio format .{ext}")
    params = list(base)
    if bitrate_k and ext not in ("wav", "flac"):
        if "-b:a" in params:
            params[params.index("-b:a") + 1] = f"{bitrate_k}k"
        else:
            params += ["-b:a", f"{bitrate_k}k"]
    return params


def convert_audio(src: str | Path, dst: str | Path, bitrate_k: int | None = None) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    ext = dst_path.suffix.lower().lstrip(".")
    params = _params(ext, bitrate_k)
    try:
        run_ffmpeg(["-i", str(src_path), *params, str(dst_path)])
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Audio conversion failed: {exc}") from exc


def extract_audio(src_video: str | Path, dst_audio: str | Path) -> None:
    src_path, dst_path = Path(src_video), Path(dst_audio)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    ext = dst_path.suffix.lower().lstrip(".")
    params = _params(ext, None)
    try:
        run_ffmpeg(["-i", str(src_path), "-vn", *params, str(dst_path)])
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Audio extraction failed: {exc}") from exc
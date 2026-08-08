from pathlib import Path

from omni.errors import ConversionError
from omni.hashgen import decode_base64 as _unb64, encode_base64 as _b64, from_hex, to_hex

TEXT_ENCODINGS = ("utf-8", "utf-16", "utf-16-le", "utf-16-be", "ascii", "latin-1")


def _read_text(src: Path, encoding: str) -> str:
    try:
        return src.read_text(encoding=encoding)
    except (UnicodeDecodeError, ValueError) as exc:
        raise ConversionError(f"Cannot decode {src.name} as {encoding}") from exc


def convert_text(
    src: str | Path,
    dst: str | Path,
    in_enc: str = "utf-8",
    out_enc: str = "utf-8",
    newline: str | None = None,
) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    if in_enc not in TEXT_ENCODINGS or out_enc not in TEXT_ENCODINGS:
        raise ConversionError("Unsupported text encoding")
    text = _read_text(src_path, in_enc)
    if newline is not None:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)
    dst_path.write_text(text, encoding=out_enc)


def convert_base64(src: str | Path, dst: str | Path, mode: str) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    try:
        if mode == "encode":
            dst_path.write_text(_b64(src_path.read_bytes()), encoding="utf-8")
        elif mode == "decode":
            dst_path.write_bytes(_unb64(src_path.read_text(encoding="utf-8")))
        else:
            raise ConversionError("mode must be 'encode' or 'decode'")
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Base64 {mode} failed: {exc}") from exc


def convert_hex(src: str | Path, dst: str | Path, mode: str) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    try:
        if mode == "encode":
            dst_path.write_text(to_hex(src_path.read_bytes()), encoding="utf-8")
        elif mode == "decode":
            dst_path.write_bytes(from_hex(src_path.read_text(encoding="utf-8")))
        else:
            raise ConversionError("mode must be 'encode' or 'decode'")
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Hex {mode} failed: {exc}") from exc
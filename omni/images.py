from pathlib import Path

from PIL import Image

from omni.errors import ConversionError

IMAGE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"})

PIXEL_FORMATS = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WEBP",
    "bmp": "BMP",
    "gif": "GIF",
    "tiff": "TIFF",
    "ico": "ICO",
}

_RGB_REQUIRED = {"JPEG", "WEBP"}


def _target_format(dst: str | Path) -> str:
    fmt = PIXEL_FORMATS.get(Path(dst).suffix.lower().lstrip("."))
    if not fmt:
        raise ConversionError(f"Unsupported output format .{Path(dst).suffix}")
    return fmt


def convert_image(src: str | Path, dst: str | Path, quality: int | None = None) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    fmt = _target_format(dst_path)
    try:
        with Image.open(src_path) as im:
            im.load()
            canvas = im
            if im.mode in ("RGBA", "LA") and fmt in _RGB_REQUIRED:
                canvas = Image.new("RGB", im.size, (255, 255, 255))
                canvas.paste(im, mask=im.getchannel("A"))
            if im.mode == "P" and fmt in _RGB_REQUIRED:
                canvas = im.convert("RGBA")
                flat = Image.new("RGB", im.size, (255, 255, 255))
                flat.paste(canvas, mask=canvas.getchannel("A"))
                canvas = flat
            params: dict = {}
            if fmt == "JPEG":
                params["optimize"] = True
                params["quality"] = quality or 90
            elif fmt == "WEBP" and quality:
                params["quality"] = quality
            if fmt == "ICO":
                canvas = canvas.copy()
                if canvas.size[0] > 256 or canvas.size[1] > 256:
                    canvas.thumbnail((256, 256))
            canvas.save(dst_path, format=fmt, **params)
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Image conversion failed: {exc}") from exc


def images_to_pdf(paths: list[str | Path], dst_pdf: str | Path) -> None:
    try:
        imgs = [Image.open(p).convert("RGB") for p in paths]
        first, rest = imgs[0], imgs[1:]
        first.save(dst_pdf, format="PDF", save_all=True, append_images=rest)
        for im in imgs:
            im.close()
    except Exception as exc:
        raise ConversionError(f"Images-to-PDF failed: {exc}") from exc


def format_image(src: str | Path) -> tuple[int, int]:
    try:
        with Image.open(src) as im:
            return im.size
    except Exception as exc:
        raise ConversionError(f"Cannot read image: {exc}") from exc


def svg_to_png(src: str | Path, dst: str | Path) -> None:
    src_path, dst_path = Path(src), Path(dst)
    if not src_path.is_file():
        raise ConversionError(f"Input file not found: {src_path}")
    try:
        import cairosvg

        cairosvg.svg2png(url=str(src_path), write_to=str(dst_path))
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(
            f"SVG to PNG failed (SVG support requires the cairosvg package): {exc}"
        ) from exc
import io
from pathlib import Path

import pytest
from PIL import Image

from omni.errors import ConversionError
from omni.images import IMAGE_EXTENSIONS, convert_image, format_image, images_to_pdf, svg_to_png


def make_png(path: Path, mode="RGBA", size=(64, 48), color=(200, 40, 40, 255)):
    Image.new(mode, size, color).save(path, format="PNG")
    return path


def test_extension_set():
    assert {"png", "jpg", "webp", "ico"} <= IMAGE_EXTENSIONS


def test_png_to_jpg(tmp_path):
    dst = tmp_path / "a.jpg"
    convert_image(make_png(tmp_path / "a.png"), dst, quality=85)
    with Image.open(dst) as im:
        assert im.format == "JPEG"


def test_alpha_to_jpg_renders_rgb(tmp_path):
    buf = io.BytesIO()
    Image.new("RGBA", (8, 8), (255, 0, 0, 128)).save(buf, "PNG")
    buf.seek(0)
    src = tmp_path / "alpha.png"
    src.write_bytes(buf.getvalue())
    convert_image(src, tmp_path / "alpha.jpg")
    with Image.open(tmp_path / "alpha.jpg") as im:
        assert im.mode == "RGB"


def test_convert_webp_and_ico(tmp_path):
    src = make_png(tmp_path / "b.png")
    for ext in ("webp", "ico"):
        dst = tmp_path / f"b.{ext}"
        convert_image(src, dst)
        assert dst.stat().st_size > 0


def test_unsupported_target_raises(tmp_path):
    src = make_png(tmp_path / "d.png")
    with pytest.raises(ConversionError):
        convert_image(src, tmp_path / "d.xyz")


def test_missing_source_raises(tmp_path):
    with pytest.raises(ConversionError):
        convert_image(tmp_path / "nope.png", tmp_path / "x.jpg")


def test_images_to_pdf_multi(tmp_path):
    paths = [make_png(tmp_path / f"p{i}.png", size=(32, 32), color=(i * 50, 0, 0)) for i in range(3)]
    pdf = tmp_path / "pages.pdf"
    images_to_pdf(paths, pdf)
    import fitz
    doc = fitz.open(pdf)
    assert doc.page_count == 3
    doc.close()


def test_format_image(tmp_path):
    src = make_png(tmp_path / "s.png", size=(10, 20))
    assert format_image(src) == (10, 20)


def test_svg_to_png_skips_if_cairosvg_missing(tmp_path):
    try:
        import cairosvg  # noqa: F401
    except Exception:
        pytest.skip("cairosvg not importable")
    svg = tmp_path / "star.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"><circle cx="20" cy="20" r="15" fill="red"/></svg>', encoding="utf-8")
    dst = tmp_path / "star.png"
    svg_to_png(svg, dst)
    with Image.open(dst) as im:
        assert im.format == "PNG"
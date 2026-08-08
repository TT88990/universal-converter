# OmniConvert Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file Windows desktop app (Python + customtkinter) that converts files across images, documents, audio, video, text encodings, and hashes — then publish it to GitHub as an MIT open-source repo with a release EXE.

**Architecture:** Pure conversion logic in an `omni/` package (no GUI imports) so every converter is unit-testable. A thin customtkinter UI (`main.py`, `omni/ui.py`) with one tab per category calls into `omni/converters`. ffmpeg is bundled via the `imageio-ffmpeg` pip package (static binary). Hash/encoding tools are stdlib-only.

**Tech Stack:** Python 3.13 (via `py` launcher), customtkinter, Pillow, PyMuPDF (pymupdf), python-docx, imageio-ffmpeg, markdown, tkinterdnd2, PyInstaller, pytest.

## Global Constraints

- Python 3.13; use the venv at `.venv` (created in Task 1). All commands: `.venv\Scripts\python.exe -m pytest ...` (PowerShell on Windows).
- Core conversion modules MUST NOT import tkinter/customtkinter (UI-free, testable).
- Every converter raises `omni.errors.ConversionError` with a user-friendly message on failure — never raw exceptions across module boundaries. Text is UTF-8 unless a converter's API specifies another encoding.
- ffmpeg is located ONLY through `omni.ffmpeg.ffmpeg_exe()`.
- No binary test assets in git — tests generate them with Pillow / wave / pymupdf / python-docx / ffmpeg `testsrc`.
- Commit after every step that ends a green test cycle; messages: `feat:`, `test:`, `build:`, `docs:`.
- Repo-local git identity (set once in Task 1): name `TT88990`, email `TT88990@users.noreply.github.com`.
- GUI must never freeze: all conversions run on a background thread with a progress callback.
- App is offline-only; no network calls in any code path except the GitHub publish task.
- README in English; conversion table generated from `omni.matrix.MATRIX`.

---

## Task 1: Project Scaffold + venv + smoke test

**Files:**
- Create: `requirements.txt`, `pyproject.toml`, `.gitignore`, `omni/__init__.py`, `omni/errors.py`, `tests/test_smoke.py`, `README.md` (placeholder)

**Interfaces:**
- Consumes: nothing.
- Produces: `omni.__version__`; `omni.errors.ConversionError` (subclasses Exception, has `.message`); `omni` importable from repo root; pytest green.

- [ ] **Step 1: Create venv and install dependencies**

```powershell
py -3 -m venv .venv
.venvScriptspython.exe -m pip install --upgrade pip
.venvScriptspython.exe -m pip install customtkinter Pillow pymupdf python-docx imageio-ffmpeg tkinterdnd2 markdown pytest pyinstaller
```

- [ ] **Step 2: Write the failing test**

`tests/test_smoke.py`:

```python
import omni
from omni.errors import ConversionError


def test_version():
    assert omni.__version__.count(".") == 2


def test_error_is_exception():
    err = ConversionError("boom")
    assert err.message == "boom"
    assert isinstance(err, Exception)
```

- [ ] **Step 3: Run it to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'omni'`

- [ ] **Step 4: Write minimal implementation**

`omni/__init__.py`:

```python
__version__ = "0.1.0"
```

`omni/errors.py`:

```python
class ConversionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
```

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

`requirements.txt`:

```
customtkinter>=5.2
pillow>=10.0
pymupdf>=1.24
python-docx>=1.1
imageio-ffmpeg>=0.4
tkinterdnd2>=0.4
markdown>=3.5
pytest>=8.0
pyinstaller>=6.3
# optional: cairosvg (enables svg -> png; needs native cairo DLLs on Windows)
```

`.gitignore`:

```
__pycache__/
*.pyc
.venv/
dist/
build/
*.spec
output/
*.log
```

- [ ] **Step 5: Run tests, verify pass**

Run: `.venv\Scripts\python.exe -m pytest -v`
Expected: 2 passed

- [ ] **Step 6: Set git identity and commit**

```bash
git config user.name "TT88990"
git config user.email "TT88990@users.noreply.github.com"
git add -A
git commit -m "feat: scaffold project, venv deps, smoke tests"
```

---

## Task 2: ffmpeg wrapper (`omni/ffmpeg.py`)

**Files:**
- Create: `omni/ffmpeg.py`, `tests/test_ffmpeg.py`

**Interfaces:**
- Consumes: `omni.errors.ConversionError`.
- Produces:
  - `ffmpeg_exe() -> str` — absolute path to bundled ffmpeg (via `imageio_ffmpeg.get_ffmpeg_exe()`); raises ConversionError with instructive message if unavailable.
  - `run_ffmpeg(args: list[str]) -> None` — runs `[ffmpeg_exe(), "-hide_banner", "-nostdin", "-y"] + args`; raises ConversionError with last 5 stderr lines on non-zero exit.
  - `has_ffmpeg() -> bool` — never raises.

- [ ] **Step 1: Write the failing test**

`tests/test_ffmpeg.py`:

```python
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
```

- [ ] **Step 2: Run, verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ffmpeg.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.ffmpeg'`

- [ ] **Step 3: Implement**

`omni/ffmpeg.py`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ffmpeg.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add omni/ffmpeg.py tests/test_ffmpeg.py
git commit -m "feat: ffmpeg binary locator and runner"
```

---

## Task 3: Hashing & encoding tools (`omni/hashgen.py`)

**Files:**
- Create: `omni/hashgen.py`, `tests/test_hashgen.py`

**Interfaces:**
- Produces:
  - `HASH_ALGORITHMS: tuple[str, ...]` — ("md5","sha1","sha224","sha256","sha384","sha512","sha3_256","sha3_512","blake2b")
  - `hash_bytes(data: bytes) -> dict[str, str]` — key per algorithm; plus `crc32` as 8-digit zero-padded hex; all lowercase hex.
  - `hash_text(text: str) -> dict[str, str]` — UTF-8 bytes.
  - `hash_file(path: str|os.PathLike) -> dict[str, str]` — reads in 64 KiB chunks.
  - `encode_base64(data: bytes) -> str`, `decode_base64(s: str) -> bytes` (ConversionError on bad input)
  - `to_hex(data: bytes) -> str`, `from_hex(s: str) -> bytes` (ConversionError on non-hex)

- [ ] **Step 1: Write the failing test**

`tests/test_hashgen.py`:

```python
import tempfile
from pathlib import Path

import pytest

from omni.errors import ConversionError
from omni.hashgen import (
    decode_base64,
    encode_base64,
    from_hex,
    hash_bytes,
    hash_file,
    hash_text,
    to_hex,
)


def test_md5_known_vector():
    assert hash_text("abc")["md5"] == "900150983cd24fb0d6963f7d28e17f72"


def test_sha256_known_vector():
    assert hash_text("abc")["sha256"] == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_crc32_vector():
    assert hash_text("hello")["crc32"] == "3610a686"


def test_all_algos_present():
    h = hash_text("abc")
    for algo in ("md5", "sha1", "sha224", "sha256", "sha384", "sha512", "sha3_256", "sha3_512", "blake2b", "crc32"):
        assert algo in h and len(h[algo]) > 0


def test_hash_bytes_and_text_agree():
    assert hash_bytes(b"abc")["md5"] == hash_text("abc")["md5"]


def test_file_hash_matches_text(tmp_path):
    p = tmp_path / "fixture.txt"
    p.write_text("abc", encoding="utf-8")
    assert hash_file(p)["md5"] == hash_text("abc")["md5"]


def test_base64_roundtrip():
    assert encode_base64(b"hello world") == "aGVsbG8gd29ybGQ="
    assert decode_base64("aGVsbG8gd29ybGQ=") == b"hello world"


def test_base64_decode_invalid():
    with pytest.raises(ConversionError):
        decode_base64("!!not-base64!!")


def test_hex_roundtrip_and_errors():
    assert to_hex(b"\x00\xff") == "00ff"
    assert from_hex("00 ff") == b"\x00\xff"
    with pytest.raises(ConversionError):
        from_hex("zz")
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_hashgen.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.hashgen'`

- [ ] **Step 3: Implement**

`omni/hashgen.py`:

```python
import base64
import hashlib
import zlib
from pathlib import Path

from omni.errors import ConversionError

HASH_ALGORITHMS = ("md5", "sha1", "sha224", "sha256", "sha384", "sha512", "sha3_256", "sha3_512", "blake2b")


def hash_bytes(data: bytes) -> dict[str, str]:
    out = {algo: hashlib.new(algo, data).hexdigest() for algo in HASH_ALGORITHMS}
    out["crc32"] = format(zlib.crc32(data) & 0xFFFFFFFF, "08x")
    return out


def hash_text(text: str) -> dict[str, str]:
    return hash_bytes(text.encode("utf-8"))


def hash_file(path: str | Path) -> dict[str, str]:
    digests = {algo: hashlib.new(algo) for algo in HASH_ALGORITHMS}
    crc = 0
    with open(path, "rb") as fh:
        while chunk := fh.read(65536):
            for d in digests.values():
                d.update(chunk)
            crc = zlib.crc32(chunk, crc)
    out = {algo: d.hexdigest() for algo, d in digests.items()}
    out["crc32"] = format(crc & 0xFFFFFFFF, "08x")
    return out


def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_base64(s: str) -> bytes:
    try:
        return base64.b64decode(s.strip(), validate=True)
    except Exception as exc:
        raise ConversionError("Invalid Base64 input") from exc


def to_hex(data: bytes) -> str:
    return data.hex()


def from_hex(s: str) -> bytes:
    try:
        return bytes.fromhex("".join(s.strip().split()))
    except ValueError as exc:
        raise ConversionError("Invalid hexadecimal input") from exc
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_hashgen.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add omni/hashgen.py tests/test_hashgen.py
git commit -m "feat: hash and encoding toolset"
```

---

## Task 4: Image converters (`omni/images.py`)

**Files:**
- Create: `omni/images.py`, `tests/test_images.py`

**Interfaces:**
- Consumes: `omni.errors.ConversionError`.
- Produces:
  - `IMAGE_EXTENSIONS: frozenset[str]` = {"png","jpg","jpeg","webp","bmp","gif","tiff","ico"}
  - `PIXEL_FORMATS: dict[str, str]` — extension → Pillow format name ("jpg"→"JPEG", "jpeg"→"JPEG", "webp"→"WEBP", "bmp"→"BMP", "gif"→"GIF", "tiff"→"TIFF", "ico"→"ICO", "png"→"PNG")
  - `convert_image(src, dst, quality: int|None = None) -> None` — RGBA→RGB on white for JPEG/WEBP; raises ConversionError for missing input or unsupported target.
  - `svg_to_png(src: str|Path, dst: str|Path) -> None` — via cairosvg; raises ConversionError with "SVG support requires cairosvg" if the package or its native deps are unavailable.
  - `images_to_pdf(paths: list[str|Path], dst_pdf: str|Path) -> None` — multi-image PDF (one page per image) via Pillow.
  - `format_image(src, dst) -> tuple[int, int]` — (width, height) used by GUI preview; raises ConversionError if unreadable.

- [ ] **Step 1: Write the failing test**

`tests/test_images.py`:

```python
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
    with Image.open(pdf) as im:
        assert im.n_frames == 3


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
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_images.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.images'`

- [ ] **Step 3: Implement**

`omni/images.py`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_images.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add omni/images.py tests/test_images.py
git commit -m "feat: image converters (Pillow)"
```

---

## Task 5: Document converters (`omni/documents.py`)

**Files:**
- Create: `omni/documents.py`, `tests/test_documents.py`

**Interfaces:**
- Consumes: `omni.errors.ConversionError`; `omni.images.images_to_pdf` (Task 4).
- Produces (all raise ConversionError on failure):
  - `pdf_to_txt(src: str|Path, dst: str|Path) -> None` — PyMuPDF text extraction, paragraphs joined by newline.
  - `pdf_to_docx(src, dst) -> None` — PyMuPDF text → python-docx paragraphs.
  - `pdf_to_md(src, dst) -> None` — text extraction wrapped in a Markdown document.
  - `docx_to_txt(src, dst) -> None` — python-docx paragraphs.
  - `docx_to_md(src, dst) -> None`.
  - `docx_to_pdf(src, dst) -> None` — python-docx → plain-text PDF via PyMuPDF (one page per ~40 lines).
  - `txt_to_docx(src, dst) -> None`.
  - `text_to_pdf(src, dst) -> None` — same text→PDF renderer as docx_to_pdf.
  - `text_to_html(src, dst) -> None` — uses `markdown.markdown()`.
  - `md_to_html(src, dst) -> None` — same.
- Internal helper `_render_text_pdf(text: str, dst: Path) -> None`.

- [ ] **Step 1: Write the failing test**

`tests/test_documents.py`:

```python
from pathlib import Path

import fitz
import pytest
from docx import Document as DocxDocument

from omni.errors import ConversionError
from omni.documents import (
    docx_to_md,
    docx_to_pdf,
    docx_to_txt,
    md_to_html,
    pdf_to_docx,
    pdf_to_md,
    pdf_to_txt,
    text_to_html,
    text_to_pdf,
    txt_to_docx,
)

SAMPLE_TEXT = "Hello OmniConvert!\nSecond line with ünicode."


def make_pdf(path: Path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), SAMPLE_TEXT)
    doc.save(path)
    doc.close()
    return path


def make_docx(path: Path):
    d = DocxDocument()
    d.add_paragraph("Hello OmniConvert!")
    d.add_paragraph("Second line with ünicode.")
    d.save(path)
    return path


def test_pdf_to_txt(tmp_path):
    src = make_pdf(tmp_path / "in.pdf")
    dst = tmp_path / "out.txt"
    pdf_to_txt(src, dst)
    assert "Hello OmniConvert" in dst.read_text(encoding="utf-8")


def test_pdf_to_docx(tmp_path):
    src = make_pdf(tmp_path / "in.pdf")
    dst = tmp_path / "out.docx"
    pdf_to_docx(src, dst)
    docx_to_txt(dst, tmp_path / "round.txt")
    text = (tmp_path / "round.txt").read_text(encoding="utf-8")
    assert "Hello OmniConvert" in text


def test_docx_to_txt(tmp_path):
    make_docx(tmp_path / "in.docx")
    dst = tmp_path / "out.txt"
    docx_to_txt(tmp_path / "in.docx", dst)
    assert "Second line" in dst.read_text(encoding="utf-8")


def test_docx_to_md(tmp_path):
    make_docx(tmp_path / "in.docx")
    docx_to_md(tmp_path / "in.docx", tmp_path / "out.md")
    assert (tmp_path / "out.md").read_text(encoding="utf-8").startswith("#")


def test_docx_to_pdf_roundtrip(tmp_path):
    make_docx(tmp_path / "in.docx")
    docx_to_pdf(tmp_path / "in.docx", tmp_path / "out.pdf")
    assert (tmp_path / "out.pdf").stat().st_size > 1000


def test_txt_to_docx(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text(SAMPLE_TEXT, encoding="utf-8")
    txt_to_docx(src, tmp_path / "out.docx")
    d = DocxDocument(str(tmp_path / "out.docx"))
    assert any("Hello OmniConvert" in p.text for p in d.paragraphs)


def test_text_to_pdf(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text(SAMPLE_TEXT, encoding="utf-8")
    text_to_pdf(src, tmp_path / "out.pdf")
    assert (tmp_path / "out.pdf").stat().st_size > 1000


def test_md_and_text_to_html(tmp_path):
    md = tmp_path / "in.md"
    md.write_text("# Title\n\npara", encoding="utf-8")
    md_to_html(md, tmp_path / "out.html")
    html = (tmp_path / "out.html").read_text(encoding="utf-8")
    assert "<h1" in html
    text_to_html(tmp_path / "out.html", tmp_path / "out2.html")


def test_missing_source_raises(tmp_path):
    with pytest.raises(ConversionError):
        pdf_to_txt(tmp_path / "nope.pdf", tmp_path / "x.txt")
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_documents.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.documents'`

- [ ] **Step 3: Implement**

`omni/documents.py`:

```python
from pathlib import Path

import fitz
import markdown as md_lib
from docx import Document as DocxDocument

from omni.errors import ConversionError
from omni.images import images_to_pdf


def _require_input(src: Path) -> None:
    if not src.is_file():
        raise ConversionError(f"Input file not found: {src}")


def _render_text_pdf(text: str, dst: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    lines_per_page = 40
    lines = text.splitlines() or [""]
    for start in range(0, len(lines), lines_per_page):
        if start > 0:
            page = doc.new_page()
        chunk = "\n".join(lines[start : start + lines_per_page])
        page.insert_textbox(fitz.Rect(72, 72, 540, 780), chunk, fontsize=11)
    doc.save(dst)
    doc.close()


def pdf_to_txt(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        doc = fitz.open(src_path)
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        dst_path.write_text(text, encoding="utf-8")
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"PDF to TXT failed: {exc}") from exc


def pdf_to_docx(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        doc = fitz.open(src_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        out = DocxDocument()
        for para in text.splitlines():
            if para.strip():
                out.add_paragraph(para)
        out.save(dst_path)
    except Exception as exc:
        raise ConversionError(f"PDF to DOCX failed: {exc}") from exc


def pdf_to_md(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        doc = fitz.open(src_path)
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        dst_path.write_text(f"# Converted from PDF\n\n{text}\n", encoding="utf-8")
    except Exception as exc:
        raise ConversionError(f"PDF to MD failed: {exc}") from exc


def docx_to_txt(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        d = DocxDocument(str(src_path))
        text = "\n".join(p.text for p in d.paragraphs)
        dst_path.write_text(text, encoding="utf-8")
    except Exception as exc:
        raise ConversionError(f"DOCX to TXT failed: {exc}") from exc


def docx_to_md(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        d = DocxDocument(str(src_path))
        parts = ["# Document", ""]
        for p in d.paragraphs:
            if p.text.strip():
                parts.append(p.text)
                parts.append("")
        dst_path.write_text("\n".join(parts), encoding="utf-8")
    except Exception as exc:
        raise ConversionError(f"DOCX to MD failed: {exc}") from exc


def docx_to_pdf(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        d = DocxDocument(str(src_path))
        text = "\n".join(p.text for p in d.paragraphs if p.text.strip())
        _render_text_pdf(text, dst_path)
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"DOCX to PDF failed: {exc}") from exc


def text_to_pdf(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        _render_text_pdf(src_path.read_text(encoding="utf-8"), dst_path)
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"TXT to PDF failed: {exc}") from exc


def txt_to_docx(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        text = src_path.read_text(encoding="utf-8")
        out = DocxDocument()
        for para in text.splitlines():
            out.add_paragraph(para)
        out.save(dst_path)
    except Exception as exc:
        raise ConversionError(f"TXT to DOCX failed: {exc}") from exc


def _text_to_html(src_path: Path, dst_path: Path) -> None:
    text = src_path.read_text(encoding="utf-8")
    body = md_lib.markdown(text) if src_path.suffix.lower() == ".md" else text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>\n")
    dst_path.write_text(
        f"<!doctype html><html><meta charset=\"utf-8\"><body>{body}</body></html>",
        encoding="utf-8",
    )


def md_to_html(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        _text_to_html(src_path, dst_path)
    except Exception as exc:
        raise ConversionError(f"MD to HTML failed: {exc}") from exc


def text_to_html(src, dst) -> None:
    src_path, dst_path = Path(src), Path(dst)
    _require_input(src_path)
    try:
        _text_to_html(src_path, dst_path)
    except Exception as exc:
        raise ConversionError(f"TXT to HTML failed: {exc}") from exc
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_documents.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add omni/documents.py tests/test_documents.py
git commit -m "feat: document converters (PDF/DOCX/TXT/MD/HTML)"
```

---

## Task 6: Audio converters (`omni/audio.py`)

**Files:**
- Create: `omni/audio.py`, `tests/test_audio.py`

**Interfaces:**
- Consumes: `omni.ffmpeg.run_ffmpeg` (Task 2).
- Produces:
  - `AUDIO_FORMATS: dict[str, str]` — ext → ffmpeg args list: mp3 `["-c:a","libmp3lame","-b:a","192k"]`, wav `["-c:a","pcm_s16le"]`, flac `["-c:a","flac"]`, ogg `["-c:a","libvorbis","-q:a","5"]`, opus `["-c:a","libopus","-b:a","128k"]`, m4a `["-c:a","aac","-b:a","192k"]`, wma `["-c:a","wmav2","-b:a","192k"]`
  - `convert_audio(src: str|Path, dst: str|Path, bitrate_k: int|None = None) -> None` — `run_ffmpeg(["-i", str(src), *params, str(dst)])`; if bitrate_k given, override `-b:a` to `{bitrate_k}k` (skip for flac/wav).
  - `extract_audio(src_video: str|Path, dst_audio: str|Path) -> None` — ffmpeg `-vn` with dst format params.

- [ ] **Step 1: Write the failing test**

`tests/test_audio.py`:

```python
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
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_audio.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.audio'`

- [ ] **Step 3: Implement**

`omni/audio.py`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_audio.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add omni/audio.py tests/test_audio.py
git commit -m "feat: audio converters via ffmpeg"
```

---

## Task 7: Video converters (`omni/video.py`)

**Files:**
- Create: `omni/video.py`, `tests/test_video.py`

**Interfaces:**
- Consumes: `omni.ffmpeg.run_ffmpeg`.
- Produces:
  - `VIDEO_FORMATS: dict[str, list[str]]` — mp4 `["-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac"]`, avi `["-c:v","mpeg4","-c:a","mp3"]`, mkv `["-c:v","libx264","-c:a","aac"]`, mov `["-c:v","libx264","-c:a","aac"]`, webm `["-c:v","libvpx-vp9","-c:a","libopus","-b:v","1M"]`, gif `["-vf","fps=15,scale=480:-1:flags=lanczos","-f","gif"]`
  - `convert_video(src, dst) -> None`
  - `extract_frames(src, out_dir: str|Path, fps: float = 1.0) -> list[Path]` — `-vf fps={fps}` PNG sequence `frame_%04d.png`; returns created files.
  - `extract_audio(src, dst) -> None` — delegate to `omni.audio.extract_audio`.

- [ ] **Step 1: Write the failing test**

`tests/test_video.py`:

```python
from pathlib import Path

import pytest

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
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_video.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.video'`

- [ ] **Step 3: Implement**

`omni/video.py`:

```python
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
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_video.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add omni/video.py tests/test_video.py
git commit -m "feat: video converters and frame extraction via ffmpeg"
```

---

## Task 8: Text/encoding converters (`omni/texconv.py`)

**Files:**
- Create: `omni/texconv.py`, `tests/test_texconv.py`

**Interfaces:**
- Consumes: `omni.errors.ConversionError`.
- Produces:
  - `TEXT_ENCODINGS: tuple[str, ...]` = ("utf-8","utf-16","utf-16-le","utf-16-be","ascii","latin-1")
  - `convert_text(src, dst, in_enc="utf-8", out_enc="utf-8", newline: str|None = None) -> None` — strict codec decoding (raises ConversionError with "undecodable" message on bad bytes); optional newline normalization to "\n"/"\r\n" via `.replace("\r\n","\n").replace("\r","\n")` then `("\n", newline)`.
  - `convert_base64(src, dst, mode: str) -> None` — mode "encode"|"decode"; reads bytes, writes text (encode) or bytes (decode).
  - `convert_hex(src, dst, mode: str) -> None` — "encode"|"decode" using omni.hashgen.to_hex/from_hex; decode writes raw bytes.

- [ ] **Step 1: Write the failing test**

`tests/test_texconv.py`:

```python
from pathlib import Path

import pytest

from omni.errors import ConversionError
from omni.texconv import TEXT_ENCODINGS, convert_base64, convert_hex, convert_text


def test_encodings_defined():
    assert set(TEXT_ENCODINGS) == {"utf-8", "utf-16", "utf-16-le", "utf-16-be", "ascii", "latin-1"}


def test_utf8_to_utf16_roundtrip(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("Hello ünïcode", encoding="utf-8")
    dst = tmp_path / "a16.txt"
    convert_text(src, dst, in_enc="utf-8", out_enc="utf-16")
    back = tmp_path / "back.txt"
    convert_text(dst, back, in_enc="utf-16", out_enc="utf-8")
    assert back.read_text(encoding="utf-8") == "Hello ünïcode"


def test_bad_bytes_raise(tmp_path):
    src = tmp_path / "bad.txt"
    src.write_bytes(b"\xff\xfe\x00 invalid")
    with pytest.raises(ConversionError):
        convert_text(src, tmp_path / "x.txt", in_enc="ascii", out_enc="utf-8")


def test_newline_normalization(tmp_path):
    src = tmp_path / "crlf.txt"
    src.write_text("a\r\nb\rc", encoding="utf-8")
    dst = tmp_path / "lf.txt"
    convert_text(src, dst, out_enc="utf-8", newline="\n")
    assert dst.read_text(encoding="utf-8") == "a\nb\nc"


def test_base64_encode_decode_files(tmp_path):
    src = tmp_path / "raw.bin"
    src.write_bytes(b"\x00\x01hello")
    enc = tmp_path / "enc.txt"
    convert_base64(src, enc, "encode")
    assert enc.read_text(encoding="utf-8") == "AAFoZWxsbw=="
    dec = tmp_path / "dec.bin"
    convert_base64(enc, dec, "decode")
    assert dec.read_bytes() == b"\x00\x01hello"


def test_hex_encode_decode_files(tmp_path):
    src = tmp_path / "raw.bin"
    src.write_bytes(b"\x00\xffAB")
    enc = tmp_path / "hex.txt"
    convert_hex(src, enc, "encode")
    assert enc.read_text(encoding="utf-8") == "00ff4142"
    dec = tmp_path / "dec.bin"
    convert_hex(enc, dec, "decode")
    assert dec.read_bytes() == b"\x00\xffAB"


def test_missing_source_raises(tmp_path):
    with pytest.raises(ConversionError):
        convert_text(tmp_path / "nope.txt", tmp_path / "x.txt")
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_texconv.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.texconv'`

- [ ] **Step 3: Implement**

`omni/texconv.py`:

```python
from pathlib import Path

from omni.errors import ConversionError
from omni.hashgen import from_hex, to_hex

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
```

Note: add helpers `_b64`/`_unb64` re-exporting `encode_base64`/`decode_base64` from `omni.hashgen` (Task 3) — implement as module-level imports: `from omni.hashgen import decode_base64 as _unb64, encode_base64 as _b64`.

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_texconv.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add omni/texconv.py tests/test_texconv.py
git commit -m "feat: text encoding, base64 and hex converters"
```

---

## Task 9: Conversion matrix + batch runner (`omni/matrix.py`, `omni/runner.py`)

**Files:**
- Create: `omni/matrix.py`, `omni/runner.py`, `tests/test_matrix.py`, `tests/test_runner.py`

**Interfaces:**
- Consumes: all converters (Tasks 2-8).
- Produces:
  - `CATEGORIES: dict[str, dict[str, list[str]]]` — category name → {input ext → [output exts]}; each entry lists which converter handles it; e.g. Images: {"png": ["jpg","webp","bmp","gif","tiff","ico","pdf"], "jpg": [...], "svg": ["png"], ...}; Documents: {"pdf": ["txt","docx","md"], "docx": ["txt","md","pdf"], "txt": ["docx","pdf","html"], "md": ["html"]}; Audio: {"wav": ["mp3","flac","ogg","opus","m4a","wma"], ...}; Video: {"mp4": ["avi","mkv","mov","webm","gif"], "avi": [...], "mkv": [...], "mov": [...], "webm": [...], "gif": ["mp4","webm"]}; Text: {"txt": ["utf-16","utf-16-le","utf-16-be","ascii","latin-1","base64","hex"], "md": ["html"]}.
  - `VALID_TARGETS(category: str, src_ext: str) -> list[str]`
  - `CONVERTERS: dict[str, dict[str, dict[str, object]]]` — category → {source ext → {target ext → converter callable}}. Signature convention: `fn(src: Path, dst: Path, **kw) -> None`; the special key ("pdf" target with image sources) is reached via `CONVERTERS["Images"][src]["pdf"]` → `omni.images.images_to_pdf` which takes a list — the Runner handles it. The runner dispatches on BOTH source and target extension.
  - `Job` dataclass: `src: Path`, `target_ext: str`, `category: str`.
  - `unique_output_path(out_dir: Path, src: Path, ext: str) -> Path` — `src.stem.ext`, suffix ` (1)`, ` (2)`...
  - `Runner.run(jobs: list[Job], out_dir: Path, on_progress: callable[[int, int, str, str], None] | None = None) -> list[tuple[Path, str|None]]` — runs sequentially in the calling thread (GUI wraps in thread), calls `on_progress(done, total, src_name, status)`; returns list of (out_path, error_message_or_None).

- [ ] **Step 1: Write the failing test**

`tests/test_matrix.py`:

```python
from omni.matrix import CATEGORIES, VALID_TARGETS


def test_categories_present():
    assert {"Images", "Documents", "Audio", "Video", "Text"} <= set(CATEGORIES)


def test_png_targets():
    t = VALID_TARGETS("Images", "png")
    assert {"jpg", "webp", "pdf"} <= set(t)


def test_pdf_targets():
    t = VALID_TARGETS("Documents", "pdf")
    assert {"txt", "docx", "md"} <= set(t)


def test_mp4_targets():
    t = VALID_TARGETS("Video", "mp4")
    assert {"avi", "webm", "gif", "mov"} <= set(t)


def test_wav_targets():
    t = VALID_TARGETS("Audio", "wav")
    assert {"mp3", "flac", "opus"} <= set(t)


def test_unknown_ext_empty():
    assert VALID_TARGETS("Images", "xyz") == []
```

`tests/test_runner.py`:

```python
import io
from pathlib import Path

from PIL import Image

from omni.runner import Job, Runner, unique_output_path


def make_png(path: Path):
    Image.new("RGBA", (32, 32), (10, 200, 30, 255)).save(path, "PNG")
    return path


def test_unique_output_path(tmp_path):
    src = tmp_path / "pic.png"
    make_png(src)
    first = unique_output_path(tmp_path, src, "jpg")
    (tmp_path / "pic.jpg").write_bytes(b"x")
    second = unique_output_path(tmp_path, src, "jpg")
    assert first.name == "pic.jpg"
    assert second.name == "pic (1).jpg"


def test_runner_converts_batch(tmp_path):
    srcs = [make_png(tmp_path / f"p{i}.png") for i in range(3)]
    out = tmp_path / "out"
    jobs = [Job(src=s, target_ext="webp", category="Images") for s in srcs]
    results = Runner().run(jobs, out)
    assert len(results) == 3
    assert all(err is None for _, err in results)
    assert all(p.exists() for p, _ in results)


def test_runner_reports_progress_and_error(tmp_path):
    src = make_png(tmp_path / "ok.png")
    missing = tmp_path / "gone.png"
    calls = []
    results = Runner().run(
        [Job(src=missing, target_ext="jpg", category="Images"), Job(src=src, target_ext="jpg", category="Images")],
        tmp_path / "out",
        on_progress=lambda d, t, n, s: calls.append((d, t, n, s)),
    )
    assert calls[-1][0] == 2 and calls[-1][1] == 2
    assert results[0][1] is not None
    assert results[1][1] is None
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_matrix.py tests/test_runner.py -v`
Expected: FAIL `ModuleNotFoundError: No module named 'omni.matrix'`

- [ ] **Step 3: Implement**

`omni/matrix.py`:

```python
from omni import audio, documents, images, texconv, video

CATEGORIES: dict[str, dict[str, list[str]]] = {
    "Images": {ext: sorted({"jpg", "png", "webp", "bmp", "gif", "tiff", "ico", "pdf"} - {ext}) for ext in images.IMAGE_EXTENSIONS}
    | {"svg": ["png"]},
    "Documents": {
        "pdf": ["txt", "docx", "md"],
        "docx": ["txt", "md", "pdf"],
        "txt": ["docx", "pdf", "html"],
        "md": ["html"],
    },
    "Audio": {ext: sorted(set(audio.AUDIO_FORMATS) - {ext}) for ext in audio.AUDIO_FORMATS},
    "Video": {
        "mp4": ["avi", "mkv", "mov", "webm", "gif"],
        "avi": ["mp4", "mkv", "mov", "webm", "gif"],
        "mkv": ["mp4", "avi", "mov", "webm", "gif"],
        "mov": ["mp4", "avi", "mkv", "webm", "gif"],
        "webm": ["mp4", "avi", "mkv", "mov", "gif"],
        "gif": ["mp4", "webm"],
    },
    "Text": {
        "txt": ["utf-16", "utf-16-le", "utf-16-be", "ascii", "latin-1", "base64", "hex"],
        "md": ["html"],
    },
}


def VALID_TARGETS(category: str, src_ext: str) -> list[str]:
    return list(CATEGORIES.get(category, {}).get(src_ext, []))


CONVERTERS: dict[str, dict[str, dict[str, object]]] = {
    "Images": {
        ext: {
            "pdf": documents.images_to_pdf,
            **{t: images.convert_image for t in ("png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico")},
        }
        for ext in ("png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico")
    }
    | {"svg": {"png": images.svg_to_png}},
    "Documents": {
        "pdf": {"txt": documents.pdf_to_txt, "docx": documents.pdf_to_docx, "md": documents.pdf_to_md},
        "docx": {"txt": documents.docx_to_txt, "md": documents.docx_to_md, "pdf": documents.docx_to_pdf},
        "txt": {"docx": documents.txt_to_docx, "pdf": documents.text_to_pdf, "html": documents.text_to_html},
        "md": {"html": documents.md_to_html},
    },
    "Audio": {ext: {t: audio.convert_audio for t in audio.AUDIO_FORMATS if t != ext} for ext in audio.AUDIO_FORMATS},
    "Video": {src: {t: video.convert_video for t in targets} for src, targets in CATEGORIES["Video"].items()},
    "Text": {
        "txt": {
            "base64": lambda s, d, **kw: texconv.convert_base64(s, d, "encode"),
            "hex": lambda s, d, **kw: texconv.convert_hex(s, d, "encode"),
            "utf-16": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="utf-16", **kw),
            "utf-16-le": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="utf-16-le", **kw),
            "utf-16-be": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="utf-16-be", **kw),
            "ascii": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="ascii", **kw),
            "latin-1": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="latin-1", **kw),
        },
        "md": {"html": documents.md_to_html},
    },
}
```

`omni/runner.py`:

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from omni.matrix import CONVERTERS

ProgressCb = Callable[[int, int, str, str], None]


@dataclass
class Job:
    src: Path
    target_ext: str
    category: str


def unique_output_path(out_dir: Path, src: Path, ext: str) -> Path:
    candidate = out_dir / f"{src.stem}.{ext}"
    n = 1
    while candidate.exists():
        candidate = out_dir / f"{src.stem} ({n}).{ext}"
        n += 1
    return candidate


class Runner:
    def __init__(self) -> None:
        self.converters = CONVERTERS

    def run(self, jobs: list[Job], out_dir: Path, on_progress: ProgressCb | None = None) -> list[tuple[Path, str | None]]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results: list[tuple[Path, str | None]] = []
        total = len(jobs)
        for done, job in enumerate(jobs, start=1):
            target = unique_output_path(out_dir, job.src, job.target_ext)
            error: str | None = None
            try:
                src_ext = job.src.suffix.lower().lstrip(".")
                fn = self.converters[job.category][src_ext][job.target_ext]
                if job.target_ext == "pdf" and job.category == "Images":
                    fn([job.src], target)
                else:
                    fn(job.src, target)
            except Exception as exc:
                error = str(exc)
            results.append((target, error))
            if on_progress:
                on_progress(done, total, job.src.name, "done" if error is None else f"error: {error}")
        return results
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_matrix.py tests/test_runner.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add omni/matrix.py omni/runner.py tests/test_matrix.py tests/test_runner.py
git commit -m "feat: conversion matrix and batch runner"
```

---

## Task 10: GUI application (`main.py`, `omni/ui.py`)

**Files:**
- Create: `omni/ui.py`, `main.py`, `tests/test_ui_selftest.py`

**Interfaces:**
- Consumes: `omni.matrix`, `omni.runner` (Task 9), `omni.hashgen` (Task 3).
- Produces:
  - `class App(ctk.CTk)` — constructor builds window (1100x700, dark, `ctk.set_appearance_mode("dark")`), tabview with tabs Images/Documents/Audio/Video/Text/Hash/Formats.
  - Each file tab: "Add Files" button, file list (multi-select listbox), output-dir picker entry + "Browse", target format OptionMenu (filled from `VALID_TARGETS`), "Convert" button, progress bar, log textbox.
  - Hash tab: text input Textbox + "Load File" button + refresh-on-type; per-hash label + "Copy" button; uses `omni.hashgen`.
  - Formats tab: scrollable frame listing each category and its source→targets from `omni.matrix.CATEGORIES`.
  - `main.py --selftest` CLI flag: builds App, pumps 10 idles, prints "SELFTEST OK", destroys, exit 0. Any tkinter init error → exit 1.

- [ ] **Step 1: Write the failing test**

`tests/test_ui_selftest.py`:

```python
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_selftest():
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--selftest"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "SELFTEST OK" in proc.stdout
```

- [ ] **Step 2: Run, verify fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ui_selftest.py -v`
Expected: FAIL (main.py missing)

- [ ] **Step 3: Implement**

`omni/ui.py`:

```python
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from omni.hashgen import hash_file, hash_text
from omni.matrix import CATEGORIES, VALID_TARGETS
from omni.runner import Job, Runner


class DnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class ConvertTab(ctk.CTkFrame):
    def __init__(self, master, category: str):
        super().__init__(master)
        self.category = category
        self.files: list[Path] = []
        self.target = ctk.StringVar(value="")
        self.out_dir = ctk.StringVar(value=str(Path.cwd() / "output"))

        ctk.CTkButton(self, text="Add Files...", command=self._pick).grid(row=0, column=0, padx=5, pady=5)
        self.file_list = ctk.CTkTextbox(self, height=160, width=560)
        self.file_list.grid(row=0, column=1, rowspan=4, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self, text="Output folder").grid(row=0, column=2, sticky="w")
        ctk.CTkEntry(self, textvariable=self.out_dir, width=200).grid(row=1, column=2, padx=5)
        ctk.CTkButton(self, text="Browse...", command=self._pick_out).grid(row=2, column=2, padx=5)
        self.target_menu = ctk.CTkOptionMenu(self, values=[], variable=self.target, state="disabled")
        self.target_menu.grid(row=3, column=2, padx=5)
        self.convert_btn = ctk.CTkButton(self, text="Convert", command=self._convert)
        self.convert_btn.grid(row=4, column=1, padx=5, pady=5)
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.log = ctk.CTkTextbox(self, height=120, width=760)
        self.log.grid(row=6, column=0, columnspan=3, padx=5, pady=5)
        self.grid_columnconfigure(1, weight=1)
        self._drop_target_register()

    def _drop_target_register(self):
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        self._add_paths([Path(p.strip("{}")) for p in self.winfo_toplevel().tk.splitlist(event.data)])

    def _pick(self):
        self._add_paths([Path(p) for p in filedialog.askopenfilenames()])

    def _add_paths(self, paths: list[Path]):
        for p in paths:
            ext = p.suffix.lower().lstrip(".")
            if VALID_TARGETS(self.category, ext):
                self.files.append(p)
            else:
                self._log(f"skipped {p.name} (no conversion in {self.category} tab)")
        self._refresh_list_and_targets()

    def _refresh_list_and_targets(self):
        self.file_list.delete("1.0", "end")
        for p in self.files:
            self.file_list.insert("end", p.name + "\n")
        ext = self.files[0].suffix.lower().lstrip(".") if self.files else ""
        targets = VALID_TARGETS(self.category, ext) if ext else []
        self.target_menu.configure(values=targets, state="normal" if targets else "disabled")
        if targets:
            self.target.set(targets[0])

    def _pick_out(self):
        d = filedialog.askdirectory()
        if d:
            self.out_dir.set(d)

    def _convert(self):
        if not self.files or not self.target.get():
            return
        self.convert_btn.configure(state="disabled")
        jobs = [Job(src=p, target_ext=self.target.get(), category=self.category) for p in self.files]
        out = Path(self.out_dir.get())
        self.progress.set(0)

        def work():
            Runner().run(jobs, out, on_progress=self._on_progress)
            self.after(0, lambda: self.convert_btn.configure(state="normal"))

        threading.Thread(target=work, daemon=True).start()

    def _on_progress(self, done, total, name, status):
        self.after(0, lambda: (self.progress.set(done / total), self._log(f"[{done}/{total}] {name}: {status}")))

    def _log(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
```

`omni/ui.py` (hash tab + formats tab, appended to same file):

```python
class HashTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.input = ctk.CTkTextbox(self, height=140, width=700)
        self.input.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(self, text="Load File...", command=self._load_file).grid(row=1, column=0, sticky="w", padx=10)
        self.results = ctk.CTkTextbox(self, height=260, width=700)
        self.results.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self._hash()

    def _load_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.input.delete("1.0", "end")
            self.input.insert("1.0", Path(p).name + " (file hashed)")
            self._hash_from_file(Path(p))

    def _hash(self):
        text = self.input.get("1.0", "end").strip()
        if not text or text.endswith("(file hashed)"):
            return
        self._show(hash_text(text))

    def _hash_from_file(self, path: Path):
        self._show(hash_file(path))

    def _show(self, digests: dict):
        self.results.delete("1.0", "end")
        for algo, value in digests.items():
            self.results.insert("end", f"{algo:10s} {value}\n")


class FormatsTab(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        row = 0
        for category, mapping in CATEGORIES.items():
            ctk.CTkLabel(self, text=f"=== {category} ===", font=("Segoe UI", 15, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=(10, 2))
            row += 1
            for src, targets in mapping.items():
                line = f"  .{src} -> " + ", ".join(f".{t}" for t in targets)
                ctk.CTkLabel(self, text=line, anchor="w").grid(row=row, column=0, sticky="w", padx=5)
                row += 1


class App(DnDApp):
    def __init__(self):
        super().__init__()
        self.title("OmniConvert")
        self.geometry("1100x700")
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True)
        for name in ("Images", "Documents", "Audio", "Video", "Text"):
            self.tabs.add(name)
            ConvertTab(self.tabs.tab(name), name).pack(fill="both", expand=True)
        self.tabs.add("Hash")
        HashTab(self.tabs.tab("Hash")).pack(fill="both", expand=True)
        self.tabs.add("Formats")
        FormatsTab(self.tabs.tab("Formats")).pack(fill="both", expand=True)
```

`main.py`:

```python
import sys


def selftest() -> int:
    try:
        from omni.ui import App

        app = App()
        for _ in range(10):
            app.update_idletasks()
        app.destroy()
        print("SELFTEST OK")
        return 0
    except Exception as exc:
        print(f"SELFTEST FAILED: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    from omni.ui import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_ui_selftest.py -v`
Expected: 1 passed

- [ ] **Step 5: Manual verification checklist (run the app yourself)**

```powershell
.venvScriptspython.exe main.py
```

1. Window opens dark-themed with 7 tabs.
2. Images tab: Add Files → pick a .png → target list shows webp/jpg/... → Convert → files appear in `output/`.
3. Hash tab: type "abc" → MD5 `900150983cd24fb0d6963f7d28e17f72` visible.
4. Formats tab shows the full conversion table.
5. Drag a file from Explorer onto the window → appears in file list.

- [ ] **Step 6: Commit**

```bash
git add omni/ui.py main.py tests/test_ui_selftest.py
git commit -m "feat: customtkinter GUI with seven tabs and selftest"
```

---

## Task 11: One-file EXE packaging (`build.ps1`)

**Files:**
- Create: `build.ps1`, `.github/workflows/release.yml` (Windows self-hosted runner optional; primary path is local build)

**Interfaces:**
- Consumes: all tasks above.
- Produces: `dist/OmniConvert.exe` (single file), runs offline, opens the GUI; `dist/OmniConvert.exe --selftest` prints `SELFTEST OK`.

- [ ] **Step 1: Write build script**

`build.ps1`:

```powershell
$ErrorActionPreference = "Stop"
.\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m PyInstaller `
  --onefile --windowed --name OmniConvert `
  --collect-all imageio_ffmpeg `
  main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
Write-Host "Built: dist\OmniConvert.exe"
```

- [ ] **Step 2: Run the build**

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```
Expected: `dist/OmniConvert.exe` exists, size > 25 MB (ffmpeg bundled).

- [ ] **Step 3: Verify the packaged EXE**

```powershell
.\dist\OmniConvert.exe --selftest
```
Expected: prints `SELFTEST OK` and exits. Then double-click: GUI opens, images tab converts a png → jpg.

- [ ] **Step 4: Commit**

```bash
git add build.ps1 .github/workflows/release.yml
git commit -m "build: one-file EXE packaging script"
```

---

## Task 12: Publish to GitHub (repo, README, LICENSE, release)

**Files:**
- Create: `LICENSE` (MIT, copyright TT88990 2026), full `README.md` (overwrites placeholder), `docs/SCREENSHOTS.md` (placeholder for future images)

**Interfaces:**
- Consumes: everything.
- Produces: public repo `TT88990/omni-convert` on GitHub; first release `v0.1.0` with `dist/OmniConvert.exe` attached; local branch pushed.

- [ ] **Step 1: Write LICENSE**

`LICENSE` (MIT text with `Copyright (c) 2026 TT88990`).

- [ ] **Step 2: Write full README.md**

README.md sections: badge line, one-line description, Features (bullets per category incl. hash tab), Format matrix table (generated content from `omni.matrix.CATEGORIES`), Install (download EXE from Releases), Build from source (build.ps1 steps), Usage, License (MIT link). Use only English.

- [ ] **Step 3: Run tests and full build once more**

```powershell
.\.venv\Scripts\python.exe -m pytest -q; if ($LASTEXITCODE -eq 0) { powershell -ExecutionPolicy Bypass -File .\build.ps1 }
```
Expected: all tests pass; `dist\OmniConvert.exe` fresh.

- [ ] **Step 4: Create repo and push**

```bash
gh auth status
git add -A
git commit -m "docs: README, LICENSE, release metadata"
git branch -M main
gh repo create omni-convert --public --source . --remote origin --push
```

- [ ] **Step 5: Create first release with the EXE**

```bash
gh release create v0.1.0 dist/OmniConvert.exe --title "OmniConvert v0.1.0" --notes "First public release. Single-file EXE, offline, MIT."
```

- [ ] **Step 6: Report the repo URL**

Print: `https://github.com/TT88990/omni-convert` and the release asset URL.

---

## Self-Review Notes

- Spec sections covered: layout (T3-6 tabs + T10 GUI), hash tab (T3 + T10 HashTab), formats matrix (T9 + T10 FormatsTab), error handling (ConversionError everywhere + T9 Runner error capture + T10 log), testing (per-task pytest), build (T11), GitHub (T12), YAGNI items excluded.
- ffmpeg bundling: `--collect-all imageio_ffmpeg` in T11 makes `imageio_ffmpeg.get_ffmpeg_exe()` resolve inside the one-file bundle (its bin-dict code checks `sys._MEIPASS`).
- Drag & drop needs tkinterdnd2 (installed T1); `DnDApp` mixes `ctk.CTk` with `TkinterDnD.DnDWrapper` per the standard recipe.

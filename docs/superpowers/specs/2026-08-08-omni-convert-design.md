# OmniConvert — Universal File Converter (Windows Desktop App)

**Date:** 2026-08-08
**Status:** Approved
**License:** MIT (open source, public GitHub repo)

## 1. Purpose

A single-file Windows desktop app that converts files between as many formats as
possible: images, documents, audio, video, text encodings, and hash/encoding
generation. The app is fully offline, free, and open source.

## 2. Tech Stack

| Component | Choice | Reason |
|---|---|---|
| Language | Python 3.13 (via `py` launcher) | Richest conversion library ecosystem |
| GUI | customtkinter | Modern dark theme, drag & drop, standard Python |
| PDF | PyMuPDF (fitz) | Best free PDF↔text/image conversion |
| DOCX | python-docx | Word documents |
| Images | Pillow | All common raster formats; svg→png via cairosvg if available, else unsupported |
| Audio/Video | ffmpeg bundled via `imageio-ffmpeg` | Static ffmpeg binary ships with the pip package (~25MB) |
| Hash | hashlib (stdlib) | MD5..BLAKE2, CRC32 via zlib |
| Encoding | stdlib | base64, hex, codecs |
| Build | PyInstaller (one-file) | Single portable EXE |

Final EXE approx 40-45 MB bundled with ffmpeg.

## 3. App Layout

customtkinter dark window, tabs on the left, work area on the right:

| Tab | Conversions |
|---|---|
| Images | png, jpg, webp, bmp, gif, tiff, ico -> each other; svg -> png |
| Documents | pdf<->txt, pdf->docx, pdf->md, pdf->png, docx->pdf, docx->txt, docx->md, txt->docx, images->pdf, txt/md->html |
| Audio | mp3, wav, flac, ogg, opus, m4a, aac, wma <-> each other; video -> audio |
| Video | mp4, avi, mkv, mov, wmv, webm, gif <-> each other via ffmpeg; extract gif frames |
| Text | encoding conversion (utf-8, utf-16-le/be, ascii, latin-1), base64 encode/decode, hex <-> ascii, unix/windows line endings |
| Hash | text or file -> MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512, SHA3-256/512, BLAKE2b, CRC32 — all at once, copy buttons |
| Help/Formats | in-app matrix of every supported source -> target conversion |

## 4. Core Behavior

- Drag & drop or Browse to select 1+ files; multi-select supported; batch converts sequentially.
- Input type derived from the active tab (user picks category first).
- Target dropdown lists only valid destination formats for the selected file(s).
- Output directory picker, default `./output` next to the EXE or in the project folder.
- Convert button -> progress bar + live log line per file.
- Filename collisions auto-suffixed (`file (1).ext`).
- Errors: toast message box + written to `omni-convert.log` next to the app.

## 5. Hash Tab Detail

- Text area input + "Load File" button (reads as bytes).
- Live table of hash name -> hash value, hex lower-case.
- CRC32 shown as 8-digit hex.
- Copy-to-clipboard button per hash.
- Encoding sub-feature: base64 encode/decode and hex views of the input bytes.

## 6. Format Matrix (in-app "Formats" tab and README)

- **Images:** png, jpg, webp, bmp, gif, tiff, ico (Pillow); svg -> png.
- **Documents:** txt, md, html, pdf, docx (PyMuPDF + python-docx), images -> pdf.
- **Audio:** ffmpeg containers/codecs via `-c:a` defaults; sample-rate 44.1k default;
  bitrate options mp3 192k, opus 128k.
- **Video:** ffmpeg default codec mapping (h264/aac for mp4 etc.); gif -> mp4/webm;
  mp4/webm -> gif; extract frames to png.
- **Text:** utf-8 <-> utf-16-le/be <-> ascii <-> latin-1 with strict error toasts;
  base64 <-> raw; hex <-> raw.
- **Hash:** listed in section 3.

## 7. Error Handling

- Every converter wrapped in per-file try/except; all errors collected, then shown together.
- ffmpeg executed via subprocess, stderr captured; non-zero exit ⇒ friendly error.
- Unsupported extension ⇒ toast "No converter for .xyz on the Images tab".
- All processed in a separate worker thread so the UI never freezes.

## 8. Testing

- pytest suite `tests/` generating real temp files:
  - Pillow synthetic image save/load roundtrip
  - PDF created by PyMuPDF -> txt/docx roundtrip
  - minimal wav (wave module) -> mp3 via ffmpeg -> back
  - hash correctness against known test vectors (MD5 "abc" -> 900150983cd24fb0d6963f7d28e17f72 etc.)
- pytest run via `py -m pytest`

## 9. Build & Packaging

- `build.ps1` script: create venv, pip install -r requirements.txt, run pytest,
  pyinstaller --onefile --windowed --name OmniConvert with added ffmpeg binary from imageio_ffmpeg.
- Output: `dist/OmniConvert.exe`.

## 10. GitHub Repo

- Public repo named `omni-convert`, MIT license file, README.md with features list,
  conversion matrix table, screenshots placeholder, requirements.txt, .gitignore,
  build.ps1.
- Releases attach the built EXE as an asset.

## 11. Out of Scope (YAGNI)

- OCR, cloud services, batch folder watch, hash cracking, video editing (cuts/filters), plugins.
# OmniConvert

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](pyproject.toml)

Universal offline file converter for Windows: images, documents, audio, video, text encodings and hashes — all in one desktop app.

## Features

**Images**
- Convert between PNG, JPG/JPEG, BMP, GIF, TIFF, ICO and WebP in any direction
- SVG → PNG rasterization
- Combine multiple images into a single multi-page PDF

**Documents**
- PDF ↔ TXT / DOCX / Markdown
- DOCX → PDF / TXT / MD, TXT → DOCX / PDF / HTML, MD → HTML

**Audio**
- Convert between MP3, WAV, FLAC, OGG, OPUS, M4A and WMA (ffmpeg bundled, no install needed)

**Video**
- Convert between MP4, AVI, MKV, MOV, WebM and GIF (animated)
- Extract frames from any video as PNG sequence

**Text**
- Re-encode TXT between UTF-8, UTF-16, UTF-16-LE, UTF-16-BE, ASCII and Latin-1
- Base64 encode/decode and hex encode/decode for text files

**Hash**
- Compute MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512, SHA3-256, SHA3-512, BLAKE2b and CRC32 for both text input and files

**GUI**
- Seven tabs (Images, Documents, Audio, Video, Text, Hash, Formats) with drag & drop
- Batch conversion with live progress and per-file log
- Fully offline — no network or cloud services used

## Format matrix

**Images**

| From | To |
|---|---|
| gif | bmp, ico, jpg, pdf, png, tiff, webp |
| bmp | gif, ico, jpg, pdf, png, tiff, webp |
| webp | bmp, gif, ico, jpg, pdf, png, tiff |
| jpeg | bmp, gif, ico, jpg, pdf, png, tiff, webp |
| tiff | bmp, gif, ico, jpg, pdf, png, webp |
| jpg | bmp, gif, ico, pdf, png, tiff, webp |
| png | bmp, gif, ico, jpg, pdf, tiff, webp |
| ico | bmp, gif, jpg, pdf, png, tiff, webp |
| svg | png |

**Documents**

| From | To |
|---|---|
| pdf | txt, docx, md |
| docx | txt, md, pdf |
| txt | docx, pdf, html |
| md | html |

**Audio**

| From | To |
|---|---|
| mp3 | flac, m4a, ogg, opus, wav, wma |
| wav | flac, m4a, mp3, ogg, opus, wma |
| flac | m4a, mp3, ogg, opus, wav, wma |
| ogg | flac, m4a, mp3, opus, wav, wma |
| opus | flac, m4a, mp3, ogg, wav, wma |
| m4a | flac, mp3, ogg, opus, wav, wma |
| wma | flac, m4a, mp3, ogg, opus, wav |

**Video**

| From | To |
|---|---|
| mp4 | avi, mkv, mov, webm, gif |
| avi | mp4, mkv, mov, webm, gif |
| mkv | mp4, avi, mov, webm, gif |
| mov | mp4, avi, mkv, webm, gif |
| webm | mp4, avi, mkv, mov, gif |
| gif | mp4, webm |

**Text**

| From | To |
|---|---|
| txt | utf-16, utf-16-le, utf-16-be, ascii, latin-1, base64, hex |
| md | html |

## Install

Download the latest `OmniConvert.exe` from the [Releases](https://github.com/TT88990/omni-convert/releases) page. It is a single-file portable executable — no installation, no Python, no ffmpeg needed.

## Build from source

Requires Windows with Python 3.13:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m pytest
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The standalone EXE (with bundled ffmpeg) is written to `dist\OmniConvert.exe`.

## Usage

1. Open OmniConvert and pick a category tab (e.g. Images).
2. Add files via the file picker or drag & drop.
3. Choose the target format.
4. Click **Convert** — results are written to the `output\` folder next to your input files (or the folder you select), with a per-file log and progress bar.

## License

[MIT](LICENSE) © 2026 TT88990

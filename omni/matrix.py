from omni import audio, documents, images, texconv, video

VIDEO_EXTS = ("mp4", "avi", "mkv", "mov", "webm", "gif")
AUDIO_EXTS = ("wav", "mp3", "flac", "ogg", "opus", "m4a", "wma")

CATEGORIES: dict[str, dict[str, list[str]]] = {
    "Images": {ext: sorted({"jpg", "png", "webp", "bmp", "gif", "tiff", "ico", "pdf"} - {ext}) for ext in images.IMAGE_EXTENSIONS}
    | {"svg": ["png"]},
    "Documents": {
        "pdf": ["txt", "docx", "md", "png"],
        "docx": ["txt", "md", "pdf"],
        "txt": ["docx", "pdf", "html"],
        "md": ["html"],
    },
    "Audio": {ext: sorted(set(audio.AUDIO_FORMATS) - {ext}) for ext in audio.AUDIO_FORMATS},
    "Video": {
        "mp4": ["avi", "mkv", "mov", "webm", "gif", "wav", "mp3", "flac", "ogg", "opus", "m4a", "wma", "frames"],
        "avi": ["mp4", "mkv", "mov", "webm", "gif", "wav", "mp3", "flac", "ogg", "opus", "m4a", "wma", "frames"],
        "mkv": ["mp4", "avi", "mov", "webm", "gif", "wav", "mp3", "flac", "ogg", "opus", "m4a", "wma", "frames"],
        "mov": ["mp4", "avi", "mkv", "webm", "gif", "wav", "mp3", "flac", "ogg", "opus", "m4a", "wma", "frames"],
        "webm": ["mp4", "avi", "mkv", "mov", "gif", "wav", "mp3", "flac", "ogg", "opus", "m4a", "wma", "frames"],
        "gif": ["mp4", "webm", "wav", "mp3", "flac", "ogg", "opus", "m4a", "wma", "frames"],
    },
    "Text": {
        "txt": ["utf-16", "utf-16-le", "utf-16-be", "ascii", "latin-1", "base64", "hex", "base64-decode", "hex-decode"],
        "md": ["html"],
    },
}


def VALID_TARGETS(category: str, src_ext: str) -> list[str]:
    return list(CATEGORIES.get(category, {}).get(src_ext, []))


def filetypes_for(category: str) -> list[tuple[str, str]]:
    exts = sorted({f"*.{e}" for e in CATEGORIES.get(category, {})})
    if not exts:
        return [("All files", "*.*")]
    return [("Supported files", " ".join(exts)), ("All files", "*.*")]


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
        "pdf": {"txt": documents.pdf_to_txt, "docx": documents.pdf_to_docx, "md": documents.pdf_to_md, "png": documents.pdf_to_png_pages},
        "docx": {"txt": documents.docx_to_txt, "md": documents.docx_to_md, "pdf": documents.docx_to_pdf},
        "txt": {"docx": documents.txt_to_docx, "pdf": documents.text_to_pdf, "html": documents.text_to_html},
        "md": {"html": documents.md_to_html},
    },
    "Audio": {ext: {t: audio.convert_audio for t in audio.AUDIO_FORMATS if t != ext} for ext in audio.AUDIO_FORMATS},
    "Video": {
        src: {
            "frames": video.extract_frames_job,
            **{t: video.convert_video for t in targets if t in VIDEO_EXTS},
            **{t: video.extract_audio for t in targets if t in AUDIO_EXTS},
        }
        for src, targets in CATEGORIES["Video"].items()
    },
    "Text": {
        "txt": {
            "base64": lambda s, d, **kw: texconv.convert_base64(s, d, "encode"),
            "hex": lambda s, d, **kw: texconv.convert_hex(s, d, "encode"),
            "base64-decode": lambda s, d, **kw: texconv.convert_base64(s, d, "decode"),
            "hex-decode": lambda s, d, **kw: texconv.convert_hex(s, d, "decode"),
            "utf-16": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="utf-16", **kw),
            "utf-16-le": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="utf-16-le", **kw),
            "utf-16-be": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="utf-16-be", **kw),
            "ascii": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="ascii", **kw),
            "latin-1": lambda s, d, **kw: texconv.convert_text(s, d, out_enc="latin-1", **kw),
        },
        "md": {"html": documents.md_to_html},
    },
}
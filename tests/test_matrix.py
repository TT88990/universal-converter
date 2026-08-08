from omni.matrix import CATEGORIES, VALID_TARGETS, filetypes_for


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


def test_video_audio_and_frames_targets():
    assert "frames" in VALID_TARGETS("Video", "mp4")
    assert "mp3" in VALID_TARGETS("Video", "gif")
    assert {"wav", "flac", "ogg", "opus", "m4a", "wma"} <= set(VALID_TARGETS("Video", "webm"))


def test_text_decode_targets():
    assert "base64-decode" in VALID_TARGETS("Text", "txt")
    assert "hex-decode" in VALID_TARGETS("Text", "txt")


def test_pdf_png_target():
    assert "png" in VALID_TARGETS("Documents", "pdf")


def test_wav_targets():
    t = VALID_TARGETS("Audio", "wav")
    assert {"mp3", "flac", "opus"} <= set(t)


def test_unknown_ext_empty():
    assert VALID_TARGETS("Images", "xyz") == []


def test_filetypes_images_cover_sources():
    types = dict(filetypes_for("Images"))
    assert "*.png" in types["Supported files"]
    assert "*.jpg" in types["Supported files"]
    assert types["All files"] == "*.*"


def test_filetypes_unknown_category_never_hides_files():
    assert filetypes_for("Nope") == [("All files", "*.*")]
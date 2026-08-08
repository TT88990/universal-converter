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
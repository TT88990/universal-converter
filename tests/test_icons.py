import pytest
import omni.icons as icons
from omni.matrix import CATEGORIES


def test_every_category_has_icon_kind():
    for cat in CATEGORIES:
        assert cat in icons.ICON_KINDS


def test_draw_icon_is_rgba_with_pixels():
    img = icons.draw_icon("photo", "#3B82F6")
    assert img.mode == "RGBA"
    assert img.size == (32, 32)
    pixels = list(img.getdata())
    assert any(p[3] > 0 for p in pixels)


def test_draw_icon_uses_color():
    img = icons.draw_icon("doc", "#F59E0B", 28)
    assert (245, 158, 11, 255) in set(img.getdata()) | set(img.resize((1, 1)).getdata())


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        icons.draw_icon("nope", "#000000")
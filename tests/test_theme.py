import omni.theme as theme
from omni.matrix import CATEGORIES

def test_required_keys():
    for key in ("surfaces", "text", "accents", "accent", "fonts", "sizes", "radius", "spacing"):
        assert key in theme.THEME

def test_every_category_has_accent():
    for cat in CATEGORIES:
        assert theme.accent(cat).startswith("#")

def test_unknown_category_falls_back():
    assert theme.accent("Nope") == theme.THEME["accent"]

def test_exact_accents():
    assert theme.THEME["accents"] == {
        "Images": "#F59E0B", "Documents": "#3B82F6", "Audio": "#22C55E",
        "Video": "#EC4899", "Text": "#A855F7", "Hash": "#14B8A6", "Formats": "#64748B",
    }

def test_color_roles():
    assert theme.color("bg").startswith("#")
    assert theme.color("primary").startswith("#")

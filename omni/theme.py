THEME = {
    "surfaces": {
        "bg": "#0B1116", "sidebar": "#10182A", "surface": "#141B2A",
        "card": "#1A2234", "border": "#253043", "drop": "#1E2A40",
    },
    "text": {
        "primary": "#E5EAF2", "muted": "#8A94A6", "on_accent": "#0B1116",
    },
    "accents": {
        "Images": "#F59E0B", "Documents": "#3B82F6", "Audio": "#22C55E",
        "Video": "#EC4899", "Text": "#A855F7", "Hash": "#14B8A6", "Formats": "#64748B",
    },
    "accent": "#3B82F6",
    "fonts": {"app": "Segoe UI", "mono": "Consolas"},
    "sizes": {"brand": 19, "page": 24, "body": 13, "small": 11, "mono": 12},
    "radius": 10,
    "spacing": 10,
}


def accent(name: str) -> str:
    return THEME["accents"].get(name, THEME["accent"])


def color(role: str) -> str:
    if role in THEME["surfaces"]:
        return THEME["surfaces"][role]
    return THEME["text"][role]
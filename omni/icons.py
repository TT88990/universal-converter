from PIL import Image, ImageDraw
import omni.theme as theme

ICON_KINDS = {
    "Images": "photo", "Documents": "doc", "Audio": "note", "Video": "play",
    "Text": "t", "Hash": "hashtag", "Formats": "grid",
}


def draw_icon(kind: str, color: str, size: int = 32) -> Image.Image:
    if kind not in ICON_KINDS.values():
        raise ValueError(f"unknown icon kind: {kind}")
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    m = max(2, s // 6)
    if kind == "photo":
        d.rounded_rectangle([m, m, s - m, s - m], radius=m, outline=color, width=2)
        d.polygon([(m + 2, s - m - 2), (s // 2, s // 3), (s - m - 2, s - m - 2)], fill=color)
        d.ellipse([s // 2, m + 2, s // 2 + s // 5, m + 2 + s // 5], fill=color)
    elif kind == "doc":
        d.rounded_rectangle([m, m, s - m, s - m], radius=m // 2, outline=color, width=2)
        d.rounded_rectangle([m, m, s - m, m + m + 4], fill=color, radius=2)
        d.line([(m + s // 5, m + s // 2), (s - m - s // 5, m + s // 2)], fill=color, width=2)
        d.line([(m + s // 5, m + s // 2 + s // 5), (s - m - s // 5, m + s // 2 + s // 5)], fill=color, width=2)
    elif kind == "note":
        d.ellipse([m, s - m - s // 4, m + s // 4, s - m], fill=color)
        d.line([(m + s // 4, s - m - s // 8), (m + s // 4, m + 2)], fill=color, width=2)
        d.line([(m + s // 4, m + 2), (s - m, m + s // 4)], fill=color, width=2)
    elif kind == "play":
        d.rounded_rectangle([m, m, s - m, s - m], radius=m, outline=color, width=2)
        d.polygon([(s // 2 - m // 4, s // 3 + 2), (s // 2 - m // 4, s * 2 // 3 - 2), (s * 3 // 4, s // 2)], fill=color)
    elif kind == "t":
        d.rounded_rectangle([m, m, s - m, 2 * m], fill=color, radius=2)
        d.rounded_rectangle([s // 2 - m // 2, m, s // 2 + m // 2, s - m], fill=color, radius=2)
    elif kind == "hashtag":
        d.rounded_rectangle([s // 2 - m, m, s // 2 + m, s - m], fill=color)
        d.rounded_rectangle([m, s // 2 - m, s - m, s // 2 + m], fill=color)
    elif kind == "grid":
        step = s // 3
        for x in (m, m + step, m + 2 * step):
            d.rectangle([x, m, x + step // 2, m + step // 2], outline=color, width=2)
            d.rectangle([x, s // 2, x + step // 2, s // 2 + step // 2], outline=color, width=2)
    return img


def photoicon(kind: str, color: str, size: int = 32):
    from PIL import ImageTk
    return ImageTk.PhotoImage(draw_icon(kind, color, size))

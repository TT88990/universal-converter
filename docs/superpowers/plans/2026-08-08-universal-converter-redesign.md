# UniversalConverter Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand OmniConvert to UniversalConverter and redesign the desktop UI (sidebar navigation, category accents, icons, polished converter pages) while keeping the conversion core untouched.

**Architecture:** Keep `omni/` core (converters, matrix, runner, hashgen) untouched except two one-line renames. Introduce `omni/theme.py` (single source of colors/fonts/accents) and `omni/icons.py` (PIL-drawn pictograms). Rewrite `omni/ui.py` as sidebar + 7 swappable pages (`ConverterPage` shared by 5 categories, `HashPage`, `FormatsPage` with live search). Extend the `--selftest` in `main.py`. Update fixtures strings, then build, rename repo, and release v0.2.0.

**Tech Stack:** Python 3.13 (`.venv`), customtkinter (dark mode only), Pillow, PyInstaller, pytest. All deps already installed; no new dependencies.

## Global Constraints

- Dark theme only; every color/font/size comes from `THEME`; no hardcoded hex in widget code (except R color strings inside `theme.py` and `icons.py`).
- Category accents (exact): Images `#F59E0B`, Documents `#3B82F6`, Audio `#22C55E`, Video `#EC4899`, Text `#A855F7`, Hash `#14B8A6`, Formats `#64748B`, default `#3B82F6`.
- Product strings: "UniversalConverter" (EXE, window, app), log file `universal-converter.log`.
- Core modules `omni/runner.py`, `omni/matrix.py`, `omni/hashgen.py`, converters (images/documents/audio/video/texconv/errors/ffmpeg) change only via the exact one-line renames listed (log file name; PDF metadata) — no other behavior change.
- No emoji anywhere in the app; pictograms are PIL-drawn.
- Every task ends green: `py -m pytest -q` from repo root (Windows; use `.venv\Scripts\python.exe -m pytest`).
- gh usage: refresh PATH first — `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')`.

---

### Task 1: Rename product strings + fixtures

**Files:**
- Modify: `omni/ui.py:179` (`self.title("OmniConvert")`)
- Modify: `omni/runner.py:55` (`"omni-convert.log"`)
- Modify: `omni/documents.py:27` (metadata title/author/creator/producer)
- Modify: `tests/test_runner.py:67`, `tests/test_documents.py:23,37,47,56,83`
- Modify: `build.ps1:6,10`
- Test: `tests/` (existing, updated fixtures) + grep guard

**Interfaces:**
- Consumes: nothing new.
- Produces: `universal-converter.log` naming on disk; `UniversalConverter` strings everywhere except `docs/superpowers/` history files.

- [ ] **Step 1: Update fixture strings and log name test**

In `tests/test_documents.py` replace all `OmniConvert` → `UniversalConverter` (5 occurrences: line 23 sample text, 37, 47, 56, 83). In `tests/test_runner.py:67` replace `omni-convert.log` → `universal-converter.log`.

- [ ] **Step 2: Run the suite — tests must fail (strings still old)**

Run: `py -m pytest tests/test_documents.py tests/test_runner.py -q`
Expected: FAIL (assertion errors on the old fixture strings).

- [ ] **Step 3: Apply the product rename**

- `omni/ui.py:179`: `self.title("UniversalConverter")`
- `omni/runner.py:55`: `out_dir / "universal-converter.log"`
- `omni/documents.py:27`:
  ```python
  {"title": "UniversalConverter", "author": "UniversalConverter", "creator": "UniversalConverter", "producer": "UniversalConverter"}
  ```
- `build.ps1:6`: `--name UniversalConverter`
- `build.ps1:10`: `Write-Host "Built: dist\UniversalConverter.exe"`
- `README.md`: replace all `OmniConvert` / `omni-convert` with `UniversalConverter` / `universal-converter` except the "formerly" note under the title (keep a one-line "formerly OmniConvert" for continuity); update the repo links to `https://github.com/TT88990/universal-converter`.

- [ ] **Step 4: Run full test suite — pass**

Run: `py -m pytest -q`
Expected: 66 passed + 1 skipped (same count as before; strings updated).

- [ ] **Step 5: Guard: no stale product name in code**

Run (PowerShell): `Select-String -Path omni\*.py,tests\*.py,main.py,build.ps1,README.md -Pattern "OmniConvert"`
Expected: no matches (only `docs/superpowers/` may contain the old name).

- [ ] **Step 6: Commit**

```bash
git add omni/ui.py omni/runner.py omni/documents.py tests build.ps1 README.md
git commit -m "feat: rename product to UniversalConverter"
```

---

### Task 2: Theme module

**Files:**
- Create: `omni/theme.py`
- Test: `tests/test_theme.py`

**Interfaces:**
- Consumes: `omni.matrix.CATEGORIES` (keys are category names).
- Produces:
  - `THEME: dict` with keys `surfaces`, `text`, `accents`, `accent`, `fonts`, `sizes`, `radius`, `spacing`.
  - `accent(name: str) -> str` — category accent; falls back to `THEME["accent"]`.
  - `color(role: str) -> str` — returns `THEME["surfaces"][role]` or `THEME["text"][role]` depending on where the key lives.

- [ ] **Step 1: Write the failing test**

```python
import pytest
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
```

- [ ] **Step 2: Run test — fails (module missing)**

Run: `py -m pytest tests/test_theme.py -v`
Expected: FAIL `ModuleNotFoundError: omni.theme`.

- [ ] **Step 3: Write minimal implementation**

Create `omni/theme.py`:

```python
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
```

- [ ] **Step 4: Run test — pass**

Run: `py -m pytest tests/test_theme.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add omni/theme.py tests/test_theme.py
git commit -m "feat: central theme module (colors, fonts, accents)"
```

---

### Task 3: PIL-drawn icon generator

**Files:**
- Create: `omni/icons.py`
- Test: `tests/test_icons.py`

**Interfaces:**
- Consumes: `omni.theme.accent`.
- Produces:
  - `ICON_KINDS: dict[str, str]` mapping category → kind: `{"Images": "photo", "Documents": "doc", "Audio": "note", "Video": "play", "Text": "t", "Hash": "hashtag", "Formats": "grid"}`.
  - `draw_icon(kind: str, color: str, size: int = 32) -> Image.Image` (PIL RGBA, transparent bg, colored glyph); raises `ValueError` for unknown kind or unparseable color.
  - `icon_path` not needed; `photoicon(kind, color, size) -> ImageTk.PhotoImage` for Tk (imported lazily so tests don't need a display).

- [ ] **Step 1: Write failing tests**

Create `tests/test_icons.py`:

```python
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
    assert (255, 158, 11, 255) in set(img.getdata()) | set(img.resize((1, 1)).getdata())


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        icons.draw_icon("nope")
```

- [ ] **Step 2: Run tests — verify they fail (module missing)**

Run: `py -m pytest tests/test_icons.py -v`
Expected: FAIL `ModuleNotFoundError: omni.icons`.

- [ ] **Step 3: Write minimal implementation**

Create `omni/icons.py`:

```python
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
```

- [ ] **Step 4: Run tests — verify pass**

Run: `py -m pytest tests/test_icons.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add omni/icons.py tests/test_icons.py
git commit -m "feat: PIL-drawn icon generator"
```

---

### Task 4: Sidebar navigation + page shell

**Files:**
- Modify: `omni/ui.py` (rewrite: DnDApp, Sidebar, App shell with page switching)
- Modify: `main.py` (extended selftest addition in Task 6 — skip here)
- Test: selftest run by hand (Task 6 adds asserts)

**Interfaces:**
- Consumes: `omni.theme`, `omni.icons`.
- Produces:
  - `Sidebar(master, on_select: Callable[[str], None])` with `.buttons: dict[str, ctk.CTkButton]` and `.select(name)`.
  - `App` (DnDApp): `.sidebar`, `.pages: dict[str, ctk.CTkFrame]` (filled later), `.current` page name; `.show_page(name)`.

- [ ] **Step 1: Rewrite the shell (write failing code first is impossible here — the shell sets up the failing state)**

Rewrite `omni/ui.py` to:

```python
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

import omni.theme as theme
from omni.icons import ICON_KINDS, photoicon
from omni.hashgen import hash_file, hash_text
from omni.matrix import CATEGORIES, VALID_TARGETS
from omni.runner import Job, Runner

CATEGORY_ORDER = ("Images", "Documents", "Audio", "Video", "Text", "Hash", "Formats")


class DnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select=None):
        super().__init__(master, width=220, fg_color=theme.THEME["surfaces"]["sidebar"])
        self.on_select = on_select
        self.buttons: dict = {}
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=12, pady=(16, 8))
        ctk.CTkLabel(brand, text="UniversalConverter",
                     font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["brand"], "bold"),
                     text_color=theme.THEME["text"]["primary"]).pack(anchor="w")
        ctk.CTkLabel(brand, text="Offline converter",
                     font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["small"]),
                     text_color=theme.THEME["text"]["muted"]).pack(anchor="w")
        self._nav = ctk.CTkFrame(self, fg_color="transparent")
        self._nav.pack(fill="both", expand=True, padx=8, pady=8)
        for name in CATEGORY_ORDER:
            self.buttons[name] = self._make_button(name)
        ctk.CTkLabel(self, text="v0.2.0  MIT",
                     font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["small"]),
                     text_color=theme.THEME["text"]["muted"]).pack(side="bottom", pady=12)

    def _make_button(self, name):
        btn = ctk.CTkButton(self._nav, text=name,
                            image=photoicon(ICON_KINDS[name], theme.accent(name)),
                            compound="left", anchor="w", height=40, corner_radius=8,
                            fg_color="transparent", text_color=theme.THEME["text"]["primary"],
                            hover_color=theme.THEME["surfaces"]["surface"],
                            command=lambda n=name: self.on_select(n) if self.on_select else None)
        btn.pack(fill="x", pady=2)
        return btn

    def select(self, name):
        for n, btn in self.buttons.items():
            btn.configure(fg_color=theme.THEME["surfaces"]["surface"]
                          if n == name else "transparent",
                          text_color=theme.accent(n) if n == name else theme.THEME["text"]["primary"])
```

- [ ] **Step 2: Run the app manually**

Run: `python main.py` — window opens, dark theme applies, `UniversalConverter` title, sidebar shows brand + seven nav names, old tab row still exists at top via `self.tabs`. This step just verifies the shell draws.

- [ ] **Step 3: Commit shell**

```bash
git add omni/ui.py
git commit -m "feat: sidebar shell (brand, nav, version)"
```

---

### Task 5: Rewrite pages as a single shared converter page + Hash + Formats

**Files:**
- Modify: `omni/ui.py` (replace `ConvertTab` with `ConverterPage`; replace `HashTab` → `HashPage`, `FormatsTab` → `FormatsPage`; wire `App` to pages)
- Test: extended `main.py --selftest` (Task 6 wires asserts; add a manual drop check here)

**Interfaces:**
- Consumes: `VALID_TARGETS`, `Job`, `Runner`, `theme`, `icons`.
- Produces:
  - `ConverterPage(category: str)` — same public methods as the old `ConvertTab` (`_on_drop`, `_pick`, `_add_paths`, `_refresh_list`, `_pick_out`, `_convert`, `_on_progress`, `_log`, plus attrs `files`, `target`, `out_dir`, `accent`).
  - `HashPage` — `.results`, `.input`, `._copy` (as before).
  - `FormatsPage` — `.filter_var: ctk.StringVar`, `.filter_entry`, `._refresh()`.

- [ ] **Step 1: Write the page UI**

Implement in `omni/ui.py` (replacing `ConvertTab` entirely):

```python
class ConverterPage(ctk.CTkFrame):
    def __init__(self, master, category: str):
        super().__init__(master, fg_color=theme.THEME["surfaces"]["surface"])
        self.category = category
        self.files: list[Path] = []
        self.target = ctk.StringVar(value="")
        self.out_dir = ctk.StringVar(value=str(Path.cwd() / "output"))
        self.accent = theme.accent(category)
        pad = theme.THEME["spacing"]

        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=pad, pady=(pad, 4))
        ctk.CTkLabel(title_row, text=self.category,
                     font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["page"], "bold"),
                     text_color=theme.THEME["text"]["primary"]).pack(side="left")
        desc = {
            "Images": "Convert raster images and SVGs",
            "Documents": "PDF, DOCX, TXT, MD and HTML",
            "Audio": "Every major audio format",
            "Video": "Video formats and frame extraction",
            "Text": "Encodings, base64, hex, line endings",
        }[category]
        ctk.CTkLabel(title_row, text=desc,
                     font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["small"]),
                     text_color=theme.THEME["text"]["muted"]).pack(side="left", padx=12)

        drop = ctk.CTkFrame(self, fg_color=theme.THEME["surfaces"]["drop"],
                            border_width=2, border_color=self.accent, corner_radius=12)
        drop.pack(fill="x", padx=pad, pady=6)
        self._hint = ctk.CTkLabel(drop, text="Drag files here or click to add",
                                  font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["body"]),
                                  text_color=theme.THEME["text"]["muted"], cursor="hand2")
        self._hint.pack(pady=10)
        self._hint.bind("<Button-1>", lambda e: self._pick())
        self._rows = ctk.CTkFrame(drop, fg_color="transparent")
        self._rows.pack(fill="x", padx=6, pady=6)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=pad, pady=8)
        ctk.CTkLabel(actions, text="Output folder").pack(side="left", padx=(0, 4))
        ctk.CTkEntry(actions, textvariable=self.out_dir, width=240).pack(side="left")
        ctk.CTkButton(actions, text="Browse", width=70, command=self._pick_out).pack(side="left", padx=6)
        ctk.CTkLabel(actions, text="Format").pack(side="left", padx=(16, 4))
        self.target_menu = ctk.CTkOptionMenu(actions, values=[], variable=self.target, state="disabled")
        self.target_menu.pack(side="left")
        self.convert_btn = ctk.CTkButton(actions, text="Convert", width=130,
                                         font=(theme.THEME["fonts"]["app"], 14, "bold"),
                                         fg_color=self.accent, hover_color=self.accent,
                                         text_color=theme.THEME["text"]["on_accent"],
                                         command=self._convert)
        self.convert_btn.pack(side="right")
        self.progress = ctk.CTkProgressBar(self, height=8)
        self.progress.pack(fill="x", padx=pad, pady=2)
        self.status = ctk.CTkLabel(self, text="Idle", anchor="w",
                                   text_color=theme.THEME["text"]["muted"])
        self.status.pack(fill="x", padx=pad, pady=2)
        self.log = ctk.CTkTextbox(self, height=110,
                                  font=(theme.THEME["fonts"]["mono"], theme.THEME["sizes"]["mono"]),
                                  fg_color=theme.THEME["surfaces"]["card"],
                                  text_color=theme.THEME["text"]["muted"])
        self.log.pack(fill="both", expand=True, padx=pad, pady=(2, pad))
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

    def _add_paths(self, paths):
        for p in paths:
            ext = p.suffix.lower().lstrip(".")
            if VALID_TARGETS(self.category, ext):
                self.files.append(p)
            else:
                self._log(f"skipped {p.name} (no conversion in {self.category} page)")
        self._refresh_list()

    def _refresh_list(self):
        for child in self._rows.winfo_children():
            child.destroy()
        for p in self.files:
            row = ctk.CTkFrame(self._rows, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(row, text=p.name, anchor="w",
                         font=(theme.THEME["fonts"]["mono"], theme.THEME["sizes"]["mono"]),
                         text_color=theme.THEME["text"]["primary"]).pack(side="left", expand=True)
            try:
                size = p.stat().st_size // 1024
                meta = f"{size} KB"
            except OSError:
                meta = p.suffix
            ctk.CTkLabel(row, text=meta, text_color=theme.THEME["text"]["muted"]).pack(side="right")
        hint = "Drag files here or click to add" if not self.files else f"{len(self.files)} file(s) added"
        self._hint.configure(text=hint)
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
            try:
                Runner().run(jobs, out, on_progress=self._on_progress)
            except Exception as exc:
                self.after(0, lambda: self._log(f"error: {exc}"))
            finally:
                self.after(0, lambda: self.convert_btn.configure(state="normal"))

        threading.Thread(target=work, daemon=True).start()

    def _on_progress(self, done, total, name, status):
        def update():
            self.progress.set(done / total)
            self.status.configure(text=f"[{done}/{total}] {name}: {status}")
            self._log(f"[{done}/{total}] {name}: {status}")
        self.after(0, update)

    def _log(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
```

- [ ] **Step 2: Add HashPage, FormatsPage and the App wiring**

Replace `HashTab` with `HashPage` (same logic, themed):

```python
class HashPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.THEME["surfaces"]["surface"])
        self._file_mode = False
        self.input = ctk.CTkTextbox(self, height=120,
                                    fg_color=theme.THEME["surfaces"]["card"],
                                    text_color=theme.THEME["text"]["primary"])
        self.input.pack(fill="x", padx=10, pady=(10, 4))
        self.input.bind("<KeyRelease>", self._on_key)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10)
        ctk.CTkButton(top, text="Load File...", command=self._load_file).pack(side="left")
        self.file_label = ctk.CTkLabel(top, text="", text_color=theme.THEME["text"]["muted"])
        self.file_label.pack(side="left", padx=12)
        self.results = ctk.CTkScrollableFrame(self)
        self.results.pack(fill="both", expand=True, padx=10, pady=10)
        self.results.grid_columnconfigure(1, weight=1)
        self._show({})

    def _on_key(self, event):
        self._file_mode = False
        self._refresh()

    def _load_file(self):
        p = filedialog.askopenfilename()
        if p:
            self._file_mode = True
            self.input.delete("1.0", "end")
            self.input.insert("1.0", Path(p).name + " (file hashed)")
            self.file_label.configure(text=str(p))
            self._show_hashes(hash_file(Path(p)))

    def _refresh(self):
        if self._file_mode:
            return
        text = self.input.get("1.0", "end").strip()
        if text:
            self._show_hashes(hash_text(text))

    def _copy(self, value):
        self.clipboard_clear()
        self.clipboard_append(value)

    def _show_hashes(self, digests):
        for child in self.results.winfo_children():
            child.destroy()
        for row, (algo, value) in enumerate(digests.items()):
            ctk.CTkLabel(self.results, text=algo, width=90, anchor="w",
                         text_color=theme.THEME["text"]["primary"]).grid(
                row=row, column=0, sticky="w", padx=6, pady=3)
            ctk.CTkLabel(self.results, text=value, anchor="w", wraplength=500,
                         font=(theme.THEME["fonts"]["mono"], theme.THEME["sizes"]["small"]),
                         text_color=theme.THEME["text"]["muted"]).grid(
                row=row, column=1, sticky="ew", padx=6, pady=3)
            ctk.CTkButton(self.results, text="Copy", width=60,
                          fg_color=theme.accent("Hash"),
                          text_color=theme.THEME["text"]["on_accent"],
                          command=lambda v=value: self._copy(v)).grid(
                row=row, column=2, padx=6, pady=3)
```

Replace `FormatsTab` with `FormatsPage` (filterable):

```python
class FormatsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=theme.THEME["surfaces"]["surface"])
        self.filter_var = ctk.StringVar(value="")
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(top, text="Search formats", text_color=theme.THEME["text"]["muted"]).pack(side="left")
        self.filter_entry = ctk.CTkEntry(top, textvariable=self.filter_var, width=320)
        self.filter_entry.pack(side="left", padx=8)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._refresh())
        self.body = ctk.CTkScrollableFrame(self)
        self.body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._refresh()

    def _refresh(self):
        for child in self.body.winfo_children():
            child.destroy()
        q = self.filter_var.get().strip().lower()
        row = 0
        for category, mapping in CATEGORIES.items():
            lines = [
                f"  .{src} -> " + ", ".join(f".{t}" for t in targets)
                for src, targets in mapping.items()
            ]
            visible = [ln for ln in lines if not q or q in ln.lower()
                       or q == category.lower()]
            if not visible and q:
                continue
            ctk.CTkLabel(self.body, text=f"=== {category} ===",
                         font=(theme.THEME["fonts"]["app"], 15, "bold"),
                         text_color=theme.accent(category)).grid(row=row, column=0, sticky="w", pady=(10, 2))
            row += 1
            for line in visible:
                ctk.CTkLabel(self.body, text=line, anchor="w",
                             font=(theme.THEME["fonts"]["mono"], theme.THEME["sizes"]["small"]),
                             text_color=theme.THEME["text"]["primary"]).grid(row=row, column=0, sticky="w")
                row += 1
```

Wire the `App` class (replaces the old CTkTabview — delete it):

```python
class App(DnDApp):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("UniversalConverter")
        self.geometry("1100x760")
        self.minsize(900, 600)
        self.sidebar = Sidebar(self, self.show_page)
        self.sidebar.pack(side="left", fill="y")
        self.content = ctk.CTkFrame(self, fg_color=theme.THEME["surfaces"]["bg"])
        self.content.pack(side="left", fill="both", expand=True)
        self.pages: dict[str, ctk.CTkFrame] = {}
        self.current_page_name = ""
        for name in CATEGORY_ORDER:
            if name in ("Hash", "Formats"):
                cls = HashPage if name == "Hash" else FormatsPage
                self.pages[name] = cls(self.content)
            else:
                self.pages[name] = ConverterPage(self.content, name)
        self.show_page("Images")

    def show_page(self, name):
        if name in self.pages:
            self.current_page_name = name
            for n, page in self.pages.items():
                if n == name:
                    page.place(relx=0, rely=0, relwidth=1, relheight=1)
                    page.lift()
                else:
                    page.place_forget()
            self.sidebar.select(name)
```

- [ ] **Step 3: Manual run**

Run: `python main.py` — verify: sidebar selects and pages switch, dropping a png into Images lists it and the target menu enables, Convert runs a job (progress + status + log), HashPage copy works, FormatsPage filter narrows rows. Note: full auto checks land in Task 6.

- [ ] **Step 4: Run test suite (regression)**

Run: `py -m pytest -q`
Expected: 66 passed + 1 skipped — no core change.

- [ ] **Step 5: Commit**

```bash
git add omni/ui.py
git commit -m "feat: sidebar navigation + polished converter pages"
```

---

### Task 6: Extended selftest in main.py

**Files:**
- Modify: `main.py` (`selftest()`)
- Test: run `python main.py --selftest`

**Interfaces:**
- Consumes: `App`, `ConverterPage._on_drop` (patch-names — Task 5 interface).

- [ ] **Step 1: Write the extended selftest code**

Replace the body of `selftest()` in `main.py`:

```python
def selftest() -> int:
    try:
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from PIL import Image
        from omni.ui import App, CATEGORY_ORDER

        with tempfile.TemporaryDirectory() as td:
            png = Path(td) / "p.png"
            Image.new("RGBA", (10, 10), (0, 120, 255)).save(png)
            app = App()
            for _ in range(10):
                app.update_idletasks()
            assert len(app.pages) == len(CATEGORY_ORDER), "page count"
            assert len(app.sidebar.buttons) == len(CATEGORY_ORDER), "nav count"
            page = app.pages["Images"]
            page._on_drop(SimpleNamespace(data="{" + str(png).replace("\\", "/") + "}"))
            app.update_idletasks()
            assert len(page.files) == 1 and page.files[0].name == "p.png", "drop" 
            app.sidebar.select("Hash")
            app.show_page("Hash")
            app.update_idletasks()
            assert app.current_page_name == "Hash"
            app.destroy()
        print("SELFTEST OK")
        return 0
    except Exception as exc:
        print(f"SELFTEST FAILED: {exc}", file=sys.stderr)
        return 1
```

`App.current_page_name` — set in `show_page`.

- [ ] **Step 2: Run selftest — pass**

Run: `python main.py --selftest`
Expected: prints `SELFTEST OK`, exit code 0 (`echo $LASTEXITCODE` → 0).

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "test: extended UI selftest (sidebar, pages, drop)"
```

---

### Task 7: Build the renamed EXE

**Files:**
- Consumes: everything above
- Run: `powershell -ExecutionPolicy Bypass -File .\build.ps1` (py-based; executed from repo root)

**Interfaces:** none new.

- [ ] **Step 1: Build**

Run: `powershell -ExecutionPolicy Bypass -File .\build.ps1`
Expected: pytest gate green; `dist\UniversalConverter.exe` produced (> 25 MB with ffmpeg).

- [ ] **Step 2: Verify artifact**

Run: `.\dist\UniversalConverter.exe --selftest` then `echo $LASTEXITCODE`
Expected: `SELFTEST OK`, exit 0.

- [ ] **Step 3: Verify working tree**

```bash
git status --short   # expect: clean (nothing new to stage; build.ps1 was updated in Task 1)
```

---

### Task 8: Rename repo + publish v0.2.0

**Files:**
- Modify: `README.md` (if any final link cleanup), no code.
- Run: gh CLI (refresh PATH first).

**Interfaces:** consumes release asset `dist\UniversalConverter.exe`.

- [ ] **Step 1: Rename the GitHub repo**

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
gh repo rename universal-converter --repo TT88990/omni-convert --yes
git remote set-url origin https://github.com/TT88990/universal-converter.git
git push origin main
```

- [ ] **Step 2: Add topics**

```powershell
gh repo edit TT88990/universal-converter --add-topic converter --add-topic file-converter --add-topic image-converter --add-topic pdf --add-topic ffmpeg --add-topic python --add-topic windows --add-topic offline
```

- [ ] **Step 3: Create release v0.2.0**

```powershell
gh release create v0.2.0 dist/UniversalConverter.exe --title "UniversalConverter v0.2.0" --notes "Renamed from Omni. New sidebar UI: dark theme, category accents, dropzone with file rows, live status, searchable Formats page. Offline single-file EXE, MIT."
```

- [ ] **Step 4: Verify release**

```powershell
gh release view v0.2.0
```
Expected: shows `asset: UniversalConverter.exe` and the tagged URL.

- [ ] **Step 5: Final suite + push**

```powershell
py -m pytest -q
git push origin main
```
Expected: suite green, push fast-forward (branch `main`).

- [ ] **Step 6: Report URLs**

Print to user: repo URL, release tag URL, asset URL — and note old `omni-convert` URL now redirects.

---

## Self-Review Notes

- Spec §2 (rename table) → Task 1 (strings/titles/log/build), Task 7/8 (EXE, repo, release, topics).
- Spec §3/§4 (sidebar, converter page, drop/status/log) → Tasks 4/5; §5 (Hash/Formats search) → Task 5; §6 (theme/icons) → Tasks 2/3.
- Spec §7 testing (theme/icon tests, extended selftest) → Tasks 2/3/6; build → Task 7; §8 publishing → Task 8.
- No new dependencies; `omni/runner.py` change only the log filename; `omni/documents.py` metadata string; all other core files untouched.
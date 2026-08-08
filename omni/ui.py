import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

import omni.theme as theme
from omni import APP_VERSION
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
        ctk.CTkLabel(self, text=f"v{APP_VERSION}  MIT",
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
                                         font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["cta"], "bold"),
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
        self._show_hashes({})

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
                       or q in category.lower()]
            if not visible and q:
                continue
            ctk.CTkLabel(self.body, text=f"=== {category} ===",
                         font=(theme.THEME["fonts"]["app"], theme.THEME["sizes"]["section"], "bold"),
                         text_color=theme.accent(category)).grid(row=row, column=0, sticky="w", pady=(10, 2))
            row += 1
            for line in visible:
                ctk.CTkLabel(self.body, text=line, anchor="w",
                             font=(theme.THEME["fonts"]["mono"], theme.THEME["sizes"]["small"]),
                             text_color=theme.THEME["text"]["primary"]).grid(row=row, column=0, sticky="w")
                row += 1


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

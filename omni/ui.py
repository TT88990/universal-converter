import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from omni.hashgen import hash_file, hash_text
from omni.matrix import CATEGORIES, VALID_TARGETS
from omni.runner import Job, Runner


class DnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class ConvertTab(ctk.CTkFrame):
    def __init__(self, master, category: str):
        super().__init__(master)
        self.category = category
        self.files: list[Path] = []
        self.target = ctk.StringVar(value="")
        self.out_dir = ctk.StringVar(value=str(Path.cwd() / "output"))

        ctk.CTkButton(self, text="Add Files...", command=self._pick).grid(row=0, column=0, padx=5, pady=5)
        self.file_list = ctk.CTkTextbox(self, height=160, width=560)
        self.file_list.grid(row=0, column=1, rowspan=4, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(self, text="Output folder").grid(row=0, column=2, sticky="w")
        ctk.CTkEntry(self, textvariable=self.out_dir, width=200).grid(row=1, column=2, padx=5)
        ctk.CTkButton(self, text="Browse...", command=self._pick_out).grid(row=2, column=2, padx=5)
        self.target_menu = ctk.CTkOptionMenu(self, values=[], variable=self.target, state="disabled")
        self.target_menu.grid(row=3, column=2, padx=5)
        self.convert_btn = ctk.CTkButton(self, text="Convert", command=self._convert)
        self.convert_btn.grid(row=4, column=1, padx=5, pady=5)
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.log = ctk.CTkTextbox(self, height=120, width=760)
        self.log.grid(row=6, column=0, columnspan=3, padx=5, pady=5)
        self.grid_columnconfigure(1, weight=1)
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

    def _add_paths(self, paths: list[Path]):
        for p in paths:
            ext = p.suffix.lower().lstrip(".")
            if VALID_TARGETS(self.category, ext):
                self.files.append(p)
            else:
                self._log(f"skipped {p.name} (no conversion in {self.category} tab)")
        self._refresh_list_and_targets()

    def _refresh_list_and_targets(self):
        self.file_list.delete("1.0", "end")
        for p in self.files:
            self.file_list.insert("end", p.name + "\n")
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
            Runner().run(jobs, out, on_progress=self._on_progress)
            self.after(0, lambda: self.convert_btn.configure(state="normal"))

        threading.Thread(target=work, daemon=True).start()

    def _on_progress(self, done, total, name, status):
        self.after(0, lambda: (self.progress.set(done / total), self._log(f"[{done}/{total}] {name}: {status}")))

    def _log(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")


class HashTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.input = ctk.CTkTextbox(self, height=140, width=700)
        self.input.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(self, text="Load File...", command=self._load_file).grid(row=1, column=0, sticky="w", padx=10)
        self.results = ctk.CTkTextbox(self, height=260, width=700)
        self.results.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self._hash()

    def _load_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.input.delete("1.0", "end")
            self.input.insert("1.0", Path(p).name + " (file hashed)")
            self._hash_from_file(Path(p))

    def _hash(self):
        text = self.input.get("1.0", "end").strip()
        if not text or text.endswith("(file hashed)"):
            return
        self._show(hash_text(text))

    def _hash_from_file(self, path: Path):
        self._show(hash_file(path))

    def _show(self, digests: dict):
        self.results.delete("1.0", "end")
        for algo, value in digests.items():
            self.results.insert("end", f"{algo:10s} {value}\n")


class FormatsTab(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master)
        row = 0
        for category, mapping in CATEGORIES.items():
            ctk.CTkLabel(self, text=f"=== {category} ===", font=("Segoe UI", 15, "bold")).grid(row=row, column=0, sticky="w", padx=5, pady=(10, 2))
            row += 1
            for src, targets in mapping.items():
                line = f"  .{src} -> " + ", ".join(f".{t}" for t in targets)
                ctk.CTkLabel(self, text=line, anchor="w").grid(row=row, column=0, sticky="w", padx=5)
                row += 1


class App(DnDApp):
    def __init__(self):
        super().__init__()
        self.title("OmniConvert")
        self.geometry("1100x700")
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True)
        for name in ("Images", "Documents", "Audio", "Video", "Text"):
            self.tabs.add(name)
            ConvertTab(self.tabs.tab(name), name).pack(fill="both", expand=True)
        self.tabs.add("Hash")
        HashTab(self.tabs.tab("Hash")).pack(fill="both", expand=True)
        self.tabs.add("Formats")
        FormatsTab(self.tabs.tab("Formats")).pack(fill="both", expand=True)
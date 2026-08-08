import sys


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


def main() -> None:
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    from omni.ui import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
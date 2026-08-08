import sys


def selftest() -> int:
    try:
        from omni.ui import App

        app = App()
        for _ in range(10):
            app.update_idletasks()
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
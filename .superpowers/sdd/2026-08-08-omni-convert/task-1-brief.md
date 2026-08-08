## Task 1: Project Scaffold + venv + smoke test

**Files:**
- Create: `requirements.txt`, `pyproject.toml`, `.gitignore`, `omni/__init__.py`, `omni/errors.py`, `tests/test_smoke.py`, `README.md` (placeholder)

**Interfaces:**
- Consumes: nothing.
- Produces: `omni.__version__`; `omni.errors.ConversionError` (subclasses Exception, has `.message`); `omni` importable from repo root; pytest green.

- [ ] **Step 1: Create venv and install dependencies**

```powershell
py -3 -m venv .venv
.venvScriptspython.exe -m pip install --upgrade pip
.venvScriptspython.exe -m pip install customtkinter Pillow pymupdf python-docx imageio-ffmpeg tkinterdnd2 markdown pytest pyinstaller
```

- [ ] **Step 2: Write the failing test**

`tests/test_smoke.py`:

```python
import omni
from omni.errors import ConversionError


def test_version():
    assert omni.__version__.count(".") == 2


def test_error_is_exception():
    err = ConversionError("boom")
    assert err.message == "boom"
    assert isinstance(err, Exception)
```

- [ ] **Step 3: Run it to verify it fails**

Run: `.venv\Scripts\python.exe -m pytest tests/test_smoke.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'omni'`

- [ ] **Step 4: Write minimal implementation**

`omni/__init__.py`:

```python
__version__ = "0.1.0"
```

`omni/errors.py`:

```python
class ConversionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
```

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

`requirements.txt`:

```
customtkinter>=5.2
pillow>=10.0
pymupdf>=1.24
python-docx>=1.1
imageio-ffmpeg>=0.4
tkinterdnd2>=0.4
markdown>=3.5
pytest>=8.0
pyinstaller>=6.3
# optional: cairosvg (enables svg -> png; needs native cairo DLLs on Windows)
```

`.gitignore`:

```
__pycache__/
*.pyc
.venv/
dist/
build/
*.spec
output/
*.log
```

- [ ] **Step 5: Run tests, verify pass**

Run: `.venv\Scripts\python.exe -m pytest -v`
Expected: 2 passed

- [ ] **Step 6: Set git identity and commit**

```bash
git config user.name "TT88990"
git config user.email "TT88990@users.noreply.github.com"
git add -A
git commit -m "feat: scaffold project, venv deps, smoke tests"
```



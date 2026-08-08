import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_selftest():
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "main.py"), "--selftest"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "SELFTEST OK" in proc.stdout
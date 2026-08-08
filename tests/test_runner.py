import io
from pathlib import Path

from PIL import Image

from omni.runner import Job, Runner, unique_output_path


def make_png(path: Path):
    Image.new("RGBA", (32, 32), (10, 200, 30, 255)).save(path, "PNG")
    return path


def test_unique_output_path(tmp_path):
    src = tmp_path / "pic.png"
    make_png(src)
    first = unique_output_path(tmp_path, src, "jpg")
    (tmp_path / "pic.jpg").write_bytes(b"x")
    second = unique_output_path(tmp_path, src, "jpg")
    assert first.name == "pic.jpg"
    assert second.name == "pic (1).jpg"


def test_runner_converts_batch(tmp_path):
    srcs = [make_png(tmp_path / f"p{i}.png") for i in range(3)]
    out = tmp_path / "out"
    jobs = [Job(src=s, target_ext="webp", category="Images") for s in srcs]
    results = Runner().run(jobs, out)
    assert len(results) == 3
    assert all(err is None for _, err in results)
    assert all(p.exists() for p, _ in results)


def test_runner_reports_progress_and_error(tmp_path):
    src = make_png(tmp_path / "ok.png")
    missing = tmp_path / "gone.png"
    calls = []
    results = Runner().run(
        [Job(src=missing, target_ext="jpg", category="Images"), Job(src=src, target_ext="jpg", category="Images")],
        tmp_path / "out",
        on_progress=lambda d, t, n, s: calls.append((d, t, n, s)),
    )
    assert calls[-1][0] == 2 and calls[-1][1] == 2
    assert results[0][1] is not None
    assert results[1][1] is None
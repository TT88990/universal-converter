import io
from pathlib import Path

from PIL import Image

from omni.ffmpeg import run_ffmpeg
from omni.runner import Job, Runner, unique_output_path


def make_png(path: Path):
    Image.new("RGBA", (32, 32), (10, 200, 30, 255)).save(path, "PNG")
    return path


def make_mp4(path: Path, seconds=2):
    run_ffmpeg(
        [
            "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=320x240:rate=15",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(path),
        ]
    )
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


def test_runner_frames_ok(tmp_path):
    src = make_mp4(tmp_path / "clip.mp4")
    out = tmp_path / "out"
    results = Runner().run([Job(src=src, target_ext="frames", category="Video")], out)
    assert results[0][1] is None
    folder = results[0][0]
    assert folder.exists() and folder.is_dir()
    assert len(list(folder.glob("*.png"))) >= 1
    log = out / "universal-converter.log"
    assert "clip.mp4" in log.read_text(encoding="utf-8")
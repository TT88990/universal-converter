from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from omni.matrix import CONVERTERS

ProgressCb = Callable[[int, int, str, str], None]


@dataclass
class Job:
    src: Path
    target_ext: str
    category: str


def unique_output_path(out_dir: Path, src: Path, ext: str) -> Path:
    candidate = out_dir / f"{src.stem}.{ext}"
    n = 1
    while candidate.exists():
        candidate = out_dir / f"{src.stem} ({n}).{ext}"
        n += 1
    return candidate


class Runner:
    def __init__(self) -> None:
        self.converters = CONVERTERS

    def run(self, jobs: list[Job], out_dir: Path, on_progress: ProgressCb | None = None) -> list[tuple[Path, str | None]]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results: list[tuple[Path, str | None]] = []
        total = len(jobs)
        for done, job in enumerate(jobs, start=1):
            target = unique_output_path(out_dir, job.src, job.target_ext)
            error: str | None = None
            try:
                src_ext = job.src.suffix.lower().lstrip(".")
                fn = self.converters[job.category][src_ext][job.target_ext]
                if job.target_ext == "pdf" and job.category == "Images":
                    fn([job.src], target)
                else:
                    fn(job.src, target)
            except Exception as exc:
                error = str(exc)
            results.append((target, error))
            if on_progress:
                on_progress(done, total, job.src.name, "done" if error is None else f"error: {error}")
        return results
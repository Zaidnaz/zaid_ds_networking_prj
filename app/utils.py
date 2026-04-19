from __future__ import annotations

from pathlib import Path


def ensure_parent_dir(file_path: str | Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

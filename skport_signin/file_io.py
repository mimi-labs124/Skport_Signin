from __future__ import annotations

from pathlib import Path
from uuid import uuid4


def write_text_atomic(path: Path, contents: str, *, encoding: str = "utf-8") -> None:
    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temp_path.write_text(contents, encoding=encoding)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

from skport_signin.app_paths import AppPaths, build_app_paths


class _NullTextIO:
    def write(self, text: str) -> int:
        return len(text)

    def flush(self) -> None:
        return None


@dataclass
class RuntimeContext:
    app_paths: AppPaths
    stdout: TextIO
    stderr: TextIO


def build_runtime_context(
    *,
    config_override: str | None = None,
    base_dir_override: str | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> RuntimeContext:
    resolved_stdout = stdout if stdout is not None else sys.stdout
    resolved_stderr = stderr if stderr is not None else sys.stderr
    return RuntimeContext(
        app_paths=build_app_paths(
            config_override=config_override,
            base_dir_override=base_dir_override,
        ),
        stdout=resolved_stdout or _NullTextIO(),
        stderr=resolved_stderr or _NullTextIO(),
    )


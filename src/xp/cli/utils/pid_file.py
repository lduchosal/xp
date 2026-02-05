"""PID file management utilities."""

import os
from contextlib import suppress
from pathlib import Path


def write_pid_file(path: str) -> None:
    """
    Write current process ID to a file.

    Creates parent directories if they don't exist.

    Args:
        path: Path to the PID file.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(str(os.getpid()))


def remove_pid_file(path: str) -> None:
    """
    Remove a PID file.

    Silently ignores if file doesn't exist.

    Args:
        path: Path to the PID file.
    """
    with suppress(FileNotFoundError):
        Path(path).unlink()

"""File IO helpers for PEPScript."""

from __future__ import annotations

from pathlib import Path

from .exceptions import FileLoadError, SaveError
from .models import ScriptFileInfo


def build_file_info(path: Path, *, encoding: str) -> ScriptFileInfo:
    """Build typed file info for a script path."""

    return ScriptFileInfo(
        path=path,
        name=path.stem,
        filename=path.name,
        suffix=path.suffix,
        exists=path.exists(),
        encoding=encoding,
    )


def read_source(path: Path, *, encoding: str) -> str:
    """Read source from disk."""

    try:
        return path.read_text(encoding=encoding)
    except OSError as error:
        raise FileLoadError(f"Failed to read file: {path}") from error


def write_source(path: Path, source: str, *, encoding: str) -> None:
    """Write source to disk."""

    try:
        path.write_text(source, encoding=encoding)
    except OSError as error:
        raise SaveError(f"Failed to write file: {path}") from error

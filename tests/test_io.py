"""Tests for file IO error handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from pepscript import PEPScript
from pepscript.exceptions import FileLoadError, SaveError


def test_read_nonexistent_file_raises_file_load_error() -> None:
    with pytest.raises(FileLoadError):
        PEPScript("/nonexistent/path/to/script.py")


def test_write_to_unwritable_path_raises_save_error(tmp_path: Path) -> None:
    src = tmp_path / "script.py"
    src.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(src)
    script.meta.add_dependency("httpx")

    # Point to a directory that doesn't exist
    script.path = tmp_path / "nonexistent_dir" / "output.py"
    with pytest.raises(SaveError):
        script.save()

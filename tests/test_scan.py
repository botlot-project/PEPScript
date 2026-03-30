from __future__ import annotations

import os
from pathlib import Path

import pytest

from pepscript import iter_scan_scripts, scan_scripts
from pepscript.diagnostics import SCAN_FILE_READ
from pepscript.exceptions import FileLoadError, MetadataValidationError


def test_scan_scripts_classifies_valid_invalid_and_non_pep(tmp_path: Path) -> None:
    valid = tmp_path / "valid.py"
    valid.write_text('# /// script\n# dependencies = ["httpx>=0.27"]\n# ///\n', "utf-8")

    invalid = tmp_path / "invalid.py"
    invalid.write_text(
        '# /// script\n# dependencies = ["requests>>2.0"]\n# ///\n', "utf-8"
    )

    plain = tmp_path / "plain.py"
    plain.write_text('print("hi")\n', "utf-8")

    results = scan_scripts(tmp_path)
    statuses = {item.path.name: item.status for item in results}
    assert statuses["valid.py"] == "valid"
    assert statuses["invalid.py"] == "invalid"
    assert statuses["plain.py"] == "non_pep723"


def test_scan_scripts_include_non_pep_false(tmp_path: Path) -> None:
    (tmp_path / "plain.py").write_text('print("hi")\n', "utf-8")
    (tmp_path / "with_meta.py").write_text(
        '# /// script\n# dependencies = ["httpx>=0.27"]\n# ///\n',
        "utf-8",
    )

    results = scan_scripts(tmp_path, include_non_pep=False)
    names = [item.path.name for item in results]
    assert names == ["with_meta.py"]


def test_iter_scan_scripts_respects_include_exclude(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text('print("a")\n', "utf-8")
    (tmp_path / "b.txt").write_text("x", "utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.py").write_text('print("c")\n', "utf-8")

    results = list(
        iter_scan_scripts(
            tmp_path,
            include=("**/*.py",),
            exclude=("sub/*.py",),
        )
    )
    names = sorted(item.path.name for item in results)
    assert names == ["a.py"]


def test_scan_scripts_strict_false_skips_validation(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.py"
    invalid.write_text(
        '# /// script\n# dependencies = ["requests>>2.0"]\n# ///\n', "utf-8"
    )

    results = scan_scripts(tmp_path, strict=False)
    assert len(results) == 1
    assert results[0].status == "valid"
    assert not results[0].validated
    assert results[0].metadata is not None


def test_scan_scripts_fail_fast_raises(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.py"
    invalid.write_text(
        '# /// script\n# dependencies = ["requests>>2.0"]\n# ///\n', "utf-8"
    )

    with pytest.raises(MetadataValidationError):
        list(iter_scan_scripts(tmp_path, fail_fast=True))


def test_scan_root_file_path_supported(tmp_path: Path) -> None:
    script_path = tmp_path / "single.py"
    script_path.write_text(
        '# /// script\n# dependencies = ["httpx>=0.27"]\n# ///\n', "utf-8"
    )

    results = list(iter_scan_scripts(script_path))

    assert len(results) == 1
    assert results[0].path == script_path
    assert results[0].status == "valid"


def test_scan_missing_root_raises_file_load_error() -> None:
    with pytest.raises(FileLoadError):
        list(iter_scan_scripts("/definitely/not/real/path/for/pepscript"))


def test_scan_reports_parse_errors(tmp_path: Path) -> None:
    bad = tmp_path / "bad.py"
    bad.write_text('# /// script\n# dependencies = ["httpx"\n# ///\n', "utf-8")

    results = scan_scripts(tmp_path)

    assert len(results) == 1
    assert results[0].status == "invalid"
    assert results[0].error is not None
    assert results[0].diagnostics
    assert results[0].diagnostics[0].code.startswith("PSP")


def test_scan_reports_file_read_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "broken.py"
    path.write_text('print("x")\n', "utf-8")

    import pepscript.scan as scan_module

    def _fake_read_source(_: Path, *, encoding: str) -> str:
        raise FileLoadError("Failed to read file: fake")

    monkeypatch.setattr(scan_module, "read_source", _fake_read_source)

    results = list(scan_module.iter_scan_scripts(tmp_path))
    assert len(results) == 1
    assert results[0].status == "invalid"
    assert results[0].diagnostics
    assert results[0].diagnostics[0].code == "PSS001"


def test_scan_reports_decode_failures_as_invalid_results(tmp_path: Path) -> None:
    path = tmp_path / "broken.py"
    path.write_bytes(b"\xff\xfe\x00")

    results = scan_scripts(tmp_path)

    assert len(results) == 1
    assert results[0].status == "invalid"
    assert isinstance(results[0].error, FileLoadError)
    assert results[0].diagnostics
    assert results[0].diagnostics[0].code == SCAN_FILE_READ


def test_scan_prunes_excluded_directories_before_descending(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "keep.py").write_text('print("keep")\n', "utf-8")
    excluded_dir = tmp_path / ".venv"
    excluded_dir.mkdir()
    (excluded_dir / "skip.py").write_text('print("skip")\n', "utf-8")

    original_scandir = os.scandir

    def _guarded_scandir(path: str | bytes | os.PathLike[str] | os.PathLike[bytes]):
        if Path(path) == excluded_dir:
            raise AssertionError("excluded directory was traversed")
        return original_scandir(path)

    monkeypatch.setattr(os, "scandir", _guarded_scandir)

    results = scan_scripts(tmp_path, exclude=(".venv/**",))

    assert [item.path.name for item in results] == ["keep.py"]

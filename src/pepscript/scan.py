"""Batch script discovery and scanning APIs."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
import fnmatch
from pathlib import Path
from typing import Literal

from .diagnostics import Diagnostic, SCAN_FILE_READ
from .exceptions import FileLoadError, MetadataValidationError, PEPScriptError
from .io import read_source
from .models import Metadata
from .parser import parse_source
from .validate import collect_validation_diagnostics


@dataclass(slots=True, frozen=True)
class ScanResult:
    """Per-file result emitted by scan APIs."""

    path: Path
    status: Literal["valid", "invalid", "non_pep723"]
    has_metadata: bool
    metadata: Metadata | None
    diagnostics: tuple[Diagnostic, ...]
    error: PEPScriptError | None
    validated: bool


def _matches_glob(path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatchcase(path, pattern[3:])
    return False


def _is_selected(path: str, *, include: Sequence[str], exclude: Sequence[str]) -> bool:
    include_match = (
        True
        if not include
        else any(_matches_glob(path, pattern) for pattern in include)
    )
    if not include_match:
        return False
    return not any(_matches_glob(path, pattern) for pattern in exclude)


def _is_excluded_directory(path: str, *, exclude: Sequence[str]) -> bool:
    if not path:
        return False
    directory = f"{path}/"
    return any(
        _matches_glob(path, pattern) or _matches_glob(directory, pattern)
        for pattern in exclude
    )


def _iter_files(root_path: Path, *, exclude: Sequence[str] = ()) -> Iterator[Path]:
    if root_path.is_file():
        yield root_path
        return
    if not root_path.exists():
        raise FileLoadError(f"Failed to read file: {root_path}")

    def walk(path: Path) -> Iterator[Path]:
        try:
            entries = sorted(path.iterdir(), key=lambda item: item.as_posix())
        except OSError as error:
            raise FileLoadError(f"Failed to read file: {path}") from error

        for entry in entries:
            relative = entry.relative_to(root_path).as_posix()
            try:
                if entry.is_dir():
                    if _is_excluded_directory(relative, exclude=exclude):
                        continue
                    yield from walk(entry)
                    continue
                if entry.is_file():
                    yield entry
            except OSError as error:
                raise FileLoadError(f"Failed to read file: {entry}") from error

    yield from walk(root_path)


def _make_invalid_result(
    *,
    path: Path,
    has_metadata: bool,
    metadata: Metadata | None,
    diagnostics: Sequence[Diagnostic],
    error: PEPScriptError,
    validated: bool,
) -> ScanResult:
    return ScanResult(
        path=path,
        status="invalid",
        has_metadata=has_metadata,
        metadata=metadata,
        diagnostics=tuple(diagnostics),
        error=error,
        validated=validated,
    )


def iter_scan_scripts(
    root: str | Path,
    *,
    include: Sequence[str] = ("**/*.py",),
    exclude: Sequence[str] = (),
    encoding: str = "utf-8",
    strict: bool = True,
    include_non_pep: bool = True,
    fail_fast: bool = False,
) -> Iterator[ScanResult]:
    """Iterate over discovered files and classify metadata status."""

    root_path = Path(root)
    for path in _iter_files(root_path, exclude=exclude):
        relative = (
            path.name if root_path.is_file() else path.relative_to(root_path).as_posix()
        )
        if not _is_selected(relative, include=include, exclude=exclude):
            continue

        try:
            source = read_source(path, encoding=encoding)
        except (FileLoadError, UnicodeDecodeError) as error:
            if isinstance(error, UnicodeDecodeError):
                message = f"Failed to read file: {path} ({encoding} decode error)"
                diagnostic = Diagnostic(
                    code=SCAN_FILE_READ,
                    message=message,
                    path=path,
                )
                error = FileLoadError(message, diagnostic=diagnostic)
            diagnostic = error.diagnostic
            if diagnostic is None:
                diagnostic = Diagnostic(
                    code=SCAN_FILE_READ,
                    message=str(error),
                    path=path,
                )
                error = FileLoadError(str(error), diagnostic=diagnostic)
            if fail_fast:
                raise error
            yield _make_invalid_result(
                path=path,
                has_metadata=False,
                metadata=None,
                diagnostics=(diagnostic,),
                error=error,
                validated=False,
            )
            continue

        try:
            parsed = parse_source(source, strict=False, path=path)
        except PEPScriptError as error:
            diagnostics = (
                error.diagnostics
                if error.diagnostics
                else ((error.diagnostic,) if error.diagnostic is not None else ())
            )
            if fail_fast:
                raise error
            yield _make_invalid_result(
                path=path,
                has_metadata=False,
                metadata=None,
                diagnostics=diagnostics,
                error=error,
                validated=False,
            )
            continue

        if parsed.meta is None:
            if not include_non_pep:
                continue
            yield ScanResult(
                path=path,
                status="non_pep723",
                has_metadata=False,
                metadata=None,
                diagnostics=(),
                error=None,
                validated=False,
            )
            continue

        diagnostics = (
            collect_validation_diagnostics(parsed.meta, path=path) if strict else []
        )
        if diagnostics:
            error = MetadataValidationError(
                diagnostics[0].message,
                diagnostic=diagnostics[0],
                diagnostics=diagnostics,
            )
            if fail_fast:
                raise error
            yield _make_invalid_result(
                path=path,
                has_metadata=True,
                metadata=parsed.meta,
                diagnostics=diagnostics,
                error=error,
                validated=True,
            )
            continue

        yield ScanResult(
            path=path,
            status="valid",
            has_metadata=True,
            metadata=parsed.meta,
            diagnostics=(),
            error=None,
            validated=strict,
        )


def scan_scripts(
    root: str | Path,
    *,
    include: Sequence[str] = ("**/*.py",),
    exclude: Sequence[str] = (),
    encoding: str = "utf-8",
    strict: bool = True,
    include_non_pep: bool = True,
    fail_fast: bool = False,
) -> list[ScanResult]:
    """Eagerly scan files and return all results as a list."""

    return list(
        iter_scan_scripts(
            root,
            include=include,
            exclude=exclude,
            encoding=encoding,
            strict=strict,
            include_non_pep=include_non_pep,
            fail_fast=fail_fast,
        )
    )

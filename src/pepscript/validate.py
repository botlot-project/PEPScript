"""PEP 508 dependency and PEP 440 version specifier validation for parsed metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from .config import ConfigNode
from .exceptions import MetadataValidationError
from .models import PEPMetadata

# PEP 508 distribution name: starts/ends with alphanumeric, may contain ._- in between
_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")

# PEP 440 version clause: operator + version string (e.g. ">=1.0", "==1.*")
_VERSION_CLAUSE_RE = re.compile(
    r"^\s*(~=|===|==|!=|<=|>=|<|>)\s*[A-Za-z0-9.*+!_-]+\s*$"
)

# Valid PEP 508 marker variable names
_VALID_MARKER_VARS = frozenset(
    {
        "os_name",
        "sys_platform",
        "platform_machine",
        "platform_python_implementation",
        "platform_release",
        "platform_system",
        "platform_version",
        "python_version",
        "python_full_version",
        "implementation_name",
        "implementation_version",
        "extra",
        # Deprecated setuptools-style dotted names still seen in the wild
        "os.name",
        "sys.platform",
        "platform.version",
        "platform.machine",
        "platform.python_implementation",
    }
)

_MARKER_KEYWORDS = frozenset({"and", "or", "not", "in"})

# Matches simple and dotted identifiers (e.g. python_version, os.name)
_MARKER_IDENT_RE = re.compile(r"\b([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*)\b")


def _raise_validation_error(message: str, *, path: Path | None = None) -> None:
    if path is None:
        raise MetadataValidationError(message)
    raise MetadataValidationError(f"{message} (path={path})")


def _is_scalar(value: object) -> bool:
    return isinstance(value, (str, int, float, bool))


def _validate_tool_value(
    value: object, *, path: Path | None = None, location: str = "tool"
) -> None:
    if isinstance(value, ConfigNode):
        _validate_tool_value(value.to_dict(), path=path, location=location)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                _raise_validation_error(f"{location} keys must be strings", path=path)
            _validate_tool_value(item, path=path, location=f"{location}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_tool_value(item, path=path, location=f"{location}[{index}]")
        return
    if _is_scalar(value):
        return
    _raise_validation_error(
        f"{location} contains unsupported value type: {type(value).__name__}", path=path
    )


def _validate_marker(marker: str, *, loc: str, path: Path | None = None) -> None:
    """Check that all unquoted identifiers in a marker expression are valid."""
    without_quotes = re.sub(r'"[^"]*"|\'[^\']*\'', "", marker)
    for match in _MARKER_IDENT_RE.finditer(without_quotes):
        ident = match.group(1)
        if ident in _MARKER_KEYWORDS:
            continue
        if ident not in _VALID_MARKER_VARS:
            _raise_validation_error(
                f"{loc} has unknown marker variable {ident!r}", path=path
            )


def _validate_pep508_dependency(
    dep: str, *, path: Path | None = None, index: int = 0
) -> None:
    """Validate a single PEP 508 dependency specifier string."""
    loc = f"dependencies[{index}]"
    raw = dep.strip()

    if not raw:
        _raise_validation_error(f"{loc} must not be empty", path=path)

    # Split off environment marker at first semicolon
    if ";" in raw:
        req_part, marker_part = raw.split(";", 1)
        _validate_marker(marker_part.strip(), loc=loc, path=path)
    else:
        req_part = raw

    req_part = req_part.strip()
    is_url = "@" in req_part

    # For URL requirements validate only the name/extras part before the @
    name_scope = req_part[: req_part.index("@")].strip() if is_url else req_part

    # Extract package name (stops at [, version operator chars, whitespace, or end)
    name_match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", name_scope)
    if not name_match:
        _raise_validation_error(
            f"{loc} has an invalid package name in {dep!r}", path=path
        )
        return  # pragma: no cover  # unreachable; satisfies type checker

    name = name_match.group()
    if not _NAME_RE.match(name):
        _raise_validation_error(
            f"{loc} has invalid package name {name!r}", path=path
        )

    rest = name_scope[name_match.end() :].strip()

    # Optional extras: [extra1, extra2, ...]
    if rest.startswith("["):
        close = rest.find("]")
        if close == -1:
            _raise_validation_error(
                f"{loc} has unclosed extras '[' in {dep!r}", path=path
            )
        for extra in rest[1:close].split(","):
            e = extra.strip()
            if not e:
                continue
            if not _NAME_RE.match(e):
                _raise_validation_error(
                    f"{loc} has invalid extra {e!r}", path=path
                )
        rest = rest[close + 1 :].strip()

    # Version specifiers (not applicable for URL requirements)
    if not is_url and rest:
        for clause in rest.split(","):
            if not _VERSION_CLAUSE_RE.match(clause):
                _raise_validation_error(
                    f"{loc} has invalid version specifier {clause.strip()!r} in {dep!r}",
                    path=path,
                )


def _validate_requires_python(spec: str, *, path: Path | None = None) -> None:
    """Validate a PEP 440 requires-python version specifier string."""
    for clause in spec.split(","):
        if not _VERSION_CLAUSE_RE.match(clause):
            _raise_validation_error(
                f"'requires-python' has invalid specifier {clause.strip()!r}",
                path=path,
            )


def validate_metadata(meta: PEPMetadata | None, *, path: Path | None = None) -> None:
    """Validate metadata structure, PEP 508 dependency specifiers, and PEP 440 version constraints."""

    if meta is None:
        return

    if not isinstance(meta.dependencies, list):
        _raise_validation_error("'dependencies' must be a list", path=path)
    for index, dep in enumerate(meta.dependencies):
        if not isinstance(dep, str):
            _raise_validation_error(
                f"'dependencies[{index}]' must be a string",
                path=path,
            )
        else:
            _validate_pep508_dependency(dep, path=path, index=index)

    if meta.requires_python is not None:
        if not isinstance(meta.requires_python, str):
            _raise_validation_error(
                "'requires-python' must be a string or None", path=path
            )
        else:
            _validate_requires_python(meta.requires_python, path=path)

    _validate_tool_value(meta.config.tool, path=path)

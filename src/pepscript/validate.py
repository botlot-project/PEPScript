"""Structural validation for parsed metadata."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .config import ConfigNode
from .exceptions import MetadataValidationError
from .models import PEPMetadata


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


def validate_metadata(meta: PEPMetadata | None, *, path: Path | None = None) -> None:
    """Validate the structural shape of metadata."""

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

    if meta.requires_python is not None and not isinstance(meta.requires_python, str):
        _raise_validation_error("'requires-python' must be a string or None", path=path)

    _validate_tool_value(meta.config.tool, path=path)

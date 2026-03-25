"""Typed models for PEPScript."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import ToolConfig


def _mapping_is_deep_empty(value: Mapping[str, Any]) -> bool:
    if not value:
        return True
    return all(
        isinstance(item, Mapping) and _mapping_is_deep_empty(item)
        for item in value.values()
    )


@dataclass(slots=True)
class ScriptFileInfo:
    """Summary of file metadata exposed by PEPScript."""

    path: Path
    name: str
    filename: str
    suffix: str
    exists: bool
    encoding: str


@dataclass(slots=True)
class BlockInfo:
    """Character offsets for a PEP 723 metadata block."""

    start: int
    end: int
    content_start: int
    content_end: int
    block_type: str


@dataclass(slots=True)
class ConfigRoot:
    """Root container for metadata configuration."""

    tool: ToolConfig = field(default_factory=ToolConfig)


@dataclass(slots=True)
class Metadata:
    """Typed metadata model for PEP 723 script metadata."""

    dependencies: list[str] = field(default_factory=list)
    requires_python: str | None = None
    config: ConfigRoot = field(default_factory=ConfigRoot)

    def add_dependency(self, dep: str) -> None:
        """Add a dependency if it is not already present (exact string match).

        Args:
            dep: A PEP 508 dependency specifier string (e.g. ``"requests>=2.0"``).
        """
        if dep not in self.dependencies:
            self.dependencies.append(dep)

    def remove_dependency(self, dep: str) -> None:
        """Remove a dependency if present (exact string match, no-op if not found).

        Args:
            dep: The exact dependency string to remove.
        """
        if dep in self.dependencies:
            self.dependencies.remove(dep)

    def set_requires_python(self, spec: str | None) -> None:
        """Set or remove the ``requires-python`` field.

        Args:
            spec: A PEP 440 version specifier string (e.g. ``">=3.12"``), or
                ``None`` to remove the field from the metadata block.
        """
        self.requires_python = spec

    @property
    def is_empty(self) -> bool:
        """Return ``True`` if this metadata object holds no meaningful content.

        Used internally to decide whether to write a ``# /// script`` block
        when the source did not originally contain one.
        """
        return (
            not self.dependencies
            and self.requires_python is None
            and _mapping_is_deep_empty(self.config.tool.to_dict())
        )

"""Typed models for PEPScript."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import ConfigNode


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
class PEPConfigRoot:
    """Root container for metadata configuration."""

    tool: ConfigNode = field(default_factory=ConfigNode)


@dataclass(slots=True)
class PEPMetadata:
    """Typed metadata model for PEP 723 script metadata."""

    dependencies: list[str] = field(default_factory=list)
    requires_python: str | None = None
    config: PEPConfigRoot = field(default_factory=PEPConfigRoot)

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

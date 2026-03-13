"""Typed models for pepscript."""

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
        if dep not in self.dependencies:
            self.dependencies.append(dep)

    def remove_dependency(self, dep: str) -> None:
        if dep in self.dependencies:
            self.dependencies.remove(dep)

    def set_requires_python(self, spec: str | None) -> None:
        self.requires_python = spec


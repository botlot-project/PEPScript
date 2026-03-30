"""Typed models for PEPScript."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Any, Literal

from .config import ToolConfig

_DEPENDENCY_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def _mapping_is_deep_empty(value: Mapping[str, Any]) -> bool:
    if not value:
        return True
    return all(
        isinstance(item, Mapping) and _mapping_is_deep_empty(item)
        for item in value.values()
    )


def canonicalize_dependency_name(name: str) -> str:
    """Normalize a distribution name for name-based matching (PEP 503-style)."""

    return re.sub(r"[-_.]+", "-", name).lower()


def extract_dependency_name(specifier: str) -> str | None:
    """Extract and normalize the package name prefix from a dependency string."""

    raw = specifier.strip()
    if not raw:
        return None

    requirement = raw.split(";", 1)[0].strip()
    name_scope = (
        requirement.split("@", 1)[0].strip() if "@" in requirement else requirement
    )
    match = _DEPENDENCY_NAME_RE.match(name_scope)
    if match is None:
        return None
    return canonicalize_dependency_name(match.group(0))


def _normalize_dependency_query(query: str) -> str | None:
    return extract_dependency_name(query)


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

    def has_dependency(
        self, query: str, *, match: Literal["exact", "name"] = "name"
    ) -> bool:
        """Return whether a dependency is present.

        Args:
            query: Dependency query. For ``match="exact"``, this is matched as-is.
                For ``match="name"``, package names are normalized before matching.
            match: Matching mode, either exact string or package-name based.
        """
        if match == "exact":
            return query in self.dependencies

        normalized = _normalize_dependency_query(query)
        if normalized is None:
            return False
        return any(
            extract_dependency_name(dep) == normalized for dep in self.dependencies
        )

    def get_dependency_by_name(self, name: str) -> str | None:
        """Return the first dependency matching *name* (normalized), if any."""

        normalized = _normalize_dependency_query(name)
        if normalized is None:
            return None
        for dep in self.dependencies:
            if extract_dependency_name(dep) == normalized:
                return dep
        return None

    def replace_dependency_by_name(
        self, dependency: str, *, add_if_missing: bool = True
    ) -> bool:
        """Replace dependencies with the same package name and preserve order.

        Returns ``True`` if the dependency list changed.
        """

        normalized = extract_dependency_name(dependency)
        if normalized is None:
            raise ValueError(
                f"Cannot determine package name from dependency: {dependency!r}"
            )

        matches = [
            index
            for index, candidate in enumerate(self.dependencies)
            if extract_dependency_name(candidate) == normalized
        ]
        if not matches:
            if not add_if_missing:
                return False
            self.dependencies.append(dependency)
            return True

        changed = False
        first = matches[0]
        if self.dependencies[first] != dependency:
            self.dependencies[first] = dependency
            changed = True

        for index in reversed(matches[1:]):
            del self.dependencies[index]
            changed = True

        return changed

    def remove_dependency_by_name(
        self, name: str, *, all_matches: bool = True
    ) -> list[str]:
        """Remove dependencies matching *name* and return removed entries."""

        normalized = _normalize_dependency_query(name)
        if normalized is None:
            return []

        removed: list[str] = []
        kept: list[str] = []
        for dep in self.dependencies:
            matches = extract_dependency_name(dep) == normalized
            if matches and (all_matches or not removed):
                removed.append(dep)
                continue
            kept.append(dep)
        if removed:
            self.dependencies[:] = kept
        return removed

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

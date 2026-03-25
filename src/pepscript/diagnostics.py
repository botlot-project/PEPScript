"""Structured diagnostics for parse and validation issues."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class Diagnostic:
    """Machine-readable diagnostic emitted by parsing/validation/scanning."""

    code: str
    message: str
    path: Path | None = None
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None
    field: str | None = None


# Parse diagnostics (PSP###)
PARSE_INDENTED_MARKER = "PSP001"
PARSE_UNCLOSED_BLOCK = "PSP002"
PARSE_INVALID_CONTENT_LINE = "PSP003"
PARSE_INVALID_TOML = "PSP004"
PARSE_INVALID_METADATA_TYPE = "PSP005"
PARSE_DUPLICATE_BLOCK = "PSP006"

# Validation diagnostics (PSV###)
VALIDATION_DEPENDENCIES_TYPE = "PSV001"
VALIDATION_DEPENDENCY_ENTRY_TYPE = "PSV002"
VALIDATION_DEPENDENCY_SPEC = "PSV003"
VALIDATION_REQUIRES_PYTHON_TYPE = "PSV004"
VALIDATION_REQUIRES_PYTHON_SPEC = "PSV005"
VALIDATION_TOOL_VALUE_TYPE = "PSV006"
VALIDATION_TOOL_KEY_TYPE = "PSV007"

# Scanner diagnostics (PSS###)
SCAN_FILE_READ = "PSS001"

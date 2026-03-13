"""Custom exceptions for pepscript."""

from __future__ import annotations


class PepScriptError(Exception):
    """Base exception for all pepscript errors."""


class FileLoadError(PepScriptError):
    """Raised when a script file cannot be read."""


class MetadataBlockNotFoundError(PepScriptError):
    """Raised when a metadata block is expected but missing."""


class DuplicateMetadataBlockError(PepScriptError):
    """Raised when multiple PEP 723 metadata blocks are present."""


class MetadataParseError(PepScriptError):
    """Raised when metadata cannot be parsed."""


class MetadataValidationError(PepScriptError):
    """Raised when metadata is structurally invalid."""


class SaveError(PepScriptError):
    """Raised when a script cannot be saved."""

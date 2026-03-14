"""Custom exceptions for PEPScript."""

from __future__ import annotations


class PEPScriptError(Exception):
    """Base exception for all PEPScript errors."""


class FileLoadError(PEPScriptError):
    """Raised when a script file cannot be read."""


class DuplicateMetadataBlockError(PEPScriptError):
    """Raised when multiple PEP 723 metadata blocks are present."""


class MetadataParseError(PEPScriptError):
    """Raised when metadata cannot be parsed."""


class MetadataValidationError(PEPScriptError):
    """Raised when metadata is structurally invalid."""


class SaveError(PEPScriptError):
    """Raised when a script cannot be saved."""

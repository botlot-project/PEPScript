"""Custom exceptions for PEPScript."""

from __future__ import annotations

from collections.abc import Iterable

from .diagnostics import Diagnostic


class PEPScriptError(Exception):
    """Base exception for all PEPScript errors."""

    diagnostic: Diagnostic | None
    diagnostics: tuple[Diagnostic, ...]

    def __init__(
        self,
        message: str,
        *,
        diagnostic: Diagnostic | None = None,
        diagnostics: Iterable[Diagnostic] | None = None,
    ) -> None:
        resolved: tuple[Diagnostic, ...]
        if diagnostics is not None:
            resolved = tuple(diagnostics)
        elif diagnostic is not None:
            resolved = (diagnostic,)
        else:
            resolved = ()

        self.diagnostic = (
            diagnostic
            if diagnostic is not None
            else (resolved[0] if resolved else None)
        )
        self.diagnostics = resolved
        super().__init__(message)


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

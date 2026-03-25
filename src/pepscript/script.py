"""Public PEPScript document API."""

from __future__ import annotations

import copy
from pathlib import Path

from .diagnostics import Diagnostic
from .exceptions import SaveError
from .io import build_file_info, read_source, write_source
from .models import BlockInfo, Metadata, ScriptFileInfo
from .parser import parse_source
from .serialize import rewrite_source
from .validate import collect_validation_diagnostics, validate_metadata


class PEPScript:
    """A typed document wrapper for PEP 723-enabled scripts."""

    path: Path | None
    encoding: str
    strict: bool
    source: str
    file: ScriptFileInfo | None
    meta: Metadata
    has_metadata: bool
    _block: BlockInfo | None
    _snapshot: tuple[Metadata, BlockInfo | None, bool] | None

    def __init__(
        self, path: str | Path, *, encoding: str = "utf-8", strict: bool = True
    ):
        """Load and parse a PEP 723 script from disk.

        Args:
            path: Path to the Python script file.
            encoding: File encoding used when reading and writing. Defaults to ``"utf-8"``.
            strict: If ``True`` (default), validate metadata immediately after parsing.

        Raises:
            FileLoadError: If the file cannot be read.
            DuplicateMetadataBlockError: If more than one ``# /// script`` block is found.
            MetadataParseError: If the embedded TOML is malformed.
            MetadataValidationError: If ``strict=True`` and the metadata fails validation.
        """
        self.path = Path(path)
        self.encoding = encoding
        self.strict = strict
        self.source = ""
        self.file = None
        self.meta = Metadata()
        self.has_metadata = False
        self._block = None
        self._snapshot = None
        self.reload()

    @classmethod
    def from_source(cls, source: str, *, strict: bool = True) -> PEPScript:
        """Create an in-memory script document from source text."""

        instance = cls.__new__(cls)
        instance.path = None
        instance.encoding = "utf-8"
        instance.strict = strict
        instance.source = source
        instance.file = None
        instance.meta = Metadata()
        instance.has_metadata = False
        instance._block = None
        instance._snapshot = None
        instance._parse_current_source()
        return instance

    def __enter__(self) -> PEPScript:
        """Enter edit mode, snapshotting current metadata for potential rollback.

        On a clean exit, changes are automatically persisted via ``save()``
        (file-backed scripts only; in-memory scripts retain edits in-memory).
        If an exception propagates out of the ``with`` block, all in-memory
        edits are discarded by restoring the pre-enter snapshot.

        Only ``meta``, ``has_metadata``, and the internal block offsets are
        snapshotted — the full source text is not copied — so this is efficient
        even for large files.
        """
        self._snapshot = (copy.deepcopy(self.meta), self._block, self.has_metadata)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit edit mode, saving or rolling back depending on whether an exception occurred.

        On clean exit, ``save()`` is called for file-backed scripts.
        On exception, in-memory state is restored from the snapshot taken at
        ``__enter__`` and the exception is re-raised.
        """
        try:
            if exc_type is None:
                if self.path is not None:
                    self.save()
            else:
                if self._snapshot is not None:
                    self.meta, self._block, self.has_metadata = self._snapshot
        finally:
            self._snapshot = None
        return None

    def _parse_current_source(self) -> None:
        parsed = parse_source(self.source, strict=self.strict, path=self.path)
        self.has_metadata = parsed.meta is not None
        self.meta = parsed.meta if parsed.meta is not None else Metadata()
        self._block = parsed.block

    def _meta_to_write(self) -> Metadata | None:
        if self.meta.is_empty:
            return None
        return self.meta

    def _validated_source_for_write(self) -> str:
        meta_to_write = self._meta_to_write()
        if meta_to_write is not None:
            validate_metadata(meta_to_write, path=self.path)
        return rewrite_source(self.source, meta=meta_to_write, block=self._block)

    def validate(self) -> None:
        """Run structural validation against the current metadata.

        This is a no-op when the script has no metadata block and ``meta``
        is empty. Validates:

        - Structural shape of the metadata (correct types for all fields)
        - Each dependency is a valid PEP 508 specifier (name, extras, version
          operators, environment markers)
        - ``requires-python`` is a valid PEP 440 version specifier

        Raises:
            MetadataValidationError: If the metadata fails structural validation.
        """
        if not self.has_metadata and self.meta.is_empty:
            return
        validate_metadata(self.meta, path=self.path)

    def collect_diagnostics(self, *, strict: bool | None = None) -> list[Diagnostic]:
        """Collect metadata diagnostics without raising exceptions.

        Args:
            strict: Validation mode override. Defaults to the script's configured
                ``strict`` setting.
        """

        should_validate = self.strict if strict is None else strict
        if not should_validate:
            return []
        if not self.has_metadata and self.meta.is_empty:
            return []
        return collect_validation_diagnostics(self.meta, path=self.path)

    def check(self, *, strict: bool | None = None) -> bool:
        """Return ``True`` when the current metadata validates cleanly."""

        return not self.collect_diagnostics(strict=strict)

    def reload(self) -> None:
        """Discard all in-memory edits and reload state from disk (or re-parse source).

        For file-backed scripts (``self.path`` is set), the source is re-read from
        disk, ``self.file`` is refreshed, and metadata is re-parsed.  For in-memory
        scripts created via ``from_source``, ``self.source`` is re-parsed without
        any I/O.
        """
        if self.path is None:
            self._parse_current_source()
            return

        self.source = read_source(self.path, encoding=self.encoding)
        self.file = build_file_info(self.path, encoding=self.encoding)
        self._parse_current_source()

    def to_source(self) -> str:
        """Serialize current state to source text without writing to disk."""
        return rewrite_source(
            self.source, meta=self._meta_to_write(), block=self._block
        )

    def save(self) -> None:
        """Persist the current state to disk, then reload.

        The metadata block is deterministically regenerated (keys sorted,
        consistent formatting) and written back to ``self.path``.  The rest of
        the source is preserved exactly.  After writing, ``reload()`` is called
        so that ``self.source``, ``self.file``, and ``self.meta`` reflect the
        saved file.

        Raises:
            SaveError: If ``self.path`` is ``None`` (in-memory script) or the
                file cannot be written.
        """
        if self.path is None:
            raise SaveError("Cannot save in-memory script without a file path")
        write_source(
            self.path, self._validated_source_for_write(), encoding=self.encoding
        )
        self.reload()

    def save_as(self, path: str | Path) -> None:
        """Write the current state to an arbitrary path, then reload from that path.

        After a successful write, ``self.path`` is updated to *path* and
        ``reload()`` is called so that ``self.source``, ``self.file``, and
        ``self.meta`` reflect the new file location.

        Args:
            path: Destination file path (``str`` or ``Path``).

        Raises:
            SaveError: If the file cannot be written.
        """
        target = Path(path)
        meta_to_write = self._meta_to_write()
        if meta_to_write is not None:
            validate_metadata(meta_to_write, path=target)
        write_source(
            target,
            rewrite_source(self.source, meta=meta_to_write, block=self._block),
            encoding=self.encoding,
        )
        self.path = target
        self.reload()


def parse_script(source: str, *, strict: bool = True) -> PEPScript:
    """Parse source text into an in-memory PEPScript."""

    return PEPScript.from_source(source, strict=strict)


def parse_file(
    path: str | Path, *, encoding: str = "utf-8", strict: bool = True
) -> PEPScript:
    """Parse a file path into a PEPScript."""

    return PEPScript(path, encoding=encoding, strict=strict)

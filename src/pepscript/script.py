"""Public PEPScript document API."""

from __future__ import annotations

from pathlib import Path

from .exceptions import SaveError
from .io import build_file_info, read_source, write_source
from .models import BlockInfo, PEPMetadata, ScriptFileInfo
from .parser import parse_source
from .serialize import rewrite_source
from .validate import validate_metadata


class PEPScript:
    """A typed document wrapper for PEP 723-enabled scripts."""

    path: Path | None
    encoding: str
    strict: bool
    source: str
    file: ScriptFileInfo | None
    meta: PEPMetadata | None
    _block: BlockInfo | None

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
        self.meta = None
        self._block = None
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
        instance.meta = None
        instance._block = None
        instance._parse_current_source()
        return instance

    def __enter__(self) -> PEPScript:
        """Enter the context manager, returning ``self``.

        Note:
            The context manager does **not** auto-save on exit. Call ``save()``
            explicitly before leaving the ``with`` block if you want to persist changes.
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit the context manager without any automatic persistence."""
        return None

    def _parse_current_source(self) -> None:
        parsed = parse_source(self.source, strict=self.strict, path=self.path)
        self.meta = parsed.meta
        self._block = parsed.block

    def ensure_meta(self) -> PEPMetadata:
        """Return the existing metadata block, or create an empty one if absent.

        When ``script.meta`` is ``None`` (script has no ``# /// script`` block),
        this method creates a new ``PEPMetadata()`` and assigns it to ``script.meta``.
        The block is not written to disk until ``save()`` is called.

        Returns:
            The existing or newly created ``PEPMetadata`` instance.
        """
        if self.meta is None:
            self.meta = PEPMetadata()
        return self.meta

    def validate(self) -> None:
        """Run structural validation against the current metadata.

        This is a no-op when ``script.meta`` is ``None``. Validates:

        - Structural shape of the metadata (correct types for all fields)
        - Each dependency is a valid PEP 508 specifier (name, extras, version
          operators, environment markers)
        - ``requires-python`` is a valid PEP 440 version specifier

        Raises:
            MetadataValidationError: If the metadata fails structural validation.
        """
        validate_metadata(self.meta, path=self.path)

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
        return rewrite_source(self.source, meta=self.meta, block=self._block)

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
        write_source(self.path, self.to_source(), encoding=self.encoding)
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
        write_source(target, self.to_source(), encoding=self.encoding)
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

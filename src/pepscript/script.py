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
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def _parse_current_source(self) -> None:
        parsed = parse_source(self.source, strict=self.strict, path=self.path)
        self.meta = parsed.meta
        self._block = parsed.block

    def ensure_meta(self) -> PEPMetadata:
        if self.meta is None:
            self.meta = PEPMetadata()
        return self.meta

    def validate(self) -> None:
        validate_metadata(self.meta, path=self.path)

    def reload(self) -> None:
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
        if self.path is None:
            raise SaveError("Cannot save in-memory script without a file path")
        write_source(self.path, self.to_source(), encoding=self.encoding)
        self.reload()

    def save_as(self, path: str | Path) -> None:
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

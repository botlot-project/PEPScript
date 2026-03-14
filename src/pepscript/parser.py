"""PEP 723 metadata block detection and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any, cast

from .config import ToolConfig
from .exceptions import DuplicateMetadataBlockError, MetadataParseError
from .models import BlockInfo, PEPConfigRoot, PEPMetadata
from .validate import validate_metadata


@dataclass(slots=True)
class ParseResult:
    """Parsed metadata and optional block offsets."""

    meta: PEPMetadata | None
    block: BlockInfo | None


def _is_start_marker(line: str) -> bool:
    return line.strip() == "# /// script"


def _is_end_marker(line: str) -> bool:
    return line.strip() == "# ///"


def _raise_parse_error(message: str, *, path: Path | None = None) -> None:
    if path is None:
        raise MetadataParseError(message)
    raise MetadataParseError(f"{message} (path={path})")


def _find_blocks(source: str, *, path: Path | None = None) -> list[BlockInfo]:
    lines = source.splitlines(keepends=True)
    offsets: list[int] = []
    total = 0
    for line in lines:
        offsets.append(total)
        total += len(line)
    offsets.append(total)

    blocks: list[BlockInfo] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not _is_start_marker(line):
            index += 1
            continue

        end_index = index + 1
        while end_index < len(lines) and not _is_end_marker(lines[end_index]):
            end_index += 1
        if end_index >= len(lines):
            _raise_parse_error(
                "Metadata block start marker without end marker", path=path
            )

        block = BlockInfo(
            start=offsets[index],
            end=offsets[end_index + 1],
            content_start=offsets[index + 1],
            content_end=offsets[end_index],
            block_type="script",
        )
        blocks.append(block)
        index = end_index + 1

    return blocks


def _extract_toml_content(
    source: str, block: BlockInfo, *, path: Path | None = None
) -> str:
    raw = source[block.content_start : block.content_end]
    lines = raw.splitlines(keepends=True)
    content_lines: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if line.strip() == "":
            _raise_parse_error(
                f"Invalid metadata content line {line_number}: expected comment-prefixed content",
                path=path,
            )

        trimmed = line.lstrip(" \t")
        if not trimmed.startswith("#"):
            _raise_parse_error(
                f"Invalid metadata content line {line_number}: expected '#'",
                path=path,
            )
        text = trimmed[1:]
        if text.startswith(" "):
            text = text[1:]
        content_lines.append(text)
    return "".join(content_lines)


def _parse_metadata_table(
    table: dict[str, Any], *, path: Path | None = None
) -> PEPMetadata:
    dependencies: list[str] = []
    if "dependencies" in table:
        value = table["dependencies"]
        if not isinstance(value, list):
            _raise_parse_error("'dependencies' must be a list", path=path)
        for item in cast(list[Any], value):
            if not isinstance(item, str):
                _raise_parse_error("'dependencies' entries must be strings", path=path)
            dependencies.append(item)

    requires_python: str | None = None
    if "requires-python" in table:
        value = table["requires-python"]
        if not isinstance(value, str):
            _raise_parse_error("'requires-python' must be a string", path=path)
        requires_python = cast(str, value)

    tool_node = ToolConfig()
    if "tool" in table:
        tool = table["tool"]
        if not isinstance(tool, dict):
            _raise_parse_error("'tool' must be a table/object", path=path)
        tool_node = ToolConfig.from_dict(cast(dict[str, Any], tool))

    return PEPMetadata(
        dependencies=dependencies,
        requires_python=requires_python,
        config=PEPConfigRoot(tool=tool_node),
    )


def parse_source(
    source: str, *, strict: bool = True, path: Path | None = None
) -> ParseResult:
    """Parse PEP 723 metadata from source text."""

    blocks = _find_blocks(source, path=path)
    if len(blocks) > 1:
        if path is None:
            raise DuplicateMetadataBlockError("Multiple PEP 723 metadata blocks found")
        raise DuplicateMetadataBlockError(
            f"Multiple PEP 723 metadata blocks found (path={path})"
        )
    if not blocks:
        return ParseResult(meta=None, block=None)

    block = blocks[0]
    content = _extract_toml_content(source, block, path=path)
    try:
        parsed = tomllib.loads(content)
    except tomllib.TOMLDecodeError as error:
        _raise_parse_error(f"Invalid metadata TOML: {error}", path=path)
        raise  # pragma: no cover  # unreachable; helps type checkers see parsed is bound

    if not isinstance(parsed, dict):
        _raise_parse_error(
            "Metadata TOML must parse into a table", path=path
        )  # pragma: no cover

    meta = _parse_metadata_table(parsed, path=path)
    if strict:
        validate_metadata(meta, path=path)
        return ParseResult(meta=meta, block=block)
    return ParseResult(meta=meta, block=block)

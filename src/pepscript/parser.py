"""PEP 723 metadata block detection and parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from typing import Any, NoReturn, cast

from .config import ToolConfig
from .diagnostics import (
    Diagnostic,
    PARSE_DUPLICATE_BLOCK,
    PARSE_INDENTED_MARKER,
    PARSE_INVALID_CONTENT_LINE,
    PARSE_INVALID_METADATA_TYPE,
    PARSE_INVALID_TOML,
    PARSE_UNCLOSED_BLOCK,
)
from .exceptions import DuplicateMetadataBlockError, MetadataParseError
from .models import BlockInfo, ConfigRoot, Metadata
from .validate import validate_metadata


@dataclass(slots=True)
class ParseResult:
    """Parsed metadata and optional block offsets."""

    meta: Metadata | None
    block: BlockInfo | None


@dataclass(slots=True, frozen=True)
class _TomlLineMap:
    source_line: int
    source_column: int


def _is_start_marker(line: str) -> bool:
    return line.rstrip("\r\n") == "# /// script"


def _is_end_marker(line: str) -> bool:
    return line.rstrip("\r\n") == "# ///"


def _is_indented_marker(line: str) -> bool:
    return line[:1] in {" ", "\t"} and line.lstrip(" \t").rstrip("\r\n") in {
        "# /// script",
        "# ///",
    }


def _format_error_message(message: str, *, path: Path | None = None) -> str:
    if path is None:
        return message
    return f"{message} (path={path})"


def _raise_parse_error(
    message: str,
    *,
    code: str,
    path: Path | None = None,
    line: int | None = None,
    column: int | None = None,
    field: str | None = None,
) -> NoReturn:
    diagnostic = Diagnostic(
        code=code,
        message=message,
        path=path,
        line=line,
        column=column,
        field=field,
    )
    raise MetadataParseError(
        _format_error_message(message, path=path),
        diagnostic=diagnostic,
    )


def _offset_to_line_col(source: str, offset: int) -> tuple[int, int]:
    line = source.count("\n", 0, offset) + 1
    line_start = source.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


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
        if _is_indented_marker(line):
            indent = len(line) - len(line.lstrip(" \t"))
            _raise_parse_error(
                "Metadata markers must start at the first column",
                code=PARSE_INDENTED_MARKER,
                path=path,
                line=index + 1,
                column=indent + 1,
            )
        if not _is_start_marker(line):
            index += 1
            continue

        end_index = index + 1
        while end_index < len(lines) and not _is_end_marker(lines[end_index]):
            if _is_indented_marker(lines[end_index]):
                indent = len(lines[end_index]) - len(lines[end_index].lstrip(" \t"))
                _raise_parse_error(
                    "Metadata markers must start at the first column",
                    code=PARSE_INDENTED_MARKER,
                    path=path,
                    line=end_index + 1,
                    column=indent + 1,
                )
            end_index += 1
        if end_index >= len(lines):
            _raise_parse_error(
                "Metadata block start marker without end marker",
                code=PARSE_UNCLOSED_BLOCK,
                path=path,
                line=index + 1,
                column=1,
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
) -> tuple[str, list[_TomlLineMap]]:
    raw = source[block.content_start : block.content_end]
    lines = raw.splitlines(keepends=True)
    content_lines: list[str] = []
    line_map: list[_TomlLineMap] = []
    base_line = source.count("\n", 0, block.content_start) + 1

    for line_number, line in enumerate(lines, start=1):
        source_line = base_line + line_number - 1
        if line.strip() == "":
            _raise_parse_error(
                f"Invalid metadata content line {line_number}: expected comment-prefixed content",
                code=PARSE_INVALID_CONTENT_LINE,
                path=path,
                line=source_line,
                column=1,
            )

        if not line.startswith("#"):
            _raise_parse_error(
                f"Invalid metadata content line {line_number}: expected '#' at column 1",
                code=PARSE_INVALID_CONTENT_LINE,
                path=path,
                line=source_line,
                column=1,
            )

        content_column = 2
        text = line[1:]
        if text.startswith(" "):
            text = text[1:]
            content_column = 3

        content_lines.append(text)
        line_map.append(
            _TomlLineMap(source_line=source_line, source_column=content_column)
        )
    return "".join(content_lines), line_map


def _parse_metadata_table(
    table: dict[str, Any], *, path: Path | None = None
) -> Metadata:
    dependencies: list[str] = []
    if "dependencies" in table:
        value = table["dependencies"]
        if not isinstance(value, list):
            _raise_parse_error(
                "'dependencies' must be a list",
                code=PARSE_INVALID_METADATA_TYPE,
                path=path,
                field="dependencies",
            )
        for item in cast(list[Any], value):
            if not isinstance(item, str):
                _raise_parse_error(
                    "'dependencies' entries must be strings",
                    code=PARSE_INVALID_METADATA_TYPE,
                    path=path,
                    field="dependencies",
                )
            dependencies.append(item)

    requires_python: str | None = None
    if "requires-python" in table:
        value = table["requires-python"]
        if not isinstance(value, str):
            _raise_parse_error(
                "'requires-python' must be a string",
                code=PARSE_INVALID_METADATA_TYPE,
                path=path,
                field="requires-python",
            )
        requires_python = cast(str, value)

    tool_node = ToolConfig()
    if "tool" in table:
        tool = table["tool"]
        if not isinstance(tool, dict):
            _raise_parse_error(
                "'tool' must be a table/object",
                code=PARSE_INVALID_METADATA_TYPE,
                path=path,
                field="tool",
            )
        tool_node = ToolConfig.from_dict(cast(dict[str, Any], tool))

    return Metadata(
        dependencies=dependencies,
        requires_python=requires_python,
        config=ConfigRoot(tool=tool_node),
    )


def _toml_error_location(
    error: tomllib.TOMLDecodeError,
    *,
    content: str,
    line_map: list[_TomlLineMap],
) -> tuple[int | None, int | None]:
    lineno = getattr(error, "lineno", None)
    colno = getattr(error, "colno", None)
    if isinstance(lineno, int) and isinstance(colno, int):
        return lineno, colno

    text = str(error)
    match = re.search(r"\(at line (\d+), column (\d+)\)$", text)
    if match is not None:
        return int(match.group(1)), int(match.group(2))

    if "at end of document" in text and line_map:
        lines = content.splitlines()
        last_col = len(lines[-1]) + 1 if lines else 1
        return len(lines) if lines else 1, last_col
    return None, None


def parse_source(
    source: str, *, strict: bool = True, path: Path | None = None
) -> ParseResult:
    """Parse PEP 723 metadata from source text."""

    blocks = _find_blocks(source, path=path)
    if len(blocks) > 1:
        line, column = _offset_to_line_col(source, blocks[1].start)
        diagnostic = Diagnostic(
            code=PARSE_DUPLICATE_BLOCK,
            message="Multiple PEP 723 metadata blocks found",
            path=path,
            line=line,
            column=column,
        )
        raise DuplicateMetadataBlockError(
            _format_error_message("Multiple PEP 723 metadata blocks found", path=path),
            diagnostic=diagnostic,
        )
    if not blocks:
        return ParseResult(meta=None, block=None)

    block = blocks[0]
    content, line_map = _extract_toml_content(source, block, path=path)
    try:
        parsed = tomllib.loads(content)
    except tomllib.TOMLDecodeError as error:
        line = None
        column = None
        toml_line, toml_column = _toml_error_location(
            error, content=content, line_map=line_map
        )
        if (
            toml_line is not None
            and toml_column is not None
            and 1 <= toml_line <= len(line_map)
        ):
            mapped = line_map[toml_line - 1]
            line = mapped.source_line
            column = mapped.source_column + max(toml_column - 1, 0)
        _raise_parse_error(
            f"Invalid metadata TOML: {error}",
            code=PARSE_INVALID_TOML,
            path=path,
            line=line,
            column=column,
        )

    meta = _parse_metadata_table(parsed, path=path)
    if strict:
        validate_metadata(meta, path=path)
    return ParseResult(meta=meta, block=block)

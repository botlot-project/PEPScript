"""Serialization and source rewrite utilities."""

from __future__ import annotations

from collections.abc import Mapping
import json
import re

from .config import ConfigNode
from .models import BlockInfo, PEPMetadata

_BARE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_CODING_RE = re.compile(r"^[ \t]*#.*coding[:=][ \t]*[-_.a-zA-Z0-9]+")


def _format_key(key: str) -> str:
    if _BARE_KEY_RE.match(key):
        return key
    return json.dumps(key)


def _to_plain(value: object) -> object:
    if isinstance(value, ConfigNode):
        return value.to_dict()
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    return value


def _format_value(value: object) -> str:
    value = _to_plain(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if value is None:
        raise TypeError("None is not a TOML scalar value")
    if isinstance(value, list):
        inner = ", ".join(_format_value(item) for item in value)
        return f"[{inner}]"
    raise TypeError(f"Unsupported TOML value type: {type(value).__name__}")


def _emit_table(path: list[str], mapping: Mapping[str, object], lines: list[str]) -> None:
    header = ".".join(_format_key(part) for part in path)
    lines.append(f"[{header}]")

    scalar_keys: list[str] = []
    table_keys: list[str] = []
    for key in sorted(mapping):
        value = _to_plain(mapping[key])
        if isinstance(value, Mapping):
            table_keys.append(key)
        else:
            scalar_keys.append(key)

    for key in scalar_keys:
        value = _to_plain(mapping[key])
        lines.append(f"{_format_key(key)} = {_format_value(value)}")

    for key in table_keys:
        if lines and lines[-1] != "":
            lines.append("")
        child = _to_plain(mapping[key])
        if isinstance(child, Mapping):
            _emit_table([*path, key], child, lines)


def serialize_metadata_toml(meta: PEPMetadata) -> str:
    """Serialize typed metadata into deterministic TOML."""

    lines: list[str] = []
    if meta.dependencies:
        lines.append(f"dependencies = {_format_value(meta.dependencies)}")
    if meta.requires_python is not None:
        lines.append(f"requires-python = {_format_value(meta.requires_python)}")

    tool = _to_plain(meta.config.tool)
    if isinstance(tool, Mapping) and tool:
        if lines:
            lines.append("")
        _emit_table(["tool"], tool, lines)

    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def render_metadata_block(meta: PEPMetadata) -> str:
    """Render a PEP 723 block from metadata."""

    toml = serialize_metadata_toml(meta)
    output: list[str] = ["# /// script\n"]
    for line in toml.splitlines():
        if line:
            output.append(f"# {line}\n")
        else:
            output.append("#\n")
    output.append("# ///\n")
    return "".join(output)


def _insertion_offset(source: str) -> int:
    lines = source.splitlines(keepends=True)
    if not lines:
        return 0
    offset = 0
    index = 0
    if lines and lines[0].startswith("#!"):
        offset += len(lines[0])
        index = 1
    if index < len(lines) and _CODING_RE.match(lines[index]):
        offset += len(lines[index])
    return offset


def rewrite_source(
    source: str,
    *,
    meta: PEPMetadata | None,
    block: BlockInfo | None,
) -> str:
    """Rewrite source with inserted/replaced/removed metadata block."""

    if block is not None:
        if meta is None:
            return source[: block.start] + source[block.end :]
        rendered = render_metadata_block(meta)
        return source[: block.start] + rendered + source[block.end :]

    if meta is None:
        return source

    rendered = render_metadata_block(meta)
    insert_at = _insertion_offset(source)
    before = source[:insert_at]
    after = source[insert_at:]

    spacer = "\n" if after and not after.startswith("\n") else ""
    return before + rendered + spacer + after

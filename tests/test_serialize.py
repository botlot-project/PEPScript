"""Tests for serialization and source rewriting."""

from __future__ import annotations

import pytest

from pepscript import ToolConfig, PEPConfigRoot, PEPMetadata, parse_script
from pepscript.models import BlockInfo
from pepscript.serialize import (
    _format_key,
    _format_value,
    render_metadata_block,
    rewrite_source,
    serialize_metadata_toml,
)


def test_serialize_empty_metadata() -> None:
    meta = PEPMetadata()
    assert serialize_metadata_toml(meta) == ""


def test_serialize_dependencies_only() -> None:
    meta = PEPMetadata(dependencies=["requests>=2.0", "httpx"])
    toml = serialize_metadata_toml(meta)
    assert toml == 'dependencies = ["requests>=2.0", "httpx"]\n'


def test_serialize_requires_python() -> None:
    meta = PEPMetadata(requires_python=">=3.12")
    toml = serialize_metadata_toml(meta)
    assert toml == 'requires-python = ">=3.12"\n'


def test_serialize_with_tool_config() -> None:
    tool = ToolConfig.from_dict({"ruff": {"line-length": 120}})
    meta = PEPMetadata(config=PEPConfigRoot(tool=tool))
    toml = serialize_metadata_toml(meta)
    assert "[tool.ruff]" in toml
    assert "line-length = 120" in toml


def test_serialize_nested_tool_tables() -> None:
    tool = ToolConfig.from_dict(
        {
            "ruff": {"lint": {"select": ["E", "F"]}},
            "mypy": {"strict": True},
        }
    )
    meta = PEPMetadata(dependencies=["ruff"], config=PEPConfigRoot(tool=tool))
    toml = serialize_metadata_toml(meta)
    assert "[tool.mypy]" in toml
    assert "[tool.ruff]" in toml
    assert "[tool.ruff.lint]" in toml
    assert 'select = ["E", "F"]' in toml
    assert "strict = true" in toml


def test_render_metadata_block() -> None:
    meta = PEPMetadata(dependencies=["requests"])
    block = render_metadata_block(meta)
    assert block.startswith("# /// script\n")
    assert block.endswith("# ///\n")
    assert '# dependencies = ["requests"]' in block


def test_rewrite_source_insert_into_empty_file() -> None:
    meta = PEPMetadata(dependencies=["httpx"])
    result = rewrite_source("", meta=meta, block=None)
    assert result.startswith("# /// script\n")
    assert result.endswith("# ///\n")


def test_rewrite_source_insert_after_shebang() -> None:
    source = "#!/usr/bin/env python3\nprint('hello')\n"
    meta = PEPMetadata(dependencies=["httpx"])
    result = rewrite_source(source, meta=meta, block=None)
    assert result.startswith("#!/usr/bin/env python3\n# /// script\n")
    assert "print('hello')" in result


def test_rewrite_source_insert_after_coding_declaration() -> None:
    source = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nprint('hello')\n"
    meta = PEPMetadata(dependencies=["httpx"])
    result = rewrite_source(source, meta=meta, block=None)
    assert result.startswith(
        "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n# /// script\n"
    )
    assert "print('hello')" in result


def test_rewrite_source_replace_existing_block() -> None:
    source = "# /// script\n# dependencies = []\n# ///\nprint('hi')\n"
    block = BlockInfo(
        start=0, end=39, content_start=14, content_end=34, block_type="script"
    )
    meta = PEPMetadata(dependencies=["new-dep"])
    result = rewrite_source(source, meta=meta, block=block)
    assert '# dependencies = ["new-dep"]' in result
    assert "print('hi')" in result


def test_rewrite_source_remove_block() -> None:
    source = "# /// script\n# dependencies = []\n# ///\nprint('hi')\n"
    block = BlockInfo(
        start=0, end=39, content_start=14, content_end=34, block_type="script"
    )
    result = rewrite_source(source, meta=None, block=block)
    assert "# /// script" not in result
    assert "print('hi')" in result


def test_round_trip_preserves_metadata() -> None:
    """Parse -> mutate -> serialize -> re-parse and verify metadata survived."""
    source = """\
# /// script
# dependencies = ["requests>=2.0"]
# requires-python = ">=3.12"
# [tool.ruff]
# line-length = 120
# ///
print("hello")
"""
    script = parse_script(source)
    assert script.meta is not None
    script.meta.add_dependency("httpx>=0.27")
    script.meta.remove_dependency("requests>=2.0")

    new_source = script.to_source()
    script2 = parse_script(new_source)
    assert script2.meta is not None
    assert script2.meta.dependencies == ["httpx>=0.27"]
    assert script2.meta.requires_python == ">=3.12"
    assert script2.meta.config.tool.ruff["line-length"] == 120
    assert 'print("hello")' in new_source


def test_serialize_false_boolean() -> None:
    tool = ToolConfig.from_dict({"mypy": {"strict": False}})
    meta = PEPMetadata(config=PEPConfigRoot(tool=tool))
    toml = serialize_metadata_toml(meta)
    assert "strict = false" in toml


def test_serialize_float_value() -> None:
    tool = ToolConfig.from_dict({"ruff": {"ratio": 1.5}})
    meta = PEPMetadata(config=PEPConfigRoot(tool=tool))
    toml = serialize_metadata_toml(meta)
    assert "ratio = 1.5" in toml


def test_rewrite_source_no_meta_no_block_returns_source() -> None:
    source = 'print("hello")\n'
    assert rewrite_source(source, meta=None, block=None) == source


def test_render_block_has_blank_separator_line() -> None:
    tool = ToolConfig.from_dict({"ruff": {"strict": True}})
    meta = PEPMetadata(dependencies=["httpx"], config=PEPConfigRoot(tool=tool))
    block = render_metadata_block(meta)
    assert "#\n" in block  # blank separator between deps and [tool.*]


def test_round_trip_empty_metadata() -> None:
    """Ensure a plain script with no metadata round-trips without injecting a block."""
    script = parse_script('print("hello")\n')
    new_source = script.to_source()
    script2 = parse_script(new_source)
    assert not script2.has_metadata
    assert script2.meta.is_empty
    assert 'print("hello")' in new_source


def test_format_key_quotes_key_with_special_characters() -> None:
    assert _format_key("my.key") == '"my.key"'
    assert _format_key("has space") == '"has space"'


def test_format_key_returns_bare_key_unchanged() -> None:
    assert _format_key("my-key") == "my-key"
    assert _format_key("my_key") == "my_key"


def test_format_value_none_raises_type_error() -> None:
    with pytest.raises(TypeError, match="None is not a TOML scalar value"):
        _format_value(None)


def test_format_value_unsupported_type_raises_type_error() -> None:
    with pytest.raises(TypeError, match="Unsupported TOML value type"):
        _format_value(object())

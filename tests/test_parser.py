from __future__ import annotations

import pytest

from pepscript import parse_script
from pepscript.diagnostics import PARSE_INVALID_CONTENT_LINE, PARSE_INVALID_TOML
from pepscript.exceptions import DuplicateMetadataBlockError, MetadataParseError


def test_parse_valid_metadata_block() -> None:
    source = """# /// script
# dependencies = ["httpx>=0.27"]
# requires-python = ">=3.12"
# [tool.botlot]
# token_env = "BOTLOT_TOKEN"
# ///
print("hello")
"""
    script = parse_script(source)

    assert script.meta is not None
    assert script.meta.dependencies == ["httpx>=0.27"]
    assert script.meta.requires_python == ">=3.12"
    assert script.meta.config.tool.botlot.token_env == "BOTLOT_TOKEN"


def test_parse_missing_metadata_block() -> None:
    script = parse_script('print("hello")\n')
    assert not script.has_metadata
    assert script.meta.is_empty
    assert script.file is None


def test_parse_malformed_metadata_toml_raises() -> None:
    source = """# /// script
# dependencies = ["httpx"
# ///
print("hello")
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_duplicate_metadata_blocks_raises() -> None:
    source = """# /// script
# dependencies = ["httpx>=0.27"]
# ///
print("hello")
# /// script
# dependencies = ["rich>=13.0"]
# ///
"""
    with pytest.raises(DuplicateMetadataBlockError):
        parse_script(source)


def test_parse_unclosed_block_raises() -> None:
    source = """# /// script
# dependencies = ["httpx"]
print("hello")
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_blank_line_in_block_raises() -> None:
    source = """# /// script
# dependencies = ["httpx"]

# ///
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_non_comment_line_in_block_raises() -> None:
    source = """# /// script
dependencies = ["httpx"]
# ///
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_non_comment_line_has_diagnostic_payload() -> None:
    source = """# /// script
dependencies = ["httpx"]
# ///
"""
    with pytest.raises(MetadataParseError) as captured:
        parse_script(source)
    assert captured.value.diagnostic is not None
    assert captured.value.diagnostic.code == PARSE_INVALID_CONTENT_LINE
    assert captured.value.diagnostic.line == 2
    assert captured.value.diagnostic.column == 1


def test_parse_indented_start_marker_raises() -> None:
    source = """def main():
    # /// script
    # dependencies = ["httpx"]
    # ///
"""
    with pytest.raises(MetadataParseError, match="first column"):
        parse_script(source)


def test_parse_indented_end_marker_raises() -> None:
    source = """# /// script
# dependencies = ["httpx"]
    # ///
"""
    with pytest.raises(MetadataParseError, match="first column"):
        parse_script(source)


def test_parse_indented_content_line_raises() -> None:
    source = """# /// script
    # dependencies = ["httpx"]
# ///
"""
    with pytest.raises(MetadataParseError, match="column 1"):
        parse_script(source)


def test_parse_non_list_dependencies_raises() -> None:
    source = """# /// script
# dependencies = "not-a-list"
# ///
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_non_string_requires_python_raises() -> None:
    source = """# /// script
# requires-python = 312
# ///
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_non_table_tool_raises() -> None:
    source = """# /// script
# tool = "not-a-table"
# ///
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_non_string_dependency_entry_raises() -> None:
    source = """# /// script
# dependencies = [123]
# ///
"""
    with pytest.raises(MetadataParseError):
        parse_script(source)


def test_parse_with_path_includes_path_in_error() -> None:
    from pathlib import Path

    from pepscript.parser import parse_source

    source = """# /// script
# dependencies = ["httpx"
# ///
"""
    with pytest.raises(MetadataParseError, match="path="):
        parse_source(source, path=Path("/tmp/test.py"))


def test_parse_toml_error_has_line_and_column() -> None:
    from pathlib import Path

    from pepscript.parser import parse_source

    source = """# /// script
# dependencies = ["httpx"
# ///
"""
    with pytest.raises(MetadataParseError) as captured:
        parse_source(source, path=Path("/tmp/test.py"))
    assert captured.value.diagnostic is not None
    assert captured.value.diagnostic.code == PARSE_INVALID_TOML
    assert captured.value.diagnostic.line == 2
    assert captured.value.diagnostic.column is not None


def test_duplicate_blocks_with_path_includes_path_in_error() -> None:
    from pathlib import Path

    from pepscript.parser import parse_source

    source = """# /// script
# dependencies = []
# ///
# /// script
# dependencies = []
# ///
"""
    with pytest.raises(DuplicateMetadataBlockError, match="path="):
        parse_source(source, path=Path("/tmp/test.py"))


def test_parse_strict_false_skips_validation() -> None:
    source = """# /// script
# dependencies = ["httpx"]
# ///
"""
    script = parse_script(source, strict=False)
    assert script.meta is not None
    assert script.meta.dependencies == ["httpx"]


def test_toml_error_location_prefers_exception_attributes() -> None:
    from pepscript.parser import _toml_error_location

    class ErrorWithAttrs:
        lineno = 3
        colno = 7

        def __str__(self) -> str:
            return "x"

    line, column = _toml_error_location(
        ErrorWithAttrs(),  # type: ignore[arg-type]
        content="a = 1\n",
        line_map=[],
    )
    assert (line, column) == (3, 7)


def test_toml_error_location_parses_message_and_fallback() -> None:
    from pepscript.parser import _toml_error_location

    class ErrorWithMessage:
        def __str__(self) -> str:
            return "Invalid value (at line 4, column 9)"

    line, column = _toml_error_location(
        ErrorWithMessage(),  # type: ignore[arg-type]
        content="a = 1\n",
        line_map=[],
    )
    assert (line, column) == (4, 9)

    class UnknownError:
        def __str__(self) -> str:
            return "Invalid value"

    unknown_line, unknown_column = _toml_error_location(
        UnknownError(),  # type: ignore[arg-type]
        content="a = 1\n",
        line_map=[],
    )
    assert unknown_line is None
    assert unknown_column is None

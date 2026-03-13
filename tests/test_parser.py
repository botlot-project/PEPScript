from __future__ import annotations

import pytest

from pepscript import parse_script
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
    assert script.meta is None
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

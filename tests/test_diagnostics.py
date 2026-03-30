from __future__ import annotations

from pathlib import Path

import pytest

from pepscript import Diagnostic
from pepscript.diagnostics import (
    PARSE_DUPLICATE_BLOCK,
    PARSE_INVALID_TOML,
    VALIDATION_DEPENDENCY_ENTRY_TYPE,
    VALIDATION_DEPENDENCY_SPEC,
)
from pepscript.exceptions import (
    DuplicateMetadataBlockError,
    MetadataParseError,
    MetadataValidationError,
)
from pepscript.parser import parse_source
from pepscript.validate import collect_validation_diagnostics, validate_metadata


def test_diagnostic_dataclass_fields() -> None:
    diagnostic = Diagnostic(
        code="PSX999",
        message="something happened",
        path=Path("/tmp/demo.py"),
        line=5,
        column=3,
        field="dependencies[0]",
    )
    assert diagnostic.code == "PSX999"
    assert diagnostic.line == 5
    assert diagnostic.column == 3
    assert diagnostic.field == "dependencies[0]"


def test_parse_error_contains_structured_diagnostic() -> None:
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
    assert captured.value.diagnostic.path == Path("/tmp/test.py")


def test_duplicate_block_error_contains_structured_diagnostic() -> None:
    source = """# /// script
# dependencies = []
# ///
# /// script
# dependencies = []
# ///
"""
    with pytest.raises(DuplicateMetadataBlockError) as captured:
        parse_source(source)

    assert captured.value.diagnostic is not None
    assert captured.value.diagnostic.code == PARSE_DUPLICATE_BLOCK
    assert captured.value.diagnostic.line == 4


def test_collect_validation_diagnostics_collects_multiple_issues() -> None:
    from pepscript import Metadata

    diagnostics = collect_validation_diagnostics(
        Metadata(dependencies=[123, "requests>>2.0"])  # type: ignore[list-item]
    )
    codes = {diag.code for diag in diagnostics}
    assert VALIDATION_DEPENDENCY_ENTRY_TYPE in codes
    assert VALIDATION_DEPENDENCY_SPEC in codes


def test_validate_metadata_error_carries_diagnostics() -> None:
    from pepscript import Metadata

    meta = Metadata(dependencies=[123, "requests>>2.0"])  # type: ignore[list-item]
    with pytest.raises(MetadataValidationError) as captured:
        validate_metadata(meta)

    error = captured.value
    assert hasattr(error, "diagnostics")
    assert len(error.diagnostics) >= 2

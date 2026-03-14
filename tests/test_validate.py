from __future__ import annotations

import pytest

from pepscript import ConfigNode, PEPConfigRoot, PEPMetadata
from pepscript.exceptions import MetadataValidationError
from pepscript.validate import validate_metadata


def test_validate_rejects_non_string_dependencies() -> None:
    meta = PEPMetadata(dependencies=["httpx>=0.27", 123])  # type: ignore[list-item]
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_rejects_non_string_requires_python() -> None:
    meta = PEPMetadata(requires_python=123)  # type: ignore[arg-type]
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_rejects_non_mapping_like_tool_values() -> None:
    meta = PEPMetadata(
        config=PEPConfigRoot(
            tool=ConfigNode.from_dict(
                {
                    "botlot": object(),
                }
            )
        )
    )
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_none_metadata_is_noop() -> None:
    validate_metadata(None)


def test_validate_with_path_includes_path_in_error() -> None:
    from pathlib import Path

    meta = PEPMetadata(dependencies=["httpx", 123])  # type: ignore[list-item]
    with pytest.raises(MetadataValidationError, match="path="):
        validate_metadata(meta, path=Path("/tmp/test.py"))


def test_validate_nested_tool_list_with_bad_entry() -> None:
    meta = PEPMetadata(
        config=PEPConfigRoot(
            tool=ConfigNode.from_dict({"ruff": {"select": [object()]}})
        )
    )
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_non_string_tool_key() -> None:
    meta = PEPMetadata(
        config=PEPConfigRoot(
            tool=ConfigNode(_data={123: "value"})  # type: ignore[dict-item]
        )
    )
    with pytest.raises(MetadataValidationError, match="keys must be strings"):
        validate_metadata(meta)


def test_validate_accepts_valid_metadata() -> None:
    meta = PEPMetadata(
        dependencies=["httpx>=0.27"],
        requires_python=">=3.12",
        config=PEPConfigRoot(
            tool=ConfigNode.from_dict(
                {"ruff": {"line-length": 120, "enabled": True, "ratio": 0.5}}
            )
        ),
    )
    validate_metadata(meta)

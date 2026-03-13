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

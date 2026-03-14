from __future__ import annotations

import pytest

from pepscript import ConfigNode, PEPConfigRoot, PEPMetadata
from pepscript.exceptions import MetadataValidationError
from pepscript.validate import validate_metadata, _validate_pep508_dependency, _validate_requires_python


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


# ---------------------------------------------------------------------------
# PEP 508 dependency specifier validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dep",
    [
        "requests",
        "requests>=2.0",
        "requests>=2.0,<3.0",
        "requests==2.31.*",
        "requests~=2.31",
        "requests!=2.0",
        "requests[security]",
        "requests[security]>=2.0",
        "requests[security,socks]>=2.0,<3.0",
        "My-Package>=1.0",
        "my_package>=1.0",
        "zope.interface>=5.0",
        "A",  # single-character name
        "requests>=2.0; python_version >= '3.8'",
        "requests>=2.0; python_version >= '3.8' and sys_platform == 'linux'",
        "requests; extra == 'security'",
        "requests @ https://example.com/requests.tar.gz",
        "requests[security] @ https://example.com/requests.tar.gz",
        # deprecated marker variables must not be rejected
        "requests; os.name == 'nt'",
        "requests; sys.platform == 'win32'",
    ],
)
def test_pep508_valid(dep: str) -> None:
    _validate_pep508_dependency(dep)


@pytest.mark.parametrize(
    "dep",
    [
        "",                             # empty string
        "@invalid",                     # no name
        "invalid-",                     # name ends with hyphen
        "-invalid",                     # name starts with hyphen
        "requests[unclosed>=1.0",       # unclosed extras bracket
        "requests[inv@lid]",            # invalid extra name
        "requests>>2.0",                # invalid version operator
        "requests>=",                   # operator with no version
        "requests; badvar >= '3'",      # unknown marker variable
        "requests; python_vers >= '3'", # typo in marker variable
    ],
)
def test_pep508_invalid(dep: str) -> None:
    with pytest.raises(MetadataValidationError):
        _validate_pep508_dependency(dep)


def test_pep508_error_includes_index() -> None:
    with pytest.raises(MetadataValidationError, match=r"dependencies\[2\]"):
        _validate_pep508_dependency("requests>>2.0", index=2)


def test_pep508_error_includes_path() -> None:
    from pathlib import Path

    with pytest.raises(MetadataValidationError, match="path="):
        _validate_pep508_dependency("@bad", path=Path("/tmp/s.py"))


# ---------------------------------------------------------------------------
# PEP 440 requires-python specifier validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spec",
    [
        ">=3.12",
        ">=3.12,<4",
        "==3.12.*",
        "~=3.12",
        "!=3.11",
        ">=3.10,!=3.11,<4",
    ],
)
def test_requires_python_valid(spec: str) -> None:
    _validate_requires_python(spec)


@pytest.mark.parametrize(
    "spec",
    [
        "3.12",         # no operator
        ">>3.12",       # invalid operator
        ">=3.12,3.13",  # second clause missing operator
        "",             # empty
    ],
)
def test_requires_python_invalid(spec: str) -> None:
    with pytest.raises(MetadataValidationError):
        _validate_requires_python(spec)


# ---------------------------------------------------------------------------
# Integration: validate_metadata enforces PEP 508 / 440
# ---------------------------------------------------------------------------


def test_validate_metadata_rejects_invalid_dep_specifier() -> None:
    meta = PEPMetadata(dependencies=["requests>>2.0"])
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_metadata_rejects_invalid_requires_python() -> None:
    meta = PEPMetadata(requires_python="3.12")  # missing operator
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)

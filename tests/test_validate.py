from __future__ import annotations

from datetime import date, datetime, time, timezone

import pytest

from pepscript import ToolConfig, ConfigRoot, Metadata
from pepscript.diagnostics import (
    VALIDATION_DEPENDENCY_ENTRY_TYPE,
    VALIDATION_DEPENDENCY_SPEC,
    VALIDATION_REQUIRES_PYTHON_SPEC,
    VALIDATION_TOOL_VALUE_TYPE,
)
from pepscript.exceptions import MetadataValidationError
from pepscript.validate import (
    collect_validation_diagnostics,
    validate_metadata,
    _validate_pep508_dependency,
    _validate_requires_python,
)


def test_validate_rejects_non_string_dependencies() -> None:
    meta = Metadata(dependencies=["httpx>=0.27", 123])  # type: ignore[list-item]
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_collect_validation_diagnostics_returns_codes() -> None:
    meta = Metadata(dependencies=[123, "requests>>2.0"])  # type: ignore[list-item]
    diagnostics = collect_validation_diagnostics(meta)
    codes = {diag.code for diag in diagnostics}
    assert VALIDATION_DEPENDENCY_ENTRY_TYPE in codes
    assert VALIDATION_DEPENDENCY_SPEC in codes


def test_validate_rejects_non_string_requires_python() -> None:
    meta = Metadata(requires_python=123)  # type: ignore[arg-type]
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_rejects_non_mapping_like_tool_values() -> None:
    meta = Metadata(
        config=ConfigRoot(
            tool=ToolConfig.from_dict(
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

    meta = Metadata(dependencies=["httpx", 123])  # type: ignore[list-item]
    with pytest.raises(MetadataValidationError, match="path="):
        validate_metadata(meta, path=Path("/tmp/test.py"))


def test_validate_nested_tool_list_with_bad_entry() -> None:
    meta = Metadata(
        config=ConfigRoot(tool=ToolConfig.from_dict({"ruff": {"select": [object()]}}))
    )
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_non_string_tool_key() -> None:
    meta = Metadata(
        config=ConfigRoot(
            tool=ToolConfig(_data={123: "value"})  # type: ignore[dict-item]
        )
    )
    with pytest.raises(MetadataValidationError, match="keys must be strings"):
        validate_metadata(meta)


def test_validate_accepts_valid_metadata() -> None:
    meta = Metadata(
        dependencies=["httpx>=0.27"],
        requires_python=">=3.12",
        config=ConfigRoot(
            tool=ToolConfig.from_dict(
                {"ruff": {"line-length": 120, "enabled": True, "ratio": 0.5}}
            )
        ),
    )
    validate_metadata(meta)


def test_validate_accepts_toml_temporal_tool_values() -> None:
    meta = Metadata(
        config=ConfigRoot(
            tool=ToolConfig.from_dict(
                {
                    "demo": {
                        "released": datetime(2026, 3, 25, 12, 30, tzinfo=timezone.utc),
                        "day": date(2026, 3, 25),
                        "clock": time(12, 30, 15),
                    }
                }
            )
        )
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
        "requests (>=2.0,<3.0)",
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
        "requests>=2.0; (python_version >= '3.8' and sys_platform == 'linux') or extra == 'test'",
        "requests; extra == 'security'",
        "requests; 'linux' == sys_platform",
        "requests; os_name not in 'nt'",
        "requests @ https://example.com/requests.tar.gz",
        "requests @ file:///tmp/requests.whl",
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
        "",  # empty string
        "@invalid",  # no name
        "invalid-",  # name ends with hyphen
        "-invalid",  # name starts with hyphen
        "requests[unclosed>=1.0",  # unclosed extras bracket
        "requests[,security]",  # empty extra
        "requests[security,]",  # trailing empty extra
        "requests[inv@lid]",  # invalid extra name
        "requests>>2.0",  # invalid version operator
        "requests>=",  # operator with no version
        "requests(>=1.0",  # unclosed version parentheses
        "requests; badvar >= '3'",  # unknown marker variable
        "requests; python_vers >= '3'",  # typo in marker variable
        "requests; python_version",  # missing marker operator + rhs
        "requests; python_version >",  # missing marker rhs
        "requests; python_version >< '3.8'",  # invalid marker operator
        "requests; (python_version >= '3.8'",  # unclosed marker parenthesis
        "requests; python_version >= 3.8",  # rhs must be quoted or variable
        "requests; extra in",  # missing rhs after `in`
        "requests[extra]garbage @ https://example.com/r.tar.gz",  # trailing garbage before @
        "requests @",  # empty direct reference
        "requests @ not-a-url",  # missing URL scheme
        "requests @ https://example.com/pkg.whl [oops]",  # invalid trailing whitespace/garbage
    ],
)
def test_pep508_invalid(dep: str) -> None:
    with pytest.raises(MetadataValidationError):
        _validate_pep508_dependency(dep)


def test_pep508_marker_with_extra_tokens_raises() -> None:
    with pytest.raises(MetadataValidationError, match="invalid marker syntax"):
        _validate_pep508_dependency("requests; python_version >= '3.8' extra")


def test_pep508_marker_trailing_operator_raises() -> None:
    with pytest.raises(MetadataValidationError, match="invalid marker syntax"):
        _validate_pep508_dependency("requests; python_version >= '3.8' and")


def test_pep508_error_includes_index() -> None:
    with pytest.raises(MetadataValidationError, match=r"dependencies\[2\]"):
        _validate_pep508_dependency("requests>>2.0", index=2)


def test_pep508_error_includes_path() -> None:
    from pathlib import Path

    with pytest.raises(MetadataValidationError, match="path="):
        _validate_pep508_dependency("@bad", path=Path("/tmp/s.py"))


def test_collect_validation_diagnostics_handles_plain_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pepscript.validate as validate_module

    def _raise_plain_error(*args, **kwargs) -> None:
        raise MetadataValidationError("plain dependency failure")

    monkeypatch.setattr(
        validate_module, "_validate_pep508_dependency", _raise_plain_error
    )
    diagnostics = collect_validation_diagnostics(Metadata(dependencies=["httpx"]))
    assert diagnostics
    assert diagnostics[0].code == VALIDATION_DEPENDENCY_SPEC


def test_collect_validation_diagnostics_handles_plain_requires_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pepscript.validate as validate_module

    def _raise_plain_error(*args, **kwargs) -> None:
        raise MetadataValidationError("plain requires-python failure")

    monkeypatch.setattr(
        validate_module, "_validate_requires_python", _raise_plain_error
    )
    diagnostics = collect_validation_diagnostics(Metadata(requires_python=">=3.12"))
    assert diagnostics
    assert diagnostics[0].code == VALIDATION_REQUIRES_PYTHON_SPEC


def test_collect_validation_diagnostics_handles_plain_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pepscript.validate as validate_module

    def _raise_plain_error(*args, **kwargs) -> None:
        raise MetadataValidationError("plain tool failure")

    monkeypatch.setattr(validate_module, "_validate_tool_value", _raise_plain_error)
    diagnostics = collect_validation_diagnostics(Metadata())
    assert diagnostics
    assert diagnostics[0].code == VALIDATION_TOOL_VALUE_TYPE


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
        "3.12",  # no operator
        ">>3.12",  # invalid operator
        ">=3.12,3.13",  # second clause missing operator
        "",  # empty
    ],
)
def test_requires_python_invalid(spec: str) -> None:
    with pytest.raises(MetadataValidationError):
        _validate_requires_python(spec)


# ---------------------------------------------------------------------------
# Integration: validate_metadata enforces PEP 508 / 440
# ---------------------------------------------------------------------------


def test_validate_metadata_rejects_invalid_dep_specifier() -> None:
    meta = Metadata(dependencies=["requests>>2.0"])
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_metadata_rejects_invalid_requires_python() -> None:
    meta = Metadata(requires_python="3.12")  # missing operator
    with pytest.raises(MetadataValidationError):
        validate_metadata(meta)


def test_validate_tool_list_values() -> None:
    meta = Metadata(
        config=ConfigRoot(tool=ToolConfig.from_dict({"ruff": {"select": ["E", "F"]}}))
    )
    validate_metadata(meta)  # should not raise


def test_validate_rejects_non_list_dependencies() -> None:
    meta = Metadata(dependencies="not-a-list")  # type: ignore[arg-type]
    with pytest.raises(MetadataValidationError, match="'dependencies' must be a list"):
        validate_metadata(meta)


def test_pep508_invalid_extra_name_raises() -> None:
    # "bad!extra" contains "!" which is not a valid extra name character
    with pytest.raises(MetadataValidationError, match="invalid extra"):
        _validate_pep508_dependency("requests[bad!extra]")

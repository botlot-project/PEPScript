from __future__ import annotations

import pytest

from pepscript import ToolConfig, ConfigRoot, Metadata
from pepscript.models import canonicalize_dependency_name, extract_dependency_name


def test_config_node_attribute_and_item_access_roundtrip() -> None:
    node = ToolConfig.from_dict(
        {
            "botlot": {
                "some_setting": "value",
                "enabled": True,
            },
            "my-tool": {"some-setting": 1},
        }
    )

    assert node.botlot.some_setting == "value"
    assert node.botlot["some_setting"] == "value"
    assert node["my-tool"]["some-setting"] == 1
    assert node.to_dict() == {
        "botlot": {"some_setting": "value", "enabled": True},
        "my-tool": {"some-setting": 1},
    }


def test_metadata_dependency_helpers_are_idempotent() -> None:
    meta = Metadata()
    meta.add_dependency("httpx>=0.27")
    meta.add_dependency("httpx>=0.27")
    meta.add_dependency("rich>=13.0")
    meta.remove_dependency("does-not-exist")
    meta.remove_dependency("rich>=13.0")
    meta.set_requires_python(">=3.12")

    assert meta.dependencies == ["httpx>=0.27"]
    assert meta.requires_python == ">=3.12"


def test_dependency_name_based_helpers() -> None:
    meta = Metadata(dependencies=["Requests>=2.31", "rich>=13", "requests[socks]>=2.0"])

    assert meta.has_dependency("requests")
    assert meta.has_dependency("requests>=2.0", match="name")
    assert meta.has_dependency("rich>=13", match="exact")
    assert not meta.has_dependency("rich >= 13", match="exact")
    assert meta.get_dependency_by_name("requests") == "Requests>=2.31"


def test_replace_dependency_by_name_replaces_first_and_dedupes() -> None:
    meta = Metadata(dependencies=["requests>=2.0", "rich>=13", "requests[socks]>=2.0"])

    changed = meta.replace_dependency_by_name("requests>=2.32")

    assert changed
    assert meta.dependencies == ["requests>=2.32", "rich>=13"]


def test_replace_dependency_by_name_add_if_missing_false() -> None:
    meta = Metadata(dependencies=["httpx>=0.27"])

    changed = meta.replace_dependency_by_name("rich>=13", add_if_missing=False)

    assert not changed
    assert meta.dependencies == ["httpx>=0.27"]


def test_replace_dependency_by_name_adds_when_missing_by_default() -> None:
    meta = Metadata(dependencies=["httpx>=0.27"])

    changed = meta.replace_dependency_by_name("rich>=13")

    assert changed
    assert meta.dependencies == ["httpx>=0.27", "rich>=13"]


def test_remove_dependency_by_name_all_or_first() -> None:
    meta = Metadata(dependencies=["requests>=2.0", "rich>=13", "requests[socks]>=2.0"])

    removed_first = meta.remove_dependency_by_name("requests", all_matches=False)
    assert removed_first == ["requests>=2.0"]
    assert meta.dependencies == ["rich>=13", "requests[socks]>=2.0"]

    removed_rest = meta.remove_dependency_by_name("requests")
    assert removed_rest == ["requests[socks]>=2.0"]
    assert meta.dependencies == ["rich>=13"]


def test_replace_dependency_by_name_rejects_invalid_dependency() -> None:
    meta = Metadata()
    with pytest.raises(ValueError):
        meta.replace_dependency_by_name("@bad")


def test_name_based_queries_handle_invalid_queries() -> None:
    meta = Metadata(dependencies=["httpx>=0.27"])

    assert not meta.has_dependency("@bad")
    assert meta.get_dependency_by_name("@bad") is None
    assert meta.remove_dependency_by_name("@bad") == []


def test_name_helpers_return_none_for_empty_or_missing() -> None:
    assert extract_dependency_name("   ") is None
    assert canonicalize_dependency_name("My_Package.Name") == "my-package-name"
    assert Metadata(dependencies=["httpx"]).get_dependency_by_name("rich") is None


def test_is_empty_default() -> None:
    assert Metadata().is_empty


def test_is_empty_with_only_requires_python() -> None:
    meta = Metadata(requires_python=">=3.12")
    assert not meta.is_empty


def test_is_empty_with_only_dependencies() -> None:
    meta = Metadata(dependencies=["httpx"])
    assert not meta.is_empty


def test_is_empty_with_only_tool_config() -> None:
    tool = ToolConfig.from_dict({"ruff": {"line-length": 120}})
    meta = Metadata(config=ConfigRoot(tool=tool))
    assert not meta.is_empty


def test_is_empty_with_only_empty_nested_tool_config() -> None:
    tool = ToolConfig.from_dict({"ruff": {}})
    meta = Metadata(config=ConfigRoot(tool=tool))
    assert meta.is_empty

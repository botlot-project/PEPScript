from __future__ import annotations

from pepscript import ConfigNode, PEPMetadata


def test_config_node_attribute_and_item_access_roundtrip() -> None:
    node = ConfigNode.from_dict(
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
    meta = PEPMetadata()
    meta.add_dependency("httpx>=0.27")
    meta.add_dependency("httpx>=0.27")
    meta.add_dependency("rich>=13.0")
    meta.remove_dependency("does-not-exist")
    meta.remove_dependency("rich>=13.0")
    meta.set_requires_python(">=3.12")

    assert meta.dependencies == ["httpx>=0.27"]
    assert meta.requires_python == ">=3.12"

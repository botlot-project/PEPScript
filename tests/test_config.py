"""Tests for ConfigNode dict-like API."""

from __future__ import annotations

import pytest

from pepscript import ConfigNode


def test_get_existing_key() -> None:
    node = ConfigNode.from_dict({"a": 1})
    assert node.get("a") == 1


def test_get_missing_key_returns_default() -> None:
    node = ConfigNode()
    assert node.get("missing") is None
    assert node.get("missing", 42) == 42


def test_setdefault_missing_key() -> None:
    node = ConfigNode()
    result = node.setdefault("key", {"nested": True})
    assert isinstance(result, ConfigNode)
    assert node["key"].to_dict() == {"nested": True}


def test_setdefault_existing_key_does_not_overwrite() -> None:
    node = ConfigNode.from_dict({"key": 1})
    result = node.setdefault("key", 99)
    assert result == 1


def test_update_from_mapping() -> None:
    node = ConfigNode()
    node.update({"a": 1, "b": {"nested": True}})
    assert node["a"] == 1
    assert isinstance(node["b"], ConfigNode)


def test_update_from_iterable() -> None:
    node = ConfigNode()
    node.update([("x", 10), ("y", 20)])
    assert node["x"] == 10
    assert node["y"] == 20


def test_update_with_kwargs() -> None:
    node = ConfigNode()
    node.update(a=1, b=2)
    assert node["a"] == 1
    assert node["b"] == 2


def test_setattr_wraps_dicts() -> None:
    node = ConfigNode()
    node.ruff = {"line-length": 120}
    assert isinstance(node.ruff, ConfigNode)
    assert node.ruff["line-length"] == 120


def test_setitem_wraps_dicts() -> None:
    node = ConfigNode()
    node["ruff"] = {"line-length": 80}
    assert isinstance(node["ruff"], ConfigNode)


def test_delitem() -> None:
    node = ConfigNode.from_dict({"a": 1, "b": 2})
    del node["a"]
    assert "a" not in node.to_dict()
    with pytest.raises(KeyError):
        del node["nonexistent"]


def test_iter_and_len() -> None:
    node = ConfigNode.from_dict({"a": 1, "b": 2, "c": 3})
    assert len(node) == 3
    assert sorted(node) == ["a", "b", "c"]


def test_getattr_missing_raises_attribute_error() -> None:
    node = ConfigNode()
    with pytest.raises(AttributeError):
        _ = node.nonexistent

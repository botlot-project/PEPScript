"""Dynamic configuration node for nested tool configuration."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any


def _wrap_value(value: object) -> object:
    if isinstance(value, ConfigNode):
        return value
    if isinstance(value, Mapping):
        return ConfigNode.from_dict(dict(value))
    if isinstance(value, list):
        return [_wrap_value(item) for item in value]
    return value


def _unwrap_value(value: object) -> object:
    if isinstance(value, ConfigNode):
        return value.to_dict()
    if isinstance(value, list):
        return [_unwrap_value(item) for item in value]
    return value


@dataclass(slots=True)
class ConfigNode(MutableMapping[str, object]):
    """Mapping-like node with attribute and item access."""

    _data: dict[str, object] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._data = {key: _wrap_value(value) for key, value in self._data.items()}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ConfigNode:
        return cls(_data={key: _wrap_value(value) for key, value in data.items()})

    def to_dict(self) -> dict[str, object]:
        return {key: _unwrap_value(value) for key, value in self._data.items()}

    def get(self, key: str, default: object = None) -> object:
        return self._data.get(key, default)

    def setdefault(self, key: str, default: object = None) -> object:
        value = self._data.setdefault(key, _wrap_value(default))
        return value

    def update(self, mapping: Mapping[str, object] | Iterable[tuple[str, object]]) -> None:
        items: Iterator[tuple[str, object]]
        if isinstance(mapping, Mapping):
            items = iter(mapping.items())
        else:
            items = iter(mapping)
        for key, value in items:
            self._data[key] = _wrap_value(value)

    def __getattr__(self, name: str) -> object:
        try:
            return self._data[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name: str, value: object) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self._data[name] = _wrap_value(value)

    def __getitem__(self, key: str) -> object:
        return self._data[key]

    def __setitem__(self, key: str, value: object) -> None:
        self._data[key] = _wrap_value(value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)


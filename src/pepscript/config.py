"""Dynamic configuration node for nested tool configuration."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, cast, overload


def _wrap_value(value: Any) -> Any:
    if isinstance(value, ConfigNode):
        return value
    if isinstance(value, Mapping):
        return ConfigNode.from_dict(dict(value))
    if isinstance(value, list):
        return [_wrap_value(item) for item in value]
    return value


def _unwrap_value(value: Any) -> Any:
    if isinstance(value, ConfigNode):
        return value.to_dict()
    if isinstance(value, list):
        return [_unwrap_value(item) for item in value]
    return value


@dataclass(slots=True)
class ConfigNode:
    """Mapping-like node with attribute and item access."""

    _data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._data = {key: _wrap_value(value) for key, value in self._data.items()}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConfigNode:
        """Create a ``ConfigNode`` from a plain mapping, wrapping nested dicts recursively.

        Args:
            data: A mapping whose values may themselves be mappings, lists, or
                scalar values.

        Returns:
            A new ``ConfigNode`` with all nested ``Mapping`` values converted to
            ``ConfigNode`` instances.
        """
        return cls(_data={key: _wrap_value(value) for key, value in data.items()})

    def to_dict(self) -> dict[str, Any]:
        """Recursively unwrap this node to a plain ``dict``.

        Returns:
            A plain ``dict`` where all nested ``ConfigNode`` values are also
            unwrapped to ``dict``.
        """
        return {key: _unwrap_value(value) for key, value in self._data.items()}

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, or *default* if the key is absent.

        Args:
            key: The key to look up.
            default: Value returned when *key* is not present. Defaults to ``None``.

        Returns:
            The stored value (which may be a ``ConfigNode``) or *default*.
        """
        return self._data.get(key, default)

    def setdefault(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, inserting *default* if the key is absent.

        Mirrors ``dict.setdefault``. If *default* is a ``Mapping`` it is wrapped
        in a ``ConfigNode`` before insertion.

        Args:
            key: The key to look up or insert.
            default: Value to insert and return when *key* is not present.
                Defaults to ``None``.

        Returns:
            The existing value for *key*, or the newly inserted *default*.
        """
        value = self._data.setdefault(key, _wrap_value(default))
        return value

    @overload
    def update(self, mapping: Mapping[str, Any], /, **kwargs: Any) -> None: ...

    @overload
    def update(self, mapping: Iterable[tuple[str, Any]], /, **kwargs: Any) -> None: ...

    @overload
    def update(self, /, **kwargs: Any) -> None: ...

    def update(
        self,
        mapping: Mapping[str, Any] | Iterable[tuple[str, Any]] = (),
        /,
        **kwargs: Any,
    ) -> None:
        """Update the node with key/value pairs, mirroring ``dict.update``.

        Accepts a ``Mapping``, an iterable of ``(key, value)`` pairs, or keyword
        arguments (or any combination).  Any ``Mapping`` values are wrapped in
        ``ConfigNode`` instances.

        Args:
            mapping: A ``Mapping`` or iterable of ``(key, value)`` pairs to merge.
            **kwargs: Additional key/value pairs to merge.
        """
        items: Iterator[tuple[str, Any]]
        if isinstance(mapping, Mapping):
            items = iter(cast(Iterable[tuple[str, Any]], mapping.items()))
        else:
            items = iter(mapping)
        for key, value in items:
            self._data[key] = _wrap_value(value)
        for key, value in kwargs.items():
            self._data[key] = _wrap_value(value)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self._data[name] = _wrap_value(value)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = _wrap_value(value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

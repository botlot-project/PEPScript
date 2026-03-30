"""PEP 508 dependency and PEP 440 version specifier validation for parsed metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import NoReturn
from urllib.parse import urlsplit

from .config import ToolConfig
from .diagnostics import (
    Diagnostic,
    VALIDATION_DEPENDENCIES_TYPE,
    VALIDATION_DEPENDENCY_ENTRY_TYPE,
    VALIDATION_DEPENDENCY_SPEC,
    VALIDATION_REQUIRES_PYTHON_SPEC,
    VALIDATION_REQUIRES_PYTHON_TYPE,
    VALIDATION_TOOL_KEY_TYPE,
    VALIDATION_TOOL_VALUE_TYPE,
)
from .exceptions import MetadataValidationError
from .models import Metadata

# PEP 508 distribution name: starts/ends with alphanumeric, may contain ._- in between
_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")

# PEP 440 version clause: operator + version string (e.g. ">=1.0", "==1.*")
_VERSION_CLAUSE_RE = re.compile(
    r"^\s*(~=|===|==|!=|<=|>=|<|>)\s*[A-Za-z0-9.*+!_-]+\s*$"
)

# Valid PEP 508 marker variable names
_VALID_MARKER_VARS = frozenset(
    {
        "os_name",
        "sys_platform",
        "platform_machine",
        "platform_python_implementation",
        "platform_release",
        "platform_system",
        "platform_version",
        "python_version",
        "python_full_version",
        "implementation_name",
        "implementation_version",
        "extra",
        # Deprecated setuptools-style dotted names still seen in the wild
        "os.name",
        "sys.platform",
        "platform.version",
        "platform.machine",
        "platform.python_implementation",
    }
)

_MARKER_TOKEN_RE = re.compile(
    r"""
    \s*(
        \(
        |\)
        |not\s+in\b
        |and\b
        |or\b
        |~=|===|==|!=|<=|>=|<|>
        |in\b
        |'(?:[^'\\]|\\.)*'
        |"(?:[^"\\]|\\.)*"
        |[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


@dataclass(slots=True)
class _MarkerToken:
    kind: str
    value: str


def _build_validation_error(
    message: str,
    *,
    code: str,
    path: Path | None = None,
    field: str | None = None,
    line: int | None = None,
    column: int | None = None,
) -> MetadataValidationError:
    diagnostic = Diagnostic(
        code=code,
        message=message,
        path=path,
        line=line,
        column=column,
        field=field,
    )
    rendered = message if path is None else f"{message} (path={path})"
    return MetadataValidationError(rendered, diagnostic=diagnostic)


def _raise_validation_error(
    message: str,
    *,
    code: str,
    path: Path | None = None,
    field: str | None = None,
    line: int | None = None,
    column: int | None = None,
) -> NoReturn:
    raise _build_validation_error(
        message,
        code=code,
        path=path,
        field=field,
        line=line,
        column=column,
    )


def _is_scalar(value: object) -> bool:
    return isinstance(value, (str, int, float, bool, date, time, datetime))


def _validate_tool_value(
    value: object, *, path: Path | None = None, location: str = "tool"
) -> None:
    if isinstance(value, ToolConfig):
        _validate_tool_value(value.to_dict(), path=path, location=location)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                _raise_validation_error(
                    f"{location} keys must be strings",
                    code=VALIDATION_TOOL_KEY_TYPE,
                    path=path,
                    field=location,
                )
            _validate_tool_value(item, path=path, location=f"{location}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_tool_value(item, path=path, location=f"{location}[{index}]")
        return
    if _is_scalar(value):
        return
    _raise_validation_error(
        f"{location} contains unsupported value type: {type(value).__name__}",
        code=VALIDATION_TOOL_VALUE_TYPE,
        path=path,
        field=location,
    )


def _validate_marker(marker: str, *, loc: str, path: Path | None = None) -> None:
    """Validate marker syntax and ensure only known marker variables are used."""

    def tokenize(text: str) -> list[_MarkerToken]:
        tokens: list[_MarkerToken] = []
        index = 0
        length = len(text)
        while index < length:
            if text[index].isspace():
                index += 1
                continue
            match = _MARKER_TOKEN_RE.match(text, index)
            if match is None:
                _raise_validation_error(
                    f"{loc} has invalid marker syntax near {text[index:]!r}",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            value = match.group(1)
            kind = "IDENT"
            if value == "(":
                kind = "LPAREN"
            elif value == ")":
                kind = "RPAREN"
            elif value.lower() == "and":
                kind = "AND"
            elif value.lower() == "or":
                kind = "OR"
            elif (
                value.lower() == "in" or re.sub(r"\s+", " ", value.lower()) == "not in"
            ):
                kind = "OP"
            elif value.startswith(("'", '"')):
                kind = "STRING"
            elif value in {"~=", "===", "==", "!=", "<=", ">=", "<", ">"}:
                kind = "OP"
            tokens.append(_MarkerToken(kind=kind, value=value))
            index = match.end()
        return tokens

    class MarkerParser:
        def __init__(self, tokens: list[_MarkerToken]):
            self.tokens = tokens
            self.index = 0

        def current(self) -> _MarkerToken | None:
            if self.index >= len(self.tokens):
                return None
            return self.tokens[self.index]

        def consume(self, kind: str) -> _MarkerToken:
            token = self.current()
            if token is None or token.kind != kind:
                _raise_validation_error(
                    f"{loc} has invalid marker syntax",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            self.index += 1
            return token

        def parse(self) -> None:
            self.parse_or_expression()
            if self.current() is not None:
                _raise_validation_error(
                    f"{loc} has invalid marker syntax",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )

        def parse_or_expression(self) -> None:
            self.parse_and_expression()
            while (token := self.current()) is not None and token.kind == "OR":
                self.consume("OR")
                self.parse_and_expression()

        def parse_and_expression(self) -> None:
            self.parse_term()
            while (token := self.current()) is not None and token.kind == "AND":
                self.consume("AND")
                self.parse_term()

        def parse_term(self) -> None:
            token = self.current()
            if token is None:
                _raise_validation_error(
                    f"{loc} has invalid marker syntax",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            if token.kind == "LPAREN":
                self.consume("LPAREN")
                self.parse_or_expression()
                self.consume("RPAREN")
                return
            self.parse_comparison()

        def parse_comparison(self) -> None:
            self.parse_operand()
            self.consume("OP")
            self.parse_operand()

        def parse_operand(self) -> None:
            token = self.current()
            if token is None or token.kind not in {"IDENT", "STRING"}:
                _raise_validation_error(
                    f"{loc} has invalid marker syntax",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            if token.kind == "IDENT" and token.value not in _VALID_MARKER_VARS:
                _raise_validation_error(
                    f"{loc} has unknown marker variable {token.value!r}",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            self.index += 1

    MarkerParser(tokenize(marker)).parse()


def _validate_direct_reference(url: str, *, loc: str, path: Path | None = None) -> None:
    if not url:
        _raise_validation_error(
            f"{loc} has an empty direct reference URL",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )
    if any(character.isspace() for character in url):
        _raise_validation_error(
            f"{loc} has invalid whitespace in direct reference URL {url!r}",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )
    parsed = urlsplit(url)
    if not parsed.scheme or not (parsed.netloc or parsed.path):
        _raise_validation_error(
            f"{loc} has an invalid direct reference URL {url!r}",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )


def _validate_pep508_dependency(
    dep: str, *, path: Path | None = None, index: int = 0
) -> None:
    """Validate a single PEP 508 dependency specifier string."""
    loc = f"dependencies[{index}]"
    raw = dep.strip()

    if not raw:
        _raise_validation_error(
            f"{loc} must not be empty",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )

    # Split off environment marker at first semicolon
    if ";" in raw:
        req_part, marker_part = raw.split(";", 1)
        _validate_marker(marker_part.strip(), loc=loc, path=path)
    else:
        req_part = raw

    req_part = req_part.strip()
    is_url = "@" in req_part

    if is_url:
        name_scope, url_part = req_part.split("@", 1)
        name_scope = name_scope.strip()
        _validate_direct_reference(url_part.strip(), loc=loc, path=path)
    else:
        name_scope = req_part

    # Extract package name (stops at [, version operator chars, whitespace, or end)
    name_match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", name_scope)
    if not name_match:
        _raise_validation_error(
            f"{loc} has an invalid package name in {dep!r}",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )

    name = name_match.group()
    if not _NAME_RE.match(name):
        _raise_validation_error(
            f"{loc} has invalid package name {name!r}",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )

    rest = name_scope[name_match.end() :].strip()

    # Optional extras: [extra1, extra2, ...]
    if rest.startswith("["):
        close = rest.find("]")
        if close == -1:
            _raise_validation_error(
                f"{loc} has unclosed extras '[' in {dep!r}",
                code=VALIDATION_DEPENDENCY_SPEC,
                path=path,
                field=loc,
            )
        for extra in rest[1:close].split(","):
            e = extra.strip()
            if not e:
                _raise_validation_error(
                    f"{loc} has an empty extra in {dep!r}",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            if not _NAME_RE.match(e):
                _raise_validation_error(
                    f"{loc} has invalid extra {e!r}",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
        rest = rest[close + 1 :].strip()

    # For URL requirements, nothing should remain between name/extras and @
    if is_url and rest:
        _raise_validation_error(
            f"{loc} has unexpected content before '@' in {dep!r}",
            code=VALIDATION_DEPENDENCY_SPEC,
            path=path,
            field=loc,
        )

    # Version specifiers (not applicable for URL requirements)
    if not is_url and rest:
        if rest.startswith("("):
            if not rest.endswith(")"):
                _raise_validation_error(
                    f"{loc} has unclosed version specifier parentheses in {dep!r}",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )
            rest = rest[1:-1].strip()
        for clause in rest.split(","):
            if not _VERSION_CLAUSE_RE.match(clause):
                _raise_validation_error(
                    f"{loc} has invalid version specifier {clause.strip()!r} in {dep!r}",
                    code=VALIDATION_DEPENDENCY_SPEC,
                    path=path,
                    field=loc,
                )


def _validate_requires_python(spec: str, *, path: Path | None = None) -> None:
    """Validate a PEP 440 requires-python version specifier string."""
    for clause in spec.split(","):
        if not _VERSION_CLAUSE_RE.match(clause):
            _raise_validation_error(
                f"'requires-python' has invalid specifier {clause.strip()!r}",
                code=VALIDATION_REQUIRES_PYTHON_SPEC,
                path=path,
                field="requires-python",
            )


def collect_validation_diagnostics(
    meta: Metadata | None, *, path: Path | None = None
) -> list[Diagnostic]:
    """Collect validation diagnostics without raising."""

    diagnostics: list[Diagnostic] = []
    if meta is None:
        return diagnostics

    if not isinstance(meta.dependencies, list):
        diagnostics.append(
            Diagnostic(
                code=VALIDATION_DEPENDENCIES_TYPE,
                message="'dependencies' must be a list",
                path=path,
                field="dependencies",
            )
        )
    else:
        for index, dep in enumerate(meta.dependencies):
            if not isinstance(dep, str):
                diagnostics.append(
                    Diagnostic(
                        code=VALIDATION_DEPENDENCY_ENTRY_TYPE,
                        message=f"'dependencies[{index}]' must be a string",
                        path=path,
                        field=f"dependencies[{index}]",
                    )
                )
                continue
            try:
                _validate_pep508_dependency(dep, path=path, index=index)
            except MetadataValidationError as error:
                if error.diagnostics:
                    diagnostics.extend(error.diagnostics)
                else:
                    diagnostics.append(
                        Diagnostic(
                            code=VALIDATION_DEPENDENCY_SPEC,
                            message=str(error),
                            path=path,
                            field=f"dependencies[{index}]",
                        )
                    )

    if meta.requires_python is not None:
        if not isinstance(meta.requires_python, str):
            diagnostics.append(
                Diagnostic(
                    code=VALIDATION_REQUIRES_PYTHON_TYPE,
                    message="'requires-python' must be a string or None",
                    path=path,
                    field="requires-python",
                )
            )
        else:
            try:
                _validate_requires_python(meta.requires_python, path=path)
            except MetadataValidationError as error:
                if error.diagnostics:
                    diagnostics.extend(error.diagnostics)
                else:
                    diagnostics.append(
                        Diagnostic(
                            code=VALIDATION_REQUIRES_PYTHON_SPEC,
                            message=str(error),
                            path=path,
                            field="requires-python",
                        )
                    )

    try:
        _validate_tool_value(meta.config.tool, path=path)
    except MetadataValidationError as error:
        if error.diagnostics:
            diagnostics.extend(error.diagnostics)
        else:
            diagnostics.append(
                Diagnostic(
                    code=VALIDATION_TOOL_VALUE_TYPE,
                    message=str(error),
                    path=path,
                    field="tool",
                )
            )

    return diagnostics


def validate_metadata(meta: Metadata | None, *, path: Path | None = None) -> None:
    """Validate metadata structure, PEP 508 specifiers, and PEP 440 constraints."""

    diagnostics = collect_validation_diagnostics(meta, path=path)
    if not diagnostics:
        return
    first = diagnostics[0]
    raise MetadataValidationError(
        first.message if path is None else f"{first.message} (path={path})",
        diagnostic=first,
        diagnostics=diagnostics,
    )

# pepscript — Final Project Plan

## Document Purpose

This document defines the final implementation and delivery plan for **pepscript**, a Python 3.12 library for working with **PEP 723 inline script metadata** using a **stdlib-first**, **minimal-dependency**, **DX-friendly** design.

The project is intended to be published as a package on **PyPI** and developed openly on **GitHub** with **semantic versioning**.

The central design decision in this final version is:

- **no runtime dependencies if possible**
- **typed nested dataclasses**
- **Pythonic object model**
- **context-manager-based file API**
- **clean public API inspired by familiar stdlib patterns**

---

# 1. Product Definition

## 1.1 Name

**pepscript**

## 1.2 Thesis

`pepscript` is an embeddable Python library that treats a PEP 723-enabled script as a **first-class typed document**.

It provides a clean Python API for:

- opening and inspecting script files
- reading and editing inline metadata
- validating supported PEP 723 fields
- accessing nested `[tool.*]` config as typed/dot-accessible objects
- serializing changes back into the script safely

The strongest version of this project is **not** a runner clone. It is a **library and SDK** for applications, tools, and frameworks that need to work with PEP 723 metadata programmatically.

## 1.3 Non-Goals

The following are out of scope for the initial release:

- replacing `uv run`, `pipx`, or other runners
- implementing environment resolution/installation as the core feature
- building a sandbox or execution security framework
- introducing mandatory third-party dependencies
- building a large plugin system in v1
- preserving arbitrary comments/formatting inside the metadata block with perfect fidelity
- implementing AST-based dependency inference as a default workflow

---

# 2. Final Product Direction

## 2.1 Key Design Decisions

The project will be built around these decisions:

1. **stdlib-first core**
2. **no runtime dependencies if feasible**
3. **nested typed dataclasses**
4. **context manager API**
5. **file-oriented primary interface**
6. **strict parsing by default**
7. **minimal but extensible public API**
8. **semantic versioning from the beginning**
9. **PyPI and GitHub release readiness**
10. **developer ergonomics prioritized**

## 2.2 Desired API Feel

The public API should feel close to familiar Python stdlib patterns such as:

```python
with open("file.txt") as f:
    data = f.read()
```

For `pepscript`, the target feeling is:

```python
from pepscript import PEPScript

with PEPScript("/path/to/script.py") as script:
    print(script.file)
    print(script.meta.dependencies)
    print(script.meta.config.tool.botlot.some_setting)
```

This should feel obvious, unsurprising, and discoverable.

---

# 3. User Experience Goals

## 3.1 Primary DX Goals

The package should make these use cases easy:

### Read metadata from an existing script

```python
from pepscript import PEPScript

with PEPScript("example.py") as script:
    print(script.meta.dependencies)
```

### Update metadata and write back safely

```python
from pepscript import PEPScript

with PEPScript("example.py") as script:
    script.meta.add_dependency("httpx>=0.27")
    script.save()
```

### Access nested tool config with dot notation

```python
with PEPScript("bot.py") as script:
    print(script.meta.config.tool.botlot.token_env)
```

### Parse from a string without file IO

```python
from pepscript import parse_script

script = parse_script(source_text)
print(script.meta.requires_python)
```

## 3.2 What Good DX Means Here

- short import paths
- obvious object names
- consistent file/path/string behavior
- precise error messages
- typed public classes
- explicit save/write semantics
- low boilerplate
- no hidden installs or subprocess side effects

---

# 4. Scope

## 4.1 In Scope for v0.1.0

- open script files through a `PEPScript` context manager
- parse PEP 723 inline metadata blocks
- expose typed metadata via dataclasses
- expose nested tool config via dot-accessible typed structures
- read from paths and raw strings
- serialize changes back into script files
- strict validation of core supported fields
- deterministic metadata block generation
- public Python API
- tests, CI, docs, changelog, release pipeline

## 4.2 Deferred

- complex runner adapters
- environment orchestration
- lockfile abstractions
- full formatting preservation inside metadata TOML
- import-to-dependency inference
- editor integrations
- pre-commit support
- framework-specific integrations beyond reference examples
- security policy engine
- CLI as a primary focus

---

# 5. Architectural Principles

## 5.1 Design Principles

### Stdlib-first
Use only the standard library unless a third-party dependency becomes clearly necessary.

### File-first, string-capable
The primary interface should be file-based via `PEPScript(path)`, but string parsing must also be supported.

### Structured and typed
Metadata should not be raw dictionaries by default. It should be structured through typed dataclasses and controlled mapping wrappers.

### Familiar Python API design
Public API naming and usage should mirror familiar stdlib conventions where appropriate.

### Explicit persistence
Nothing should be written to disk unless the caller explicitly requests it.

### Strict by default
Invalid metadata should fail clearly and early.

---

# 6. Proposed Package Layout

```text
pepscript/
├── src/
│   └── pepscript/
│       ├── __init__.py
│       ├── py.typed
│       ├── script.py
│       ├── parser.py
│       ├── models.py
│       ├── config.py
│       ├── edit.py
│       ├── io.py
│       ├── serialize.py
│       ├── validate.py
│       ├── exceptions.py
│       ├── block.py
│       └── compat.py
├── tests/
│   ├── fixtures/
│   ├── test_script_api.py
│   ├── test_parser.py
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_edit.py
│   ├── test_serialize.py
│   ├── test_validate.py
│   └── test_io.py
├── examples/
│   ├── open_and_read.py
│   ├── edit_and_save.py
│   ├── parse_from_string.py
│   └── nested_tool_config.py
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   ├── api.md
│   ├── design.md
│   └── examples.md
├── .github/
│   └── workflows/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

---

# 7. Public API Design

## 7.1 Main Entry Points

The main public entry points should be:

```python
from pepscript import PEPScript, parse_script, parse_file
```

Potential top-level exports:

```python
from pepscript import (
    PEPScript,
    PEPMetadata,
    PEPToolConfig,
    parse_script,
    parse_file,
)
```

## 7.2 Primary Class: `PEPScript`

This should be the central object and context manager.

### Constructor goals

```python
PEPScript(path: str | Path, *, encoding: str = "utf-8", strict: bool = True)
```

### Responsibilities

- open/read the target script file
- parse metadata
- expose file/path/source state
- expose typed metadata as `script.meta`
- allow modifications
- support explicit `save()`
- support `reload()`
- support context manager lifecycle

### Example

```python
from pepscript import PEPScript

with PEPScript("script.py") as script:
    print(script.path)
    print(script.source)
    print(script.meta.dependencies)
```

## 7.3 Proposed `PEPScript` Public Surface

```python
class PEPScript:
    path: Path
    encoding: str
    source: str
    file: ScriptFileInfo
    meta: PEPMetadata | None

    def __enter__(self) -> "PEPScript": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...

    def save(self) -> None: ...
    def save_as(self, path: str | Path) -> None: ...
    def reload(self) -> None: ...
    def to_source(self) -> str: ...
    def validate(self) -> None: ...
```

## 7.4 `script.file`

The user explicitly wants access to an underlying file API shape.

Do **not** expose a raw live file handle as the primary abstraction. That would blur responsibility and complicate lifecycle semantics.

Instead, expose a small typed object such as:

```python
@dataclass(slots=True)
class ScriptFileInfo:
    path: Path
    name: str
    filename: str
    suffix: str
    exists: bool
    encoding: str
```

This satisfies the desired ergonomic goal:

```python
with PEPScript("bot.py") as script:
    print(script.file.filename)
```

This is safer and clearer than exposing a mutable file descriptor directly.

## 7.5 `script.meta`

`script.meta` should be a typed dataclass representing parsed PEP 723 metadata.

Example target:

```python
with PEPScript("bot.py") as script:
    print(script.meta.dependencies)
    print(script.meta.requires_python)
```

If no metadata block exists:
- either `script.meta is None`
- or provide an explicit empty metadata object

## Recommendation
Use:
- `None` when no block exists
- plus a helper such as `script.ensure_meta()` if mutation should create one

Example:

```python
with PEPScript("bot.py") as script:
    meta = script.ensure_meta()
    meta.add_dependency("requests")
    script.save()
```

---

# 8. Dataclass Model Design

## 8.1 Core Model Strategy

Use `dataclasses` from the standard library for all core structured objects.

This matches the user requirement and the minimal-dependency goal.

## 8.2 Proposed Models

### `ScriptFileInfo`

```python
@dataclass(slots=True)
class ScriptFileInfo:
    path: Path
    name: str
    filename: str
    suffix: str
    exists: bool
    encoding: str
```

### `BlockInfo`

```python
@dataclass(slots=True)
class BlockInfo:
    start: int
    end: int
    content_start: int
    content_end: int
    block_type: str
```

### `PEPMetadata`

```python
@dataclass(slots=True)
class PEPMetadata:
    dependencies: list[str] = field(default_factory=list)
    requires_python: str | None = None
    config: "PEPConfigRoot" = field(default_factory=lambda: PEPConfigRoot())
```

### `PEPConfigRoot`

```python
@dataclass(slots=True)
class PEPConfigRoot:
    tool: "ConfigNode" = field(default_factory=lambda: ConfigNode())
```

### `ConfigNode`

This is the key abstraction for nested `[tool.*]` access.

A strict fully static type for arbitrary user-defined tool sections is not realistic because section names and nested keys are dynamic. The best approach is:

- dataclass root containers where structure is known
- nested config nodes that allow attribute access over mapping-backed values

Proposed shape:

```python
@dataclass(slots=True)
class ConfigNode:
    _data: dict[str, object] = field(default_factory=dict, repr=False)
```

With methods:
- `__getattr__`
- `__setattr__`
- `to_dict()`
- `from_dict()`
- `get()`
- `setdefault()`

This allows:

```python
script.meta.config.tool.botlot.some_setting
```

while remaining stdlib-only.

## 8.3 Important Design Clarification

The user requested “Use `dataclasses` for nested, typed objects.”

That should be interpreted as:

- the top-level public model objects are dataclasses
- dynamic nested config can use a dataclass-backed access node

Because arbitrary `[tool.<name>]` sections are user-defined, fully static nested dataclasses for unknown config schemas are not feasible in the general case without code generation or user-supplied schemas.

## 8.4 Recommended Model Compromise

Use this layered strategy:

1. `PEPScript` → dataclass-backed objects
2. `PEPMetadata` → dataclass
3. `PEPConfigRoot` → dataclass
4. `ConfigNode` → dataclass wrapping nested dict data with attribute access

This keeps the API clean while remaining practical.

---

# 9. API Usage Targets

## 9.1 Target Example: Read Existing Metadata

```python
from pepscript import PEPScript

with PEPScript("script.py") as script:
    print(script.file.filename)
    print(script.meta.dependencies)
    print(script.meta.requires_python)
```

## 9.2 Target Example: Nested Tool Config

```python
from pepscript import PEPScript

with PEPScript("bot.py") as script:
    print(script.meta.config.tool.botlot.some_setting)
```

## 9.3 Target Example: Add Dependency

```python
from pepscript import PEPScript

with PEPScript("script.py") as script:
    meta = script.ensure_meta()
    meta.add_dependency("requests>=2.32")
    script.save()
```

## 9.4 Target Example: Parse From String

```python
from pepscript import parse_script

script = parse_script(source_text)
print(script.meta.dependencies)
```

## 9.5 Target Example: Create New Metadata Block

```python
from pepscript import PEPScript

with PEPScript("plain_script.py") as script:
    meta = script.ensure_meta()
    meta.requires_python = ">=3.12"
    meta.add_dependency("httpx")
    script.save()
```

---

# 10. Parsing Strategy

## 10.1 Parsing Requirements

The parser must:

- detect PEP 723 metadata blocks reliably
- extract and parse block content
- reject duplicate blocks where appropriate
- distinguish missing block from malformed block
- preserve original source text
- populate typed models

## 10.2 Implementation

Use only stdlib:

- `re` for block detection
- `tomllib` for TOML parsing
- `pathlib` for file handling

## 10.3 Parser Modes

### Strict mode
Default. Raises on malformed or invalid metadata.

### Non-strict mode
Potential later addition. Can return diagnostics instead of raising.

## 10.4 Parsing Output

Both file and string parsing should produce a `PEPScriptDocument`-style internal object or directly hydrate `PEPScript` / metadata models.

For public simplicity, the user-facing API should return a `PEPScript`-like structured object for both path and string workflows.

---

# 11. Validation Strategy

## 11.1 Validation Philosophy

Since the project is stdlib-first and dependency-free if possible, validation should initially be:

- structural
- deterministic
- useful
- not overly magical

## 11.2 Core Validation Scope

Validate at minimum:

- metadata block existence and uniqueness
- TOML parseability
- `dependencies` exists only as a list of strings
- `requires-python` exists only as a string
- `tool` exists only as a table/object
- nested tool structures remain serializable

## 11.3 About PEP 508 Validation

Strict full PEP 508 requirement parsing typically benefits from `packaging`.

Because the user explicitly prefers stdlib-first and no dependencies if possible, the plan is:

### v0.1.0
Implement structural validation only:
- string entries required
- no full `packaging.Requirement` parsing

### Future optional enhancement
Potential optional extra for enhanced validation, only if clearly justified.

This is the correct tradeoff for the initial version.

---

# 12. Editing and Persistence

## 12.1 Editing Goals

Users must be able to:

- add/remove dependencies
- update `requires_python`
- read and modify nested `tool` config
- write changes back into the file explicitly

## 12.2 Persistence Rules

- entering the context manager does **not** save automatically
- exiting the context manager does **not** save automatically
- `save()` must be explicit
- `save_as()` must be explicit

This avoids surprising file mutations.

## 12.3 Write-Back Guarantees

v0.1.0 should guarantee:

- non-metadata script content remains unchanged
- metadata block is replaced deterministically
- metadata block can be inserted if missing
- metadata block can be removed if required

## 12.4 Methods to Support

### On `PEPScript`
- `save()`
- `save_as(path)`
- `reload()`
- `to_source()`
- `ensure_meta()`
- `validate()`

### On `PEPMetadata`
- `add_dependency(dep: str)`
- `remove_dependency(dep: str)`
- `set_requires_python(spec: str | None)`

### On `ConfigNode`
- `to_dict()`
- `update(mapping)`
- `get(name, default=None)`

---

# 13. Nested Tool Config Design

## 13.1 Problem

Users want:

```python
script.meta.config.tool.botlot.some_setting
```

PEP 723 allows arbitrary `[tool.*]` sections. These are schema-less by nature.

## 13.2 Solution

Implement a `ConfigNode` wrapper around nested dictionaries that:

- supports attribute access
- recursively wraps child dicts
- preserves lists/scalars
- can serialize back to dict form

Example behavior:

```python
node = ConfigNode.from_dict(
    {"botlot": {"some_setting": "value", "enabled": True}}
)

print(node.botlot.some_setting)  # "value"
print(node.botlot.enabled)       # True
```

## 13.3 Constraints

This is dot-access convenience, not a formal schema system.

Therefore:

- keys that are not valid Python identifiers will need fallback access via `node["some-key"]` or `node.get("some-key")`
- conflicts with reserved/internal attributes must be handled carefully

## 13.4 Recommendation

Support both:

- attribute access for valid identifiers
- item access for everything else

Example:

```python
script.meta.config.tool.mytool.some_setting
script.meta.config.tool["my-tool"]["some-setting"]
```

---

# 14. Exceptions

Create a small explicit exception hierarchy:

```python
class PepScriptError(Exception): ...
class FileLoadError(PepScriptError): ...
class MetadataBlockNotFoundError(PepScriptError): ...
class DuplicateMetadataBlockError(PepScriptError): ...
class MetadataParseError(PepScriptError): ...
class MetadataValidationError(PepScriptError): ...
class SaveError(PepScriptError): ...
```

Error messages should include:

- file path if applicable
- field name if applicable
- clear remediation hint where helpful

---

# 15. Packaging and Tooling

## 15.1 Python Version

- **Python 3.12+**

## 15.2 Build Backend

Use **Hatchling** unless a strong reason appears to switch.

Reason:
- modern
- lightweight
- straightforward packaging
- good fit with `uv`

## 15.3 Development Tooling

Use:

- **uv** for environment and dependency management
- **ruff** for linting and formatting
- **ty** for static type checking
- **pytest** for tests

## 15.4 Dependency Policy

### Runtime
- stdlib only if possible

### Development
Development-only dependencies are fine:
- pytest
- pytest-cov
- hatchling
- build
- twine or trusted publishing workflow tooling as needed

---

# 16. Repository and Packaging Structure

## 16.1 `pyproject.toml` Requirements

Include:

- package metadata
- Python requirement `>=3.12`
- build backend
- project URLs
- classifiers
- semantic version
- tool config for ruff, ty, pytest

## 16.2 `src/` Layout

Use `src/` layout to avoid import confusion during development.

## 16.3 Typing Marker

Ship `py.typed`.

This is important because a typed API is part of the project value.

---

# 17. Documentation Plan

## 17.1 README Must Cover

- what pepscript is
- what it is not
- install
- quick examples
- context manager usage
- parsing from strings
- nested config access
- editing and saving
- versioning policy

## 17.2 Documentation Sections

- quickstart
- public API
- design rationale
- config model behavior
- limitations
- examples

## 17.3 Example Coverage

Examples should show:

- read metadata
- create metadata
- modify dependencies
- nested config access
- save and reload
- handling missing metadata

---

# 18. Testing Strategy

## 18.1 Test Categories

### Parser tests
- valid block
- no block
- malformed block
- duplicate blocks
- odd spacing/newlines
- block-like content inside strings/comments

### Model tests
- dataclass initialization
- `ensure_meta()`
- dependency mutation helpers
- config node wrapping/unwrapping

### File API tests
- open existing file
- save changes
- save as new file
- reload behavior
- encoding handling

### Serialization tests
- deterministic output
- nested tool table serialization
- preservation of non-metadata source text

### Exception tests
- path-aware errors
- malformed TOML diagnostics
- invalid metadata structure

## 18.2 Coverage Goal

Target:
- **90%+ meaningful coverage**

---

# 19. CI/CD

## 19.1 CI Workflow

On push and pull request:

- install via `uv`
- run `ruff check`
- run `ruff format --check`
- run `ty check`
- run tests

## 19.2 Release Workflow

On version tag:

- build wheel and sdist
- verify artifacts
- publish to PyPI
- create GitHub release

## 19.3 Release Recommendation

Use **Trusted Publishing** for PyPI if practical.

---

# 20. Semantic Versioning Policy

Use semantic versioning throughout.

## 20.1 Rules

- **MAJOR**: breaking public API changes
- **MINOR**: backward-compatible features
- **PATCH**: backward-compatible bug fixes

## 20.2 Recommended Initial Version

Start with:
- **0.1.0**

Move to `1.0.0` only after:
- real-world use in at least one or two projects
- API naming confidence
- stable serialization behavior
- no major regrets in the public object model

---

# 21. Final API Proposal

## 21.1 Top-Level Exports

```python
from pepscript import (
    PEPScript,
    PEPMetadata,
    PEPConfigRoot,
    ConfigNode,
    parse_script,
    parse_file,
)
```

## 21.2 Main Class Sketch

```python
class PEPScript:
    path: Path | None
    source: str
    encoding: str
    file: ScriptFileInfo | None
    meta: PEPMetadata | None

    def __enter__(self) -> "PEPScript": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...

    def ensure_meta(self) -> PEPMetadata: ...
    def validate(self) -> None: ...
    def reload(self) -> None: ...
    def save(self) -> None: ...
    def save_as(self, path: str | Path) -> None: ...
    def to_source(self) -> str: ...
```

## 21.3 Metadata Class Sketch

```python
@dataclass(slots=True)
class PEPMetadata:
    dependencies: list[str] = field(default_factory=list)
    requires_python: str | None = None
    config: PEPConfigRoot = field(default_factory=PEPConfigRoot)

    def add_dependency(self, dep: str) -> None: ...
    def remove_dependency(self, dep: str) -> None: ...
    def set_requires_python(self, spec: str | None) -> None: ...
```

## 21.4 Config Classes Sketch

```python
@dataclass(slots=True)
class PEPConfigRoot:
    tool: "ConfigNode" = field(default_factory=lambda: ConfigNode())

@dataclass(slots=True)
class ConfigNode:
    _data: dict[str, object] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ConfigNode": ...
    def to_dict(self) -> dict[str, object]: ...
    def get(self, key: str, default=None): ...
```

## 21.5 String Parsing Functions

```python
def parse_script(source: str, *, strict: bool = True) -> PEPScript: ...
def parse_file(path: str | Path, *, encoding: str = "utf-8", strict: bool = True) -> PEPScript: ...
```

---

# 22. Concrete Roadmap

## Phase 0 — Bootstrap

### Tasks
1. create GitHub repository
2. initialize `src/` package layout
3. configure `pyproject.toml`
4. configure `uv`, `ruff`, `ty`, `pytest`
5. add README scaffold
6. add CI workflow

### Exit criteria
- repo exists
- local dev setup works
- CI passes on scaffold

---

## Phase 1 — Core File and Model API

### Tasks
1. implement `ScriptFileInfo`
2. implement `BlockInfo`
3. implement `PEPMetadata`
4. implement `PEPConfigRoot`
5. implement `ConfigNode`
6. implement `PEPScript` skeleton

### Exit criteria
- file/model API imports cleanly
- basic object construction works
- type checker passes

---

## Phase 2 — Parsing

### Tasks
1. implement metadata block detection
2. implement TOML extraction
3. parse `dependencies`
4. parse `requires-python`
5. parse `[tool]` section into `ConfigNode`
6. connect parser output to `PEPScript`

### Exit criteria
- valid scripts parse successfully
- malformed scripts fail cleanly
- nested tool config is accessible

---

## Phase 3 — Validation

### Tasks
1. validate core field types
2. validate duplicate metadata blocks
3. validate invalid TOML cases
4. improve diagnostics and exceptions
5. test edge cases thoroughly

### Exit criteria
- invalid structure yields clear exceptions
- tests cover main failure modes

---

## Phase 4 — Editing and Saving

### Tasks
1. implement dependency mutation helpers
2. implement config mutation support
3. implement serializer
4. implement block insertion/replacement/removal
5. implement `save()`
6. implement `save_as()`
7. implement `reload()`

### Exit criteria
- source round-trips correctly
- non-metadata code stays unchanged
- explicit save flow works

---

## Phase 5 — API Polish

### Tasks
1. refine naming
2. reduce public surface
3. improve docstrings
4. improve examples
5. audit error messages
6. finalize README quickstart

### Exit criteria
- public API feels coherent
- examples match intended DX

---

## Phase 6 — Release Preparation

### Tasks
1. add changelog
2. add issue templates
3. add release workflow
4. build wheel and sdist
5. verify package metadata
6. publish `0.1.0`

### Exit criteria
- GitHub release exists
- package is on PyPI
- install/import works in clean environment

---

# 23. Initial GitHub Issue Backlog

1. Bootstrap repository and `pyproject.toml`
2. Configure `uv`, `ruff`, `ty`, and `pytest`
3. Implement exception hierarchy
4. Implement `ScriptFileInfo`
5. Implement `PEPMetadata`
6. Implement `PEPConfigRoot`
7. Implement `ConfigNode`
8. Implement `PEPScript`
9. Implement metadata block parser
10. Implement TOML parse layer
11. Implement nested tool config conversion
12. Implement validation
13. Implement serializer
14. Implement save/reload logic
15. Add parser fixtures
16. Add model tests
17. Add round-trip tests
18. Write README quickstart
19. Add GitHub Actions CI
20. Prepare `0.1.0` release

---

# 24. Risks and Mitigations

## Risk: arbitrary tool config is not fully statically typable
**Mitigation:** use dataclass root objects plus `ConfigNode` for dynamic nested access.

## Risk: users expect raw file handle behavior
**Mitigation:** expose typed `script.file` metadata object, not a raw mutable handle.

## Risk: formatting-preservation expectations become too high
**Mitigation:** document clearly that v0.1.0 preserves non-metadata source exactly and regenerates metadata block deterministically.

## Risk: stdlib-only validation is less strict than packaging-based validation
**Mitigation:** accept this tradeoff in v0.1.0; consider optional enhanced validation later only if justified.

---

# 25. Final Recommendation

This project is worth building, and the revised direction is stronger than the earlier version.

The right implementation strategy is:

- **stdlib-first**
- **file-first**
- **dataclass-based**
- **context-manager-oriented**
- **explicit save semantics**
- **typed top-level model objects**
- **dynamic but ergonomic nested tool config**
- **minimal public API**
- **0.x release first, then harden**

The most valuable differentiator is not execution. It is the **quality of the Python API** for working with PEP 723 scripts as structured documents.

---

# 26. Definition of Done for v0.1.0

`pepscript` v0.1.0 is done when:

- package installs on Python 3.12
- runtime has no third-party dependencies
- `PEPScript(path)` works as a context manager
- `script.file` exposes typed file info
- `script.meta` exposes typed metadata
- nested tool config can be accessed via dot/item access
- missing metadata can be created with `ensure_meta()`
- `save()` persists updates correctly
- `save_as()` and `reload()` work
- parser handles valid/missing/malformed/duplicate block scenarios
- tests cover parser, models, config node, editing, and IO
- CI passes
- README and docs are complete enough for first public users
- wheel and sdist build successfully
- package is published to PyPI
- GitHub repo is public with changelog and semver policy

---

# 27. Immediate Next Step

Build the repository in this order:

1. package skeleton
2. exception hierarchy
3. file/model dataclasses
4. `ConfigNode`
5. `PEPScript` class skeleton
6. metadata block parser
7. TOML hydration into dataclasses
8. validation
9. serializer and save flow
10. tests and `0.1.0` release preparation

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run pytest                    # Run all tests
uv run pytest tests/test_foo.py  # Run a single test file
uv run pytest -k test_name       # Run a single test by name
uv run ruff format .             # Format code
uv run ruff check .              # Lint code
uv run ty check .                # Type check
```

## Architecture

**PEPScript** is a zero-dependency Python 3.12+ library for programmatically reading, editing, and serializing [PEP 723](https://peps.python.org/pep-0723/) inline script metadata. It is a library/SDK, not a script runner.

### Layered design

```
src/pepscript/
├── script.py      # PEPScript — main entry point (context manager)
├── parser.py      # Detect # /// script blocks; extract + parse TOML
├── models.py      # @dataclass(slots=True) models: PEPMetadata, BlockInfo, ScriptFileInfo
├── config.py      # ConfigNode — dynamic attribute+item access for [tool.*] sections
├── serialize.py   # Deterministic TOML serialization + block rewriting
├── validate.py    # Structural metadata validation (no PEP 508 checks in v0.1)
├── exceptions.py  # Custom exception hierarchy rooted at PEPScriptError
└── io.py          # File read/write, wraps OSError in custom exceptions
```

### Key design rules

- **Explicit persistence** — `save()` must be called; context manager exit does NOT auto-save.
- **Strict by default** — `PEPScript(path)` validates on parse; disable with `strict=False`.
- **Deterministic serialization** — The metadata block is fully regenerated on save (sorted keys, consistent formatting); non-metadata source is preserved exactly.
- **`script.file`** is a typed `ScriptFileInfo` dataclass, not a live file handle.
- **`script.meta`** can be `None` for scripts without a metadata block. Use `ensure_meta()` to create one.
- **`ConfigNode`** wraps arbitrary `[tool.*]` dicts for both attribute access (`node.ruff.line_length`) and item access (`node["my-tool"]`).
- Validation is structural only — no `packaging` dependency, so PEP 508 version specifiers are not validated.

### Public API

```python
from pepscript import (
    PEPScript,       # Main context manager
    parse_file,      # Convenience: parse from Path/str
    parse_script,    # Convenience: parse from source string
    PEPMetadata,     # Typed metadata dataclass
    PEPConfigRoot,   # Root config container (holds .tool: ConfigNode)
    ConfigNode,      # Dynamic nested config access
    ScriptFileInfo,  # Typed file metadata
)
```

### Exception hierarchy

```
PEPScriptError
├── FileLoadError
├── DuplicateMetadataBlockError
├── MetadataParseError
├── MetadataValidationError
└── SaveError
```

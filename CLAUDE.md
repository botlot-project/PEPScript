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
uv build                         # Build wheel and sdist
uv run zensical serve            # Serve docs locally (http://127.0.0.1:8000)
uv run zensical build            # Build static docs site into site/
uv run prek install              # Install pre-commit hooks (run once after cloning)
uv run git-cliff                 # Preview release notes from conventional commits
```

## Architecture

**PEPScript** is a zero-dependency Python 3.12+ library for programmatically reading, editing, and serializing [PEP 723](https://peps.python.org/pep-0723/) inline script metadata. It is a library/SDK, not a script runner.

### Layered design

```
src/pepscript/
├── script.py      # PEPScript — main entry point (context manager)
├── parser.py      # Detect # /// script blocks; extract + parse TOML
├── models.py      # @dataclass(slots=True) models: Metadata, BlockInfo, ScriptFileInfo
├── config.py      # ToolConfig — dynamic attribute+item access for [tool.*] sections
├── serialize.py   # Deterministic TOML serialization + block rewriting
├── validate.py    # PEP 508 dependency + PEP 440 version specifier validation
├── exceptions.py  # Custom exception hierarchy rooted at PEPScriptError
└── io.py          # File read/write, wraps OSError in custom exceptions
```

### Key design rules

- **Context manager = edit mode** — auto-saves on clean exit (file-backed); rolls back in-memory edits on exception. Outside a `with` block, `save()` must be called explicitly.
- **Strict by default** — `PEPScript(path)` validates on parse; disable with `strict=False`.
- **Deterministic serialization** — The metadata block is fully regenerated on save (sorted keys, consistent formatting); non-metadata source is preserved exactly.
- **`script.file`** is a typed `ScriptFileInfo` dataclass, not a live file handle.
- **`script.meta`** is always a non-`None` `Metadata`. Use `script.has_metadata` to check whether a `# /// script` block was present. Use `meta.is_empty` to check whether any data has been set.
- **`ToolConfig`** wraps arbitrary `[tool.*]` dicts for both attribute access (`node.ruff`) and item access (`node["ruff"]["line-length"]`, `node["my-tool"]`).
- Validation covers structure, PEP 508 dependency specifiers (name, extras, version operators, environment markers), and PEP 440 `requires-python` specifiers — all via regex, no `packaging` dependency.

### Public API

```python
from pepscript import (
    PEPScript,       # Main context manager
    parse_file,      # Convenience: parse from Path/str
    parse_script,    # Convenience: parse from source string
    Metadata,     # Typed metadata dataclass
    ConfigRoot,   # Root config container (holds .tool: ToolConfig)
    ToolConfig,      # Dynamic nested config access
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

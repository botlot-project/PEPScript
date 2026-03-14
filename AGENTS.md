# AGENTS.md

## Project Overview

**PEPScript** is a Python 3.12+ library for working with PEP 723 inline script metadata. It treats PEP 723-enabled scripts as first-class typed documents.

**Key Value:** Library/SDK for tools that need to work with PEP 723 metadata programmatically — *not* a script runner.

## Core Design Constraints

| Constraint | Details |
|------------|---------|
| **Runtime Dependencies** | None (stdlib only) |
| **Python Version** | 3.12+ |
| **Build Backend** | uv_build |
| **Package Layout** | `src/` layout |
| **Typing** | Full type hints, ship `py.typed` |

## Development Tooling

```bash
uv run ruff format .      # Formatting
uv run ruff check .       # Linting
uv run ty check .         # Type checking
uv run pytest             # Tests
```

## Key Design Patterns

1. **Context Manager API** — `PEPScript` is the primary entry point
2. **Context Manager = Edit Mode** — auto-saves on clean exit (file-backed); rolls back in-memory edits on exception. Outside `with`, call `save()` explicitly.
3. **Typed Dataclasses** — All core models use `@dataclass(slots=True)`
4. **Strict by Default** — Invalid metadata fails early with clear errors
5. **File-First, String-Capable** — Primary interface is file-based, but string parsing supported

## Public API Surface

```python
from pepscript import (
    PEPScript,        # Main context manager
    PEPMetadata,      # Typed metadata model
    ConfigNode,       # Nested tool config access
    parse_script,     # Parse from string
    parse_file,       # Parse from path
)
```

## Architecture

```
src/pepscript/
├── script.py      # PEPScript class
├── parser.py      # Metadata block detection & TOML parsing
├── models.py      # Dataclass models (PEPMetadata, etc.)
├── config.py      # ConfigNode for nested tool access
├── serialize.py   # Write metadata back to source
├── validate.py    # PEP 508 dependency + PEP 440 specifier validation
├── exceptions.py  # Custom exception hierarchy
└── io.py          # File operations
```

## Important Notes

- **No raw file handles** — Expose `script.file` as typed `ScriptFileInfo`, not live descriptors
- **Dynamic tool config** — Use `ConfigNode` wrapper for arbitrary `[tool.*]` sections (attribute + item access)
- **Metadata block** — Regenerate deterministically on save; preserve non-metadata source exactly
- **Validation** — PEP 508 dependency specifiers and PEP 440 `requires-python` validated via regex; no `packaging` dependency

## Versioning

- Semantic versioning (MAJOR.MINOR.PATCH)
- Current target: `1.0.0`

## References

- [PEP 723](https://peps.python.org/pep-0723/)


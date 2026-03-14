# PEPScript Changelog

## 0.1.0 (2026-03-14)

Initial release.

- Parse PEP 723 inline script metadata blocks from files or source strings
- Typed dataclass models (`PEPMetadata`, `ToolConfig`, `ScriptFileInfo`)
- Add, remove, and modify dependencies and `requires-python`
- Dynamic `[tool.*]` configuration access via `ToolConfig` (attribute and item access)
- Deterministic TOML serialization and metadata block rewriting
- PEP 508 dependency specifier validation (name, extras, version operators, environment markers)
- PEP 440 `requires-python` specifier validation
- Structural metadata validation (strict mode by default)
- Context manager API: auto-save on clean exit, rollback on exception; explicit `save()` / `save_as()` outside `with` blocks
- Zero runtime dependencies (stdlib only)
- Full type hints with `py.typed` marker
- GitHub Actions CI (lint, format, type check, tests on Python 3.12 + 3.13)
- Release workflow with PyPI Trusted Publishing

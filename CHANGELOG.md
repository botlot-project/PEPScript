# PEPScript Changelog

## 0.1.0 (2026-03-14)

Initial release.

- Parse PEP 723 inline script metadata blocks from files or source strings
- Typed dataclass models (`PEPMetadata`, `ConfigNode`, `ScriptFileInfo`)
- Add, remove, and modify dependencies and `requires-python`
- Dynamic `[tool.*]` configuration access via `ConfigNode` (attribute and item access)
- Deterministic TOML serialization and metadata block rewriting
- Structural metadata validation (strict mode by default)
- Context manager API with explicit `save()` / `save_as()` persistence
- Zero runtime dependencies (stdlib only)
- Full type hints with `py.typed` marker
- GitHub Actions CI (lint, format, type check, tests on Python 3.12 + 3.13)
- Release workflow with PyPI Trusted Publishing

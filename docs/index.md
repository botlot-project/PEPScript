# PEPScript

**PEPScript** is a zero-dependency Python 3.12+ library for programmatically reading, editing, and serializing [PEP 723](https://peps.python.org/pep-0723/) inline script metadata.

## Key features

- **Zero runtime dependencies** — stdlib only; no `packaging`, no `tomllib` backport needed.
- **Strict by default** — metadata is validated immediately on parse; opt out with `strict=False`.
- **Explicit persistence** — changes are never auto-saved. Call `save()` when you're ready.
- **Deterministic serialization** — the metadata block is fully regenerated on save with sorted keys and consistent formatting; your source code is preserved exactly.
- **Typed API** — all models are `@dataclass(slots=True)` with full type hints and a `py.typed` marker.
- **Dynamic tool config access** — `ConfigNode` supports both attribute access (`node.ruff.line_length`) and item access (`node["my-tool"]`) for arbitrary `[tool.*]` sections.

## Quick example

```python
from pepscript import PEPScript

with PEPScript("script.py") as script:
    meta = script.ensure_meta()
    meta.add_dependency("requests>=2.31")
    meta.set_requires_python(">=3.12")
    script.save()
```

That's it — PEPScript handles creating the `# /// script` block if it doesn't exist,
serializing the TOML, and writing it back to disk.

## Next steps

- [Getting Started](getting-started.md) — installation and first walkthrough
- [User Guide](user-guide.md) — full coverage of all usage patterns
- [API Reference](api-reference.md) — auto-generated reference for every public symbol

# PEPScript

**PEPScript** is a Python library for programmatically reading, editing, and serializing [PEP 723](https://peps.python.org/pep-0723/) inline script metadata.

## Key features

|                                 |                                                                                                                                                            |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Zero dependencies**   | Stdlib only — no `packaging`, no `tomllib` backport.                                                                                                       |
| **Strict by default**           | Metadata is validated on parse ([PEP 508](https://peps.python.org/pep-0508/) + [PEP 440](https://peps.python.org/pep-0440/)); opt out with `strict=False`. |
| **Safe context manager**        | Auto-saves on clean exit; rolls back all in-memory edits on exception.                                                                                     |
| **Deterministic serialization** | The `# /// script` block is fully regenerated on save — sorted keys, consistent formatting — while your source code is preserved exactly.                  |
| **Typed API**                   | All models are `@dataclass(slots=True)` with full type hints and a `py.typed` marker.                                                                      |
| **Dynamic tool config**         | [`ToolConfig`][pepscript.ToolConfig] supports attribute access (`node.ruff`) and item access (`node["my-tool"]`) for arbitrary `[tool.*]` sections.        |

## Quick examples

### Simple usage

Most (read-only) use cases can use this simple pattern:

```python
from pepscript import PEPScript

script = PEPScript("/path/to/script.py")
for dep in script.meta.dependencies:
    print(dep)
```

### Advanced usage

Use the provided context manager to enter "edit mode" with automatic persistence / recovery. This example auto-saves on clean exit and rolls back changes otherwise:

```python
from pepscript import PEPScript

with PEPScript("script.py") as script:
    script.meta.add_dependency("requests>=2.31")
    script.meta.set_requires_python(">=3.12")
```

That's it — PEPScript handles creating the `# /// script` block if it doesn't exist, serializing the TOML, and writing it back to disk.

## Next steps

- **[Getting Started](getting-started.md)**

    Install PEPScript and follow the first walkthrough.

- **[User Guide](user-guide.md)**

    Full coverage of all usage patterns and API behaviours.

- **[API Reference](api-reference.md)**

    Auto-generated reference for every public class, function, and exception.

- **[Changelog](changelog.md)**

    Release history and what changed in each version.


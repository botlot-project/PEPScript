# User Guide

## Reading metadata from a file

Open a script with [`PEPScript(path)`][pepscript.PEPScript]. After construction, `script.meta` is
always a [`PEPMetadata`][pepscript.PEPMetadata] instance. Use [`script.has_metadata`][pepscript.PEPScript.has_metadata]
to check whether a `# /// script` block was actually present in the file.

```python
from pepscript import PEPScript

script = PEPScript("my_script.py")

if script.has_metadata:
    print(script.meta.requires_python)  # e.g. ">=3.12"
    print(script.meta.dependencies)     # e.g. ["requests>=2.31"]
```

`script.file` is a typed [`ScriptFileInfo`][pepscript.ScriptFileInfo] dataclass — not a live file handle:

```python
print(script.file.path)      # PosixPath("my_script.py")
print(script.file.name)      # "my_script"
print(script.file.filename)  # "my_script.py"
print(script.file.suffix)    # ".py"
print(script.file.encoding)  # "utf-8"
```

## Editing and saving

### Context manager

[`PEPScript`][pepscript.PEPScript] is a context manager that provides automatic save/rollback semantics:

- **Clean exit** — [`save()`][pepscript.PEPScript.save] is called automatically (file-backed scripts only).
- **Exception** — all in-memory edits are discarded; the pre-enter state is restored.

```python
with PEPScript("my_script.py") as script:
    script.meta.add_dependency("rich>=13.0")
# save() called automatically on clean exit
```

!!! note
    For in-memory scripts created with [`from_source()`][pepscript.PEPScript.from_source], auto-save is
    skipped on clean exit (no file path to write to), but rollback on exception still applies.

Only `meta` and the internal block offsets are snapshotted at context manager entry — the full
source text is not copied — so this is efficient even for large files.

### `save` and `save_as`

[`save()`][pepscript.PEPScript.save] writes to the original file path and calls
[`reload()`][pepscript.PEPScript.reload] so the in-memory state reflects the saved file.

[`save_as(path)`][pepscript.PEPScript.save_as] writes to an arbitrary path, updates `self.path`, and calls
[`reload()`][pepscript.PEPScript.reload]:

```python
script.save_as("output/my_script.py")
# script.path is now "output/my_script.py"
```

## Adding and removing dependencies

```python
script.meta.add_dependency("requests>=2.31")   # no-op if already present (exact match)
script.meta.add_dependency("rich>=13.0")

script.meta.remove_dependency("rich>=13.0")    # no-op if not found (exact match)
```

!!! warning "Exact string matching"
    Matching is **exact string comparison** — `"requests>=2.31"` and
    `"requests >= 2.31"` are treated as different entries.

## Parsing from a source string

Use [`parse_script`][pepscript.parse_script] when you already have source code in memory:

```python
from pepscript import parse_script

source = """\
# /// script
# dependencies = ["httpx>=0.27"]
# requires-python = ">=3.12"
# ///
import httpx
"""

script = parse_script(source)
```

An in-memory script has `script.path = None`. Calling [`save()`][pepscript.PEPScript.save] raises
[`SaveError`][pepscript.SaveError]. Use [`save_as(path)`][pepscript.PEPScript.save_as] to write it to disk.

## Accessing tool configuration

`[tool.*]` sections in the metadata TOML are exposed via `script.meta.config.tool`,
which is a [`ToolConfig`][pepscript.ToolConfig]. It supports both **attribute access** (for Python-friendly
keys) and **item access** (for hyphenated or otherwise non-identifier keys):

```python
# Given:
# [tool.ruff]
# line-length = 88
# [tool.my-tool]
# enabled = true

node = script.meta.config.tool

# Attribute access
print(node.ruff.line_length)   # 88

# Item access (required for hyphenated keys)
print(node["ruff"]["line-length"])  # 88
print(node["my-tool"]["enabled"])   # True
```

!!! tip
    Prefer item access (`node["ruff"]["line-length"]`) over attribute access for keys that
    contain hyphens — hyphens are not valid Python identifiers, so attribute access will
    silently convert them to underscores.

## Modifying tool configuration

```python
tool = script.meta.config.tool

# Set a value
tool["ruff"] = {"line-length": 100}

# Or use attribute assignment for simple keys
tool.ruff = {"line-length": 100}

# Nested update
tool["ruff"].update({"select": ["E", "F"]})

# Convert back to a plain dict
plain = tool.to_dict()
```

[`ToolConfig.setdefault`][pepscript.ToolConfig.setdefault] mirrors `dict.setdefault`:

```python
tool.setdefault("ruff", {"line-length": 88})
```

## Validating metadata

By default, [`PEPScript(path)`][pepscript.PEPScript] validates metadata immediately after parsing
(`strict=True`). Disable this for performance-sensitive or exploratory use:

```python
script = PEPScript("my_script.py", strict=False)
```

Run validation on demand with [`script.validate()`][pepscript.PEPScript.validate]:

```python
from pepscript import MetadataValidationError

try:
    script.validate()
except MetadataValidationError as exc:
    print(exc)
```

[`validate()`][pepscript.PEPScript.validate] is a no-op when `script.has_metadata` is `False` and `meta` is empty. Validation covers:

- **Structure** — correct types for all metadata fields
- **[PEP 508](https://peps.python.org/pep-0508/)** — each dependency specifier is checked for a valid name, extras,
  version operators (e.g. `>=`, `~=`, `===`), and environment marker variables
- **[PEP 440](https://peps.python.org/pep-0440/)** — `requires-python` must use valid version specifier syntax

!!! note
    All checks are regex-based — no `packaging` dependency is required.

## Reloading from disk

[`reload()`][pepscript.PEPScript.reload] discards all in-memory edits and re-reads the file from disk:

```python
script.reload()  # reverts to the saved state
```

For in-memory scripts (`path=None`), [`reload()`][pepscript.PEPScript.reload] re-parses `self.source` in place.

## Serialization behaviour

[`to_source()`][pepscript.PEPScript.to_source] returns the fully serialized source text without writing to disk:

```python
text = script.to_source()
print(text)
```

Serialization guarantees:

- The `# /// script` block is **fully regenerated** — keys are sorted,
  formatting is consistent (one space after `#`).
- Everything **outside** the metadata block is preserved byte-for-byte.
- If no block existed before [`save()`][pepscript.PEPScript.save], a new one is prepended.

## Exception handling

| Exception | When raised |
|---|---|
| [`PEPScriptError`][pepscript.PEPScriptError] | Base class — catch this to handle any PEPScript error |
| [`FileLoadError`][pepscript.FileLoadError] | The script file cannot be read (wraps `OSError`) |
| [`DuplicateMetadataBlockError`][pepscript.DuplicateMetadataBlockError] | More than one `# /// script` block found |
| [`MetadataParseError`][pepscript.MetadataParseError] | The embedded TOML is malformed |
| [`MetadataValidationError`][pepscript.MetadataValidationError] | Metadata fails structural validation |
| [`SaveError`][pepscript.SaveError] | The file cannot be written, or `save()` called on an in-memory script |

```python
from pepscript import (
    PEPScriptError,
    FileLoadError,
    MetadataValidationError,
    SaveError,
)

try:
    with PEPScript("script.py") as script:
        script.save()
except FileLoadError as exc:
    print(f"Could not read file: {exc}")
except MetadataValidationError as exc:
    print(f"Invalid metadata: {exc}")
except SaveError as exc:
    print(f"Could not write file: {exc}")
except PEPScriptError as exc:
    print(f"Unexpected PEPScript error: {exc}")
```

!!! tip "Catch the base class for broad coverage"
    All PEPScript exceptions inherit from [`PEPScriptError`][pepscript.PEPScriptError], so a single
    `except PEPScriptError` will catch anything the library raises.

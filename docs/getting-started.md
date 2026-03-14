# Getting Started

## Requirements

- Python **3.12** or newer

PEPScript has **zero runtime dependencies** — the standard library is all you need.

## Installation

=== "pip"

    <div data-termynal>
      <span data-ty="input">pip install pepscript</span>
      <span data-ty="progress"></span>
      <span data-ty>Successfully installed pepscript-0.1.0</span>
    </div>

=== "uv"

    <div data-termynal>
      <span data-ty="input">uv add pepscript</span>
      <span data-ty="progress"></span>
      <span data-ty>Installed pepscript==0.1.0</span>
    </div>

## First walkthrough: add a metadata block to a plain script

Start with a simple script that has no metadata:

```python
# hello.py
print("Hello, world!")
```

Use [`PEPScript`][pepscript.PEPScript] as a context manager to add a metadata block and save it back:

```python
from pepscript import PEPScript

with PEPScript("hello.py") as script:
    script.meta.add_dependency("rich>=13.0")
    script.meta.set_requires_python(">=3.12")
# save() is called automatically on clean exit
```

After running this, `hello.py` will look like:

```python
# /// script
# dependencies = ["rich>=13.0"]
# requires-python = ">=3.12"
# ///
print("Hello, world!")
```

!!! tip "Context manager = edit mode"
    Inside a `with` block, [`save()`][pepscript.PEPScript.save] is called automatically on a clean exit. If an exception propagates out, all in-memory edits are discarded and the file is left untouched.

## Reading existing metadata

```python
from pepscript import PEPScript

with PEPScript("hello.py") as script:
    if script.has_metadata:
        print(script.meta.requires_python)   # ">=3.12"
        print(script.meta.dependencies)      # ["rich>=13.0"]
```

[`script.file`][pepscript.ScriptFileInfo] gives you typed file metadata (name, path, encoding, …):

```python
print(script.file.name)      # "hello"
print(script.file.filename)  # "hello.py"
```

## Parsing from a string

For cases where you have source code in memory rather than on disk, use
[`parse_script`][pepscript.parse_script]:

```python
from pepscript import parse_script

source = """\
# /// script
# dependencies = ["httpx"]
# requires-python = ">=3.12"
# ///
import httpx
"""

script = parse_script(source)
print(script.meta.dependencies)  # ["httpx"]
```

!!! warning "In-memory scripts cannot be saved in place"
    An in-memory script has no associated file path. Calling [`save()`][pepscript.PEPScript.save] on it will
    raise [`SaveError`][pepscript.SaveError] — use [`save_as(path)`][pepscript.PEPScript.save_as] to write it to disk first.

## Next steps

- [User Guide](user-guide.md) — full coverage of all usage patterns
- [API Reference](api-reference.md) — complete symbol reference

# Getting Started

## Requirements

- Python **3.12** or newer

PEPScript has **zero runtime dependencies** — the standard library is all you need.

## Installation

```bash
pip install pepscript
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add pepscript
```

## First walkthrough: add a metadata block to a plain script

Start with a simple script that has no metadata:

```python
# hello.py
print("Hello, world!")
```

Use PEPScript to add a metadata block and save it back:

```python
from pepscript import PEPScript

with PEPScript("hello.py") as script:
    meta = script.ensure_meta()          # creates an empty block if absent
    meta.add_dependency("rich>=13.0")
    meta.set_requires_python(">=3.12")
    script.save()
```

After running this, `hello.py` will look like:

```python
# /// script
# dependencies = ["rich>=13.0"]
# requires-python = ">=3.12"
# ///
print("Hello, world!")
```

## Reading existing metadata

```python
from pepscript import PEPScript

with PEPScript("hello.py") as script:
    if script.meta:
        print(script.meta.requires_python)   # ">=3.12"
        print(script.meta.dependencies)      # ["rich>=13.0"]
```

`script.file` gives you typed file metadata (name, path, encoding, …):

```python
print(script.file.name)      # "hello"
print(script.file.filename)  # "hello.py"
```

## Parsing from a string

For cases where you have source code in memory rather than on disk, use
`parse_script`:

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

An in-memory script has no associated file path. Calling `save()` on it will
raise a `SaveError` — use `save_as(path)` to write it to disk first.

## Next steps

- [User Guide](user-guide.md) — full coverage of all usage patterns
- [API Reference](api-reference.md) — complete symbol reference

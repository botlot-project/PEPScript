# pepscript

A typed Python library for working with [PEP 723](https://peps.python.org/pep-0723/) inline script metadata. Parse, edit, validate, and serialize metadata blocks programmatically — without being a script runner.

- Zero runtime dependencies (stdlib only)
- Python 3.12+
- Full type hints with `py.typed`

## Installation

```bash
pip install pepscript
```

## Usage

### Read metadata from a script

```python
from pepscript import PEPScript

script = PEPScript("my_script.py")
if script.meta:
    print(script.meta.dependencies)
    print(script.meta.requires_python)
```

### Edit and save

```python
from pepscript import PEPScript

with PEPScript("my_script.py") as script:
    meta = script.ensure_meta()
    meta.add_dependency("httpx>=0.27")
    meta.set_requires_python(">=3.12")
    script.save()
```

### Parse from a string

```python
from pepscript import parse_script

script = parse_script("""\
# /// script
# dependencies = ["requests>=2.0"]
# requires-python = ">=3.12"
# ///
print("hello")
""")
print(script.meta.dependencies)  # ['requests>=2.0']
```

### Access tool configuration

```python
from pepscript import PEPScript

script = PEPScript("my_script.py")
if script.meta:
    # Attribute access
    line_length = script.meta.config.tool.ruff.line_length
    # Item access (for keys with hyphens)
    setting = script.meta.config.tool["my-tool"]["some-setting"]
```

### Validate metadata

```python
from pepscript import PEPScript, MetadataValidationError

script = PEPScript("my_script.py", strict=False)
try:
    script.validate()
except MetadataValidationError as e:
    print(f"Invalid metadata: {e}")
```

## License

MIT

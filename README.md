# PEPScript

[![CI](https://github.com/botlot-project/PEPscript/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/botlot-project/PEPscript/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pepscript)](https://pypi.org/project/pepscript/)
[![Python](https://img.shields.io/pypi/pyversions/pepscript)](https://pypi.org/project/pepscript/)
[![License](https://img.shields.io/pypi/l/pepscript)](https://github.com/botlot-project/PEPscript/blob/main/LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/botlot-project/PEPscript)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://botlot-project.github.io/PEPscript/)

A Python library for parsing, validating, editing, and saving [PEP 723](https://peps.python.org/pep-0723/) inline script metadata through a typed API.

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
if script.has_metadata:
    print(script.meta.dependencies)
    print(script.meta.requires_python)
```

### Edit and save

```python
from pepscript import PEPScript

with PEPScript("my_script.py") as script:
    script.meta.add_dependency("httpx>=0.27")
    script.meta.set_requires_python(">=3.12")
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
if script.has_metadata:
    # Attribute access
    ruff = script.meta.config.tool.ruff
    # Item access (for keys with hyphens)
    line_length = ruff["line-length"]
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

## Contributing

### Setup

```bash
uv sync
```

### Running checks

```bash
uv run pytest              # Tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run ty check .          # Type check
```

### Versioning and releases

This project uses [Semantic Versioning](https://semver.org/). The version is set in `pyproject.toml`.
Release notes are generated automatically from [Conventional Commits](https://www.conventionalcommits.org/) when a version tag is pushed.

To release:

1. Update `version` in `pyproject.toml`
2. Tag and push:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org/) (`fix:`, `feat:`, `feat!:` for breaking changes).

## License

MIT

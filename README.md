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

### Collect structured diagnostics

```python
from pepscript import PEPScript

script = PEPScript("my_script.py", strict=False)
for diagnostic in script.collect_diagnostics():
    print(diagnostic.code, diagnostic.message, diagnostic.line, diagnostic.column)
```

`collect_diagnostics()` validates by default, even if the script was loaded with `strict=False`.
Pass `strict=False` to skip validation explicitly.

### Batch scan a repository

```python
from pepscript import iter_scan_scripts

for result in iter_scan_scripts(".", include=("**/*.py",)):
    print(result.path, result.status, len(result.diagnostics))
```

Unreadable or undecodable files are reported as `invalid` results, and excluded
directories are skipped before traversal.

### Replace dependencies by package name

```python
from pepscript import PEPScript

with PEPScript("my_script.py") as script:
    script.meta.replace_dependency_by_name("requests>=2.32")
    script.meta.remove_dependency_by_name("urllib3")
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
2. Push your changes and merge them into `main`
3. Wait for the `CI` workflow on `main` to pass
4. Tag the merged commit on `main` and push the tag:
   ```bash
   git checkout main
   git pull origin main
   git tag v0.1.2
   git push origin v0.1.2
   ```

Pushing the tag triggers the release workflow, which builds the package, publishes it to PyPI, generates release notes with `git-cliff`, and creates the GitHub release.

Commit messages should follow [Conventional Commits](https://www.conventionalcommits.org/) (`fix:`, `feat:`, `feat!:` for breaking changes).

## License

MIT

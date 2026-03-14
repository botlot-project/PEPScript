# Changelog

## Unreleased

### Bug Fixes

- Reject trailing garbage between extras and @ in URL dependencies
- Make ScriptFileInfo.name return stem, not duplicate of filename
- Guard __exit__ against missing snapshot and failed save()
- Collapse wrapped docstring Returns descriptions to single lines
- Replace broken content tabs with plain code blocks, use list-style docstring sections
- Remove stale type: ignore and tighten None guard in test
- Correct validation error message, remove dead code, improve type safety

### Documentation

- Update description, add docs badge, rename node to tools in examples
- Add CI, PyPI, Python version, and license badges to README
- Update all references to validation scope for PEP 508/440 support
- Include root CHANGELOG.md in docs instead of duplicating it
- Add documentation site pages
- Add mkdocs.yml with material theme and mkdocstrings
- Add missing docstrings to public API
- Fix stale exception name and build backend in project docs
- Add contributing section to README
- Add release artifacts and fix project metadata for v0.1.0
- Add AGENTS.md
- Add project plan

### Features

- Add __contains__, __bool__, and __repr__ to ToolConfig
- Context manager auto-saves on clean exit and rolls back on exception
- Add PEP 508 dependency and PEP 440 requires-python validation
- Export all exception types from public API

### Miscellaneous

- Remove Termynal — replace animated terminals with plain code blocks
- Add prek pre-commit hooks for ruff lint and format
- Update repo URLs to botlot-project org
- Add pytest-cov to dev dependencies
- Replace MkDocs with Zensical
- Update uv.lock for mkdocstrings-python
- Add mkdocstrings-python to dev dependencies
- Add mkdocs commands to CLAUDE.md, gitignore site/
- Add mkdocs, mkdocs-material, and mkdocstrings to dev dependencies
- Remove PLAN.md
- Initial commit

### Refactor

- Deduplicate return statement in parse_source
- Annotate error helpers as NoReturn, remove unreachable code
- Rename PEPMetadata→Metadata, PEPConfigRoot→ConfigRoot
- Remove ensure_meta(), make script.meta always non-None
- Rename ConfigNode to ToolConfig
- Rename PepScriptError to PEPScriptError, use PEPScript in prose

### Testing

- Add URL dependency with trailing garbage before @ to invalid cases
- Add strict=False, save failure, parse_script, and file info tests
- Add Metadata.is_empty tests for each field independently
- Add ToolConfig __contains__, __bool__, and __repr__ tests
- Achieve 100% coverage for all public API edge cases
- Improve coverage from 88% to 98%
- Add serialization, rewrite, and round-trip tests

# API Reference

## PEPScript

The main entry point. Wraps a PEP 723 script file (or in-memory source) and exposes
typed access to its metadata. See the [User Guide](user-guide.md) for usage patterns.

::: pepscript.PEPScript
    options:
      members:
        - __init__
        - from_source
        - ensure_meta
        - validate
        - reload
        - to_source
        - save
        - save_as
        - __enter__
        - __exit__

## Convenience functions

Thin wrappers around [`PEPScript`][pepscript.PEPScript] for common one-liner usage.

::: pepscript.parse_file

::: pepscript.parse_script

## Data models

Typed, slot-based dataclasses that represent parsed PEP 723 metadata.
See [Reading metadata](user-guide.md#reading-metadata-from-a-file) and
[Tool configuration](user-guide.md#accessing-tool-configuration) in the User Guide.

::: pepscript.PEPMetadata

::: pepscript.PEPConfigRoot

::: pepscript.ToolConfig

::: pepscript.ScriptFileInfo

## Exceptions

All exceptions inherit from [`PEPScriptError`][pepscript.PEPScriptError].
See [Exception handling](user-guide.md#exception-handling) in the User Guide.

::: pepscript.PEPScriptError
    options:
      show_source: false

::: pepscript.FileLoadError
    options:
      show_source: false

::: pepscript.DuplicateMetadataBlockError
    options:
      show_source: false

::: pepscript.MetadataParseError
    options:
      show_source: false

::: pepscript.MetadataValidationError
    options:
      show_source: false

::: pepscript.SaveError
    options:
      show_source: false

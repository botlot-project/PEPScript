# API Reference

## PEPScript

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

::: pepscript.parse_file

::: pepscript.parse_script

## Data models

::: pepscript.PEPMetadata

::: pepscript.PEPConfigRoot

::: pepscript.ConfigNode

::: pepscript.ScriptFileInfo

## Exceptions

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

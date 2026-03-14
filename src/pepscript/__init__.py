"""Public API for PEPScript."""

from .config import ToolConfig
from .exceptions import (
    DuplicateMetadataBlockError,
    FileLoadError,
    MetadataParseError,
    MetadataValidationError,
    PEPScriptError,
    SaveError,
)
from .models import ConfigRoot, Metadata, ScriptFileInfo
from .script import PEPScript, parse_file, parse_script

__all__ = [
    "ToolConfig",
    "DuplicateMetadataBlockError",
    "FileLoadError",
    "MetadataParseError",
    "MetadataValidationError",
    "ConfigRoot",
    "Metadata",
    "PEPScript",
    "PEPScriptError",
    "SaveError",
    "ScriptFileInfo",
    "parse_file",
    "parse_script",
]

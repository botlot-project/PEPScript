"""Public API for PEPScript."""

from .config import ToolConfig
from .diagnostics import Diagnostic
from .exceptions import (
    DuplicateMetadataBlockError,
    FileLoadError,
    MetadataParseError,
    MetadataValidationError,
    PEPScriptError,
    SaveError,
)
from .models import ConfigRoot, Metadata, ScriptFileInfo
from .scan import ScanResult, iter_scan_scripts, scan_scripts
from .script import PEPScript, parse_file, parse_script

__all__ = [
    "Diagnostic",
    "ToolConfig",
    "DuplicateMetadataBlockError",
    "FileLoadError",
    "MetadataParseError",
    "MetadataValidationError",
    "ConfigRoot",
    "Metadata",
    "PEPScript",
    "PEPScriptError",
    "ScanResult",
    "SaveError",
    "ScriptFileInfo",
    "iter_scan_scripts",
    "parse_file",
    "parse_script",
    "scan_scripts",
]

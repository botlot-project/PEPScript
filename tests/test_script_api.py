from __future__ import annotations

from pathlib import Path

import pytest

from pepscript import PEPScript, parse_script
from pepscript.exceptions import MetadataValidationError, SaveError


def test_save_replaces_block_and_preserves_non_metadata_code(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        """# /// script
# dependencies = ["requests>=2.0"]
# requires-python = ">=3.12"
# [tool.botlot]
# enabled = true
# ///
print("keep me")
""",
        encoding="utf-8",
    )

    script = PEPScript(path)
    assert script.has_metadata
    script.meta.add_dependency("httpx>=0.27")
    script.save()

    saved = path.read_text(encoding="utf-8")
    assert 'print("keep me")\n' in saved
    assert 'dependencies = ["requests>=2.0", "httpx>=0.27"]' in saved
    assert 'requires-python = ">=3.12"' in saved
    assert "[tool.botlot]" in saved


def test_save_preserves_crlf_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_bytes(
        b'# /// script\r\n# dependencies = ["httpx"]\r\n# ///\r\nprint("hello")\r\n'
    )

    script = PEPScript(path)
    script.meta.add_dependency("rich")
    script.save()

    saved = path.read_bytes()
    assert b"\r\n" in saved
    assert b"\n" not in saved.replace(b"\r\n", b"")


def test_meta_edit_on_plain_script_inserts_new_block(tmp_path: Path) -> None:
    path = tmp_path / "plain.py"
    path.write_text(
        """#!/usr/bin/env python3
print("hello")
""",
        encoding="utf-8",
    )

    script = PEPScript(path)
    assert not script.has_metadata
    script.meta.set_requires_python(">=3.12")
    script.meta.add_dependency("httpx>=0.27")
    script.save()

    saved = path.read_text(encoding="utf-8")
    assert saved.startswith("#!/usr/bin/env python3\n# /// script\n")
    assert '# requires-python = ">=3.12"' in saved
    assert '# dependencies = ["httpx>=0.27"]' in saved
    assert 'print("hello")\n' in saved


def test_plain_script_save_does_not_inject_empty_block(tmp_path: Path) -> None:
    path = tmp_path / "plain.py"
    path.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(path)
    assert not script.has_metadata
    script.save()  # nothing added — no block should appear

    assert "# /// script" not in path.read_text(encoding="utf-8")


def test_plain_script_save_does_not_inject_empty_tool_tables(tmp_path: Path) -> None:
    path = tmp_path / "plain.py"
    path.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(path)
    script.meta.config.tool["ruff"] = {}
    script.save()

    assert "# /// script" not in path.read_text(encoding="utf-8")


def test_save_removes_block_when_metadata_is_cleared(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        '# /// script\n# dependencies = ["httpx"]\n# requires-python = ">=3.12"\n# ///\nprint("hello")\n',
        encoding="utf-8",
    )

    script = PEPScript(path)
    script.meta.dependencies.clear()
    script.meta.requires_python = None
    script.save()

    assert not script.has_metadata
    assert path.read_text(encoding="utf-8") == 'print("hello")\n'


def test_save_as_writes_new_file_and_updates_path(tmp_path: Path) -> None:
    src = tmp_path / "source.py"
    dst = tmp_path / "copy.py"
    src.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(src)
    script.meta.add_dependency("rich>=13.0")
    script.save_as(dst)

    assert dst.exists()
    assert script.path == dst
    assert script.file is not None
    assert script.file.path == dst


def test_reload_refreshes_from_disk(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        """# /// script
# dependencies = ["httpx>=0.27"]
# ///
print("hello")
""",
        encoding="utf-8",
    )

    script = PEPScript(path)
    assert script.has_metadata
    assert script.meta.dependencies == ["httpx>=0.27"]

    path.write_text(
        """# /// script
# dependencies = ["rich>=13.0"]
# ///
print("hello")
""",
        encoding="utf-8",
    )
    script.reload()

    assert script.has_metadata
    assert script.meta.dependencies == ["rich>=13.0"]


def test_context_manager_auto_saves_on_clean_exit(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        """# /// script
# dependencies = ["httpx"]
# ///
print("hello")
""",
        encoding="utf-8",
    )

    with PEPScript(path) as script:
        script.meta.add_dependency("rich")

    saved = path.read_text(encoding="utf-8")
    assert "rich" in saved


def test_context_manager_rolls_back_on_exception(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        """# /// script
# dependencies = ["httpx"]
# ///
print("hello")
""",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError):
        with PEPScript(path) as script:
            script.meta.add_dependency("rich")
            raise RuntimeError("something went wrong")

    # disk is untouched
    assert "rich" not in path.read_text(encoding="utf-8")
    # in-memory state is also rolled back
    assert "rich" not in script.meta.dependencies


def test_context_manager_in_memory_no_save_on_clean_exit() -> None:
    script = PEPScript.from_source(
        "# /// script\n# dependencies = []\n# ///\nprint('hi')\n"
    )
    with script:
        script.meta.add_dependency("rich")

    # no path, so no save — but edits remain in memory
    assert script.has_metadata
    assert "rich" in script.meta.dependencies


def test_context_manager_in_memory_rolls_back_on_exception() -> None:
    script = PEPScript.from_source(
        "# /// script\n# dependencies = []\n# ///\nprint('hi')\n"
    )

    with pytest.raises(ValueError):
        with script:
            script.meta.add_dependency("rich")
            raise ValueError("oops")

    assert "rich" not in script.meta.dependencies


def test_save_in_memory_script_raises() -> None:
    script = PEPScript.from_source('print("hello")\n')
    with pytest.raises(SaveError):
        script.save()


def test_from_source_without_metadata() -> None:
    script = PEPScript.from_source('print("hello")\n')
    assert not script.has_metadata
    assert script.meta.is_empty
    assert script.path is None
    assert script.file is None


def test_to_source_without_saving(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(path)
    script.meta.add_dependency("httpx")
    result = script.to_source()

    assert "httpx" in result
    # Original file unchanged
    assert "httpx" not in path.read_text(encoding="utf-8")


def test_validate_method_passes_for_valid_metadata(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        '# /// script\n# dependencies = ["httpx>=0.27"]\n# ///\n', encoding="utf-8"
    )
    script = PEPScript(path)
    script.validate()  # should not raise


def test_validate_is_noop_for_plain_script(tmp_path: Path) -> None:
    path = tmp_path / "plain.py"
    path.write_text('print("hello")\n', encoding="utf-8")
    script = PEPScript(path)
    script.validate()  # no block, empty meta — should not raise


def test_reload_in_memory_rereparses_source() -> None:
    source = '# /// script\n# dependencies = ["httpx"]\n# ///\n'
    script = PEPScript.from_source(source)
    assert script.has_metadata
    script.meta.add_dependency("rich")
    assert "rich" in script.meta.dependencies
    script.reload()
    assert "rich" not in script.meta.dependencies


def test_parse_file_convenience_function(tmp_path: Path) -> None:
    from pepscript import parse_file

    path = tmp_path / "script.py"
    path.write_text(
        '# /// script\n# dependencies = ["httpx"]\n# ///\n', encoding="utf-8"
    )
    script = parse_file(path)
    assert script.has_metadata
    assert script.meta.dependencies == ["httpx"]


def test_constructor_strict_false_skips_validation(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        '# /// script\n# dependencies = [">>invalid"]\n# ///\n',
        encoding="utf-8",
    )
    script = PEPScript(path, strict=False)
    assert script.meta.dependencies == [">>invalid"]


def test_save_validates_before_write_and_leaves_file_untouched(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    original = '# /// script\n# dependencies = ["httpx"]\n# ///\nprint("hello")\n'
    path.write_text(original, encoding="utf-8")

    script = PEPScript(path)
    script.meta.dependencies = [">>invalid"]

    with pytest.raises(MetadataValidationError):
        script.save()

    assert path.read_text(encoding="utf-8") == original


def test_save_strict_false_still_validates_before_write(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    original = 'print("hello")\n'
    path.write_text(original, encoding="utf-8")

    script = PEPScript(path, strict=False)
    script.meta.dependencies = [">>invalid"]

    with pytest.raises(MetadataValidationError):
        script.save()

    assert path.read_text(encoding="utf-8") == original


def test_save_as_validates_before_write_and_does_not_create_target(
    tmp_path: Path,
) -> None:
    src = tmp_path / "source.py"
    dst = tmp_path / "copy.py"
    src.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(src, strict=False)
    script.meta.dependencies = [">>invalid"]

    with pytest.raises(MetadataValidationError):
        script.save_as(dst)

    assert not dst.exists()
    assert script.path == src


def test_save_failure_in_context_manager_clears_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text(
        '# /// script\n# dependencies = ["httpx"]\n# ///\n', encoding="utf-8"
    )

    script = PEPScript(path)
    path.unlink()
    path.mkdir()  # make path a directory so save() fails

    with pytest.raises(SaveError):
        with script:
            script.meta.add_dependency("rich")

    assert script._snapshot is None


def test_parse_script_convenience_function() -> None:
    script = parse_script('# /// script\n# dependencies = ["httpx"]\n# ///\n')
    assert script.has_metadata


def test_collect_diagnostics_for_invalid_metadata_in_non_strict_mode() -> None:
    script = parse_script(
        '# /// script\n# dependencies = ["requests>>2.0"]\n# ///\n', strict=False
    )
    diagnostics = script.collect_diagnostics()
    assert diagnostics
    assert diagnostics[0].code.startswith("PSV")
    assert script.collect_diagnostics(strict=False) == []


def test_check_returns_false_for_invalid_metadata() -> None:
    script = parse_script(
        '# /// script\n# dependencies = ["requests>>2.0"]\n# ///\n', strict=False
    )
    assert not script.check()
    assert script.check(strict=False)


def test_collect_diagnostics_empty_plain_script_returns_empty() -> None:
    script = parse_script('print("hello")\n')
    assert script.collect_diagnostics() == []


def test_file_info_name_is_stem(tmp_path: Path) -> None:
    path = tmp_path / "my_script.py"
    path.write_text('print("hello")\n', encoding="utf-8")
    script = PEPScript(path)
    assert script.file is not None
    assert script.file.name == "my_script"
    assert script.file.filename == "my_script.py"

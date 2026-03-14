from __future__ import annotations

from pathlib import Path

import pytest

from pepscript import PEPScript
from pepscript.exceptions import SaveError


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
    assert script.meta is not None
    script.meta.add_dependency("httpx>=0.27")
    script.save()

    saved = path.read_text(encoding="utf-8")
    assert 'print("keep me")\n' in saved
    assert 'dependencies = ["requests>=2.0", "httpx>=0.27"]' in saved
    assert 'requires-python = ">=3.12"' in saved
    assert "[tool.botlot]" in saved


def test_ensure_meta_and_save_inserts_new_block(tmp_path: Path) -> None:
    path = tmp_path / "plain.py"
    path.write_text(
        """#!/usr/bin/env python3
print("hello")
""",
        encoding="utf-8",
    )

    script = PEPScript(path)
    meta = script.ensure_meta()
    meta.set_requires_python(">=3.12")
    meta.add_dependency("httpx>=0.27")
    script.save()

    saved = path.read_text(encoding="utf-8")
    assert saved.startswith("#!/usr/bin/env python3\n# /// script\n")
    assert '# requires-python = ">=3.12"' in saved
    assert '# dependencies = ["httpx>=0.27"]' in saved
    assert 'print("hello")\n' in saved


def test_save_as_writes_new_file_and_updates_path(tmp_path: Path) -> None:
    src = tmp_path / "source.py"
    dst = tmp_path / "copy.py"
    src.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(src)
    script.ensure_meta().add_dependency("rich>=13.0")
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
    assert script.meta is not None
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

    assert script.meta is not None
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
        script.ensure_meta().add_dependency("rich")

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
            script.ensure_meta().add_dependency("rich")
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
        script.ensure_meta().add_dependency("rich")

    # no path, so no save — but edits remain in memory
    assert script.meta is not None
    assert "rich" in script.meta.dependencies


def test_context_manager_in_memory_rolls_back_on_exception() -> None:
    script = PEPScript.from_source(
        "# /// script\n# dependencies = []\n# ///\nprint('hi')\n"
    )

    with pytest.raises(ValueError):
        with script:
            script.ensure_meta().add_dependency("rich")
            raise ValueError("oops")

    assert "rich" not in script.meta.dependencies


def test_save_in_memory_script_raises() -> None:
    script = PEPScript.from_source('print("hello")\n')
    with pytest.raises(SaveError):
        script.save()


def test_from_source_without_metadata() -> None:
    script = PEPScript.from_source('print("hello")\n')
    assert script.meta is None
    assert script.path is None
    assert script.file is None


def test_to_source_without_saving(tmp_path: Path) -> None:
    path = tmp_path / "script.py"
    path.write_text('print("hello")\n', encoding="utf-8")

    script = PEPScript(path)
    script.ensure_meta().add_dependency("httpx")
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


def test_reload_in_memory_rereparses_source() -> None:
    source = '# /// script\n# dependencies = ["httpx"]\n# ///\n'
    script = PEPScript.from_source(source)
    assert script.meta is not None
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
    assert script.meta is not None
    assert script.meta.dependencies == ["httpx"]

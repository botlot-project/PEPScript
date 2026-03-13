from __future__ import annotations

from pathlib import Path

from pepscript import PEPScript


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

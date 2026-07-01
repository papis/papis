"""Tests for papis.commands.mv."""

from __future__ import annotations

import logging
import os
import shutil
from typing import TYPE_CHECKING

import papis.database
import papis.document
import papis.tui.utils
from papis.commands.mv import cli
from papis.testing import PapisRunner, TemporaryLibrary

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

    from papis.database.base import Database


import pytest


def _doc_by_author(db: Database, author: str) -> papis.document.Document:
    """Find a document by author. Assumes unique match for simplicity."""
    return next(d for d in db.get_all_documents() if d["author"] == author)


def _setup_runner_db_doc() -> tuple[PapisRunner, Database, papis.document.Document]:
    """Return a runner, the current DB, and Turing's document."""
    db = papis.database.get()
    return PapisRunner(), db, _doc_by_author(db, "Turing, A. M.")


def _assert_moved(old_folder: str, expected_folder: str) -> None:
    """Assert the move completed correctly on disk and in the DB."""
    assert not os.path.exists(old_folder)
    assert os.path.exists(expected_folder)

    matches = [
        doc
        for doc in papis.database.get().get_all_documents()
        if doc.get_main_folder() == expected_folder
    ]
    assert len(matches) == 1
    assert matches[0].get_main_folder() == expected_folder


# ---------------------------------------------------------------------------
# Tests for cli()
# ---------------------------------------------------------------------------


def test_to_renames_folder(tmp_library: TemporaryLibrary) -> None:
    """--to renames the document folder."""
    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    result = cli_runner.invoke(
        cli, ["--to", "renamed-turing", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    expected = os.path.join(tmp_library.libdir, "renamed-turing")
    _assert_moved(old_folder, expected)


def test_to_with_formatpattern(tmp_library: TemporaryLibrary) -> None:
    """--to with a format pattern produces the expected folder."""
    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    result = cli_runner.invoke(
        cli, ["--to", "{doc[year]}", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    expected = os.path.join(tmp_library.libdir, "1937")
    _assert_moved(old_folder, expected)


def test_without_to_renames_to_default(tmp_library: TemporaryLibrary) -> None:
    """Without --to, the default folder name is used."""
    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder
    doc_id = doc["papis_id"]

    result = cli_runner.invoke(cli, ["Turing"], catch_exceptions=False)
    assert result.exit_code == 0, result.output

    assert not os.path.exists(old_folder)
    expected = os.path.join(tmp_library.libdir, doc_id)
    assert os.path.exists(expected)


def test_to_slugification_of_special_chars(tmp_library: TemporaryLibrary) -> None:
    """--to slugifies the target folder name."""
    cli_runner, _, doc = _setup_runner_db_doc()

    old_folder = doc.get_main_folder()
    assert old_folder

    result = cli_runner.invoke(
        cli, ["--to", "Rick Astley", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    expected = os.path.join(tmp_library.libdir, "rick-astley")
    _assert_moved(old_folder, expected)


def test_to_existing_dir_moves_into(tmp_library: TemporaryLibrary) -> None:
    """--to pointing to an existing directory moves into it."""
    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder
    old_basename = os.path.basename(old_folder)

    target_dir = os.path.join(tmp_library.libdir, "papers-archive")
    os.makedirs(target_dir)

    result = cli_runner.invoke(
        cli, ["--to", "papers-archive", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    expected = os.path.join(target_dir, old_basename)
    _assert_moved(old_folder, expected)


def test_to_same_folder_is_skipped(tmp_library: TemporaryLibrary) -> None:
    """Moving to the same folder is a no-op."""
    cli_runner, _, _ = _setup_runner_db_doc()

    # moving to this first, since the default folder name is something
    # that would be slugified, making renaming to the same name impossible
    result = cli_runner.invoke(
        cli, ["--to", "turing-folder", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    folder_path = os.path.join(tmp_library.libdir, "turing-folder")
    result = cli_runner.invoke(
        cli, ["--to", "turing-folder", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output
    assert os.path.exists(folder_path)


def test_to_existing_other_doc_folder_warns(
    tmp_library: TemporaryLibrary,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    """Moving to another doc folder warns about nesting."""
    caplog.set_level(logging.WARNING)
    cli_runner, db, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    # Find another doc (Krishnamurti) and pre-move it to a clean slugified name
    krish = next(d for d in db.get_all_documents() if d["author"] == "J. Krishnamurti")
    assert krish.get_main_folder()
    result = cli_runner.invoke(
        cli, ["--to", "krish-doc", "Krishnamurti"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    # Now try to move Turing into Krish's folder
    def mock_confirm(msg: str, **kwargs: object) -> bool:
        return True  # skip

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", mock_confirm)
        result = cli_runner.invoke(
            cli, ["--to", "krish-doc", "Turing"], catch_exceptions=False
        )
        assert result.exit_code == 0, result.output

    warning_messages = [r.message for r in caplog.records]
    assert any("would nest inside another document" in msg for msg in warning_messages)
    assert os.path.exists(old_folder)


def test_to_target_already_exists_warns(
    tmp_library: TemporaryLibrary,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    """Disk conflict warns."""
    caplog.set_level(logging.WARNING)
    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder
    old_basename = os.path.basename(old_folder)

    # Pre-create target dir with a subfolder matching the doc's name
    target_dir = os.path.join(tmp_library.libdir, "target-dir")
    os.makedirs(os.path.join(target_dir, old_basename))

    def mock_confirm(msg: str, **kwargs: object) -> bool:
        return True  # skip

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", mock_confirm)
        result = cli_runner.invoke(
            cli, ["--to", "target-dir", "Turing"], catch_exceptions=False
        )
        assert result.exit_code == 0, result.output

    warning_messages = [r.message for r in caplog.records]
    assert any("target already exists" in msg for msg in warning_messages)


@pytest.mark.skipif(
    os.environ.get("PAPIS_DATABASE_BACKEND") == "whoosh",
    reason="Whoosh cannot query documents whose folders have been deleted",
)
def test_source_folder_missing_warns(
    tmp_library: TemporaryLibrary, caplog: pytest.LogCaptureFixture
) -> None:
    """Missing source folder warns."""
    caplog.set_level(logging.WARNING)
    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder
    shutil.rmtree(old_folder)

    result = cli_runner.invoke(
        cli, ["--to", "target", "Turing"], catch_exceptions=False
    )
    assert result.exit_code == 0, result.output

    warning_messages = [r.message for r in caplog.records]
    assert any("does not exist on disk" in msg for msg in warning_messages)


def test_batch_skips_confirm_with_warnings(
    tmp_library: TemporaryLibrary,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    """Batch mode skips confirm prompts, warns, and moves valid docs."""
    caplog.set_level(logging.WARNING)
    cli_runner, db, _ = _setup_runner_db_doc()

    # there are two test_author docs, we delete one to trigger a warning
    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2
    warned_doc = docs[0]
    valid_doc = docs[1]
    warned_folder = warned_doc.get_main_folder()
    assert warned_folder
    valid_old_folder = valid_doc.get_main_folder()
    assert valid_old_folder
    valid_id = valid_doc["papis_id"]
    shutil.rmtree(warned_folder)

    confirm_called = False

    def track_confirm(*args: object, **kwargs: object) -> bool:
        nonlocal confirm_called
        confirm_called = True
        return True

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", track_confirm)
        result = cli_runner.invoke(
            cli, ["--batch", "--all", "test_author"], catch_exceptions=False
        )
        assert result.exit_code == 0, result.output

    assert not confirm_called
    warning_messages = [r.message for r in caplog.records]
    assert len(warning_messages) == 1
    assert "source folder does not exist on disk" in warning_messages[0]

    # this works since that's the papis_id is the default folder name
    expected = os.path.join(tmp_library.libdir, valid_id)
    _assert_moved(valid_old_folder, expected)


def test_multiple_docs_moved(tmp_library: TemporaryLibrary) -> None:
    """Multiple docs moved into a directory each get their own subfolder."""
    cli_runner, db, _ = _setup_runner_db_doc()

    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2

    old_folders: list[str] = []
    for doc in docs:
        folder = doc.get_main_folder()
        assert folder is not None
        old_folders.append(folder)

    target_dir = os.path.join(tmp_library.libdir, "batch-target")
    os.makedirs(target_dir)

    result = cli_runner.invoke(
        cli,
        ["--to", "batch-target", "--all", "test_author"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    # Both docs moved into target dir
    for old_folder in old_folders:
        old_basename = os.path.basename(old_folder)
        expected = os.path.join(target_dir, old_basename)
        assert not os.path.exists(old_folder)
        assert os.path.exists(expected)


def test_no_documents_returns_early(
    tmp_library: TemporaryLibrary, caplog: pytest.LogCaptureFixture
) -> None:
    """No matching documents returns early with a warning."""
    caplog.set_level(logging.WARNING)
    cli_runner, _, _ = _setup_runner_db_doc()

    result = cli_runner.invoke(cli, ["nonexistent_author_xyz"], catch_exceptions=False)
    assert result.exit_code == 0

    warning_messages = [r.message for r in caplog.records]
    assert any("No documents retrieved" in msg for msg in warning_messages)


def test_selection_conflict_batch_warns_and_skips(
    tmp_library: TemporaryLibrary, caplog: pytest.LogCaptureFixture
) -> None:
    """Batch mode: selection conflicts trigger warnings and docs stay put."""
    caplog.set_level(logging.WARNING)
    cli_runner, db, _ = _setup_runner_db_doc()

    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2
    old_folders = [d.get_main_folder() for d in docs]

    result = cli_runner.invoke(
        cli,
        ["--batch", "--all", "--to", "same-target", "test_author"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    warning_messages = [r.message for r in caplog.records]
    for doc in docs:
        assert any(
            doc["title"] in msg and "duplicate target" in msg
            for msg in warning_messages
        )

    # Neither doc was moved
    for folder in old_folders:
        assert folder and os.path.exists(folder)


def test_selection_conflict_user_skips(
    tmp_library: TemporaryLibrary,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    """Non-batch: when user skips the conflicting docs, docs stay put."""
    caplog.set_level(logging.WARNING)
    cli_runner, db, _ = _setup_runner_db_doc()

    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2
    old_folders = [d.get_main_folder() for d in docs]

    def confirm_skip(msg: str, **kwargs: object) -> bool:
        return True  # skip

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", confirm_skip)
        result = cli_runner.invoke(
            cli,
            ["--all", "--to", "same-target", "test_author"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

    # Neither doc moved
    for folder in old_folders:
        assert folder and os.path.exists(folder)


def test_selection_conflict_user_renames(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
) -> None:
    """Non-batch: user chooses to rename, types valid names, docs move."""
    cli_runner, db, _ = _setup_runner_db_doc()

    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2

    old0 = docs[0].get_main_folder()
    old1 = docs[1].get_main_folder()
    assert old0 and old1

    # First confirm: don't skip. Then prompt for new names.
    prompt_count = 0
    new_names = ["doc-one", "doc-two"]

    def confirm_no_skip(msg: str, **kwargs: object) -> bool:
        return False  # don't skip

    def mock_prompt(msg: str, **kwargs: object) -> str:
        nonlocal prompt_count
        name = new_names[prompt_count]
        prompt_count += 1
        return name

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", confirm_no_skip)
        m.setattr(papis.tui.utils, "prompt", mock_prompt)
        result = cli_runner.invoke(
            cli,
            ["--all", "--to", "same-target", "test_author"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

    # Both docs moved to renamed folders
    assert not os.path.exists(old0)
    assert os.path.exists(os.path.join(tmp_library.libdir, "doc-one"))
    assert not os.path.exists(old1)
    assert os.path.exists(os.path.join(tmp_library.libdir, "doc-two"))


def test_selection_conflict_rename_loops_on_collision(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
) -> None:
    """Renamed target collides with existing path triggers reprompting."""
    cli_runner, db, _ = _setup_runner_db_doc()

    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2

    old0 = docs[0].get_main_folder()
    old1 = docs[1].get_main_folder()
    assert old0 and old1

    # Pre-create a folder that the rename will collide with
    os.makedirs(os.path.join(tmp_library.libdir, "existing-folder"))

    prompt_index = 0
    renames = ["existing-folder", "doc-one", "doc-two"]

    def confirm_no_skip(msg: str, **kwargs: object) -> bool:
        return False

    def mock_prompt(msg: str, **kwargs: object) -> str:
        nonlocal prompt_index
        name = renames[prompt_index]
        prompt_index += 1
        return name

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", confirm_no_skip)
        m.setattr(papis.tui.utils, "prompt", mock_prompt)
        result = cli_runner.invoke(
            cli,
            ["--all", "--to", "same-target", "test_author"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

    # doc1: first rename "existing-folder" collides → re-prompt → "doc-two"
    # doc2: "doc-one" is free → moved
    assert not os.path.exists(old0)
    assert os.path.exists(os.path.join(tmp_library.libdir, "doc-one"))
    assert not os.path.exists(old1)
    assert os.path.exists(os.path.join(tmp_library.libdir, "doc-two"))


def test_batch_continues_on_execution_error(
    tmp_library: TemporaryLibrary,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: MonkeyPatch,
) -> None:
    """Batch mode: one move fails mid-moving, the rest still move."""
    caplog.set_level(logging.WARNING)
    cli_runner, db, _ = _setup_runner_db_doc()

    docs = [d for d in db.get_all_documents() if d["author"] == "test_author"]
    assert len(docs) >= 2

    old0 = docs[0].get_main_folder()
    old1 = docs[1].get_main_folder()
    assert old0 and old1

    # Fail the first move only
    original_move = shutil.move
    call_count = 0

    def flaky_move(src: str, dst: str, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("Simulated error")
        return original_move(src, dst)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", lambda *a, **kw: True)
        m.setattr(shutil, "move", flaky_move)
        result = cli_runner.invoke(
            cli,
            ["--batch", "--all", "test_author"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output

    warning_messages = [r.message for r in caplog.records]
    assert any("Failed to move" in msg for msg in warning_messages)

    # First doc stays put, second moved
    assert os.path.exists(old0)
    assert not os.path.exists(old1)


def test_to_default_from_target_library(tmp_library: TemporaryLibrary) -> None:
    """The default folder pattern comes from the target library."""
    import papis.config

    cli_runner, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    # Set up a second library with a different add-folder-name
    target_lib_name = "target-lib"
    target_lib_dir = os.path.join(tmp_library.tmpdir, "target-lib")
    os.makedirs(target_lib_dir)
    papis.config.set("dir", target_lib_dir, section=target_lib_name)
    papis.config.set(
        "add-folder-name",
        "custom-{doc[year]}",
        section=target_lib_name,
    )

    result = cli_runner.invoke(
        cli,
        ["--target-library", target_lib_name, "Turing"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output

    # Doc moved out of source library
    assert not os.path.exists(old_folder)

    # Doc landed in target library with target library's folder pattern
    assert os.path.exists(os.path.join(target_lib_dir, "custom-1937"))


# ---------------------------------------------------------------------------
# Tests for run()
# ---------------------------------------------------------------------------


def test_creates_parent_directories(tmp_library: TemporaryLibrary) -> None:
    """Parent directories are created when needed."""
    from papis.commands.mv import run

    _, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    new_folder = os.path.join(tmp_library.libdir, "year", "2024", "papers")
    run(doc, new_folder, git=False)

    _assert_moved(old_folder, new_folder)


def test_move_preserves_source_on_failure(
    tmp_library: TemporaryLibrary, monkeypatch: MonkeyPatch
) -> None:
    """Source folder is preserved when the move fails."""
    from papis.commands.mv import run

    _, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    def failing_move(src: str | Path, dst: str | Path) -> Path:
        raise OSError("Simulated move failure")

    with monkeypatch.context() as m:
        m.setattr(shutil, "move", failing_move)
        try:
            run(doc, os.path.join(tmp_library.libdir, "new-folder"), git=False)
        except OSError:
            pass

    assert os.path.exists(old_folder)


@pytest.mark.skipif(
    not shutil.which("git"), reason="Test requires 'git' executable to be in the PATH"
)
@pytest.mark.library_setup(use_git=True)
def test_run_with_git_commits(tmp_library: TemporaryLibrary) -> None:
    """Git tracks the move when git=True."""
    import subprocess

    from papis.commands.mv import run

    _, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder

    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_library.libdir,
        capture_output=True,
        text=True,
        check=True,
    )
    commits_before = len(result.stdout.strip().split("\n"))

    new_folder = os.path.join(tmp_library.libdir, "moved-turing")
    run(doc, new_folder, git=True)

    assert not os.path.exists(old_folder)
    assert os.path.exists(new_folder)

    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_library.libdir,
        capture_output=True,
        text=True,
        check=True,
    )
    commits_after = len(result.stdout.strip().split("\n"))
    assert commits_after == commits_before + 1

    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=tmp_library.libdir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Move" in result.stdout
    assert "On Computable Numbers" in result.stdout


def test_raises_when_source_missing(tmp_library: TemporaryLibrary) -> None:
    """run() raises FileNotFoundError when source is missing."""
    from papis.commands.mv import run

    _, _, doc = _setup_runner_db_doc()
    old_folder = doc.get_main_folder()
    assert old_folder
    shutil.rmtree(old_folder)

    with pytest.raises(FileNotFoundError):
        run(doc, os.path.join(tmp_library.libdir, "new-folder"), git=False)


def test_raises_when_target_is_same_folder(tmp_library: TemporaryLibrary) -> None:
    """run() raises FileExistsError when target is the source folder."""
    from papis.commands.mv import run

    _, _, doc = _setup_runner_db_doc()
    same_folder = doc.get_main_folder()
    assert same_folder

    with pytest.raises(FileExistsError):
        run(doc, same_folder, git=False)


def test_raises_when_target_exists(tmp_library: TemporaryLibrary) -> None:
    """run() raises FileExistsError when target already exists."""
    from papis.commands.mv import run

    _, _, doc = _setup_runner_db_doc()

    new_folder = os.path.join(tmp_library.libdir, "already-exists")
    os.makedirs(new_folder)

    with pytest.raises(FileExistsError):
        run(doc, new_folder, git=False)

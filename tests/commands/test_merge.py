from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

import pytest

import papis.database
from papis.testing import PapisRunner, TemporaryLibrary

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

    from papis.document import Document


def put_file(doc: Document, name: str, content: str) -> str:
    """Add a file with *content* to *doc* and register it in its metadata."""
    folder = doc.get_main_folder()
    assert folder is not None
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as fd:
        fd.write(content)
    doc["files"] = [*doc.get("files", []), name]

    from papis.api import save_doc

    save_doc(doc)

    return path


def put_note(doc: Document, name: str, content: str) -> str:
    """Add a note with *content* to *doc* and register it as its ``notes``."""
    path = put_file(doc, name, content)
    doc["files"].remove(name)
    doc["notes"] = name

    from papis.api import save_doc

    save_doc(doc)

    return path


def fail(*args: Any, **kwargs: Any) -> Any:
    """Fail the test: batch mode must not prompt."""
    raise AssertionError("batch mode must not prompt")


def test_merge_run(tmp_library: TemporaryLibrary) -> None:
    """Picked files are added to the main document, which is left otherwise
    untouched; removing the second document is left to the caller."""
    from papis.commands.merge import run
    from papis.document import Document

    db = papis.database.get()
    (a,) = db.query_dict({"author": "turing"})
    (b,) = db.query_dict({"author": "krishnamurti"})

    a_folder = a.get_main_folder()
    b_folder = b.get_main_folder()
    assert a_folder is not None and b_folder is not None

    a_files = a.get_files()
    (b_file,) = b.get_files()

    changeset = Document(data={"title": "Merged"})
    changeset.set_folder(b_folder)
    changeset["files"] = [os.path.basename(b_file)]

    run(a, changeset)

    # NOTE: the files of the main document are never deleted by a merge
    for path in a_files:
        assert os.path.exists(path)

    copied = os.path.join(a_folder, os.path.basename(b_file))
    assert os.path.exists(copied)
    # NOTE: removing the second document is the caller's job
    assert os.path.exists(b_folder)

    assert a["title"] == "Merged"
    assert a["files"] == [
        *(os.path.basename(f) for f in a_files),
        os.path.basename(b_file),
    ]


def test_merge_run_same_filename(tmp_library: TemporaryLibrary) -> None:
    """A same-named file is renamed instead of overwriting the main file."""
    from papis.commands.merge import run
    from papis.document import Document

    db = papis.database.get()
    (a,) = db.query_dict({"author": "popper"})
    (b,) = db.query_dict({"author": "krishnamurti"})

    put_file(a, "paper.pdf", "keep")
    b_paper = put_file(b, "paper.pdf", "erase")

    b_folder = b.get_main_folder()
    assert b_folder is not None
    changeset = Document()
    changeset.set_folder(b_folder)
    changeset["files"] = [os.path.basename(b_paper)]

    run(a, changeset)

    a_folder = a.get_main_folder()
    assert a_folder is not None
    assert a["files"] == ["paper.pdf", "paper-a.pdf"]
    for name, content in [("paper.pdf", "keep"), ("paper-a.pdf", "erase")]:
        with open(os.path.join(a_folder, name), encoding="utf-8") as fd:
            assert fd.read() == content


def test_merge_run_empty_selection(tmp_library: TemporaryLibrary) -> None:
    """An empty selection adds no files and removes nothing."""
    from papis.commands.merge import run
    from papis.document import Document

    db = papis.database.get()
    (a,) = db.query_dict({"author": "krishnamurti"})

    (a_file,) = a.get_files()
    a_names_before = list(a["files"])

    run(a, Document())

    assert os.path.exists(a_file)
    assert a["files"] == a_names_before


def test_merge_run_notes(tmp_library: TemporaryLibrary) -> None:
    """The note file is added to the main document's notes."""
    from papis.commands.merge import run
    from papis.document import Document

    db = papis.database.get()
    (a,) = db.query_dict({"author": "popper"})
    (b,) = db.query_dict({"author": "krishnamurti"})

    b_note = put_note(b, "notes.md", "note")

    b_folder = b.get_main_folder()
    assert b_folder is not None
    changeset = Document()
    changeset.set_folder(b_folder)
    changeset["notes"] = os.path.basename(b_note)

    run(a, changeset)

    assert a["notes"] == "notes.md"
    a_folder = a.get_main_folder()
    assert a_folder is not None
    with open(os.path.join(a_folder, "notes.md"), encoding="utf-8") as fd:
        assert fd.read() == "note"


def test_merge_run_notes_copy_failure(
    tmp_library: TemporaryLibrary, monkeypatch: MonkeyPatch
) -> None:
    """A failed copy leaves the existing notes untouched and no temporary files
    behind."""
    import shutil

    from papis.commands.merge import run
    from papis.document import Document

    db = papis.database.get()
    (a,) = db.query_dict({"author": "popper"})
    (b,) = db.query_dict({"author": "krishnamurti"})

    put_note(a, "a-notes.md", "a note")
    b_note = put_note(b, "notes.md", "b note")

    b_folder = b.get_main_folder()
    assert b_folder is not None
    changeset = Document()
    changeset.set_folder(b_folder)
    changeset["notes"] = os.path.basename(b_note)

    def fail_copy(*args: Any, **kwargs: Any) -> None:
        raise OSError("no space left")

    with monkeypatch.context() as m:
        m.setattr(shutil, "copy", fail_copy)
        with pytest.raises(OSError):
            run(a, changeset)

    a_folder = a.get_main_folder()
    assert a_folder is not None
    assert a["notes"] == "a-notes.md"
    with open(os.path.join(a_folder, "a-notes.md"), encoding="utf-8") as fd:
        assert fd.read() == "a note"

    tmp_files = [n for n in os.listdir(a_folder) if n.startswith("papis-merge-note-")]
    assert not tmp_files


def test_merge_run_notes_replace(tmp_library: TemporaryLibrary) -> None:
    """The notes of the changeset replace the notes of the main document: the
    old file is deleted and the new one keeps its name."""
    from papis.commands.merge import run
    from papis.document import Document

    db = papis.database.get()
    (a,) = db.query_dict({"author": "popper"})
    (b,) = db.query_dict({"author": "krishnamurti"})

    put_note(a, "a-notes.md", "a note")
    b_note = put_note(b, "notes.md", "b note")

    b_folder = b.get_main_folder()
    assert b_folder is not None
    changeset = Document()
    changeset.set_folder(b_folder)
    changeset["notes"] = os.path.basename(b_note)

    run(a, changeset)

    a_folder = a.get_main_folder()
    assert a_folder is not None
    # NOTE: the old notes file is deleted, so the new one keeps its name
    assert a["notes"] == "notes.md"
    assert not os.path.exists(os.path.join(a_folder, "a-notes.md"))
    with open(os.path.join(a_folder, "notes.md"), encoding="utf-8") as fd:
        assert fd.read() == "b note"


@pytest.mark.parametrize("second", [False, True])
def test_merge_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    second: bool,
) -> None:
    """The CLI carries over the picked files and keeps the main document's
    identity and metadata."""
    import papis.pick
    import papis.tui.utils
    import papis.utils
    from papis.commands.merge import cli
    from papis.document import from_folder

    db = papis.database.get()
    (first,) = db.query_dict({"author": "popper"})
    (last,) = db.query_dict({"author": "krishnamurti"})

    # NOTE: with '--second' the second picked document is the main one
    a, b = (last, first) if second else (first, last)

    a_folder = a.get_main_folder()
    b_folder = b.get_main_folder()
    assert a_folder is not None and b_folder is not None

    put_file(b, "paper.pdf", "b")
    b_dropped = put_file(b, "other.pdf", "o")
    a_files = a.get_files()

    # NOTE: captured before the merge: the documents change below
    id_a, id_b = a["papis_id"], b["papis_id"]
    title_a, title_b = a["title"], b["title"]

    selections: list[str] = []
    seen_data: list[dict[str, Any]] = []
    prompts: list[str] = []

    def fake_pick_doc(documents: list[Document], **kwargs: Any) -> list[Document]:
        return [first, last]

    def fake_merge(data: dict[str, Any], other: dict[str, Any], name: str) -> None:
        seen_data.extend([data, other])

    def fake_select_range(options: list[str], message: str, **kwargs: Any) -> list[int]:
        selections.append(message)
        return [next(i for i, o in enumerate(options) if o.endswith("paper.pdf"))]

    def fake_confirm(message: str, **kwargs: Any) -> bool:
        prompts.append(message)
        return True

    with monkeypatch.context() as m:
        m.setattr(papis.pick, "pick_doc", fake_pick_doc)
        m.setattr(papis.utils, "update_doc_from_data_interactively", fake_merge)
        m.setattr(papis.tui.utils, "select_range", fake_select_range)
        m.setattr(papis.tui.utils, "confirm", fake_confirm)

        caplog.set_level(logging.INFO)
        cli_runner = PapisRunner()
        args = ["--second", "krishnamurti"] if second else ["krishnamurti"]
        result = cli_runner.invoke(cli, args)
        assert result.exit_code == 0

    # the documents are introduced by their paths, since the descriptions of
    # duplicates are the same
    assert "Merging document B into A" in caplog.text
    assert a_folder in caplog.text

    # what the user is about to be asked about is announced first
    assert "Select the metadata changes of B to apply to A." in caplog.text
    assert "Document B has files." in caplog.text

    # only the secondary document's files are offered
    assert selections == ["Files of B to keep"]

    # identity and files are not offered for merging and the main document
    # provides the base of the merge
    assert len(seen_data) == 2
    assert all(
        "papis_id" not in d and "files" not in d and "notes" not in d for d in seen_data
    )
    assert seen_data[0]["title"] == title_a
    assert seen_data[1]["title"] == title_b

    # a warning lists the unselected files of the removed document
    assert "will be removed" in caplog.text
    assert f"  {os.path.basename(b_dropped)}" in caplog.text
    assert prompts == ["Are you sure you want to merge?"]

    # the main document survives and keeps its identity and metadata
    assert not os.path.exists(b_folder)
    merged = from_folder(a_folder)
    assert merged["papis_id"] == id_a
    assert merged["papis_id"] != id_b
    assert merged["title"] == title_a
    assert merged["title"] != title_b

    # only the picked file is carried over, the main document is untouched
    assert not os.path.exists(b_dropped)
    for path in a_files:
        assert os.path.exists(path)
    assert sorted(merged["files"]) == sorted([
        "paper.pdf",
        *(os.path.basename(f) for f in a_files),
    ])
    with open(os.path.join(a_folder, "paper.pdf"), encoding="utf-8") as fd:
        assert fd.read() == "b"


@pytest.mark.parametrize("a_has_notes", [False, True])
def test_merge_cli_notes(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    a_has_notes: bool,
) -> None:
    """Notes of the second document are always offered, replacing the notes of
    the first document if it has any."""
    import papis.pick
    import papis.tui.utils
    import papis.utils
    from papis.commands.merge import cli
    from papis.document import from_folder

    db = papis.database.get()
    (a,) = db.query_dict({"author": "popper"})
    (b,) = db.query_dict({"author": "krishnamurti"})

    if a_has_notes:
        put_note(a, "notes.md", "a note")
    b_note = put_note(b, "notes.md", "b note")

    picker_options: list[list[str]] = []
    prompts: list[str] = []

    def fake_pick_doc(documents: list[Document], **kwargs: Any) -> list[Document]:
        return [a, b]

    def fake_select_range(options: list[str], message: str, **kwargs: Any) -> list[int]:
        picker_options.append(options)
        return []

    def fake_confirm(message: str, **kwargs: Any) -> bool:
        prompts.append(message)
        return True

    with monkeypatch.context() as m:
        m.setattr(papis.pick, "pick_doc", fake_pick_doc)
        m.setattr(papis.utils, "update_doc_from_data_interactively", lambda *args: None)
        m.setattr(papis.tui.utils, "select_range", fake_select_range)
        m.setattr(papis.tui.utils, "confirm", fake_confirm)

        caplog.set_level(logging.INFO)
        cli_runner = PapisRunner()
        result = cli_runner.invoke(cli, ["krishnamurti"])
        assert result.exit_code == 0

    # notes are never mixed into the file picker
    assert all(b_note not in options for options in picker_options)

    # the note is always offered and carried over
    assert prompts == ["Add the notes of B to A?", "Are you sure you want to merge?"]
    assert "Document B has notes." in caplog.text
    assert "The note of B" not in caplog.text

    if a_has_notes:
        assert "will be replaced" in caplog.text

    a_folder = a.get_main_folder()
    assert a_folder is not None
    merged = from_folder(a_folder)
    assert merged["notes"] == "notes.md"
    with open(os.path.join(a_folder, "notes.md"), encoding="utf-8") as fd:
        assert fd.read() == "b note"


def test_merge_cli_batch(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Batch mode carries over missing metadata, files and notes without prompting."""
    import papis.pick
    import papis.tui.utils
    import papis.utils
    from papis.commands.merge import cli
    from papis.document import from_folder

    db = papis.database.get()
    a, b = db.query("test_author")

    b["title"] = a["title"]
    b["abstract"] = "b abstract"
    put_file(b, "paper.pdf", "b")
    put_note(b, "notes.md", "b note")

    a_folder = a.get_main_folder()
    b_folder = b.get_main_folder()
    assert a_folder is not None and b_folder is not None

    # NOTE: captured before the merge: the documents change below
    id_a = a["papis_id"]
    title_a = a["title"]
    a_names = list(a["files"])
    b_names = list(b["files"])

    with monkeypatch.context() as m:
        m.setattr(papis.pick, "pick_doc", fail)
        m.setattr(papis.utils, "update_doc_from_data_interactively", fail)
        m.setattr(papis.tui.utils, "select_range", fail)
        m.setattr(papis.tui.utils, "confirm", fail)

        caplog.set_level(logging.INFO)
        cli_runner = PapisRunner()
        result = cli_runner.invoke(cli, ["--batch", "test_author"])
        assert result.exit_code == 0

    assert "Merging document B into A" in caplog.text
    assert "Keeping the values of A" not in caplog.text
    assert "Select the metadata changes" not in caplog.text

    # missing metadata is filled in and the rest is left untouched
    merged = from_folder(a_folder)
    assert merged["abstract"] == "b abstract"
    assert merged["title"] == title_a
    assert merged["papis_id"] == id_a

    # all files and the note are carried over
    assert sorted(merged["files"]) == sorted([*a_names, *b_names])
    assert merged["notes"] == "notes.md"
    with open(os.path.join(a_folder, "notes.md"), encoding="utf-8") as fd:
        assert fd.read() == "b note"

    assert not os.path.exists(b_folder)


def test_merge_cli_batch_conflict(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Conflicting metadata keeps the main document's values and is warned about."""
    import papis.pick
    import papis.tui.utils
    import papis.utils
    from papis.commands.merge import cli
    from papis.document import from_folder

    db = papis.database.get()
    a, b = db.query("test_author")

    b["abstract"] = "b abstract"
    put_file(b, "paper.pdf", "b")

    a_folder = a.get_main_folder()
    assert a_folder is not None
    title_a = a["title"]

    with monkeypatch.context() as m:
        m.setattr(papis.pick, "pick_doc", fail)
        m.setattr(papis.utils, "update_doc_from_data_interactively", fail)
        m.setattr(papis.tui.utils, "select_range", fail)
        m.setattr(papis.tui.utils, "confirm", fail)

        caplog.set_level(logging.INFO)
        cli_runner = PapisRunner()
        result = cli_runner.invoke(cli, ["--batch", "test_author"])
        assert result.exit_code == 0

    # the conflicting key is warned about and keeps the main document's value
    assert "Keeping the values of A" in caplog.text
    assert "title" in caplog.text

    merged = from_folder(a_folder)
    assert merged["title"] == title_a
    assert merged["abstract"] == "b abstract"


def test_merge_cli_batch_needs_two(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Batch mode merges nothing unless the query matches exactly two documents."""
    import papis.pick
    import papis.tui.utils
    import papis.utils
    from papis.commands.merge import cli

    db = papis.database.get()
    (b,) = db.query_dict({"author": "krishnamurti"})
    b_folder = b.get_main_folder()
    assert b_folder is not None

    with monkeypatch.context() as m:
        m.setattr(papis.pick, "pick_doc", fail)
        m.setattr(papis.utils, "update_doc_from_data_interactively", fail)
        m.setattr(papis.tui.utils, "select_range", fail)
        m.setattr(papis.tui.utils, "confirm", fail)

        caplog.set_level(logging.INFO)
        cli_runner = PapisRunner()
        result = cli_runner.invoke(cli, ["--batch", "krishnamurti"])
        assert result.exit_code == 0

    assert "exactly two documents" in caplog.text
    assert "Merging document B" not in caplog.text
    assert os.path.exists(b_folder)


def test_merge_cli_keep_two(
    tmp_library: TemporaryLibrary,
    monkeypatch: MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``--keep`` merges the documents but leaves the second one in place."""
    import papis.pick
    import papis.tui.utils
    import papis.utils
    from papis.commands.merge import cli
    from papis.document import from_folder

    db = papis.database.get()
    a, b = db.query("test_author")

    b_paper = put_file(b, "paper.pdf", "b")
    b_dropped = put_file(b, "other.pdf", "o")
    a_folder = a.get_main_folder()
    b_folder = b.get_main_folder()
    assert a_folder is not None and b_folder is not None

    # NOTE: captured before the merge: the documents change below
    a_names = list(a["files"])

    def fake_confirm(message: str, **kwargs: Any) -> bool:
        return True

    def fake_select_range(options: list[str], message: str, **kwargs: Any) -> list[int]:
        return [next(i for i, o in enumerate(options) if o.endswith("paper.pdf"))]

    with monkeypatch.context() as m:
        m.setattr(papis.pick, "pick_doc", lambda docs, **kwargs: [a, b])
        m.setattr(papis.utils, "update_doc_from_data_interactively", lambda *args: None)
        m.setattr(papis.tui.utils, "select_range", fake_select_range)
        m.setattr(papis.tui.utils, "confirm", fake_confirm)

        caplog.set_level(logging.INFO)
        result = PapisRunner().invoke(cli, ["--keep", "test_author"])
        assert result.exit_code == 0

    # nothing is warned about being removed, since nothing is removed
    assert "will be removed" not in caplog.text
    assert "Keeping both documents." in caplog.text

    # both documents survive, with the unselected file left in place
    assert os.path.exists(b_folder)
    assert os.path.exists(b_dropped)
    assert os.path.exists(b_paper)
    assert os.path.exists(os.path.join(a_folder, "paper.pdf"))

    merged = from_folder(a_folder)
    assert merged["files"] == [*a_names, "paper.pdf"]

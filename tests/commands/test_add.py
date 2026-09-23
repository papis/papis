from __future__ import annotations

import os
import shutil
import sys
from typing import TYPE_CHECKING, Any

import pytest

from papis.document import Document
from papis.testing import (
    PapisRunner,
    TemporaryConfiguration,
    TemporaryLibrary,
    make_lookup_handler,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def make_document(name: str, dir: str, nfiles: int = 0) -> Document:
    folder = os.path.join(dir, name)
    if not os.path.exists(folder):
        os.makedirs(folder)

    from papis.testing import create_random_file
    files = [os.path.basename(create_random_file(dir=folder)) for _ in range(nfiles)]
    data = {
        "author": "Plato",
        "title": "Republic",
        "year": 375,
        "files": files
    }

    from papis.id import ID_KEY_NAME, compute_an_id

    doc = Document(folder, data)
    doc[ID_KEY_NAME] = compute_an_id(doc)
    doc.save()

    return doc


@pytest.mark.skipif(
    not shutil.which("git"),
    reason="Test requires 'git' executable to be in the PATH")
@pytest.mark.library_setup(use_git=True)
def test_add_run(tmp_library: TemporaryLibrary, nfiles: int = 5) -> None:
    from papis.commands.add import run

    # add non-existent file
    with pytest.raises(OSError, match=r"exist.pdf"):
        run(
            ["/path/does/not/exist.pdf"],
            data={"author": "Bohm", "title": "My effect"})

    # add no files
    run([], data={"author": "Evangelista", "title": "MRCI"})

    from papis.database import get_database

    db = get_database()
    doc, = db.query_dict({"author": "Evangelista"})
    assert len(doc.get_files()) == 0

    # add many files
    data = {
        "journal": "International Journal of Quantum Chemistry",
        "language": "en",
        "issue": "15",
        "title": "How many-body perturbation theory has changed QM",
        "url": "https://doi.wiley.com/10.1002/qua.22384",
        "volume": "109",
        "author": "Kutzelnigg, Werner",
        "type": "article",
        "doi": "10.1002/qua.22384",
        "year": "2009",
        "ref": "2FJT2E3A"
    }
    paths = [tmp_library.create_random_file() for _ in range(nfiles)]

    run(paths, data=data, git=True)

    doc, = db.query_dict({"author": "Kutzelnigg"})
    assert len(doc.get_files()) == nfiles


def test_add_auto_doctor_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import run

    data = {
        "journal": "International Journal of Quantum Chemistry",
        "language": "en",
        "issue": "15",
        "title": "How many-body perturbation theory has changed QM",
        "url": "https://doi.wiley.com/10.1002/qua.22384",
        "volume": "109",
        "author": "Kutzelnigg, Werner",
        "type": "article",
        "doi": "10.1002/qua.22384",
        "year": "2009",
        "ref": "#{2FJT2E3A}"
    }
    paths: list[str] = []

    import papis.config

    # add document with auto-doctor on
    papis.config.set("doctor-default-checks", ["keys-missing", "field-type", "refs"])
    run(paths, data=data, auto_doctor=True)

    # check that all the broken fields are fixed
    from papis.database import get_database
    db = get_database()
    doc, = db.query_dict({"author": "Kutzelnigg"})

    assert doc["author_list"] == [{"given": "Werner", "family": "Kutzelnigg"}]
    assert isinstance(doc["year"], int) and doc["year"] == 2009
    assert doc["ref"] == "2FJT2E3A"


def test_add_set_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Bertrand Russell",
         "--set", "title", "Principia",
         "--batch"])
    assert result.exit_code == 0

    from papis.database import get_database

    db = get_database()
    doc, = db.query_dict({"author": "Bertrand Russell"})
    assert doc["title"] == "Principia"
    assert not doc.get_files()


@pytest.mark.xfail(sys.platform == "win32", reason="Developer mode not enabled")
def test_add_link_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    filename = tmp_library.create_random_file()
    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Plato",
         "--set", "title", "Republic",
         "--batch",
         "--link",
         filename])
    assert result.exit_code == 0

    from papis.database import get_database

    db = get_database()
    doc, = db.query_dict({"author": "Plato"})

    files = doc.get_files()
    assert len(files) == 1
    assert os.path.islink(files[0])


def test_add_folder_name_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    filename = tmp_library.create_random_file()
    _, ext = os.path.splitext(filename)
    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Aristotle",
         "--set", "title", "The apology of Socrates",
         "--batch",
         "--folder-name", "test-the-apology",
         "--file-name", f"test-the-apology{ext}",
         filename])
    assert result.exit_code == 0

    from papis.database import get_database

    db = get_database()
    doc, = db.query_dict({"author": "Aristotle"})

    folder = doc.get_main_folder()
    assert folder is not None
    assert os.path.basename(folder) == "test-the-apology"

    files = doc.get_files()
    assert len(files) == 1
    assert os.path.basename(files[0]) == f"test-the-apology{ext}"


def test_add_from_folder_cli(tmp_library: TemporaryLibrary,
                             monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    doc = make_document("test-add-from-folder", tmp_library.tmpdir, nfiles=1)
    folder = doc.get_main_folder()
    assert folder is not None

    import papis.tui.utils
    import papis.utils

    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(
            cli,
            ["--from", "folder", folder])
        assert result.exit_code == 0

    from papis.database import get_database
    db = get_database()

    from papis.database.cache import PickleDatabase
    if not isinstance(db, PickleDatabase):
        return

    db.documents = None
    doc, = db.query_dict({"author": "Plato"})

    assert doc["title"] == "Republic"
    assert len(doc.get_files()) == 1


def test_add_from_folder_no_download_files_cli(
        tmp_library: TemporaryLibrary) -> None:
    """'--no-download-files' drops client source files (legacy parity)."""
    from papis.commands.add import cli

    doc = make_document("test-add-from-folder", tmp_library.tmpdir, nfiles=1)
    folder = doc.get_main_folder()
    assert folder is not None

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli,
        ["--batch", "--no-download-files", "--from", "folder", folder])
    assert result.exit_code == 0

    from papis.database import get_database
    db = get_database()

    from papis.database.cache import PickleDatabase
    if not isinstance(db, PickleDatabase):
        return

    db.documents = None
    doc, = db.query_dict({"author": "Plato"})

    assert doc["title"] == "Republic"
    assert len(doc.get_files()) == 0


def test_add_from_library_name_cli(tmp_library: TemporaryLibrary,
                                  monkeypatch: pytest.MonkeyPatch,
                                  caplog: pytest.LogCaptureFixture) -> None:
    """The library client source matches library names: 'papis add <lib>'
    offers importing from it (the legacy suggestion path)."""
    import papis.pick
    import papis.tui.utils
    from papis.commands.add import cli

    picked: list[Any] = []

    def fake_pick(x: list[Any], **k: Any) -> list[Any]:
        docs = [max(x, key=lambda d: len(d.get_files()))] if x else []
        picked.extend(docs)
        return docs

    monkeypatch.setattr(papis.pick, "pick", fake_pick)
    # NOTE: the duplicate report is a TUI pager that cannot run headless
    monkeypatch.setattr(papis.tui.utils, "text_area", lambda *args, **kwargs: None)

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["--batch", tmp_library.libname])
    assert result.exit_code == 0

    # the library's documents were offered and the picked one was imported
    # faithfully: copying it into the same library is then declined as a
    # duplicate by 'add' itself (see 'run')
    assert picked
    assert "No new document is created" in caplog.text


def test_add_from_unknown_source_cli(
        tmp_library: TemporaryLibrary,
        caplog: pytest.LogCaptureFixture) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["--from", "bogus", "some-input"])
    assert result.exit_code == 1
    assert "unknown source 'bogus'" in caplog.text

    # a pinned source that cannot classify its input is a 'no_match' warning,
    # but no document is created, so the command exits with an error
    result = cli_runner.invoke(cli, ["--from", "lib", "nope"])
    assert result.exit_code == 1
    assert "Source 'lib': did not match the given input" in caplog.text

    result = cli_runner.invoke(cli, ["--from", "folder", "nope"])
    assert result.exit_code == 1
    assert "Source 'folder': did not match the given input" in caplog.text


def test_add_bibtex_cli(tmp_library: TemporaryLibrary,
                        monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    bibtex_string = (
        "@article{10.1002/andp.19053221004,\n"
        "    author = {A. Einstein},\n"
        "    doi = {10.1002/andp.19053221004},\n"
        "    issue = {10},\n"
        "    journal = {Ann. Phys.},\n"
        "    pages = {891--921},\n"
        "    title = {Zur Elektrodynamik bewegter Körper},\n"
        "    type = {article},\n"
        "    volume = {322},\n"
        "    year = {1905}\n"
        "}"
    )

    bibfile = os.path.join(tmp_library.tmpdir, "test-add.bib")
    with open(bibfile, "w", encoding="utf-8") as f:
        f.write(bibtex_string)

    import papis.tui.utils
    import papis.utils

    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        filename = tmp_library.create_random_file()
        result = cli_runner.invoke(
            cli,
            ["--from", "bibtex", bibfile, filename])
        assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "einstein", "title": "Elektrodynamik bewegter"})

    assert doc["doi"] == "10.1002/andp.19053221004"
    assert len(doc.get_files()) == 1


def test_add_yaml_cli(tmp_library: TemporaryLibrary,
                      monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.add import cli
    from papis.yaml import data_to_yaml

    cli_runner = PapisRunner()

    yamlfile = os.path.join(tmp_library.tmpdir, "test-add.yaml")
    data_to_yaml(yamlfile, {
        "author": "Tolkien",
        "title": "The lord of the rings",
        })

    import papis.tui.utils
    import papis.utils

    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        filename = tmp_library.create_random_file()
        result = cli_runner.invoke(
            cli,
            ["--from", "yaml", yamlfile, filename])
        assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "Tolkien"})

    assert len(doc.get_files()) == 1


def test_add_lib_cli(tmp_library: TemporaryLibrary,
                     monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    doc = make_document("test-add-from-folder", tmp_library.tmpdir)
    folder = doc.get_main_folder()
    assert folder is not None

    import papis.tui.utils
    import papis.utils

    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        m.setattr(papis.tui.utils, "text_area", lambda *args, **kwargs: None)
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(
            cli,
            ["--from", "lib", folder, "--open", "--confirm"])
        assert result.exit_code == 0


def test_add_set_invalid_format_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    import papis.config

    papis.config.set("add-file-name",
                     "{doc[author_list][0][family]} - {doc[year]} - {doc[title]}")

    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Bertrand Russell",
         "--set", "title", "Principia",
         "--batch"])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bertrand Russell"})
    assert doc["title"] == "Principia"
    assert not doc.get_files()


@pytest.mark.skipif(
    not shutil.which("false"),
    reason="Test requires 'false' executable to be in the PATH")
def test_add_edit_failure(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch) -> None:
    import tempfile

    import papis.config
    from papis.commands.add import run

    papis.config.set("editor", "false")

    temp_dirs = []
    mkdtemp = tempfile.mkdtemp

    def record_mkdtemp(*args: Any, **kwargs: Any) -> str:
        path: str = mkdtemp(*args, **kwargs)
        temp_dirs.append(path)
        return path

    monkeypatch.setattr(tempfile, "mkdtemp", record_mkdtemp)

    from papis.testing import create_random_file
    filename = create_random_file(dir=tmp_library.tmpdir)

    run([filename],
        data={"author": "Whitehead", "title": "Process and Reality"},
        edit=True)

    import papis.database

    db = papis.database.get()
    assert not db.query_dict({"author": "Whitehead"})

    # the temporary document folder should not be left behind (see gh-1211)
    assert temp_dirs
    assert not [d for d in temp_dirs if os.path.exists(d)]


def test_add_nested_folder_name_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    filename = tmp_library.create_random_file()
    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Euclid",
         "--set", "title", "Elements",
         "--batch",
         "--folder-name", "math/ancient/elements",
         filename])
    assert result.exit_code == 0

    from papis.database import get_database

    db = get_database()
    doc, = db.query_dict({"author": "Euclid"})
    folder = doc.get_main_folder()
    assert folder is not None
    assert os.path.exists(folder)
    assert folder.endswith(os.path.join("math", "ancient", "elements"))


def test_add_subfolder_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    filename = tmp_library.create_random_file()
    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Archimedes",
         "--set", "title", "On the Sphere and Cylinder",
         "--batch",
         "--subfolder", "greek/math",
         filename])
    assert result.exit_code == 0

    from papis.database import get_database

    db = get_database()
    doc, = db.query_dict({"author": "Archimedes"})
    folder = doc.get_main_folder()
    assert folder is not None
    assert os.path.exists(folder)
    assert os.path.join("greek", "math") in folder


def test_add_subfolder_outside_base(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.add import run

    filename = tmp_library.create_random_file()
    with pytest.raises(ValueError, match="outside of directory"):
        run([filename],
            data={"author": "Test", "title": "Escape"},
            subfolder="../../outside",
            batch=True)


def test_add_run_missing_library(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.commands.add import run

    # Custom base path that does not exist
    with pytest.raises(NotADirectoryError, match="base path does not exist"):
        run([],
            data={"author": "Test", "title": "No Base"},
            base_path=os.path.join(tmp_config.tmpdir, "nonexistent"),
            batch=True)

    # Configured library path that does not exist
    lib_name = papis.config.get_lib_name()
    nonexistent_lib = os.path.join(tmp_config.tmpdir, "missing_lib")
    papis.config.set("dir", nonexistent_lib, section=lib_name)
    papis.config.set_lib_from_name(lib_name)

    with pytest.raises(
        NotADirectoryError, match=r"library '.*' directory does not exist"
    ):
        run([],
            data={"author": "Test", "title": "No Lib"},
            batch=True)


def test_add_cli_missing_library_batch(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    lib_name = papis.config.get_lib_name()
    nonexistent_lib = os.path.join(tmp_config.tmpdir, "batch_new_lib")
    papis.config.set("dir", nonexistent_lib, section=lib_name)
    papis.config.set_lib_from_name(lib_name)

    assert not os.path.exists(nonexistent_lib)

    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Newton",
         "--set", "title", "Principia",
         "--batch"])
    assert result.exit_code == 0
    assert os.path.exists(nonexistent_lib)


def test_add_cli_missing_library_interactive(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.config
    import papis.tui.utils
    import papis.utils
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    lib_name = papis.config.get_lib_name()

    # User confirms creation
    nonexistent_lib_yes = os.path.join(tmp_config.tmpdir, "interactive_yes_lib")
    papis.config.set("dir", nonexistent_lib_yes, section=lib_name)
    papis.config.set_lib_from_name(lib_name)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", lambda *args, **kwargs: True)
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        result = cli_runner.invoke(
            cli,
            ["--set", "author", "Kepler",
             "--set", "title", "Astronomia Nova"])  # spell: disable
        assert result.exit_code == 0
        assert os.path.exists(nonexistent_lib_yes)

    # User denies creation
    nonexistent_lib_no = os.path.join(tmp_config.tmpdir, "interactive_no_lib")
    papis.config.set("dir", nonexistent_lib_no, section=lib_name)
    papis.config.set_lib_from_name(lib_name)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", lambda *args, **kwargs: False)
        result = cli_runner.invoke(
            cli,
            ["--set", "author", "Galileo",
             "--set", "title", "Sidereus Nuncius"])
        assert result.exit_code == 1
        assert not os.path.exists(nonexistent_lib_no)


def test_add_set_precedence_cli(tmp_library: TemporaryLibrary,
                                handler_registry: Callable[..., None],
                                ) -> None:
    """``--set`` overwrites importer data."""
    from papis.commands.add import cli

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler(
        "fake", document={"author": "Bohm", "title": "My effect"}))

    filename = tmp_library.create_random_file()
    result = cli_runner.invoke(
        cli,
        ["--batch", "--set", "author", "Plato", filename])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Plato"})

    assert doc["title"] == "My effect"

    files = doc.get_files()
    assert len(files) == 1
    assert os.path.exists(files[0])


def test_add_importer_files_cli(tmp_library: TemporaryLibrary,
                                handler_registry: Callable[..., None],
                                ) -> None:
    """Explicit files and files from the importer are both collected."""
    from papis.commands.add import cli

    cli_runner = PapisRunner()
    extra_file = tmp_library.create_random_file()
    handler_registry(make_lookup_handler(
        "fake", document={"author": "Bohm", "title": "My effect"}, files=[extra_file]))

    filename = tmp_library.create_random_file()
    result = cli_runner.invoke(
        cli,
        ["--batch", "--download-files", filename])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bohm"})

    files = doc.get_files()
    assert len(files) == 2
    assert all(os.path.exists(f) for f in files)


def test_add_from_pinned_file_is_evidence_only(
        tmp_library: TemporaryLibrary,
        handler_registry: Callable[..., None],
        ) -> None:
    """A '--from' item's gathered file is evidence, not document content."""
    from papis.commands.add import cli

    handler_registry(make_lookup_handler(
        "fake", document={"author": "Bohm", "title": "Pinned"}))
    filename = tmp_library.create_random_file()

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["--batch", "--from", "fake", filename])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bohm"})
    assert doc.get_files() == []


def test_add_no_importer_data_cli(tmp_library: TemporaryLibrary,
                                  handler_registry: Callable[..., None],
                                  ) -> None:
    """No document is created when sources provide no data and no file exists."""
    from papis.commands.add import cli

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler("fake"))

    import papis.database

    db = papis.database.get()
    ndocs = len(db.get_all_documents())

    result = cli_runner.invoke(
        cli,
        ["--batch", "/path/that/does/not/exist.pdf"])
    assert result.exit_code == 1

    assert len(db.get_all_documents()) == ndocs


def test_add_doi_cli(tmp_library: TemporaryLibrary,
                     monkeypatch: pytest.MonkeyPatch,
                     handler_registry: Any) -> None:
    """Add a document from a bare DOI (end-to-end, service mocked)."""
    import papis.crossref
    from papis.sources.handlers.doi import DoiHandler

    handler_registry(DoiHandler)
    monkeypatch.setattr(
        papis.crossref, "doi_to_data",
        lambda doi: {"title": "From a DOI", "author": "A. Einstein", "doi": doi})

    from papis.commands.add import cli

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli, ["--batch", "10.1103/PhysRevLett.123.156401"])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"doi": "10.1103/PhysRevLett.123.156401"})
    assert doc["title"] == "From a DOI"


def test_add_arxiv_cli(tmp_library: TemporaryLibrary,
                       monkeypatch: pytest.MonkeyPatch,
                       handler_registry: Any) -> None:
    """Add a document from a bare arXiv ID, downloading the PDF reference."""
    import papis.arxiv
    import papis.utils
    from papis.sources.handlers.arxiv import ArxivHandler

    handler_registry(ArxivHandler)
    monkeypatch.setattr(
        papis.arxiv, "get_data",
        lambda **kwargs: [{
            "title": "From arXiv",
            "author": "A. Author",
            "doc_url": "https://arxiv.org/pdf/1701.08223",
            }])

    pdf_path = os.path.join(tmp_library.tmpdir, "arxiv.pdf")
    with open(pdf_path, "w", encoding="utf-8") as fd:
        fd.write("fake pdf")

    monkeypatch.setattr(
        "papis.gather.download_document",
        lambda url, **kwargs: pdf_path)

    from papis.commands.add import cli

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["--batch", "1701.08223"])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"title": "From arXiv"})
    assert len(doc.get_files()) == 1


def test_add_rejects_wrong_file_type(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch,
        handler_registry: Any,
        caplog: pytest.LogCaptureFixture) -> None:
    """A file reference's expected extension (FileReference.extension) guards
    the download: an HTML page served in place of the arXiv PDF is dropped
    instead of being attached."""
    import papis.arxiv
    import papis.utils
    from papis.sources.handlers.arxiv import ArxivHandler

    handler_registry(ArxivHandler)
    monkeypatch.setattr(
        papis.arxiv, "get_data",
        lambda **kwargs: [{
            "title": "From arXiv",
            "author": "A. Author",
            "doc_url": "https://arxiv.org/pdf/1701.08223",
            }])

    class FakeResponse:
        ok = True
        status_code = 200
        reason = "OK"
        url = "https://arxiv.org/pdf/1701.08223"

        def __init__(self) -> None:
            self.content = b"<html><body>consent</body></html>"
            self.headers = {"Content-Type": "text/html"}

    class FakeSession:
        def __init__(self) -> None:
            self.response = FakeResponse()

        def get(self, url: str, **kwargs: object) -> FakeResponse:
            return self.response

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        papis.utils, "get_session",
        lambda: FakeSession())  # ruff: ignore[unnecessary-lambda]

    from papis.commands.add import cli

    cli_runner = PapisRunner()
    with caplog.at_level("ERROR"):
        result = cli_runner.invoke(cli, ["--batch", "1701.08223"])
    assert result.exit_code == 0
    assert "expected type 'pdf'" in caplog.text

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"title": "From arXiv"})
    assert len(doc.get_files()) == 0


def test_add_website_cli(tmp_library: TemporaryLibrary,
                         monkeypatch: pytest.MonkeyPatch,
                         handler_registry: Any) -> None:
    """Add from a journal URL, end-to-end: page scrape + BibTeX followup
    (publisher data wins) + PDF reference download."""
    import papis.utils
    from papis.sources.handlers.formats.bibtex import BibTeXHandler
    from papis.sources.handlers.web.aps import APSHandler

    handler_registry(APSHandler, BibTeXHandler)

    html_path = os.path.join(
        os.path.dirname(__file__), "..", "sources", "handlers", "web",
        "resources", "APS_PhysRevLett.122.145901.html")
    with open(html_path, encoding="utf-8") as fd:
        html = fd.read()

    class FakeSession:
        ok = True
        status_code = 200
        reason = "OK"

        def get(self, url: str, timeout: int | None = None) -> FakeSession:
            if "/export/" in url:
                self.headers = {"Content-Type": "text/plain"}
                self.content = (
                    b"@article{prl,\n"
                    b"  title = {Publisher title},\n"
                    b"  author = {Publisher, Author},\n"
                    b"  year = {2019},\n"
                    b"  doi = {10.1103/PhysRevLett.122.145901},\n"
                    b"}\n")
            else:
                self.headers = {"Content-Type": "text/html"}
                self.content = html.encode()
            return self

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        papis.utils, "get_session",
        lambda: FakeSession())  # ruff: ignore[unnecessary-lambda]

    pdf_path = os.path.join(tmp_library.tmpdir, "aps.pdf")
    with open(pdf_path, "w", encoding="utf-8") as fd:
        fd.write("fake pdf")

    monkeypatch.setattr(
        "papis.gather.download_document",
        lambda url, **kwargs: pdf_path)

    from papis.commands.add import cli

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli, ["--batch",
              "https://journals.aps.org/prl/abstract/"
              "10.1103/PhysRevLett.122.145901"])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"doi": "10.1103/PhysRevLett.122.145901"})
    # the followup (BibTeX export) data wins over the scraped meta
    assert doc["title"] == "Publisher title"
    # scraped fields that the export lacks are kept
    assert doc["journal"] == "Physical Review Letters"
    assert len(doc.get_files()) == 1


def test_add_source_error_warns(
    tmp_library: TemporaryLibrary,
    handler_registry: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed source is warned about and does not abort the command."""
    from papis.commands.add import cli
    from papis.exceptions import SourceError

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler("fake", lookup_exc=SourceError("boom")))

    filename = tmp_library.create_random_file()
    with caplog.at_level("WARNING"):
        result = cli_runner.invoke(cli, ["--batch", filename])

    assert result.exit_code == 0
    assert "fake" in caplog.text
    assert "boom" in caplog.text


def test_add_surfaces_result_message(
    tmp_library: TemporaryLibrary,
    handler_registry: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A non-fatal caveat the handler reports as a result message is surfaced
    by the client (it could not cross an API boundary from a server log)."""
    from papis.commands.add import cli

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler(
        "fake",
        document={"title": "T"},
        message="The content contains 2 entries; picking the first."))

    filename = tmp_library.create_random_file()
    with caplog.at_level("WARNING"):
        result = cli_runner.invoke(cli, ["--batch", filename])

    assert result.exit_code == 0
    assert "2 entries" in caplog.text


def test_add_fan_out_no_match_is_not_surfaced(
    tmp_library: TemporaryLibrary,
    handler_registry: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A plain file is gathered unpinned: fan-out declines are expected and
    not shown to the user."""
    from papis.commands.add import cli

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler("fake", match_result=False))

    filename = tmp_library.create_random_file()
    with caplog.at_level("WARNING"):
        result = cli_runner.invoke(cli, ["--batch", filename])

    assert result.exit_code == 0
    assert "did not match" not in caplog.text


def test_add_from_order_decides_precedence_cli(
        tmp_library: TemporaryLibrary,
        handler_registry: Callable[..., None],
        ) -> None:
    """Later '--from' pairs win conflicts: client sources take part in the
    list-order precedence like any handler (see 'papis.sources.client.merge')."""
    from papis.commands.add import cli

    doc = make_document("folder-source", tmp_library.tmpdir, nfiles=0)
    folder = doc.get_main_folder()
    assert folder is not None

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler(
        "fake", document={"author": "Bohm", "title": "My effect"}))

    # the folder is first: the source data wins the conflicts
    result = cli_runner.invoke(
        cli, ["--batch", "--from", "folder", folder, "--from", "fake", "x"])
    assert result.exit_code == 0

    # ... and with the arguments reversed the folder data wins
    result = cli_runner.invoke(
        cli, ["--batch", "--from", "fake", "x", "--from", "folder", folder])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bohm"})
    assert doc["title"] == "My effect"

    doc, = db.query_dict({"title": "Republic"})
    assert doc["author"] == "Plato"


def test_add_from_order_folds_client_sources_cli(
        tmp_library: TemporaryLibrary,
        handler_registry: Any) -> None:
    """'--from' results fold in command-line order (later pairs win conflicts),
    client sources included."""
    from papis.commands.add import cli

    handler_registry(
        make_lookup_handler(
            "fake-a", document={"author": "A-author", "title": "A-title", "a": "A"}
        ),
        make_lookup_handler("fake-b", document={"title": "B-title", "b": "B"}))

    doc = make_document("folder-source", tmp_library.tmpdir, nfiles=0)
    folder = doc.get_main_folder()
    assert folder is not None

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, [
        "--batch",
        "--from", "fake-a", "x",
        "--from", "folder", folder,
        "--from", "fake-b", "y",
        ])
    assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Plato"})

    # 'fake-a' (1st) loses to the folder record (2nd): the folder wins
    # 'author', which 'fake-b' (3rd) does not touch
    assert doc["author"] == "Plato"
    assert doc["a"] == "A"
    # the folder record (2nd) loses to 'fake-b' (3rd)
    assert doc["title"] == "B-title"


def test_add_interactive_selection_cli(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch,
        handler_registry: Any,
        ) -> None:
    """A deselected inferred result contributes neither data nor files."""
    import papis.tui.utils
    import papis.utils
    from papis.commands.add import cli
    from papis.sources.handler import FileReference

    handler_registry(
        make_lookup_handler(
            "fake-a", document={"author": "Bohm", "title": "My effect"}),
        make_lookup_handler(
            "fake-b",
            document={"title": "Other"},
            files=[FileReference(path=tmp_library.create_random_file())]))

    cli_runner = PapisRunner()

    with monkeypatch.context() as m:
        # keep only the 'fake-a' result in the source-selection stage
        m.setattr(
            papis.tui.utils, "select_range",
            lambda options, message, **kwargs: [
                i for i, option in enumerate(options)
                if option.startswith("[fake-a]")])
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(cli, ["--download-files", "x"])
        assert result.exit_code == 0

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bohm"})

    assert doc["title"] == "My effect"
    # the deselected 'fake-b' result contributes no data and no files
    assert doc.get_files() == []


def test_add_from_no_source_picker_cli(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch,
        handler_registry: Any,
        ) -> None:
    """Explicit '--from' results fold in command-line order without selection."""
    import papis.tui.utils
    import papis.utils
    from papis.commands.add import cli

    handler_registry(
        make_lookup_handler("fake-a", document={"author": "Bohm", "title": "First"}),
        make_lookup_handler("fake-b", document={"title": "Second"}))

    def _fail(options: Any, message: str, **kwargs: Any) -> list[int]:
        raise AssertionError("'--from' results must not be offered for selection")

    offered: list[str] = []

    def _record(doc: Document, data: Any, name: str) -> None:
        offered.append(name)
        doc.update(data)

    cli_runner = PapisRunner()

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "select_range", _fail)
        m.setattr(papis.utils, "update_doc_from_data_interactively", _record)
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(
            cli, ["--from", "fake-a", "x", "--from", "fake-b", "y"])
        assert result.exit_code == 0

    # the first result merges silently, later '--from' pairs resolve fields
    assert offered == ["fake-b"]

    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bohm"})

    # the later '--from' pair wins the conflicting key
    assert doc["title"] == "Second"

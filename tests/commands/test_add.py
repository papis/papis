import os
import pytest
import shutil
import sys

import papis.config
import papis.document

from papis.testing import TemporaryLibrary, PapisRunner


def make_document(name: str, dir: str, nfiles: int = 0) -> papis.document.Document:
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

    import papis.id

    doc = papis.document.Document(folder, data)
    doc[papis.id.key_name()] = papis.id.compute_an_id(doc)
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

    db = papis.database.get()
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
    paths = []

    # add document with auto-doctor on
    papis.config.set("doctor-default-checks", ["keys-missing", "key-type", "refs"])
    run(paths, data=data, auto_doctor=True)

    # check that all the broken fields are fixed
    db = papis.database.get()
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

    db = papis.database.get()
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

    db = papis.database.get()
    doc, = db.query_dict({"author": "Plato"})

    files = doc.get_files()
    assert len(files) == 1
    assert os.path.islink(files[0])


def test_add_folder_name_cli(tmp_library: TemporaryLibrary) -> None:
    import papis.yaml
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

    db = papis.database.get()
    doc, = db.query_dict({"author": "Aristotle"})

    folder = doc.get_main_folder()
    assert folder is not None
    assert os.path.basename(folder) == "test-the-apology"

    files = doc.get_files()
    assert len(files) == 1

    assert os.path.basename(files[0]) == f"test-the-apology{ext}"


def test_add_from_folder_cli(tmp_library: TemporaryLibrary,
                             monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.yaml
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    doc = make_document("test-add-from-folder", tmp_library.tmpdir, nfiles=1)
    folder = doc.get_main_folder()
    assert folder is not None

    with monkeypatch.context() as m:
        m.setattr(papis.utils, "update_doc_from_data_interactively",
                  lambda doc, d, name: doc.update(d))
        m.setattr(papis.utils, "open_file", lambda x: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(
            cli,
            ["--from", "folder", folder])
        assert result.exit_code == 0

    from papis.database.cache import Database
    db = papis.database.get()
    assert isinstance(db, Database)

    db.documents = None
    doc, = db.query_dict({"author": "Plato"})

    assert doc["title"] == "Republic"
    assert len(doc.get_files()) == 1


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
    import papis.yaml
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    yamlfile = os.path.join(tmp_library.tmpdir, "test-add.yaml")
    papis.yaml.data_to_yaml(yamlfile, {
        "author": "Tolkien",
        "title": "The lord of the rings",
        })

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
    import papis.yaml
    from papis.commands.add import cli
    cli_runner = PapisRunner()

    doc = make_document("test-add-from-folder", tmp_library.tmpdir)
    folder = doc.get_main_folder()
    assert folder is not None

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

    papis.config.set("add-file-name",
                     "{doc[author_list][0][family]} - {doc[year]} - {doc[title]}")

    result = cli_runner.invoke(
        cli,
        ["--set", "author", "Bertrand Russell",
         "--set", "title", "Principia",
         "--batch"])
    assert result.exit_code == 0

    db = papis.database.get()
    doc, = db.query_dict({"author": "Bertrand Russell"})
    assert doc["title"] == "Principia"
    assert not doc.get_files()

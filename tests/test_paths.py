import os
import re

from papis.testing import TemporaryConfiguration, TemporaryLibrary


def test_unique_suffixes() -> None:
    import string
    from papis.paths import unique_suffixes

    expected = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
        "AA", "AB", "AC", "AD"
    ]
    for value, output in zip(expected, unique_suffixes(string.ascii_uppercase)):
        assert output == value

    for value, output in zip(expected[3:], unique_suffixes(skip=3)):
        assert output == value.lower()


def test_normalize_path(tmp_config: TemporaryConfiguration) -> None:
    from papis.paths import normalize_path

    assert (
        normalize_path("{{] __ }}albert )(*& $ß $+_ einstein (*]")
        == "albert-ss-einstein"
    )
    assert (
        normalize_path(
            os.path.basename('/ashfd/df/  #$%@#$ }{_+"[ ]hello öworld--- .pdf')
        )
        == "hello-oworld-.pdf"
    )
    assert normalize_path("масса и енергиа.pdf") == "massa-i-energia.pdf"
    assert normalize_path("الامير الصغير.pdf") == "lmyr-lsgyr.pdf"


def test_normalize_path_config(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    from papis.paths import normalize_path

    papis.config.set("doc-paths-lowercase", "False")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "Albert-ss-Einstein"
    )

    papis.config.set("doc-paths-extra-chars", "_")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "__-Albert-ss-_-Einstein"
    )
    assert (
        normalize_path("{{] __Albert )(*& $ß $+_ Einstein (*]")
        == "__Albert-ss-_-Einstein"
    )

    papis.config.set("doc-paths-word-separator", "_")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "___Albert_ss___Einstein"
    )

    papis.config.set("doc-paths-lowercase", "True")
    assert (
        normalize_path("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "___albert_ss___einstein"
    )


def test_get_document_file_name(tmp_library: TemporaryLibrary) -> None:
    import papis.config
    from papis.document import from_data

    doc = from_data({"title": "blah"})
    pdf = tmp_library.create_random_file("pdf")
    path = tmp_library.create_random_file(
        "text", prefix="papis-get-name-", suffix=".data")

    # make sure the configuration is empty
    assert not papis.config.get("add-file-name")

    from papis.paths import get_document_file_name

    filename = get_document_file_name(doc, path, suffix="3")
    assert re.match(r"^papis-get-name-.*-3\.data$", filename) is not None

    # with suffix
    filename = get_document_file_name(doc, pdf, suffix="3")
    assert len(re.split(r".*-3\.pdf", filename)) == 2

    # without suffix
    filename = get_document_file_name(doc, pdf)
    assert len(re.split(r".*\.pdf", filename)) == 2

    papis.config.set(
        "add-file-name",
        "{doc[title]} {doc[author]} {doc[year]}"
    )

    # check file name generation
    filename = get_document_file_name(doc, path, suffix="2")
    assert filename == "blah-2.data"

    pdf = tmp_library.create_random_file("pdf")
    filename = get_document_file_name(doc, pdf, suffix="2")
    assert filename == "blah-2.pdf"

    pdf = tmp_library.create_random_file("pdf")
    filename = get_document_file_name(doc, pdf, suffix="2")
    assert filename == "blah-2.pdf"

    yaml = tmp_library.create_random_file("text", suffix=".yaml")
    filename = get_document_file_name(doc, yaml, suffix="2")
    assert filename == "blah-2.yaml"

    # check over limit
    base_name_limit = 100
    doc = papis.document.from_data({"title": "b" * 200})
    filename = get_document_file_name(doc, path,
                                      base_name_limit=base_name_limit,
                                      suffix="2")
    assert filename == "b" * base_name_limit + "-2.data"


def test_get_document_file_name_format(tmp_library: TemporaryLibrary) -> None:
    from papis.document import from_data

    doc = from_data({"title": "blah"})
    pdf = tmp_library.create_random_file("pdf")

    from papis.paths import get_document_file_name

    filename = get_document_file_name(
        doc, pdf, suffix="2",
        file_name_format="{doc[title]} {doc[year]}")
    assert filename == "blah-2.pdf"


def test_get_document_folder(tmp_library: TemporaryLibrary) -> None:
    from papis.document import from_data
    import papis.database

    db = papis.database.get()
    doc = from_data({
        "author": "Niels / Bohr",
        "title": "On the constitution of atoms and molecules",
        "year": 1913,
        "volume": 26,
        "doi": "10.1080/14786441308634955",
        })
    doc.set_folder(os.path.join(tmp_library.libdir,
                                doc["papis_id"]))
    db.maybe_compute_id(doc)

    from papis.paths import get_document_folder, get_document_unique_folder

    # check no folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir)
    assert re.match(r"\w{32}", os.path.basename(folder_name))[0] == doc["papis_id"]

    # check simple folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir,
                                      folder_name_format="{doc[author]}")
    assert os.path.basename(folder_name) == "niels-bohr"

    # check uniqueness with suffices
    os.mkdir(folder_name)
    folder_name = get_document_unique_folder(doc, tmp_library.libdir,
                                             folder_name_format="{doc[author]}")
    assert os.path.basename(folder_name) == "niels-bohr-a"

    # check incorrect folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir,
                                      folder_name_format="{doc.author}")
    assert re.match(r"\w{32}", os.path.basename(folder_name))[0] == doc["papis_id"]

    # check multiple subfolders in folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir,
                                      folder_name_format="{doc[year]}/{doc[author]}")
    assert os.path.basename(folder_name) == "niels-bohr"
    assert os.path.basename(os.path.dirname(folder_name)) == "1913"

    # check path that is not relative to libdir
    folder_name = get_document_folder(doc, tmp_library.libdir,
                                      folder_name_format="../{doc[author]}")
    assert re.match(r"\w{32}", os.path.basename(folder_name))[0] == doc["papis_id"]


def test_rename_document_files(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    papis.config.set("add-file-name", "{doc[year]} {doc[author]}")

    from papis.paths import rename_document_files

    doc = {
        "author": "Niels Bohr",
        "title": "On the constitution of atoms and molecules",
        "year": 1913,
    }

    # check no existing files: no suffix should be added
    new_files = rename_document_files(doc, [
        tmp_config.create_random_file("pdf"),
        tmp_config.create_random_file("text", suffix=".md"),
        ], file_name_format="x {doc[year]} {doc[author]}")

    assert new_files == ["x-1913-niels-bohr.pdf", "x-1913-niels-bohr.md"]

    # check that correct suffixes are added base on existing files
    doc["files"] = rename_document_files(doc, [
        tmp_config.create_random_file("pdf"),
        tmp_config.create_random_file("pdf"),
        tmp_config.create_random_file("text", suffix=".md"),
        ])

    new_files = rename_document_files(doc, [
        tmp_config.create_random_file("pdf"),
        tmp_config.create_random_file("pdf"),
        tmp_config.create_random_file("text", suffix=".md"),
        tmp_config.create_random_file("djvu"),
        ])

    assert new_files == [
        "1913-niels-bohr-b.pdf",
        "1913-niels-bohr-c.pdf",
        "1913-niels-bohr-a.md",
        "1913-niels-bohr.djvu",
        ]

    # check that files are left alone when no 'file_name_format' is given
    orig_files = [
        tmp_config.create_random_file("pdf"),
        tmp_config.create_random_file("text", suffix=".md"),
        tmp_config.create_random_file("djvu"),
        ]
    new_files = rename_document_files(doc, orig_files, file_name_format=False)

    from papis.paths import normalize_path
    assert new_files == [
        normalize_path(os.path.basename(filename)) for filename in orig_files
        ]

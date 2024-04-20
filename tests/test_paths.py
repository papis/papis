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
        assert output == value


def test_normalize_path(tmp_config: TemporaryConfiguration) -> None:
    from papis.paths import normalize_path

    assert (
        normalize_path("{{] __ }}albert )(*& $ß $+_ einstein (*]")
        == "albert-ss-einstein"
    )
    assert (
        normalize_path('/ashfd/df/  #$%@#$ }{_+"[ ]hello öworld--- .pdf')
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
        "{doc[title]} {doc[author]} {doc[yeary]}"
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
        file_name_format="{doc.title} {doc.year}")
    assert filename == "blah-2.pdf"


def test_get_document_hash_folder(tmp_library: TemporaryLibrary) -> None:
    from papis.paths import get_document_hash_folder

    data = {"author": "don quijote de la mancha"}
    filename = tmp_library.create_random_file()

    # check folder with one filename
    hh = get_document_hash_folder(data, [filename])
    assert re.match(r".*-don-quijote-de-la-ma$", hh) is not None

    # check folder with more files
    three_files_hh = get_document_hash_folder(data, [filename, filename, filename])
    assert re.match(r".*-don-quijote-de-la-ma$", three_files_hh) is not None
    assert three_files_hh != hh

    # check folder with no files
    no_files_hh = get_document_hash_folder(data, [])
    assert re.match(r".*-don-quijote-de-la-ma$", no_files_hh) is not None
    assert no_files_hh != hh

    # check folder with no data
    data = {}
    hh = get_document_hash_folder(data, [filename])
    assert re.match(r".*-don-quijote-de-la-ma$", hh) is None

    # check folder with a different file
    filename = tmp_library.create_random_file()
    newhh = get_document_hash_folder(data, [filename])
    assert hh != newhh

    # check folder with same file (hash has a random seed)
    newnewhh = get_document_hash_folder(data, [filename])
    assert newnewhh != newhh


def test_get_document_folder(tmp_library: TemporaryLibrary) -> None:
    from papis.document import from_data

    pdf = tmp_library.create_random_file("pdf")
    doc = from_data({
        "author": "Niels / Bohr",
        "title": "On the constitution of atoms and molecules",
        "year": 1913,
        "volume": 26,
        "doi": "10.1080/14786441308634955",
        })

    from papis.paths import get_document_folder

    # check no folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir, [pdf])
    assert re.match(r"\w{32}-niels-bohr", os.path.basename(folder_name)) is not None

    # check simple folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir, [pdf],
                                      folder_name_format="{doc[author]}")
    assert os.path.basename(folder_name) == "niels-bohr"

    # check uniqueness with suffices
    os.mkdir(folder_name)
    folder_name = get_document_folder(doc, tmp_library.libdir, [pdf],
                                      folder_name_format="{doc[author]}")
    assert os.path.basename(folder_name) == "niels-bohr-a"

    # check incorrect folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir, [pdf],
                                      folder_name_format="{doc.author}")
    assert re.match(r"\w{32}-niels-bohr", os.path.basename(folder_name)) is not None

    # check multiple subfolders in folder_name_format
    folder_name = get_document_folder(doc, tmp_library.libdir, [pdf],
                                      folder_name_format="{doc[year]}/{doc[author]}")
    assert os.path.basename(folder_name) == "niels-bohr"
    assert os.path.basename(os.path.dirname(folder_name)) == "1913"

    # check path that is not relative to libdir -> we get get_document_hash_folder
    folder_name = get_document_folder(doc, tmp_library.libdir, [pdf],
                                      folder_name_format="../{doc[author]}")
    assert re.match(r"\w{32}-niels-bohr", os.path.basename(folder_name)) is not None

import os
import tempfile

import pytest

import papis.api
import papis.document

from papis.testing import TemporaryConfiguration

DOCTOR_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


def test_files_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import files_check

    with tempfile.NamedTemporaryFile("w") as tmp:
        folder = os.path.dirname(tmp.name)
        doc = papis.document.from_data({
            "files": [os.path.basename(tmp.name), "non-existent-file"],
            })

        # check: without folder
        errors = files_check(doc)
        assert not errors

        # check: non-existent file
        doc.set_folder(folder)
        error, = files_check(doc)
        assert error.payload == os.path.join(folder, "non-existent-file")

        error.fix_action()
        assert "non-existent-file" not in doc["files"]


def test_keys_missing_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import keys_missing_check

    # check extend functionality
    papis.config.set("doctor-keys-missing-keys",
                     ["author", "author_list", "title"])
    papis.config.set("doctor-keys-missing-keys-extend",
                     ["ref"])

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })

    error1, error2 = keys_missing_check(doc)
    assert error1.payload == "ref" or error2.payload == "ref"
    assert error1.payload == "author_list" or error2.payload == "author_list"


def test_keys_missing_check_authors(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import keys_missing_check

    papis.config.set("doctor-keys-missing-keys", ["author_list", "author"])
    full_doc = papis.document.from_data(
        {
            "title": "DNA sequencing with chain-terminating inhibitors",
            "author": "John Doe, Jane Doe",
            "author_list": [
                {"family": "Doe", "given": "John"},
                {"family": "Doe", "given": "Jane"},
            ],
        }
    )

    doc = full_doc.copy()
    errors = keys_missing_check(doc)
    assert not errors

    # check author -> author_list
    del doc["author_list"]
    error, = keys_missing_check(doc)

    error.fix_action()
    assert doc["author_list"][0]["family"] == "Doe"
    assert doc["author_list"][0]["given"] == "John"
    assert doc["author_list"][1]["family"] == "Doe"
    assert doc["author_list"][1]["given"] == "Jane"

    # check author_list -> author
    doc = full_doc.copy()
    del doc["author"]

    error, = keys_missing_check(doc)
    error.fix_action()
    assert doc["author"] == "Doe, John and Doe, Jane"


def test_refs_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import refs_check

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })

    # check: missing ref
    error, = refs_check(doc)
    assert error.msg == "Reference missing"

    error.fix_action()
    assert "ref" in doc
    assert doc["ref"] == "DNA_sequencing_Sanger"

    # check: empty ref
    doc["ref"] = "    "
    error, = refs_check(doc)
    assert error.msg == "Reference missing"

    # check: ref with invalid symbols
    doc["ref"] = "[myref]"
    error, = refs_check(doc)
    assert "Bad characters" in error.msg

    error.fix_action()
    assert doc["ref"] == "myref"


def test_duplicated_keys_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import duplicated_keys_check

    # check extend functionality
    papis.config.set("doctor-duplicated-keys-keys-extend", ["year"])
    docs = [
        papis.document.from_data({"ref": "ref1", "year": 1901}),
        papis.document.from_data({"ref": "ref2", "year": 1901}),
        papis.document.from_data({"ref": "ref1", "year": 2024}),
    ]

    errors = duplicated_keys_check(docs[0])
    assert not errors

    error, = duplicated_keys_check(docs[1])
    assert error.payload == "year"

    error, = duplicated_keys_check(docs[2])
    assert error.payload == "ref"


def test_duplicated_values_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import duplicated_values_check

    doc = papis.document.from_data({
        "files": ["a.pdf"],
        #: NOTE: this also tests entries that are not hashable
        "author_list": [{"given": "John", "family": "Smith", "affiliation": []}]
        })

    errors = duplicated_values_check(doc)
    assert not errors

    doc = papis.document.from_data({
        "files": ["a.pdf", "b.pdf", "c.pdf", "a.pdf"],
        #: NOTE: this also tests entries that are not hashable
        "author_list": [
            {"given": "John", "family": "Smith", "affiliation": []},
            {"given": "Jane", "family": "Smith", "affiliation": []},
            {"given": "John", "family": "Smith", "affiliation": []},
            ]
        })

    error_files, error_author_list = duplicated_values_check(doc)
    assert error_files.payload == "files"
    assert error_author_list.payload == "author_list"

    error_files.fix_action()
    assert doc["files"] == ["a.pdf", "b.pdf", "c.pdf"]

    error_author_list.fix_action()
    assert doc["author_list"] == [
        {"given": "John", "family": "Smith", "affiliation": []},
        {"given": "Jane", "family": "Smith", "affiliation": []}]


def test_bibtex_type_check(tmp_config: TemporaryConfiguration) -> None:
    import papis.bibtex
    from papis.commands.doctor import bibtex_type_check

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })

    error, = bibtex_type_check(doc)
    assert error.payload == "type"
    assert "does not define a type" in error.msg

    doc["type"] = "blog"
    error, = bibtex_type_check(doc)
    assert error.payload == "blog"
    assert "not a valid BibTeX type" in error.msg

    doc["type"] = "podcast"
    error, = bibtex_type_check(doc)
    assert error.payload == "podcast"
    error.fix_action()
    assert doc["type"] == "audio"

    for bib_type in papis.bibtex.bibtex_types:
        doc["type"] = bib_type
        errors = bibtex_type_check(doc)
        assert not errors


def test_key_type_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import key_type_check

    doc = papis.document.from_data({
        "author_list": [{"given": "F.", "family": "Sanger"}],
        "year": ["2023"],
        "projects": "test-key-project",
        "tags": "test-key-tag-1 test-key-tag-2      test-key-tag-3",
        })

    # check: invalid setting parsing
    papis.config.set("doctor-key-type-keys", ["year = WithoutColon"])
    errors = key_type_check(doc)
    assert not errors

    papis.config.set("doctor-key-type-keys", ["year:NotBuiltin"])
    errors = key_type_check(doc)
    assert not errors

    # check: incorrect type
    papis.config.set("doctor-key-type-keys", ["year:int"])
    error, = key_type_check(doc)
    assert error.payload == "year"

    # check: correct type
    papis.config.set("doctor-key-type-keys", ["  author_list :    list"])
    errors = key_type_check(doc)
    assert not errors

    # check: fix int
    papis.config.set("doctor-key-type-keys", ["year:int"])
    error, = key_type_check(doc)
    assert error.payload == "year"
    error.fix_action()
    assert doc["year"] == 2023

    # check: fix list
    papis.config.set("doctor-key-type-separator", " ")
    papis.config.set("doctor-key-type-keys", ["projects:list"])
    error, = key_type_check(doc)
    assert error.payload == "projects"
    error.fix_action()
    assert doc["projects"] == ["test-key-project"]

    papis.config.set("doctor-key-type-keys", ["tags:list"])
    error, = key_type_check(doc)
    assert error.payload == "tags"
    error.fix_action()
    assert doc["tags"] == ["test-key-tag-1", "test-key-tag-2", "test-key-tag-3"]

    papis.config.set("doctor-key-type-separator", ",")
    doc["tags"] = "test-key-tag-1,test-key-tag-2    ,  test-key-tag-3"
    error, = key_type_check(doc)
    assert error.payload == "tags"
    error.fix_action()
    assert doc["tags"] == ["test-key-tag-1", "test-key-tag-2", "test-key-tag-3"]

    papis.config.set("doctor-key-type-keys", [])
    papis.config.set("doctor-key-type-keys-extend", ["tags:str"])
    error, = key_type_check(doc)
    assert error.payload == "tags"
    error.fix_action()
    assert doc["tags"] == "test-key-tag-1,test-key-tag-2,test-key-tag-3"


def test_html_codes_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import html_codes_check

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })
    errors = html_codes_check(doc)
    assert not errors

    for amp in ("&amp;", "&#38;", "&#x26;", "&Amp;"):
        doc["title"] = f"DNA sequencing with chain-terminating inhibitors {amp} stuff"

        error, = html_codes_check(doc)
        assert error.payload == "title"

        error.fix_action()
        assert (doc["title"]
                == "DNA sequencing with chain-terminating inhibitors & stuff")

    # check extend functionality
    doc["publisher"] = "Society for Industrial &amp; Applied Mathematics (SIAM)"

    errors = html_codes_check(doc)
    assert not errors

    papis.config.set("doctor-html-codes-keys-extend", ["publisher"])

    error, = html_codes_check(doc)
    assert error.payload == "publisher"


def test_html_tags_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import html_tags_check

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })

    # check no errors
    errors = html_tags_check(doc)
    assert not errors

    # check multiple nested tags
    doc["title"] = (
        "<emph>DNA sequencing with chain-terminating <div>inhibitors</div></emph>"
        )
    error, = html_tags_check(doc)
    assert error.payload == "title"

    error.fix_action()
    assert doc["title"] == "DNA sequencing with chain-terminating inhibitors"

    # check tags with missing spaces
    doc["title"] = (
        "<emph>DNA</emph>sequencing with chain terminating inhibitors"
        )
    error, = html_tags_check(doc)
    assert error.payload == "title"

    error.fix_action()
    assert doc["title"] == "DNA sequencing with chain terminating inhibitors"

    # check extend functionality
    doc["publisher"] = "<strong>SIAM</strong>"

    errors = html_tags_check(doc)
    assert not errors

    papis.config.set("doctor-html-tags-keys-extend", ["publisher"])

    error, = html_tags_check(doc)
    assert error.payload == "publisher"


@pytest.mark.parametrize("basename", [
    "doctor_html_tags_jats_1",
    "doctor_html_tags_jats_2",
    "doctor_html_tags_jats_3",
    "doctor_html_tags_jats_4",
    ])
def test_html_tags_check_jats(tmp_config: TemporaryConfiguration,
                              basename: str) -> None:
    from papis.commands.doctor import html_tags_check

    with open(os.path.join(DOCTOR_RESOURCES, f"{basename}.xml"),
              encoding="utf-8") as f:
        abstract = f.read()

    with open(os.path.join(DOCTOR_RESOURCES, f"{basename}_out.txt"),
              encoding="utf-8") as f:
        expected = f.read()

    doc = papis.document.from_data({"abstract": abstract})

    error, = html_tags_check(doc)
    assert error.payload == "abstract"

    error.fix_action()
    assert "\n".join(doc["abstract"].split()) == "\n".join(expected.strip().split())
    assert doc["abstract"] == expected.strip()

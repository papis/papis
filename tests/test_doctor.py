import os
import pytest
import tempfile

import papis.api
import papis.document

from tests.testlib import TemporaryConfiguration


def test_files_check(tmp_config: TemporaryConfiguration,
                     monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.doctor import files_check
    monkeypatch.setattr(papis.api, "save_doc", lambda _: None)

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


def test_keys_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import keys_exist_check

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })

    error, = keys_exist_check(doc)
    assert error.payload == "ref"


def test_refs_check(tmp_config: TemporaryConfiguration,
                    monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.doctor import refs_check
    monkeypatch.setattr(papis.api, "save_doc", lambda _: None)

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })

    # check: missing ref
    error, = refs_check(doc)
    assert error.msg == "Reference missing."

    error.fix_action()
    assert "ref" in doc
    assert doc["ref"] == "DnaSequencingSanger"

    # check: empty ref
    doc["ref"] = "    "
    error, = refs_check(doc)
    assert error.msg == "Reference missing."

    # check: ref with invalid symbols
    doc["ref"] = "[myref]"
    error, = refs_check(doc)
    assert "Bad characters" in error.msg

    error.fix_action()
    assert doc["ref"] == "myref"


def test_duplicated_keys_check(tmp_config: TemporaryConfiguration) -> None:
    from papis.commands.doctor import duplicated_keys_check

    docs = [
        papis.document.from_data({"ref": "ref1"}),
        papis.document.from_data({"ref": "ref2"}),
        papis.document.from_data({"ref": "ref1"}),
    ]

    errors = duplicated_keys_check(docs[0])
    assert not errors

    errors = duplicated_keys_check(docs[1])
    assert not errors

    error, = duplicated_keys_check(docs[2])
    assert error.payload == "ref"


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

    for bib_type in papis.bibtex.bibtex_types:
        doc["type"] = bib_type
        errors = bibtex_type_check(doc)
        assert not errors


def test_key_type_check(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.doctor import key_type_check
    monkeypatch.setattr(papis.api, "save_doc", lambda _: None)

    doc = papis.document.from_data({
        "author_list": [{"given": "F.", "family": "Sanger"}],
        "year": ["2023"],
        "projects": "test-key-project",
        "tags": "test-key-tag-1 test-key-tag-2      test-key-tag-3",
        })

    # check: invalid setting parsing
    papis.config.set("doctor-key-type-check-keys", ["('year', Unknown)"])
    errors = key_type_check(doc)
    assert not errors

    papis.config.set("doctor-key-type-check-keys", ["('year', 'int', 'str')"])
    errors = key_type_check(doc)
    assert not errors

    papis.config.set("doctor-key-type-check-keys", ["('year', 'Unknown')"])
    errors = key_type_check(doc)
    assert not errors

    # check: incorrect type
    papis.config.set("doctor-key-type-check-keys", ["('year', 'int')"])
    error, = key_type_check(doc)
    assert error.payload == "year"

    # check: correct type
    papis.config.set("doctor-key-type-check-keys", ["('author_list', 'list')"])
    errors = key_type_check(doc)
    assert not errors

    # check: fix int
    papis.config.set("doctor-key-type-check-keys", ["('year', 'int')"])
    error, = key_type_check(doc)
    assert error.payload == "year"
    error.fix_action()
    assert doc["year"] == 2023

    # check: fix list
    papis.config.set("doctor-key-type-check-separator", " ")
    papis.config.set("doctor-key-type-check-keys", ["('projects', 'list')"])
    error, = key_type_check(doc)
    assert error.payload == "projects"
    error.fix_action()
    assert doc["projects"] == ["test-key-project"]

    papis.config.set("doctor-key-type-check-keys", ["('tags', 'list')"])
    error, = key_type_check(doc)
    assert error.payload == "tags"
    error.fix_action()
    assert doc["tags"] == ["test-key-tag-1", "test-key-tag-2", "test-key-tag-3"]

    papis.config.set("doctor-key-type-check-separator", ",")
    doc["tags"] = "test-key-tag-1,test-key-tag-2    ,  test-key-tag-3"
    error, = key_type_check(doc)
    assert error.payload == "tags"
    error.fix_action()
    assert doc["tags"] == ["test-key-tag-1", "test-key-tag-2", "test-key-tag-3"]

    papis.config.set("doctor-key-type-check-keys", ["('tags', 'str')"])
    error, = key_type_check(doc)
    assert error.payload == "tags"
    error.fix_action()
    assert doc["tags"] == "test-key-tag-1,test-key-tag-2,test-key-tag-3"


def test_html_codes_check(tmp_config: TemporaryConfiguration,
                          monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.doctor import html_codes_check
    monkeypatch.setattr(papis.api, "save_doc", lambda _: None)

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })
    errors = html_codes_check(doc)
    assert not errors

    for amp in ("&amp;", "&#38;", "&#x26;"):
        doc["title"] = (
            "DNA sequencing with chain-terminating inhibitors {} stuff"
            .format(amp))

        error, = html_codes_check(doc)
        assert error.payload == "title"

        error.fix_action()
        assert (doc["title"]
                == "DNA sequencing with chain-terminating inhibitors & stuff")


def test_html_tags_check(tmp_config: TemporaryConfiguration,
                         monkeypatch: pytest.MonkeyPatch) -> None:
    from papis.commands.doctor import html_tags_check
    monkeypatch.setattr(papis.api, "save_doc", lambda _: None)

    doc = papis.document.from_data({
        "title": "DNA sequencing with chain-terminating inhibitors",
        "author": "Sanger, F. and Nicklen, S. and Coulson, A. R.",
        })
    errors = html_tags_check(doc)
    assert not errors

    doc["title"] = (
        "<emph>DNA sequencing with chain-terminating <div>inhibitors</div></emph>"
        )
    error, = html_tags_check(doc)
    assert error.payload == "title"

    error.fix_action()
    assert doc["title"] == "DNA sequencing with chain-terminating inhibitors"

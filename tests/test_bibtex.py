import os
import re
import pytest

import papis
import papis.bibtex
import papis.document
import papis.logging

papis.logging.setup("DEBUG")

BIBTEX_RESOURCES = os.path.join(os.path.dirname(__file__), "resources", "bibtex")


def test_bibtex_to_dict():
    bibpath = os.path.join(BIBTEX_RESOURCES, "1.bib")
    bibs = papis.bibtex.bibtex_to_dict(bibpath)
    expected_keys = {
        "title",
        "author",
        "journal",
        "abstract",
        "volume",
        "issue",
        "pages",
        "numpages",
        "year",
        "month",
        "publisher",
        "doi",
        "url",
        }

    assert len(bibs) == 1
    for bib in bibs:
        assert not (expected_keys - bib.keys())

    assert bib["type"] == "article"
    assert re.match(r".*Rev.*", bib["journal"])
    assert re.match(r".*concurrent inter.*", bib["abstract"])


def test_bibkeys_exist():
    assert hasattr(papis.bibtex, "bibtex_keys")
    assert len(papis.bibtex.bibtex_keys) != 0


def test_bibtypes_exist():
    assert hasattr(papis.bibtex, "bibtex_types")
    assert len(papis.bibtex.bibtex_types) != 0


@pytest.mark.parametrize("bibfile", ["1.bib", "2.bib", "3.bib"])
def test_author_list_conversion(bibfile, overwrite=False):
    jsonfile = "{}_out.json".format(os.path.splitext(bibfile)[0])

    bibpath = os.path.join(BIBTEX_RESOURCES, bibfile)
    jsonpath = os.path.join(BIBTEX_RESOURCES, jsonfile)

    bib = papis.bibtex.bibtex_to_dict(bibpath)[0]
    if overwrite or not os.path.exists(jsonpath):
        with open(jsonpath, "w") as f:
            import json
            json.dump(bib, f,
                      indent=2,
                      sort_keys=True,
                      ensure_ascii=False)

    with open(jsonpath, "r") as f:
        import json
        expected = json.loads(f.read())

    assert bib["author_list"] == expected["author_list"]


def test_clean_ref() -> None:
    for (r, rc) in [
            ("Einstein über etwas und so 1923", "EinsteinUberEtwasUndSo1923"),
            ("Äöasf () : Aλבert Eιنς€in", "AoasfAlbertEinseurin"),
            (r"Albert_Ein\_stein\.1923.b", "AlbertEin_stein.1923B"),
            ]:
        assert rc == papis.bibtex.ref_cleanup(r)


def test_to_bibtex_wrong_type() -> None:
    """Test no BibTeX entry is constructed for incorrect types."""

    doc = papis.document.from_data({
        "type": "fictional",
        "ref": "MyDocument",
        "author": "Albert Einstein",
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350
        })

    result = papis.bibtex.to_bibtex(doc)
    assert not result


def test_to_bibtex_no_ref() -> None:
    """Test no BibTeX entry is constructed for invalid references."""
    doc = papis.document.from_data({
        "type": "techreport",
        "author": "Albert Einstein",
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        })

    # NOTE: this seems to be one of the few ways to fail the ref construction,
    # i.e. set it to some invalid characters.
    papis.config.set("ref-format", "--")

    result = papis.bibtex.to_bibtex(doc)
    assert not result


def test_to_bibtex_formatting() -> None:
    """Test formatting for the `to_bibtex` function."""
    doc = papis.document.from_data({
        "type": "report",
        "author": "Albert Einstein",
        "title": "The Theory of Everything",
        "journal": "Nature",
        "year": 2350,
        "ref": "MyDocument"
        })

    expected_bibtex = (
        "@report{MyDocument,\n"
        + "  author = {Albert Einstein},\n"
        + "  journal = {Nature},\n"
        + "  title = {The Theory of Everything},\n"
        + "  year = {2350},\n"
        + "}"
        )

    assert papis.bibtex.to_bibtex(doc) == expected_bibtex

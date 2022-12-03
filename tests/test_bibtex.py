import os
import re
import pytest

import papis
import papis.bibtex
import papis.document

import logging
logging.basicConfig(level=logging.DEBUG)

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

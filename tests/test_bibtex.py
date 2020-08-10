import os
import re
import pytest

import papis
import papis.bibtex
import papis.document

import logging
logging.basicConfig(level=logging.DEBUG)


def test_bibtex_to_dict():
    bibpath = os.path.join(os.path.dirname(__file__),
                           "resources", "bibtex", "1.bib")
    bibs = papis.bibtex.bibtex_to_dict(bibpath)
    keys = [ "title",
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
             "url" ]

    assert len(bibs) == 1
    for bib in bibs:
        for key in keys:
            assert key in bib

    assert bib["type"] == "article"
    assert re.match(r".*Rev.*", bib["journal"])
    assert re.match(r".*concurrent inter.*", bib["abstract"])


def test_bibkeys_exist():
    assert(len(papis.bibtex.bibtex_keys) != 0)


def test_bibtypes_exist():
    assert(len(papis.bibtex.bibtex_types) != 0)


@pytest.mark.parametrize("bibfile", ["1.bib", "2.bib", "3.bib"])
def test_author_list_conversion(bibfile, overwrite=False):
    jsonfile = "{}_out.json".format(os.path.splitext(bibfile)[0])
    bibpath = os.path.join(os.path.dirname(__file__),
            "resources", "bibtex", bibfile)
    jsonpath = os.path.join(os.path.dirname(__file__),
            "resources", "bibtex", jsonfile)

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

    assert bib['author_list'] == expected['author_list']


def test_clean_ref() -> None:
    for (r, rc) in [("Einstein über etwas und so 1923",
                     "EinsteinUberEtwasUndSo1923"),
                    ("Äöasf () : Aλבert Eιنς€in",
                     "AoasfAlbertEinseurin")
                   ]:
        assert rc == papis.bibtex.ref_cleanup(r)

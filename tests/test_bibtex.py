import unittest
import logging
import tempfile
import os
import re

import papis
import papis.bibtex

logging.basicConfig(level=logging.DEBUG)

def test_bibtex_to_dict():
    bib_file = os.path.join(
        os.path.dirname(__file__), 'resources', 'bibtex', '1.bib')
    bib_dic = papis.bibtex.bibtex_to_dict(bib_file)[0]
    keys = [
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
      "url"
      ]
    assert(bib_dic["type"] == "article")
    for key in keys:
        assert(key in list(bib_dic.keys()))
    assert(re.match(r".*Rev.*", bib_dic['journal']))
    assert(re.match(r".*concurrent inter.*", bib_dic['abstract']))

def test_bibkeys_exist():
    assert(len(papis.bibtex.bibtex_keys) != 0)

def test_bibtypes_exist():
    assert(len(papis.bibtex.bibtex_types) != 0)

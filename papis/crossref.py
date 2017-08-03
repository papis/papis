#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Adapted for papis from
#   author: François-Xavier Coudert
#   e-mail: fxcoudert@gmail.com
#   license: MIT License
#   src: https://github.com/fxcoudert/tools/blob/master/doi2bib
#
from __future__ import unicode_literals
import logging
logger = logging.getLogger("crossref")
logger.debug("#############################")

import sys
import unicodedata
import re

# CrossRef queries
#
# CrossRef documentation comes from here:
# http://labs.crossref.org/site/quick_and_dirty_api_guide.html
#
# You need a CrossRef API key. 
#
CROSSREF_KEY = "fx.coudert@chimie-paristech.fr"
#
# Using Google allows one to find other API keys:
# zter:zter321
# ourl_rdmpage:peacrab
# egon@spenglr.com
# s_allannz@yahoo.com
# dollar10boy@hotmail.com

# LaTeX accents replacement
latex_accents = {
  "à": "\\`a",  # Grave accent
  "è": "\\`e",
  "ì": "\\`{\\i}",
  "ò": "\\`o",
  "ù": "\\`u",
  "ỳ": "\\`y",
  "À": "\\`A",
  "È": "\\`E",
  "Ì": "\\`{\\I}",
  "Ò": "\\`O",
  "Ù": "\\`U",
  "Ỳ": "\\`Y",
  "á": "\\'a",  # Acute accent
  "ć": "\\'c",
  "é": "\\'e",
  "í": "\\'{\\i}",
  "ó": "\\'o",
  "ú": "\\'u",
  "ý": "\\'y",
  "Á": "\\'A",
  "É": "\\'E",
  "Í": "\\'{\\I}",
  "Ó": "\\'O",
  "Ú": "\\'U",
  "Ý": "\\'Y",
  "â": "\\^a",  # Circumflex
  "ê": "\\^e",
  "î": "\\^{\\i}",
  "ô": "\\^o",
  "û": "\\^u",
  "ŷ": "\\^y",
  "Â": "\\^A",
  "Ê": "\\^E",
  "Î": "\\^{\\I}",
  "Ô": "\\^O",
  "Û": "\\^U",
  "Ŷ": "\\^Y",
  "ä": "\\\"a",  # Umlaut or dieresis
  "ë": "\\\"e",
  "ï": "\\\"{\\i}",
  "ö": "\\\"o",
  "ü": "\\\"u",
  "ÿ": "\\\"y",
  "Ä": "\\\"A",
  "Ë": "\\\"E",
  "Ï": "\\\"{\\I}",
  "Ö": "\\\"O",
  "Ü": "\\\"U",
  "Ÿ": "\\\"Y",
  "ã": "\\~{a}",  # Tilde
  "ñ": "\\~{n}",
  "ă": "\\u{a}",  # Breve
  "ĕ": "\\u{e}",
  "ŏ": "\\u{o}",
  "š": "\\v{s}",  # Caron
  "č": "\\v{c}",
  "ç": "\\c{c}",  # Cedilla
  "Ç": "\\c{C}",
  "œ": "{\\oe}",  # Ligatures
  "Œ": "{\\OE}",
  "æ": "{\\ae}",
  "Æ": "{\\AE}",
  "å": "{\\aa}",
  "Å": "{\\AA}",
  "–": "--",  # Dashes
  "—": "---",
  "−": "--",
  "ø": "{\\o}",  # Misc latin-1 letters
  "Ø": "{\\O}",
  "ß": "{\\ss}",
  "¡": "{!`}",
  "¿": "{?`}",
  "\\": "\\\\",  # Characters that should be quoted
  "~": "\\~",
  "&": "\\&",
  "$": "\\$",
  "{": "\\{",
  "}": "\\}",
  "%": "\\%",
  "#": "\\#",
  "_": "\\_",
  "≥": "$\\ge$",  # Math operators
  "≤": "$\\le$",
  "≠": "$\\neq$",
  "©": "\copyright", # Misc
  "ı": "{\\i}",
  "α": "$\\alpha$",
  "β": "$\\beta$",
  "γ": "$\\gamma$",
  "δ": "$\\delta$",
  "ε": "$\\epsilon$",
  "η": "$\\eta$",
  "θ": "$\\theta$",
  "λ": "$\\lambda$",
  "µ": "$\\mu$",
  "ν": "$\\nu$",
  "π": "$\\pi$",
  "σ": "$\\sigma$",
  "τ": "$\\tau$",
  "φ": "$\\phi$",
  "χ": "$\\chi$",
  "ψ": "$\\psi$",
  "ω": "$\\omega$",
  "°": "$\\deg$",
  "‘": "`",  # Quotes
  "’": "'",
  "′": "$^\\prime$",
  "“": "``",
  "”": "''",
  "‚": ",",
  "„": ",,",
  "\xa0": " ",     # Unprintable characters
}


def replace_latex_accents(str):
    s = unicodedata.normalize('NFC', str)
    return "".join([latex_accents[c] if c in latex_accents else c for c in s])


def validate_doi(doi):
    """We check that the DOI can be resolved by official means.  If so, we
    return the resolved URL, otherwise, we return None (which means the DOI is
    invalid).

    :param doi: Doi identificator
    :type  doi: str
    """
    from urllib.request import urlopen, Request
    handle_url = "http://dx.doi.org/" + doi
    logger.debug('handle url %s' % handle_url)
    try:
      handle = urlopen(handle_url)
    except:
      return None

    resolvedURL = handle.geturl()
    logger.debug('resolved url %s' % resolvedURL)
    if resolvedURL[0:18] == "http://dx.doi.org/":
      return None
    else:
      return resolvedURL




def get_cross_ref(doi):
    """Get the XML from CrossRef
    """
    global CROSSREF_KEY
    global logger
    import xml.dom.minidom
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    params = urlencode({
        "id": "doi:" + doi,
        "noredirect": "true",
        "pid": CROSSREF_KEY,
        "format": "unixref"
    })
    req_url = "http://www.crossref.org/openurl/?" + params
    url = Request(req_url)
    doc = urlopen(url).read()
    logger.debug("Request url: %s" % req_url)

    # Parse it
    doc = xml.dom.minidom.parseString(doc)
    records = doc.getElementsByTagName("journal")

    # No results. Is it a valid DOI?
    if len(records) == 0:
        res = validate_doi(doi)
        if res is None:
            raise Exception("Invalid DOI")
        else:
            raise Exception("Can't locate metadata")

    if (len(records) != 1):
        raise Exception("CrossRef returned more than one record")

    record = records[0]

    # Helper functions
    def findItemNamed(container, name):
        list = container.getElementsByTagName(name)
        if (len(list) == 0):
            return None
        else:
            return list[0]
    def data(node):
        if node is None:
            return None
        else:
            return node.firstChild.data

    res = dict(doi=doi)

    # Journal information
    journal = findItemNamed(record, "journal_metadata")
    if journal:
        res["fullJournal"] = data(findItemNamed(journal, "full_title"))
        res["shortJournal"] = data(findItemNamed(journal, "abbrev_title"))

    # Volume information
    issue = findItemNamed(record, "journal_issue")
    res["issue"] = data(findItemNamed(issue, "issue"))
    res["volume"] = data(findItemNamed(issue, "volume"))
    res["year"] = data(findItemNamed(issue, "year"))

    # Other information
    other = findItemNamed(record, "journal_article")
    res["title"] = data(findItemNamed(other, "title"))
    res["firstPage"] = data(findItemNamed(other, "first_page"))
    res["lastPage"] = data(findItemNamed(other, "last_page"))
    res["doi"] = data(findItemNamed(other, "doi"))
    if res["year"] is None:
        res["year"] = data(findItemNamed(other, "year"))

    # Author list
    res["authors"] = []
    for node in other.getElementsByTagName("person_name"):
        surname = data(findItemNamed(node, "surname"))
        givenName = data(findItemNamed(node, "given_name"))

    if givenName is None:
        res["authors"].append(surname)
    elif surname is None:
        res["authors"].append(givenName)
    else:
        res["authors"].append(surname + ", " + givenName)

    # Create a citation key
    r = re.compile("\W")
    if len(res["authors"]) > 0:
        key = r.sub('', res["authors"][0].split(",")[0])
    else:
        key = ""
    if res["year"] is not None:
        key = key + res["year"]

    res["key"] = key

    return res


def bibtex_entry(ref):
    # Output all information in bibtex format
    latex = replace_latex_accents
    s = "@article{" + ref["key"] + ",\n"

    if len(ref["authors"]) > 0:
        s = s + "  author = {" + latex(" and ".join(ref["authors"])) + "},\n"

    if ref["doi"] is not None:
        s = s + "  doi = {" + ref["doi"] + "},\n"
    try:
        s = s + "  url = {" + ref["url"] + "},\n"
    except:
        s = s + "  url = {https://doi.org/"+ ref["doi"] + "},\n"
    if ref["title"] is not None:
        s = s + "  title = {" + latex(ref["title"]) + "},\n"
    if ref["shortJournal"] is not None:
        s = s + "  journal = {" + latex(ref["shortJournal"]) + "},\n"
    if ref["year"] is not None:
        s = s + "  year = {" + latex(ref["year"]) + "},\n"
    if ref["volume"] is not None:
        s = s + "  volume = {" + latex(ref["volume"]) + "},\n"
    if ref["issue"] is not None:
        s = s + "  issue = {" + latex(ref["issue"]) + "},\n"
    if ref["firstPage"] is not None:
        if ref["lastPage"] is not None:
            s = s + "  pages = {" + latex(ref["firstPage"]) + "--" + latex(ref["lastPage"]) + "},\n"
        else:
            s = s + "  pages = {" + latex(ref["firstPage"]) + "},\n"

    s = s + "}"
    return s


def doi_to_data(doi):
    """Search through crossref and get a dictionary containing the data

    :param doi: Doi identificator
    :type  doi: str
    :returns: Dictionary containing the data

    """
    global logger
    try:
        data = get_cross_ref(doi)
    except Exception as e:
        logger.error(
            "Couldn't resolve DOI '" + doi + "' through CrossRef: " + str(e) + "\n"
        )
        return dict()
    else:
        return data


def doi_to_bibtex(doi):
    """Search throu crossref information from doi entry

    :param doi: Doi identificator
    :type  doi: str
    :returns: Bibtex entry string

    """
    global logger
    try:
        ref = get_cross_ref(doi)
    except Exception as e:
        logger.error(
            "Couldn't resolve DOI '" + doi + "' through CrossRef: " + str(e) + "\n"
        )
    else:
        return bibtex_entry(ref)

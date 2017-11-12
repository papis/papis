import re
import logging
import os
import papis.config

logger = logging.getLogger("bibtex")

bibtex_types = [
  "article",
  "book",
  "booklet",
  "conference",
  "inbook",
  "incollection",
  "inproceedings",
  "manual",
  "mastersthesis",
  "misc",
  "phdthesis",
  "proceedings",
  "techreport",
  "unpublished"
] + re.sub(r" *", "", papis.config.get('extra-bibtex-types')).split(',')

bibtex_keys = [
  "address",
  "annote",
  "author",
  "booktitle",
  "doi",
  "chapter",
  "crossref",
  "edition",
  "editor",
  "howpublished",
  "institution",
  "journal",
  "key",
  "month",
  "note",
  "number",
  "organization",
  "pages",
  "publisher",
  "school",
  "series",
  "title",
  "volume",
  "year"
  ] + re.sub(r" *", "", papis.config.get('extra-bibtex-keys')).split(',')


def bibtexparser_entry_to_papis(entry):
    """Convert keys of a bib entry in bibtexparser format to papis compatible
    format.

    :param entry: Dictionary with keys of bibtexparser format.
    :type  entry: dict
    :returns: Dictionary with keys of papis format.

    """
    result = dict()
    for key in entry.keys():
        if key == 'ID':
            result['ref'] = entry[key]
        elif key == 'ENTRYTYPE':
            result['type'] = entry[key]
        elif key == 'link':
            result['url'] = entry[key]
        else:
            result[key] = entry[key]
    return result


def bibtex_to_dict(bibtex):
    """
    Convert bibtex file to dict

    .. code:: python

        { type: "article ...", "ref": "example1960etAl", author:" ..."}

    :param bibtex: Bibtex file path or bibtex information in string format.
    :type  bibtex: str
    :returns: Dictionary with bibtex information with keys that bibtex
        formally recognizes.
    :rtype:  list
    """
    import bibtexparser
    # bibtexparser has too many debug messages to be useful
    logging.getLogger("bibtexparser.bparser").setLevel(logging.WARNING)
    global logger
    result = dict()
    if os.path.exists(bibtex):
        with open(bibtex) as fd:
            logger.debug("Reading in file %s" % bibtex)
            text = fd.read()
    else:
        text = bibtex
    logger.debug("Removing comments...")
    text = re.sub(r" +%.*", "", text)
    logger.debug("Removing empty lines...")
    text = re.sub(r"^\s*$", "", text)
    entries = bibtexparser.loads(text).entries
    # Clean entries
    return [bibtexparser_entry_to_papis(entry) for entry in entries]


#! /usr/bin/env python3
# papis-short-help: Abbreviate journal titles.
# Copyright © 2017 Alejandro Gallo. GPLv3

"""
.. note::

    This is just an example script and does not follow the ISO 4 standard to the
    letter, but only implements basic abbreviations.

This command abbreviates the journal title of a document according to the ISO 4
standard. For example, calling::

    papis abbrev -a Einstein

will add an ``abbrev_journal_title`` key to all documents matching the query.
For example, the following abbreviations are made::

    'Journal of Fluid Mechanics'        > 'J. Fluid Mech.'
    'ACM Transactions on Graphics'      > 'ACM Trans. On Graph.'.
    'Annual Review of Fluid Mechanics'  > 'Annu. Rev. Fluid Mech.'.

Command Options
^^^^^^^^^^^^^^^

.. papis-config:: ltwa
    :section: abbrev

    The path of the ``LTWA.json`` file containing an abbreviation list.

.. papis-config:: ignore-words
    :section: abbrev

    A list of words to ignore in the abbreviation, e.g. ``"the"`` is ignored
    by default, but other such short words may be required.

.. papis-config:: ignore-acronyms
    :section: abbrev

    A list of words to always uppercase and leave unabbreviated if they appear
    in the journal title.
"""

import os
import json
from typing import Dict, Optional

import papis.api
import papis.document
import papis.logging

papis.logging.setup()
logger = papis.logging.get_logger("papis.commands.abbrev")

papis.config.register_default_settings({
    "abbrev": {
        "ltwa": "",
        "ignore-acronyms": [],
        "ignore-words": [],
    }
})

# load the LTWA dictionary
LTWA_FILE_PATH = papis.config.getstring("ltwa", section="abbrev")
if not LTWA_FILE_PATH:
    SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    LTWA_FILE_PATH = os.path.join(SCRIPT_PATH, "LTWA.json")

try:
    with open(LTWA_FILE_PATH, encoding="utf-8") as f:
        LTWA_ABBREVS = json.load(f)
except FileNotFoundError:
    LTWA_ABBREVS = {}

# List of short words that are omitted in abbreviations
ABBREV_IGNORE_WORDS = frozenset([
    # en
    "of", "in", "the", "and", "part",
    # fr
    "des", "de", "dans", "la", "l", "le", "et",
    # de
    "fur", "und",
    # ru
    "i"
]) | frozenset(papis.config.getlist("ignore-words", section="abbrev"))

# List of acronyms that should remain in uppercase in abbreviations
ABBREV_IGNORE_ACRONYMS = frozenset([
    "3D", "2D", "ACS", "ACI", "ACH", "MRS", "ECS",
    "LC", "GC", "NATO", "ASI", "PLOS",
    "AAPG", "AAPS", "AATCC", "ABB", "DDR",
    "ACA", "ACM", "APL", "AQEIC", "DLG",
    "ASSAY", "ASTM", "ASTRA",
    "ESAIM", "SSRN", "SIAM",
]) | frozenset(papis.config.getlist("ignore-acronyms", section="abbrev"))


def ltwa_abbreviate(full_journal_name: str, d: Optional[Dict[str, str]] = None) -> str:
    """
    Abbreviates a journal name using International Standard Serial
    Number (ISSN) guidelines.

    ISSN abbreviations list last updated 14/09/2017. Available
    `here <http://www.issn.org/services/online-services/access-to-the-ltwa/>`__
    for download as a CSV file.
    """

    if d is None:
        d = LTWA_ABBREVS

    # initialize a new list
    return_list = []
    hyphenation = False

    # if just one word, return that word
    words = full_journal_name.split(" ")
    if len(words) <= 1:
        return full_journal_name

    # for all words in the full name...
    words = full_journal_name.replace("-", " _").split(" ")
    for word in words:
        # add a full stop to allow [:-i] to function as intended
        lower_word = f"{word.lower()}."
        hyphenation = False

        if "-" in lower_word:
            # if word contains a hyphen, remove it and set 'hyphenation' to True
            lower_word = lower_word.replace("-", "")
            hyphenation = True
            logger.debug("Processing word '%s'.", lower_word)

        # shrink the word from right to left.
        for i in range(len(lower_word)):
            # If it matches a suffix / prefix
            suffix = lower_word[:-i]
            if suffix in d:
                # ...add it to the list.
                if hyphenation:
                    return_list.append(f"-{d[suffix]}")
                else:
                    return_list.append(d[suffix])
                break

            elif lower_word[:-1] in ABBREV_IGNORE_WORDS:
                # Don't add the word if in ignore list
                break

            # If we get to the end of the word and it doesn't match...
            elif i == len(lower_word[:-1]):
                # ...add the full word to the list.
                if hyphenation:
                    return_list.append(f"-{lower_word[:-1]}")
                else:
                    return_list.append(lower_word[:-1])

    # concatenate the list to a string, capitalising the first letter of each word
    for j, word in enumerate(return_list):
        if word.upper().replace("-", "") in ABBREV_IGNORE_ACRONYMS:
            return_list[j] = word.upper()
        else:
            return_list[j] = word.capitalize()

    return " ".join(return_list).replace(" -", "-")


def run(query: str, all_: bool = True) -> int:
    if not LTWA_ABBREVS:
        logger.error("'LTWA.json' not found at '%s'!", LTWA_FILE_PATH)
        logger.error("Did you forget to copy or symlink it to your config directory?")
        return 1

    documents = papis.api.get_documents_in_lib(
        papis.api.get_lib_name(),
        search=query
    )

    if all_:
        picked_documents = documents
    else:
        picked_documents = list(papis.api.pick_doc(documents))

    for doc in picked_documents:
        if "journal" not in doc:
            logger.info("The document does not have a 'journal' set.")
        else:
            full_journal_title = doc["journal"]

            # Get the data from the picked document
            data = papis.document.to_dict(doc)

            # Set the new abbrev_journal_title
            data["abbrev_journal_title"] = ltwa_abbreviate(full_journal_title)
            logger.info("%s: Abbreviated '%s' to '%s'.",
                        data["ref"],
                        full_journal_title,
                        data["abbrev_journal_title"])

            # Update the data and save
            doc.update(data)
            doc.save()

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "query",
        default=papis.config.getstring("default-query-string"),
        help="A query to run over the documents")
    parser.add_argument(
        "-a", "--all", dest="all_", action="store_true",
        help="Apply command to all documents returned by the query")
    args = parser.parse_args()

    raise SystemExit(run(args.query, all_=args.all_))

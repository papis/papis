from typing import TYPE_CHECKING

import papis.logging

if TYPE_CHECKING:
    import papis.document

logger = papis.logging.get_logger(__name__)


def to_bibtex(document: "papis.document.Document", *, indent: int = 2) -> str:
    """Convert a document to a BibTeX containing only valid metadata.

    To convert a document, it must have a valid BibTeX type
    (see :data:`~papis.bibtex.bibtex_types`) and a valid reference under the
    ``"ref"`` key (see :func:`~papis.bibtex.create_reference`). Valid BibTeX keys
    (see :data:`~papis.bibtex.bibtex_keys`) are exported, while other keys are
    ignored (see :data:`~papis.bibtex.bibtex_ignore_keys`) with the following rules:

    * :confval:`bibtex-unicode` is used to control whether the field values can
      contain unicode characters.
    * :confval:`bibtex-journal-key` is used to define the field name for the journal.
    * :confval:`bibtex-export-file` is used to also add a ``"file"`` field to
      the BibTeX entry, which can be used by e.g. Zotero to import documents.

    :param indent: set indentation for the BibTeX fields.
    :returns: a string containing the document metadata in a BibTeX format.
    """
    from papis.bibtex import bibtex_type_converter, bibtex_types

    bibtex_type = ""

    # determine bibtex type
    if "type" in document:
        if document["type"] in bibtex_types:
            bibtex_type = document["type"]
        elif document["type"] in bibtex_type_converter:
            bibtex_type = bibtex_type_converter[document["type"]]
        else:
            logger.error("Invalid BibTeX type '%s' in document: '%s'.",
                         document["type"],
                         document.get_info_file())
            return ""

    if not bibtex_type:
        bibtex_type = "article"

    from papis.bibtex import create_reference

    # determine ref value
    ref = create_reference(document)
    if not ref:
        logger.error("No valid ref found for document: '%s'.",
                     document.get_info_file())

        return ""

    logger.debug("Using ref '%s'.", ref)

    from bibtexparser.latexenc import string_to_latex

    # process keys
    from papis.config import getboolean, getstring

    supports_unicode = getboolean("bibtex-unicode")
    journal_key = getstring("bibtex-journal-key")

    entry = {
        "ID": ref,
        "ENTRYTYPE": bibtex_type,
    }

    from papis.bibtex import (
        author_list_to_author,
        bibtex_ignore_keys,
        bibtex_key_converter,
        bibtex_keys,
        bibtex_verbatim_fields,
    )

    for key in sorted(document):
        bib_key = bibtex_key_converter.get(key, key)
        if bib_key not in bibtex_keys:
            continue

        if bib_key in bibtex_ignore_keys:
            continue

        bib_value = str(document[key])
        logger.debug("Processing BibTeX entry: '%s: %s'.", bib_key, bib_value)

        if bib_key == "journal":
            if journal_key in document:
                bib_value = str(document[journal_key])
            else:
                logger.warning(
                    "'journal-key' key '%s' is not present for ref '%s'.",
                    journal_key, document["ref"])
        elif bib_key == "author" and "author_list" in document:
            bib_value = author_list_to_author(document, document["author_list"])

        override_key = f"{bib_key}_latex"
        if override_key in document:
            bib_value = str(document[override_key])

        if not supports_unicode and bib_key not in bibtex_verbatim_fields:
            bib_value = string_to_latex(bib_value)

        entry[bib_key] = bib_value

    # handle file exporting
    from papis.exceptions import DefaultSettingValueMissing
    try:
        # NOTE: this option is deprecated and should be removed in the future
        export_file = getboolean("bibtex-export-zotero-file")
        logger.warning("The 'bibtex-export-zotero-file' option is deprecated. "
                       "Use 'bibtex-export-file' instead.")
    except DefaultSettingValueMissing:
        export_file = getboolean("bibtex-export-file")

    files = document.get_files()
    if export_file and files:
        entry["file"] = ";".join(files)

    from bibtexparser import dumps
    from bibtexparser.bibdatabase import BibDatabase
    from bibtexparser.bwriter import BibTexWriter

    db = BibDatabase()
    db.entries = [entry]

    writer = BibTexWriter()
    writer.add_trailing_comma = True
    writer.indent = " " * indent

    return str(dumps(db, writer=writer).strip())


def exporter(documents: list["papis.document.Document"]) -> str:
    """Convert documents into a list of BibLaTeX entries"""
    from papis.document import describe

    result = []
    for doc in documents:
        bib = to_bibtex(doc)
        if not bib:
            logger.warning("Skipping document export: '%s'.", describe(doc))
            continue

        result.append(bib)

    return "\n\n".join(result)

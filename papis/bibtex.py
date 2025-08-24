"""
A set of utilities for working with BibTeX and BibLaTeX (as described in
the `manual`_).

.. _manual: https://ctan.org/pkg/biblatex?lang=en
.. _biblatex_software: https://ctan.org/pkg/biblatex-software?lang=en
"""
import os
import string
from functools import cache
from typing import TYPE_CHECKING, Any

import papis.config
import papis.logging

if TYPE_CHECKING:
    import papis.document

logger = papis.logging.get_logger(__name__)

#: Regular BibLaTeX types (`Section 2.1.1 <manual_>`_).
bibtex_standard_types = frozenset([
    "article",
    "book", "mvbook", "inbook", "bookinbook", "suppbook", "booklet",
    "collection", "mvcollection", "incollection", "suppcollection",
    "dataset",
    "manual",
    "misc",
    "online",
    "patent",
    "periodical", "suppperiodical",
    "proceedings", "mvproceedings", "inproceedings",
    "reference", "mvreference", "inreference",
    "report",
    # "set",
    "software",
    "thesis",
    "unpublished",
    # "xdata",
    # "custom[a-f]",
])

#: BibLaTeX type aliases (`Section 2.1.2 <manual_>`_).
bibtex_type_aliases = {
    "conference": "inproceedings",
    "electronic": "online",
    "mastersthesis": "thesis",
    "phdthesis": "thesis",
    "techreport": "report",
    "www": "online",
}

#: Non-standard BibLaTeX types (`Section 2.1.3 <manual_>`_).
bibtex_non_standard_types = frozenset([
    "artwork",
    "audio",
    "bibnote",
    "commentary",
    "image",
    "jurisdiction",
    "legislation",
    "legal",
    "letter",
    "movie",
    "music",
    "performance",
    "review",
    "standard",
    "video",
])

#: BibLaTeX Software types (`Section 2 <biblatex_software_>`_).
biblatex_software_types = frozenset([
    "software",
    "softwareversion",
    "softwaremodule",
    "codefragment",
])

#: A set of known BibLaTeX types (as described in Section 2.1 of the `manual`_).
#: These types are a union of the types above and can be extended with
#: :confval:`extra-bibtex-types`.
bibtex_types = (
    bibtex_standard_types
    | frozenset(bibtex_type_aliases)
    | bibtex_non_standard_types
    | biblatex_software_types
    | frozenset(papis.config.getlist("extra-bibtex-types")))


#: BibLaTeX data fields (`Section 2.2.2 <manual_>`_).
bibtex_standard_keys = frozenset([
    "abstract", "addendum", "afterword", "annotation", "annotator", "author",
    "authortype", "bookauthor", "bookpagination", "booksubtitle", "booktitle",
    "booktitleaddon", "chapter", "commentator", "date", "doi", "edition",
    "editor", "editora", "editorb", "editorc", "editortype", "editoratype",
    "editorbtype", "editorctype", "eid", "entrysubtype", "eprint", "eprintclass",
    "eprinttype", "eventdate", "eventtitle", "eventtitleaddon", "file",
    "foreword", "holder", "howpublished", "indextitle", "institution",
    "introduction", "isan", "isbn", "ismn", "isrn", "issn", "issue",
    "issuesubtitle", "issuetitle", "issuetitleaddon", "iswc", "journalsubtitle",
    "journaltitle", "journaltitleaddon", "label", "language", "library",
    "location", "mainsubtitle", "maintitle", "maintitleaddon", "month",
    "nameaddon", "note", "number", "organization", "origdate", "origlanguage",
    "origlocation", "origpublisher", "origtitle", "pages", "pagetotal",
    "pagination", "part", "publisher", "pubstate", "reprinttitle",
    "series", "shortauthor", "shorteditor", "shorthand", "shorthandintro",
    "shortjournal", "shortseries", "shorttitle", "subtitle", "title",
    "titleaddon", "translator", "url", "urldate", "venue", "version",
    "volume", "volumes", "year",
    # fields that we ignore
    # type,
])

#: BibLaTeX field aliases (`Section 2.2.5 <manual_>`_).
bibtex_key_aliases = {
    "address": "location",
    "annote": "annotation",  # spell: disable
    "archiveprefix": "eprinttype",
    "journal": "journaltitle",
    "key": "sortkey",
    "pdf": "file",
    "primaryclass": "eprintclass",
    "school": "institution",
}

#: Special BibLaTeX fields (`Section 2.2.3 <manual_>`_).
bibtex_special_keys = frozenset([
    "crossref", "entryset", "execute", "gender", "langid", "langidopts",
    "ids", "indexsorttitle", "keywords", "options", "presort", "related",
    "relatedoptions", "relatedtype", "relatedstring", "sortkey", "sortname",
    "sortshorthand", "sorttitle", "sortyear", "xdata", "xref",
    # custom fields (Section 2.3.4)
    # name[a-c]
    # name[a-c]type
    # list[a-f]
    # user[a-f]
    # verb[a-c]
])

#: BibLaTeX software keys (`Section 3 <biblatex_software_>`_). Most of these
#: keys are already standard BibLaTeX keys from :data:`bibtex_standard_keys`.
biblatex_software_keys = frozenset([
    "abstract", "author", "date", "editor", "file", "doi", "eprint", "eprinttype",
    "eprintclass", "hal_id", "hal_version", "license", "month", "note",
    "institution", "introducedin", "organization", "publisher", "related",
    "relatedtype", "relatedstring", "repository", "swhid", "subtitle",
    "title", "url", "urldate", "version", "year",
])

#: A set of known BibLaTeX fields (as described in Section 2.2 of the `manual`_).
#: These fields are a union of the above fields and can be extended with
#: extended with :confval:`extra-bibtex-keys`.
bibtex_keys = (
    bibtex_standard_keys
    | frozenset(bibtex_key_aliases)
    | bibtex_special_keys
    | biblatex_software_keys
    | frozenset(papis.config.getlist("extra-bibtex-keys")))

#: A mapping of supported BibLaTeX entry types (see :data:`bibtex_types`) to
#: BibLaTeX fields (see :data:`bibtex_keys`). Each value is a tuple of disjoint
#: sets that can contain multiple fields required for the particular type, e.g.
#: an article may require either a ``year`` or a ``date`` field.
bibtex_type_required_keys = {
    None: (),
    # regular types (Section 2.1.1)
    "article": (
        {"author"}, {"title"}, {"journaltitle", "eprinttype"}, {"year", "date"}),
    "book": ({"author"}, {"title"}, {"year", "date"}),
    "inbook": ({"author"}, {"title"}, {"booktitle"}, {"year", "date"}),
    "booklet": ({"author", "editor"}, {"title"}, {"year", "date"}),
    "collection": ({"editor"}, {"title"}, {"year", "date"}),
    "incollection": (
        {"author"}, {"title"}, {"editor"}, {"booktitle"}, {"year", "date"}),
    "manual": ({"author", "editor"}, {"title"}, {"year", "date"}),
    "misc": ({"author", "editor"}, {"title"}, {"year", "date"}),
    "online": (
        {"author", "editor"}, {"title"}, {"year", "date"}, {"doi", "eprint", "url"}),
    "patent": ({"author"}, {"title"}, {"number"}, {"year", "date"}),
    "periodical": ({"editor"}, {"title"}, {"year", "date"}),
    "proceedings": ({"title"}, {"year", "date"}),
    "inproceedings": ({"author"}, {"title"}, {"booktitle"}, {"year", "date"}),
    "dataset": ({"author", "editor"}, {"title"}, {"year", "date"}),
    "report": ({"author"}, {"title"}, {"type"}, {"institution"}, {"year", "date"}),
    # "set": (),
    "thesis": ({"author"}, {"title"}, {"type"}, {"institution"}, {"year", "date"}),
    "unpublished": ({"author"}, {"title"}, {"year", "date"}),

    # field aliases (Section 2.1.2)
    # NOTE: use the `bibtex_type_aliases` dict to replace before looking here
    # non-standard type (Section 2.1.3)
    # NOTE: these have no required keys

    # biblatex-software (Section 2)
    "software": ({"author", "editor"}, {"title"}, {"url"}, {"year"}),
    "softwareversion": (
        {"author", "editor"}, {"title"}, {"url"}, {"version"}, {"year"}),
    "softwaremodule": ({"author"}, {"subtitle"}, {"url"}, {"year"}),
    "codefragment": ({"url"},),
}

#: A mapping for additional BibLaTeX types that have the same required fields. This
#: mapping can be used to convert types before looking into
#: :data:`bibtex_type_required_keys`.
bibtex_type_required_keys_aliases = {
    "mvbook": "book",
    "bookinbook": "inbook",
    "suppbook": "book",
    "mvcollection": "collection",
    "suppcollection": "collection",
    "suppperiodical": "periodical",
    "mvproceedings": "proceedings",
    "reference": "collection",
    "mvreference": "collection",
    "inreference": "incollection",
}

# NOTE: Zotero translator fields are defined in
#   https://github.com/zotero/zotero-schema
# and were extracted with
#   curl -s https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json | jq ' .itemTypes[].itemType'  # noqa: E501

#: A mapping of arbitrary types to BibLaTeX types in :data:`bibtex_types`. This
#: mapping can be used when translating from other software, e.g. Zotero has
#: custom fields in its `schema <https://github.com/zotero/zotero-schema>`__.
bibtex_type_converter: dict[str, str] = {
    # Zotero
    "annotation": "misc",
    "attachment": "misc",
    "audioRecording": "audio",
    "bill": "legislation",
    "blogPost": "online",
    "bookSection": "inbook",
    "case": "jurisdiction",
    "computerProgram": "software",
    "conferencePaper": "inproceedings",
    "dictionaryEntry": "misc",
    "document": "article",
    "email": "online",
    "encyclopediaArticle": "article",
    "film": "video",
    "forumPost": "online",
    "hearing": "jurisdiction",
    "instantMessage": "online",
    "interview": "article",
    "journalArticle": "article",
    "magazineArticle": "article",
    "manuscript": "unpublished",
    "map": "misc",
    "newspaperArticle": "article",
    "note": "misc",
    "podcast": "audio",
    "preprint": "unpublished",
    "presentation": "misc",
    "radioBroadcast": "audio",
    "statute": "jurisdiction",
    "tvBroadcast": "video",
    "videoRecording": "video",
    "webpage": "online",
    # Others
    "journal": "article",
    "monograph": "book",
    # Dublin Core
    "OriginalPaper": "article",
}

#: A mapping of arbitrary fields to BibLaTeX fields in :data:`bibtex_keys`. This
#: mapping can be used when translating from other software.
bibtex_key_converter: dict[str, str] = {
    "abstractNote": "abstract",
    "university": "school",
    "conferenceName": "eventtitle",
    "place": "location",
    "publicationTitle": "journal",
    "proceedingsTitle": "booktitle"
}

#: A set of BibLaTeX fields to ignore when exporting from the Papis database.
#: These can be extended with :confval:`bibtex-ignore-keys`.
bibtex_ignore_keys = (
    frozenset(["file"])
    | frozenset(papis.config.getlist("bibtex-ignore-keys"))
)

#: A regex for acceptable characters to use in a reference string. These are
#: used by :func:`ref_cleanup` to remove any undesired characters.
ref_allowed_characters = r"([^a-zA-Z0-9._]+|(?<!\\)[._])"

#: A list of fields that should not be escaped. In general, these will be
#: escaped by the BibTeX engine and should not be modified
#: (e.g. Verbatim fields and URI fields in `Section 2.2.1 <manual_>`_).
bibtex_verbatim_fields = frozenset({"doi", "eprint", "file", "pdf", "url", "urlraw"})


@cache
def _get_bibtexparser_key_conversion() -> list["papis.document.KeyConversionPair"]:
    from bibtexparser.latexenc import latex_to_unicode

    from papis.document import KeyConversionPair, split_authors_name

    return [
        KeyConversionPair("ID", [{"key": "ref", "action": None}]),
        KeyConversionPair("ENTRYTYPE", [{"key": "type", "action": None}]),
        KeyConversionPair("link", [{"key": "url", "action": None}]),
        KeyConversionPair("title", [{
            "key": "title",
            "action": lambda x: latex_to_unicode(x.replace("\n", " "))
            }]),
        KeyConversionPair("author", [{
            "key": "author_list",
            "action": lambda author: split_authors_name([author], separator="and")
            }]),
    ]


def bibtexparser_entry_to_papis(entry: dict[str, Any]) -> dict[str, Any]:
    """Convert the keys of a BibTeX entry parsed by :mod:`bibtexparser` to a
    papis-compatible format.

    :param entry: a dictionary with keys parsed by :mod:`bibtexparser`.
    :returns: a dictionary with keys converted to a papis-compatible format.
    """

    from papis.document import keyconversion_to_data

    key_conversion = _get_bibtexparser_key_conversion()
    return keyconversion_to_data(key_conversion, entry, keep_unknown_keys=True)


def bibtex_to_dict(bibtex: str) -> list["papis.document.DocumentLike"]:
    """Convert a BibTeX file (or string) to a list of Papis-compatible dictionaries.

    This will convert an entry like:

    .. code:: tex

        @article{ref,
            author = { ... },
            title = { ... },
            ...,
        }

    to a dictionary such as:

    .. code:: python

        { "type": "article", "author": "...", "title": "...", ...}

    :param bibtex: a path to a BibTeX file or a string containing BibTeX
        formatted data. If it is a file, its contents are passed to
        :class:`~bibtexparser.bparser.BibTexParser`.
    :returns: a list of entries from the BibTeX data in a compatible format.
    """
    from bibtexparser.bparser import BibTexParser
    parser = BibTexParser(
        common_strings=True,
        ignore_nonstandard_types=False,
        homogenize_fields=False,
        interpolate_strings=True)

    # bibtexparser has too many debug messages to be useful
    import logging
    logging.getLogger("bibtexparser.bparser").setLevel(logging.WARNING)

    if os.path.exists(bibtex):
        with open(bibtex, encoding="utf-8") as fd:
            logger.debug("Reading in file: '%s'.", bibtex)
            text = fd.read()
    else:
        text = bibtex

    entries = parser.parse(text, partial=True).entries
    return [bibtexparser_entry_to_papis(entry) for entry in entries]


def ref_cleanup(ref: str,
                ref_word_separator: str | None = None) -> str:
    """Function to cleanup reference strings so that they are accepted by BibLaTeX.

    This uses the :data:`ref_allowed_characters` to remove any disallowed characters
    from the given *ref*. Furthermore, ``slugify`` is used to remove unicode
    characters and ensure consistent use of the underscore ``_`` as a separator.

    :returns: a reference without any disallowed characters.
    """
    import slugify

    if ref_word_separator is None:
        ref_word_separator = papis.config.getstring("ref-word-separator")

    ref = slugify.slugify(ref,
                          lowercase=False,
                          word_boundary=False,
                          separator=ref_word_separator,
                          regex_pattern=ref_allowed_characters)

    return str(ref).strip()


def create_reference(doc: "papis.document.DocumentLike", *,
                     ref_format: "papis.strings.AnyString | None" = None,
                     ref_word_separator: str | None = None,
                     force: bool = False) -> str:
    """Try to create a reference for the document *doc*.

    If the document *doc* does not have a ``"ref"`` key, this function attempts
    to create one, otherwise the existing key is returned. When creating a new
    reference:

    * the :confval:`ref-format` key is used, if available,
    * the document DOI is used, if available,
    * a string is constructed from the document data (author, title, etc.).

    :param force: if *True*, the reference is re-created even if the document
        already has a ``"ref"`` key.
    :param ref_word_separator: separator passed to :func:`ref_cleanup`.
    :returns: a clean (see :func:`ref_cleanup`) reference for the document.
    """
    import papis.format

    # check first if the paper has a reference
    ref = str(doc.get("ref", ""))
    if not force and ref:
        return ref

    # otherwise, try to generate one somehow
    if ref_format is None:
        try:
            ref_format = papis.config.getformatpattern("ref-format")
        except ValueError:
            pass

    if ref_format:
        ref = papis.format.format(ref_format, doc, default="")

    if not ref:
        ref = str(doc.get("doi", ""))

    if not ref:
        ref = str(doc.get("isbn", ""))

    if not ref:
        # Just try to get something out of the data
        ref = "{:.30}".format(
              " ".join(string.capwords(str(d)) for d in doc.values()))
        ref = string.capwords(ref).replace(" ", "").strip()

    logger.debug("Generated ref '%s'.", ref)
    return ref_cleanup(ref, ref_word_separator=ref_word_separator)


def author_list_to_author(doc: "papis.document.Document",
                          author_list: list[dict[str, Any]]) -> str:
    """Construct the BibTeX author field from the document's *author_list*.

    This function is similar to :func:`papis.document.author_list_to_author`,
    but takes into account some BibTeX peculiarities:
    * The separator between the authors is always *"and"* and
    * Authors with only a family or given names are surrounded by curly brackets.

    :returns: an author string.
    """
    from papis.document import describe

    if not author_list:
        return ""

    result = []
    fmt = "{au[family]}, {au[given]}"

    for author in author_list:
        if not isinstance(author, dict):
            logger.error("Incorrect 'author_list' type (author is not a 'dict'): %s",
                         describe(doc))
            continue

        family = author.get("family")
        given = author.get("given")
        if family and given:
            result.append(fmt.format(au=author))
        elif family:
            result.append(f"{{{family}}}")
        elif given:
            result.append(f"{{{given}}}")
        else:
            # NOTE: empty author, just skip it
            pass

    return " and ".join(result)


def to_bibtex(document: "papis.document.Document", *, indent: int = 2) -> str:
    from warnings import warn

    warn("'papis.bibtex.to_bibtex' is deprecated and will be removed in Papis v0.16. "
         "Use 'papis.exporters.bibtex.to_bibtex' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.exporters.bibtex import to_bibtex as _to_bibtex
    return _to_bibtex(document, indent=indent)

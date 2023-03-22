import os
import string
from typing import Optional, List, FrozenSet, Dict, Any, Iterator

import click

import papis.config
import papis.importer
import papis.filetype
import papis.document
import papis.format
import papis.logging

logger = papis.logging.get_logger(__name__)

# NOTE: see the BibLaTeX docs for an up to date list of types and keys:
#   https://ctan.org/pkg/biblatex?lang=en

bibtex_types = frozenset([
    # regular types (Section 2.1.1)
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
    # non-standard types (Section 2.1.3)
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
    # type aliases (Section 2.1.2)
    "conference", "electronic", "masterthesis", "phdthesis", "techreport", "www",
]) | frozenset(papis.config.getlist("extra-bibtex-types"))  # type: FrozenSet[str]

# Zotero translator fields, see also
#   https://github.com/zotero/zotero-schema
#   https://github.com/papis/papis/pull/121
bibtex_type_converter = {
    "conferencePaper": "inproceedings",
    "journalArticle": "article",
    "journal": "article",
}  # type: Dict[str, str]

bibtex_keys = frozenset([
    # data fields (Section 2.2.2)
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
    # special fields (Section 2.2.3)
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
    # field aliases (Section 2.2.5)
    "address", "annote", "archiveprefix", "journal", "key", "pdf",
    "primaryclass", "school"
    # fields that we ignore
    # type,
]) | frozenset(papis.config.getlist("extra-bibtex-keys"))  # type: FrozenSet[str]

# Zotero translator fields, see also
#   https://github.com/zotero/zotero-schema
#   https://github.com/papis/papis/pull/121
bibtex_key_converter = {
    "abstractNote": "abstract",
    "university": "school",
    "conferenceName": "eventtitle",
    "place": "location",
    "publicationTitle": "journal",
    "proceedingsTitle": "booktitle"
}  # type: Dict[str, str]

bibtex_ignore_keys = (
    frozenset(papis.config.getlist("bibtex-ignore-keys"))
)  # type: FrozenSet[str]


def exporter(documents: List[papis.document.Document]) -> str:
    return "\n\n".join(to_bibtex_multiple(documents))


class Importer(papis.importer.Importer):

    """Importer that parses BibTeX files"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name="bibtex", **kwargs)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if (not os.path.exists(uri) or os.path.isdir(uri)
                or papis.filetype.get_document_extension(uri) == "pdf"):
            return None
        importer = Importer(uri=uri)
        importer.fetch()
        return importer if importer.ctx else None

    def fetch_data(self: papis.importer.Importer) -> Any:
        self.logger.info("Reading input file = '%s'", self.uri)
        try:
            bib_data = bibtex_to_dict(self.uri)
        except Exception as e:
            self.logger.error(e)
            return

        if not bib_data:
            return

        if len(bib_data) > 1:
            self.logger.warning(
                "The bibtex file contains %d entries, only taking the first entry",
                len(bib_data))

        self.ctx.data = bib_data[0]


@click.command("bibtex")
@click.pass_context
@click.argument("bibfile", type=click.Path(exists=True))
@click.help_option("--help", "-h")
def explorer(ctx: click.core.Context, bibfile: str) -> None:
    """
    Import documents from a bibtex file

    Examples of its usage are

    papis explore bibtex lib.bib pick

    """
    logger.info("Reading in bibtex file '%s'", bibfile)

    docs = [
        papis.document.from_data(d)
        for d in bibtex_to_dict(bibfile)]
    ctx.obj["documents"] += docs

    logger.info("%d documents found", len(docs))


def bibtexparser_entry_to_papis(entry: Dict[str, str]) -> Dict[str, str]:
    """Convert keys of a bib entry in bibtexparser format to papis
    compatible format.

    :param entry: Dictionary with keys of bibtexparser format.
    :returns: Dictionary with keys of papis format.
    """
    from bibtexparser.latexenc import latex_to_unicode

    _k = papis.document.KeyConversionPair
    key_conversion = [
        _k("ID", [{"key": "ref", "action": lambda x: None}]),
        _k("ENTRYTYPE", [{"key": "type", "action": None}]),
        _k("link", [{"key": "url", "action": None}]),
        _k("title", [{
            "key": "title",
            "action": lambda x: latex_to_unicode(x.replace("\n", " "))
            }]),
        _k("author", [{
            "key": "author_list",
            "action": lambda author: papis.document.split_authors_name([
                latex_to_unicode(author)
                ])
            }]),
    ]

    result = papis.document.keyconversion_to_data(
        key_conversion, entry, keep_unknown_keys=True)

    return result


def bibtex_to_dict(bibtex: str) -> List[Dict[str, str]]:
    """
    Convert bibtex file to dict

    .. code:: python

        { "type": "article", "author": "...", "title": "...", ...}

    :param bibtex: Bibtex file path or bibtex information in string format.
    :returns: Dictionary with bibtex information with keys that bibtex
        formally recognizes.
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
        with open(bibtex) as fd:
            logger.debug("Reading in file '%s'", bibtex)
            text = fd.read()
    else:
        text = bibtex
    entries = parser.parse(text, partial=True).entries
    # Clean entries
    return [bibtexparser_entry_to_papis(entry) for entry in entries]


def ref_cleanup(ref: str) -> str:
    """
    Function to cleanup references to be acceptable for latex
    """
    import slugify
    allowed_characters = r"([^a-zA-Z0-9._]+|(?<!\\)[._])"
    return string.capwords(str(slugify.slugify(
        ref,
        lowercase=False,
        word_boundary=False,
        separator=" ",
        regex_pattern=allowed_characters))).replace(" ", "")


def create_reference(doc: Dict[str, Any], force: bool = False) -> str:
    """
    Try to create a sane reference for the document
    """
    ref = ""
    # Check first if the paper has a reference
    if doc.get("ref") and not force:
        return str(doc["ref"])
    elif papis.config.get("ref-format"):
        try:
            ref = papis.format.format(papis.config.getstring("ref-format"),
                                      doc)
        except Exception as e:
            logger.error(e)
            ref = ""

    logger.debug("Generated 'ref = %s'", ref)
    if not ref:
        if doc.get("doi"):
            ref = doc["doi"]
        else:
            # Just try to get something out of the data
            ref = "{:.30}".format(
                " ".join(string.capwords(str(d)) for d in doc.values()))

    return ref_cleanup(ref)


def to_bibtex_multiple(documents: List[papis.document.Document]) -> Iterator[str]:
    for doc in documents:
        bib = to_bibtex(doc)
        if not bib:
            logger.warning("Skipping document export: '%s'",
                           doc.get_info_file())
            continue

        yield bib


def to_bibtex(document: papis.document.Document, *, indent: int = 2) -> str:
    """Create a bibtex string from document's information

    :param document: Papis document
    :returns: String containing bibtex formatting
    """
    bibtex_type = ""

    # determine bibtex type
    if "type" in document:
        if document["type"] in bibtex_types:
            bibtex_type = document["type"]
        elif document["type"] in bibtex_type_converter:
            bibtex_type = bibtex_type_converter[document["type"]]
        else:
            logger.error("BibTeX type '%s' not valid: '%s'",
                         document["type"],
                         document.get_info_file())
            return ""

    if not bibtex_type:
        bibtex_type = "article"

    # determine ref value
    ref = create_reference(document)
    if not ref:
        logger.error("No valid ref found for document: '%s'",
                     document.get_info_file())

        return ""

    logger.debug("Used 'ref = %s'", ref)

    from bibtexparser.latexenc import string_to_latex

    # process keys
    supports_unicode = papis.config.getboolean("bibtex-unicode")
    journal_key = papis.config.getstring("bibtex-journal-key")
    lines = ["{}".format(ref)]

    for key in sorted(document):
        bib_key = bibtex_key_converter.get(key, key)
        if bib_key not in bibtex_keys:
            continue

        if bib_key in bibtex_ignore_keys:
            continue

        bib_value = str(document[bib_key])
        logger.debug("BibTeX entry: '%s: %s'", bib_key, bib_value)

        if bib_key == "journal":
            if journal_key in document:
                bib_value = str(document[journal_key])
            else:
                logger.warning(
                    "Key '%s' is not present for ref '%s'",
                    journal_key, document["ref"])

        override_key = bib_key + "_latex"
        if override_key in document:
            bib_value = str(document[override_key])

        if not supports_unicode:
            bib_value = string_to_latex(bib_value)

        lines.append("{} = {{{}}}".format(bib_key, bib_value))

    # Handle file for zotero exporting
    if (papis.config.getboolean("bibtex-export-zotero-file")
            and document.get_files()):
        lines.append("{} = {{{}}}".format("file",
                                          ";".join(document.get_files())))

    separator = ",\n" + " " * indent
    return "@{type}{{{keys},\n}}".format(type=bibtex_type,
                                         keys=separator.join(lines))

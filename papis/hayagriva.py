from typing import Any, Dict, List

import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

# NOTE: the Hayagriva YAML format is described at
#   https://github.com/typst/hayagriva/blob/main/docs/file-format.md

HAYAGRIVA_TYPES = frozenset({
    "article", "chapter", "entry", "anthos", "report", "thesis", "web",
    "scene", "artwork", "patent", "case", "newspaper", "legislation",
    "manuscript", "tweet", "misc", "periodical", "proceedings",
    "book", "blog", "reference", "conference", "anthology", "repository",
    "thread", "video", "audio", "exibition",
})

# NOTE: only types that are different are stored
# NOTE: keep in sync with papis.bibtex.bibtex_types
BIBTEX_TO_HAYAGRIVA_TYPE_MAP = {
    # regular types (Section 2.1.1)
    # "article": "article",
    # "book": "book",
    "mvbook": "book",
    "inbook": "chapter",
    "bookinbook": "anthos",
    "suppbook": "chapter",
    "booklet": "book",
    "collection": "anthology",
    "mvcollection": "anthology",
    "incollection": "anthos",
    "suppcollection": "anthos",
    "dataset": "misc",
    "manual": "report",
    # "misc": "misc",
    "online": "web",
    # "patent": "patent",
    # "periodical": "periodical",
    "suppperiodical": "periodical",
    # "proceedings": "proceedings",
    "mvproceedings": "proceedings",
    "inproceedings": "proceedings",
    "reference": "reference",
    "mvreference": "reference",
    "inreference": "reference",
    "report": "report",
    # "set": "misc",
    "software": "misc",
    # "thesis": "thesis",
    "unpublished": "manuscript",
    # "xdata",
    # "custom[a-f]",
    # non-standard types (Section 2.1.3)
    # "artwork": "artwork",
    # "audio": "audio",
    # "bibnote": "misc",
    "commentary": "misc",
    "image": "misc",
    "jurisdiction": "case",
    # "legislation": "legislation",
    "legal": "legislation",
    "letter": "misc",
    "movie": "video",
    "music": "audio",
    "performance": "scene",
    "review": "article",
    "standard": "article",
    # "video": "video",
    # type aliases (Section 2.1.2)
    "conference": "conference",
    "electronic": "web",
    "masterthesis": "thesis",
    "phdthesis": "thesis",
    "techreport": "report",
    "www": "web",
}

# NOTE: not all fields are implemented, since they're not well-supported
_k = papis.document.KeyConversionPair
PAPIS_TO_HAYAGRIVA_KEY_CONVERSION_MAP = [
    _k("type", [{"key": "type", "action": lambda t: to_hayagriva_type(t)}]),
    _k("title", [papis.document.EmptyKeyConversion]),
    _k("author_list", [{"key": "author", "action": lambda a: to_hayagriva_authors(a)}]),
    _k("year", [papis.document.EmptyKeyConversion]),
    _k("date", [{"key": "date", "action": None}]),
    _k("editor", [papis.document.EmptyKeyConversion]),
    _k("publisher", [papis.document.EmptyKeyConversion]),
    _k("location", [papis.document.EmptyKeyConversion]),
    _k("organization", [papis.document.EmptyKeyConversion]),
    _k("institution", [{"key": "organization", "action": None}]),
    _k("issue", [papis.document.EmptyKeyConversion]),
    _k("volume", [papis.document.EmptyKeyConversion]),
    _k("volumes", [{"key": "volume-total", "action": None}]),
    _k("edition", [papis.document.EmptyKeyConversion]),
    _k("pages", [{"key": "page-range", "action": None}]),
    _k("pagetotal", [{"key": "page-total", "action": None}]),
    _k("url", [papis.document.EmptyKeyConversion]),
    _k("doi", [papis.document.EmptyKeyConversion]),
    _k("eprint", [{"key": "serial-number", "action": None}]),
    _k("isbn", [papis.document.EmptyKeyConversion]),
    _k("issn", [papis.document.EmptyKeyConversion]),
    _k("language", [papis.document.EmptyKeyConversion]),
]


def to_hayagriva_type(entry_type: str) -> str:
    # NOTE: the fields are case insensitive, but typst seems to capitalize them
    return BIBTEX_TO_HAYAGRIVA_TYPE_MAP.get(entry_type, entry_type).capitalize()


def to_hayagriva_authors(authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"given-name": a["given"], "name": a["family"]} for a in authors]


def to_hayagriva(doc: papis.document.Document) -> Dict[str, Any]:
    from papis.document import keyconversion_to_data
    data = keyconversion_to_data(PAPIS_TO_HAYAGRIVA_KEY_CONVERSION_MAP, doc)

    return data


def exporter(documents: List[papis.document.Document]) -> str:
    import yaml
    from papis.bibtex import create_reference

    result = yaml.dump({
        create_reference(doc): to_hayagriva(doc) for doc in documents
        }, allow_unicode=True, indent=2, sort_keys=True)

    return str(result)

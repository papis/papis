from typing import Any, Dict, List, Optional

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
    "thread", "video", "audio", "exhibition",
})

HAYAGRIVA_PARENT_TYPES = {
    "article": "periodical",
    "chapter": "book",
    "entry": "reference",
    "anthos": "anthology",
    "web": "web",
    "scene": "video",
    "artwork": "exhibition",
    "legislation": "anthology",
    "tweet": "tweet",
    "video": "video",
    "audio": "audio",
}

# NOTE: these are mostly taken from
#   https://github.com/typst/hayagriva/blob/main/tests/data/basic.yml
# as there does not seem to be any official list of what goes in the entry and
# what goes in the parent (some fields can even repeat, which is not supported
# by papis)

HAYAGRIVA_TYPE_PARENT_KEYS = {
    "article": frozenset({
        "date", "edition", "isbn", "issn", "issue", "journal", "location",
        "organization", "publisher", "volume",
    }),
    "chapter": frozenset({
        "journal", "author", "volume", "volume-total", "isbn", "issn",
        "page-total", "date",
    }),
    "entry": frozenset({"journal"}),
    "anthos": frozenset({
        "journal", "volume", "date", "isbn", "location", "publisher",
        "editor",
    }),
    "web": frozenset({}),
    "scene": frozenset({}),
    "artwork": frozenset({}),
    "legislation": frozenset({}),
    "tweet": frozenset({}),
    "video": frozenset({}),
    "audio": frozenset({}),
}

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
    "mvproceedings": "article",
    "inproceedings": "article",
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
    "mastersthesis": "thesis",
    "phdthesis": "thesis",
    "techreport": "report",
    "www": "web",
}

# NOTE: not all fields are implemented, since they're not well-supported
_k = papis.document.KeyConversionPair
PAPIS_TO_HAYAGRIVA_KEY_CONVERSION_MAP = [
    _k("title", [papis.document.EmptyKeyConversion]),
    _k("author", [{
        "key": "author",
        # NOTE: this is mostly the case in tests, but might as well include it
        "action": lambda a: to_hayagriva_authors(papis.document.split_authors_name([a]))
    }]),
    _k("author_list", [{"key": "author", "action": lambda a: to_hayagriva_authors(a)}]),  # noqa: PLW0108
    _k("year", [{"key": "date", "action": None}]),
    _k("date", [{"key": "date", "action": None}]),
    _k("editor", [{"key": "editor", "action": lambda a:
                   to_hayagriva_authors(papis.document.split_authors_name([a]))}]),
    _k("editor_list", [{"key": "editor", "action": lambda a: to_hayagriva_authors(a)}]),  # noqa: PLW0108
    _k("publisher", [papis.document.EmptyKeyConversion]),
    _k("location", [papis.document.EmptyKeyConversion]),
    _k("venue", [{"key": "location", "action": None}]),
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
    # NOTE: this is mostly for the parent
    _k("journal", [{"key": "title", "action": None}]),
]


def to_hayagriva_authors(authors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{"given-name": a["given"], "name": a["family"]} for a in authors]


def to_hayagriva(doc: papis.document.Document) -> Dict[str, Any]:
    from contextlib import suppress

    bibtype = doc["type"]
    htype = BIBTEX_TO_HAYAGRIVA_TYPE_MAP.get(bibtype, bibtype)

    parent_known_keys = HAYAGRIVA_TYPE_PARENT_KEYS[htype]
    ptype: Optional[str] = None

    if htype == "article":
        if "proceedings" in bibtype:
            # NOTE: heuristic: proceedings are published and have a DOI
            ptype = "proceedings" if "doi" in doc else "conference"
        elif "eprint" in doc or "ssrn" in doc.get("journal", "").lower():
            # NOTE: this mostly supports arXiv and SSRN
            ptype = "Repository"
        else:
            # NOTE: hayagriva also supports articles in blogs or newspapers, but
            # we don't really have a way to distinguish at the moment
            ptype = "periodical"
    else:
        ptype = HAYAGRIVA_PARENT_TYPES.get(htype)

    # NOTE: the type is case insensitive, but typst seems to capitalize them
    data: Dict[str, Any] = {"type": htype.capitalize()}
    parent: Dict[str, Any] = {"type": ptype.capitalize()} if ptype else {}

    for foreign_key, conversions in PAPIS_TO_HAYAGRIVA_KEY_CONVERSION_MAP:
        if foreign_key not in doc:
            continue

        for conversion in conversions:
            key = conversion.get("key") or foreign_key
            value = doc[foreign_key]

            action = conversion.get("action")
            conv_value = None
            if action:
                with suppress(Exception):
                    conv_value = action(value)
            else:
                conv_value = value

            if isinstance(conv_value, str):
                conv_value = conv_value.strip()

            if conv_value:
                if ptype and (
                        key in parent_known_keys
                        or foreign_key in parent_known_keys):
                    parent[key] = conv_value
                else:
                    data[key] = conv_value

    if parent:
        data["parent"] = parent

    return data


def exporter(documents: List[papis.document.Document]) -> str:
    """Convert document to the Hayagriva format used by Typst"""
    import yaml
    from papis.bibtex import create_reference

    result = yaml.dump({
        create_reference(doc): to_hayagriva(doc) for doc in documents
        }, allow_unicode=True, indent=2, sort_keys=True)

    return str(result)

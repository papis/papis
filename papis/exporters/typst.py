from typing import Any

import papis.logging
from papis.document import (
    Document,
    EmptyKeyConversion,
    KeyConversionPair,
    describe,
    split_authors_name,
)

logger = papis.logging.get_logger(__name__)

# NOTE: not all fields are implemented, since they're not well-supported
PAPIS_TO_HAYAGRIVA_KEY_CONVERSION_MAP = [
    KeyConversionPair("title", [EmptyKeyConversion]),
    KeyConversionPair("author", [{
        "key": "author",
        # NOTE: this is mostly the case in tests, but might as well include it
        "action": lambda a: to_hayagriva_authors(split_authors_name([a]))
    }]),
    KeyConversionPair("author_list", [{
        "key": "author",
        "action": lambda a: to_hayagriva_authors(a)  # noqa: PLW0108
    }]),
    KeyConversionPair("year", [{"key": "date", "action": None}]),
    KeyConversionPair("date", [{"key": "date", "action": None}]),
    KeyConversionPair("editor", [{
        "key": "editor",
        "action": lambda a: to_hayagriva_authors(split_authors_name([a]))
    }]),
    KeyConversionPair("editor_list", [{
        "key": "editor",
        "action": lambda a: to_hayagriva_authors(a)  # noqa: PLW0108
    }]),
    KeyConversionPair("publisher", [EmptyKeyConversion]),
    KeyConversionPair("location", [EmptyKeyConversion]),
    KeyConversionPair("venue", [{"key": "location", "action": None}]),
    KeyConversionPair("organization", [EmptyKeyConversion]),
    KeyConversionPair("institution", [{"key": "organization", "action": None}]),
    KeyConversionPair("issue", [EmptyKeyConversion]),
    KeyConversionPair("volume", [EmptyKeyConversion]),
    KeyConversionPair("volumes", [{"key": "volume-total", "action": None}]),
    KeyConversionPair("edition", [EmptyKeyConversion]),
    KeyConversionPair("pages", [{"key": "page-range", "action": None}]),
    KeyConversionPair("pagetotal", [{"key": "page-total", "action": None}]),
    KeyConversionPair("url", [EmptyKeyConversion]),
    KeyConversionPair("doi", [EmptyKeyConversion]),
    KeyConversionPair("eprint", [{"key": "serial-number", "action": None}]),
    KeyConversionPair("isbn", [EmptyKeyConversion]),
    KeyConversionPair("issn", [EmptyKeyConversion]),
    KeyConversionPair("language", [EmptyKeyConversion]),
    # NOTE: this is mostly for the parent
    KeyConversionPair("journal", [{"key": "title", "action": None}]),
]


def to_hayagriva_authors(authors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"given-name": a["given"], "name": a["family"]} for a in authors]


def to_hayagriva(doc: Document) -> dict[str, Any]:
    from contextlib import suppress

    from papis.hayagriva import (
        BIBTEX_TO_HAYAGRIVA_TYPE_MAP,
        HAYAGRIVA_PARENT_TYPES,
        HAYAGRIVA_TYPE_PARENT_KEYS,
    )

    bibtype = doc["type"]
    htype = BIBTEX_TO_HAYAGRIVA_TYPE_MAP.get(bibtype, bibtype)

    parent_known_keys = HAYAGRIVA_TYPE_PARENT_KEYS.get(htype, frozenset())
    ptype: str | None = None

    if htype == "article":
        if "proceedings" in bibtype:
            # NOTE: heuristic: proceedings are published and have a DOI
            ptype = "proceedings" if "doi" in doc else "conference"
        elif "eprint" in doc or "ssrn" in doc.get("journal", "").lower():
            # NOTE: this mostly supports arXiv and SSRN
            ptype = "repository"
        else:
            # NOTE: hayagriva also supports articles in blogs or newspapers, but
            # we don't really have a way to distinguish at the moment
            ptype = "periodical"
    else:
        ptype = HAYAGRIVA_PARENT_TYPES.get(htype)

    # NOTE: the type is case insensitive, but typst seems to capitalize them
    data: dict[str, Any] = {"type": htype.capitalize()}
    parent: dict[str, Any] = {"type": ptype.capitalize()} if ptype else {}

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


def exporter(documents: list[Document]) -> str:
    """Convert document to the Hayagriva format used by Typst."""
    import yaml

    from papis.bibtex import create_reference
    from papis.paths import unique_suffixes

    results = {}
    for doc in documents:
        ref = create_reference(doc)
        if ref in results:
            # ensure that ref is unique
            suffix = unique_suffixes()
            unique_ref = ref
            while unique_ref in results:
                unique_ref = f"{ref}{next(suffix)}"

            logger.warning("Document with reference '%s' already exists (duplicate). "
                           "Create a new ref names '%s' for this document: %s",
                           ref, unique_ref, describe(doc))
            ref = unique_ref

        results[ref] = to_hayagriva(doc)

    return str(yaml.dump(results, allow_unicode=True, indent=2, sort_keys=True))

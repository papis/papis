from __future__ import annotations

import collections
import os
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NamedTuple, TypeAlias

import papis.config
import papis.logging

if TYPE_CHECKING:
    from papis.document import Document

logger = papis.logging.get_logger(__name__)

#: Callable for automatic doctor fixers. This callable is constructed by a
#: check and is expected to wrap all the required data, so it takes no arguments.
FixFn: TypeAlias = Callable[[], None]
#: Callable for doctor document checks.
CheckFn: TypeAlias = "Callable[[Document], list[Error]]"


class Error(NamedTuple):
    """A detailed error returned by a doctor check."""

    #: Name of the check generating the error.
    name: str
    #: Path to the document that generated the error.
    path: str
    #: A value that caused the error (usually a document key).
    payload: str
    #: A short message describing the error that can be displayed to the user.
    msg: str
    #: A callable that can autofix the error (see :data:`FixFn`). Note that this
    #: will change the attached :attr:`doc`.
    fix_action: FixFn | None
    #: The document that generated the error.
    doc: Document | None


class Check(NamedTuple):
    #: Name of the check
    name: str
    #: A callable that takes a document and returns a list of errors generated
    #: by the current check (see :data:`CheckFn`).
    operate: CheckFn


REGISTERED_CHECKS: dict[str, Check] = {}


def make_error(
        doc: Document,
        name: str, *,
        msg: str,
        payload: str,
        fix_action: FixFn | None = None,
    ) -> Error:
    if name not in REGISTERED_CHECKS:
        raise ValueError(f"unknown check '{name}'")

    folder = doc.get_main_folder()
    if folder is None:
        # FIXME: this should only be hit during testing?
        folder = "NOTFOUND"

    return Error(name=name,
                 path=folder,
                 msg=msg,
                 fix_action=fix_action,
                 payload=payload,
                 doc=doc)


def register_check(name: str, check: CheckFn) -> None:
    """
    Register a new check.

    Registered checks are recognized by ``papis`` and can be used by users
    in their configuration files through :confval:`doctor-default-checks`
    or on the command line through the ``--checks`` flag.
    """
    REGISTERED_CHECKS[name] = Check(name=name, operate=check)


def registered_checks_names() -> list[str]:
    return list(REGISTERED_CHECKS.keys())


FILES_CHECK_NAME = "files"


def files_check(doc: Document) -> list[Error]:
    """
    Check whether the files of a document actually exist in the filesystem.

    :returns: a :class:`list` of errors, one for each file that does not exist.
    """

    files = doc.get_files()
    folder = doc.get_main_folder() or ""
    if not folder:
        return []

    def make_fixer(filename: str) -> FixFn:
        def fixer() -> None:
            """
            Files fixer function that removes non-existent files from the document.

            For now it only works if the file name is not of the form
            ``subdirectory/filename``, but only ``filename``.
            """

            basename = os.path.basename(filename)
            if basename in doc["files"]:
                logger.info("[FIX] Removing file from document: '%s'.", basename)
                doc["files"].remove(basename)

        return fixer

    if "file" in doc:
        error = [
            make_error(doc, FILES_CHECK_NAME,
                       msg="Use the 'files' key instead of 'file' to list files",
                       payload="file")
        ]
    else:
        error = []

    return [make_error(doc, FILES_CHECK_NAME,
                       msg=f"File '{f}' declared but does not exist",
                       fix_action=make_fixer(f),
                       payload=f)
            for f in files if not os.path.exists(f)] + error


KEYS_MISSING_CHECK_NAME = "keys-missing"


def keys_missing_check(doc: Document) -> list[Error]:
    """
    Checks whether the keys provided in the configuration
    option :confval:`doctor-keys-missing-keys` exist in the document
    and are non-empty.

    :returns: a :class:`list` of errors, one for each missing key.
    """
    from papis.defaults import NOT_SET
    from papis.document import author_list_to_author, split_authors_name

    keys = papis.config.get("keys-exist-keys", section="doctor")
    if keys is NOT_SET:
        keys = papis.config.getlist("keys-missing-keys", section="doctor")
    else:
        logger.warning("The configuration option 'doctor-keys-exist-keys' "
                       "is deprecated and will be removed in the next version. "
                       "Use 'doctor-keys-missing-keys' instead.")

    if keys is None:
        keys = []

    keys.extend(papis.config.getlist("keys-missing-keys-extend", section="doctor"))

    def make_fixer(key: str) -> FixFn | None:
        def fixer_author_from_author_list() -> None:
            if "author_list" not in doc:
                return

            logger.info("[FIX] Parsing 'author_list' into 'author': '%s'.",
                        doc["author_list"])
            doc["author"] = author_list_to_author(doc)

        def fixer_author_list_from_author() -> None:
            if "author" not in doc:
                return

            logger.info("[FIX] Parsing 'author' into 'author_list': '%s'.",
                        doc["author"])
            doc["author_list"] = split_authors_name(doc["author"])

        if key == "author":
            return fixer_author_from_author_list
        elif key == "author_list":
            return fixer_author_list_from_author
        else:
            return None

    return [make_error(doc, KEYS_MISSING_CHECK_NAME,
                       msg=f"Key '{k}' does not exist",
                       fix_action=make_fixer(k),
                       payload=k)
            for k in keys if k not in doc]


REFS_CHECK_NAME = "refs"
REFS_BAD_SYMBOL_REGEX = re.compile(r"[ ,{}\[\]@#`']")


def refs_check(doc: Document) -> list[Error]:
    """
    Checks that a ref exists and if not it tries to create one
    according to the :confval:`ref-format` configuration option.

    :returns: an error if the reference does not exist or contains invalid
        characters (as required by BibTeX).
    """
    from papis.bibtex import create_reference

    def create_ref_fixer() -> None:
        ref = create_reference(doc, force=True)
        logger.info("[FIX] Setting ref to '%s'.", ref)

        doc["ref"] = ref

    def clean_ref_fixer() -> None:
        ref = REFS_BAD_SYMBOL_REGEX.sub("", doc["ref"]).strip()
        if not ref:
            create_ref_fixer()
        else:
            logger.info("[FIX] Cleaning ref from '%s' to '%s'.", doc["ref"], ref)

            doc["ref"] = ref

    ref = doc.get("ref")
    ref = str(ref).strip() if ref is not None else ref

    if not ref:
        return [make_error(doc, REFS_CHECK_NAME,
                           msg="Reference missing",
                           fix_action=create_ref_fixer,
                           payload="ref")]

    m = REFS_BAD_SYMBOL_REGEX.findall(ref)
    if m:
        return [make_error(doc, REFS_CHECK_NAME,
                           msg=f"Bad characters ({set(m)}) found in reference",
                           fix_action=clean_ref_fixer,
                           payload="ref")]

    return []


DUPLICATED_KEYS_SEEN: dict[str, set[str]] = collections.defaultdict(set)
DUPLICATED_KEYS_NAME = "duplicated-keys"


def duplicated_keys_check(doc: Document) -> list[Error]:
    """
    Check for duplicated keys in the list given by the
    :confval:`doctor-duplicated-keys-keys` configuration option.

    :returns: a :class:`list` of errors, one for each key with a value that already
        exist in the documents from the current query.
    """
    keys = papis.config.getlist("duplicated-keys-keys", section="doctor")
    keys.extend(papis.config.getlist("duplicated-keys-keys-extend", section="doctor"))

    results: list[Error] = []
    for key in keys:
        value = doc.get(key)
        if value is None:
            continue

        value = str(value)
        seen = DUPLICATED_KEYS_SEEN[key]
        if value not in seen:
            seen.update({value})
            continue

        results.append(make_error(doc, DUPLICATED_KEYS_NAME,
                                  msg=f"Key '{key}' is duplicated ({value})",
                                  payload=key))

    return results


DUPLICATED_VALUES_NAME = "duplicated-values"


def duplicated_values_check(doc: Document) -> list[Error]:
    """
    Check if the keys given by :confval:`doctor-duplicated-values-keys`
    contain any duplicate entries. These keys are expected to be lists of items.

    :returns: a :class:`list` of errors, one for each key with a value that
        has duplicate entries.
    """
    keys = papis.config.getlist("duplicated-values-keys", section="doctor")
    keys.extend(papis.config.getlist("duplicated-values-keys-extend", section="doctor"))

    def make_fixer(key: str, entries: list[Any]) -> FixFn:
        def fixer() -> None:
            logger.info("[FIX] Removing duplicates entries from key '%s'.", key)
            doc[key] = entries

        return fixer

    def make_hashable(f: Any) -> Any:
        if isinstance(f, list):
            return tuple(make_hashable(entry) for entry in f)
        elif isinstance(f, dict):
            return tuple((k, make_hashable(v)) for k, v in f.items())
        else:
            return f

    results: list[Error] = []
    for key in keys:
        value = doc.get(key)
        if value is None:
            continue

        if not isinstance(value, list):
            logger.warning("Check '%s' expected key '%s' to be a list.",
                           DUPLICATED_VALUES_NAME, key)
            continue

        seen = {}
        dupes = [f for f in value
                 if (h := make_hashable(f)) in seen or seen.update({h: f})]
        if not dupes:
            continue

        results.append(make_error(doc, DUPLICATED_VALUES_NAME,
                                  msg=(
                                      "Key '{}' contains duplicate entries: '{}'"
                                      .format(key, "', '".join(str(d) for d in dupes))),
                                  fix_action=make_fixer(key, list(seen.values())),
                                  payload=key))

    return results


BIBTEX_TYPE_CHECK_NAME = "bibtex-type"


def bibtex_type_check(doc: Document) -> list[Error]:
    """
    Check that the document type is compatible with BibTeX or BibLaTeX type descriptors.

    :returns: an error if the types are not compatible.
    """
    from papis.bibtex import bibtex_type_converter, bibtex_types

    def make_fixer(bib_type: str) -> FixFn | None:
        def fixer() -> None:
            new_bib_type = bibtex_type_converter[bib_type]
            logger.info("[FIX] Replacing type '%s' with '%s'.", bib_type, new_bib_type)
            doc["type"] = new_bib_type

        if bib_type in bibtex_type_converter:
            return fixer
        else:
            return None

    bib_type = doc.get("type")
    if bib_type is None:
        return [make_error(doc, BIBTEX_TYPE_CHECK_NAME,
                           msg="Document does not define a type",
                           payload="type")]

    if bib_type not in bibtex_types:
        return [make_error(doc, BIBTEX_TYPE_CHECK_NAME,
                           msg=f"Document type '{bib_type}' is not a valid BibTeX type",
                           fix_action=make_fixer(bib_type),
                           payload=bib_type)]

    return []


BIBLATEX_TYPE_ALIAS_CHECK_NAME = "biblatex-type-alias"


def biblatex_type_alias_check(doc: Document) -> list[Error]:
    """
    Check that the BibLaTeX type of the document is not a known alias.

    The aliases are described by :data:`~papis.bibtex.bibtex_type_aliases`.

    :returns: an error if the type of the document is an alias.
    """
    from papis.bibtex import bibtex_type_aliases

    def make_fixer(value: str) -> FixFn:
        def fixer() -> None:
            logger.info("[FIX] Setting BibLaTeX 'type' from '%s' to '%s'.",
                        doc["type"], value)
            doc["type"] = value

        return fixer

    errors = bibtex_type_check(doc)
    if errors:
        return [e._replace(name=BIBLATEX_TYPE_ALIAS_CHECK_NAME) for e in errors]

    bib_type = doc["type"]
    bib_type_base = bibtex_type_aliases.get(bib_type)
    if bib_type is not None and bib_type_base is not None:
        return [make_error(doc, BIBLATEX_TYPE_ALIAS_CHECK_NAME,
                           msg=(f"Document type '{bib_type}' is an alias for "
                                f"'{bib_type_base}' in BibLaTeX"),
                           fix_action=make_fixer(bib_type_base),
                           payload=bib_type)]

    return []


# NOTE: `journal` is a key that papis relies on and we do not want to rename it
BIBLATEX_KEY_ALIAS_IGNORED = {"journal"}
BIBLATEX_KEY_ALIAS_CHECK_NAME = "biblatex-key-alias"


def biblatex_key_alias_check(doc: Document) -> list[Error]:
    """
    Check that no BibLaTeX keys in the document are known aliases.

    The aliases are described by :data:`~papis.bibtex.bibtex_key_aliases`. Note
    that these keys can also be converted on export to BibLaTeX.

    :returns: an error for each key of the document that is an alias.
    """
    from papis.bibtex import bibtex_key_aliases

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            new_key = bibtex_key_aliases[key]
            logger.info("[FIX] Renaming BibLaTeX key '%s' to '%s'.", key, new_key)
            doc[new_key] = doc[key]
            del doc[key]

        return fixer

    return [make_error(doc, BIBLATEX_KEY_ALIAS_CHECK_NAME,
                       msg=(f"Document key '{key}' is an alias for "
                            f"'{bibtex_key_aliases[key]}' in BibLaTeX"),
                       fix_action=make_fixer(key),
                       payload=key)
            for key in doc
            if key not in BIBLATEX_KEY_ALIAS_IGNORED and key in bibtex_key_aliases]


BIBLATEX_REQUIRED_KEYS_CHECK_NAME = "biblatex-required-keys"


def biblatex_required_keys_check(doc: Document) -> list[Error]:
    """
    Check that required BibLaTeX keys are part of the document based on its type.

    The required keys are described by :data:`papis.bibtex.bibtex_type_required_keys`.
    Note that most BibLaTeX processors will be quite forgiving if these keys are
    missing.

    :returns: an error for each key of the document that is missing.
    """
    from papis.bibtex import (
        bibtex_key_aliases,
        bibtex_type_aliases,
        bibtex_type_required_keys,
        bibtex_type_required_keys_aliases,
    )

    errors = bibtex_type_check(doc)
    if errors:
        return [e._replace(name=BIBLATEX_REQUIRED_KEYS_CHECK_NAME) for e in errors]

    # translate bibtex type
    bib_type = doc["type"]
    bib_type = bibtex_type_aliases.get(bib_type, bib_type)

    if bib_type not in bibtex_type_required_keys:
        bib_type = bibtex_type_required_keys_aliases.get(bib_type)

    required_keys = bibtex_type_required_keys[bib_type]
    aliases = {v: k for k, v in bibtex_key_aliases.items()}

    return [make_error(doc, BIBLATEX_REQUIRED_KEYS_CHECK_NAME,
                       msg=("Document of type '{}' requires one of the keys ['{}'] "
                            "to be compatible with BibLaTeX"
                            .format(bib_type, "', '".join(keys))),
                       payload=", ".join(keys))
            for keys in required_keys
            if not any(key in doc or aliases.get(key) in doc for key in keys)]


BIBLATEX_KEY_CONVERT_CHECK_NAME = "biblatex-key-convert"
BIBLATEX_KEY_CONVERT_NUMBER_REGEX = re.compile(
    # optional "No." / "Nr." / "Suppl."
    r"^(?:(?:no\.?|nr\.?|suppl\.?)\s*)?"
    r"(?:"
    # pure numeric or range, e.g. 3, 3-4
    r"\d+(?:\s*[-–]\s*\d+)?"  # ruff:ignore[ambiguous-unicode-character-string]
    # letter+number combos, e.g. S1, 4B, 4es
    r"|[A-Za-z]?\s*\d+(?:[A-Za-z]+)?"
    # letter-hyphen-number, e.g. A-1, Suppl-A-3
    r"|[A-Za-z]+\s*[-–]\s*\d+"  # ruff:ignore[ambiguous-unicode-character-string]
    r")$",
    re.I
)


def biblatex_key_convert_check(doc: Document) -> list[Error]:
    """
    Check if any BibLaTeX keys in the document are incorrectly assigned.

    Note that this is a heuristic in most cases, as we cannot always determine
    allowable values. Implemented checks include:

    * ``issue`` entries that should be ``number``: issue is generally reserved
      for periodicals (e.g. "Spring" issue) and not meant as short designator
      for a publication (see Section 2.3.11 from the BibLaTeX manual).

    :returns: a list of errors for each key that appears misassigned.
    """

    def issue_to_number_fixer() -> None:
        if "issue" in doc and "number" not in doc:
            logger.info("[FIX] Renaming BibLaTeX field 'issue' to 'number'.")
            doc["number"] = doc.pop("issue")

    def is_number_like(value: Any) -> bool:
        if isinstance(value, int):
            return True

        # NOTE: most things are just a single digit, so this check should be
        # pretty fast, while the regex acts as a fallback for fancy cases
        value = value.strip()
        return (
            value.isdigit()
            or (len(value) <= 2 and value.isalpha())
            or BIBLATEX_KEY_CONVERT_NUMBER_REGEX.match(value) is not None)

    results = []
    for key in ("issue",):
        if key not in doc:
            continue

        value = doc[key]
        fix_action = None
        if key == "issue":
            if is_number_like(value):
                msg = (f"Document key 'issue' looks like a 'number'"
                       f" (see BibLaTeX manual §2.3.11): '{value}'")
                fix_action = issue_to_number_fixer

        if fix_action is None:
            continue

        results.append(make_error(doc, BIBLATEX_KEY_CONVERT_CHECK_NAME,
                                  msg=msg,
                                  fix_action=fix_action,
                                  payload=key))

    return results


FIELD_TYPE_CHECK_NAME = "field-type"


def get_key_type_check_keys() -> dict[str, type]:
    from warnings import warn
    warn("'papis.doctor.get_key_type_check_keys' is deprecated and will "
         "be removed in Papis v0.17. Use 'papis.document.get_document_field_types' "
         "instead.", DeprecationWarning, stacklevel=2)

    from papis.document import get_document_field_types
    return get_document_field_types()


def field_type_check(doc: Document) -> list[Error]:
    """
    Check document keys have expected types.

    :returns: a :class:`list` of errors, one for each key does not have the
        expected type (if it exists).
    """
    from papis.defaults import NOT_SET

    # NOTE: the separator can be quoted so that it can force whitespace
    separator = papis.config.get("key-type-check-separator", section="doctor")
    if separator is NOT_SET:
        separator = papis.config.get("key-type-separator", section="doctor")
        if separator is NOT_SET:
            separator = papis.config.get("field-type-separator", section="doctor")
        else:
            logger.warning("The configuration option 'doctor-key-type-separator' "
                           "is deprecated and will be removed in Papis 0.17. "
                           "Use 'doctor-field-type-separator' instead.")
    else:
        logger.warning("The configuration option 'doctor-key-type-check-separator' "
                       "is deprecated and will be removed in Papis 0.17. "
                       "Use 'doctor-field-type-separator' instead.")

    separator = separator.strip("'").strip('"') if separator else None

    from papis.document import describe

    def make_fixer(key: str, cls: type) -> FixFn:
        def fixer_convert_list() -> None:
            value = doc[key]

            logger.info("[FIX] Convert type of '%s' from '%s' to '%s'.",
                        key, type(value).__name__, cls.__name__)
            if isinstance(value, str) and separator:
                doc[key] = re.split(fr"\s*{separator}\s*", value)
            else:
                doc[key] = [value]

        def fixer_convert_str() -> None:
            value = doc[key]

            logger.info("[FIX] Convert type of '%s' from '%s' to '%s'.",
                        key, type(value).__name__, cls.__name__)
            if isinstance(value, list):
                if len(value) == 1:
                    doc[key] = str(value[0])
                elif separator:
                    doc[key] = separator.join(value)
                else:
                    doc[key] = str(value)
            else:
                doc[key] = str(value)

        def fixer_convert_any() -> None:
            value = doc[key]

            logger.info("[FIX] Convert type of '%s' from '%s' to '%s'.",
                        key, type(value).__name__, cls.__name__)
            if isinstance(value, list) and len(value) == 1:
                value = value[0]

            try:
                doc[key] = cls(value)
            except Exception as exc:
                logger.error("Failed to convert key '%s' to '%s': '%s'.",
                             key, cls, describe(doc), exc_info=exc)

        if cls is list:
            return fixer_convert_list
        if cls is str:
            return fixer_convert_str
        else:
            return fixer_convert_any

    from papis.document import get_document_field_types

    results = []
    for key, cls in get_document_field_types().items():
        doc_value = doc.get(key)

        if doc_value is not None and not isinstance(doc_value, cls):
            results.append(
                make_error(doc, FIELD_TYPE_CHECK_NAME,
                           msg=(f"Key '{key}' should be of type '{cls.__name__}' "
                                f"but got '{type(doc_value).__name__}': "
                                f"{doc_value!r}"),
                           fix_action=make_fixer(key, cls),
                           payload=key))

    return results


# NOTE: https://www.w3schools.com/html/html_symbols.asp
HTML_CODES_REGEX = re.compile(r"&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-fA-F]{1,6});", re.I)
HTML_CODES_CHECK_NAME = "html-codes"


def html_codes_check(doc: Document) -> list[Error]:
    """
    Checks that the keys in :confval:`doctor-html-codes-keys`
    configuration options do not contain any HTML codes like ``&amp;`` etc.

    :returns: a :class:`list` of errors, one for each key that contains HTML codes.
    """
    from html import unescape

    results = []

    def make_fixer(key: str) -> FixFn:
        def lower(p: re.Match[str]) -> str:
            result, = p.groups()
            return f"&{result.lower()};"

        def fixer() -> None:
            doc[key] = unescape(HTML_CODES_REGEX.sub(lower, doc[key]))
            logger.info("[FIX] Removing HTML codes from '%s'.", key)

        return fixer

    keys = papis.config.getlist("html-codes-keys", section="doctor")
    keys.extend(papis.config.getlist("html-codes-keys-extend", section="doctor"))

    for key in keys:
        value = doc.get(key)
        if value is None:
            continue

        m = HTML_CODES_REGEX.findall(str(value))
        if m:
            codes = "', '".join([f"&{c.lower()};" for c in m])
            results.append(
                make_error(doc, HTML_CODES_CHECK_NAME,
                           msg=f"Field '{key}' contains HTML codes: '{codes}'",
                           fix_action=make_fixer(key),
                           payload=key))

    return results


HTML_TAGS_CHECK_NAME = "html-tags"
HTML_TAGS_REGEX = re.compile(r"<.*?>")
HTML_TAGS_WHITESPACE_REGEX = re.compile(r"\s+")


def html_tags_check(doc: Document) -> list[Error]:
    """
    Checks that the keys in :confval:`doctor-html-tags-keys`
    configuration options do not contain any HTML tags like ``<href>`` etc.

    :returns: a :class:`list` of errors, one for each key that contains HTML codes.
    """
    from bs4 import BeautifulSoup

    results = []

    def convert_markup(text: str) -> str:
        if "<jats:" in text or "<mml:" in text:
            soup = BeautifulSoup(text, features="lxml")

            for tag in soup.find_all("jats:inline-formula"):
                tex = tag.find("jats:tex-math")
                if tex:
                    tag.replace_with(f" {tex.text.strip()} ")
                else:
                    tag.replace_with(f" {tag.text.strip()} ")

            for tag in soup.find_all("jats:title"):
                if tag.text.strip().lower() in {"abstract", "summary", "synopsis"}:
                    tag.extract()
                else:
                    # NOTE: these will get cleaned up in `make_fixer`
                    tag.insert_before("\n")
                    tag.insert_after("\n\n")

            for tag in soup.find_all("inline-formula"):
                annotation = tag.find("mml:annotation")
                if annotation:
                    tag.replace_with(f" {annotation.text.strip()} ")
                else:
                    tag.replace_with(f" {tag.text.strip()} ")

            # NOTE: can't use `soup.text` here because it doesn't add some spaces
            # around cases like "<p>Text</p>some more text", so we hack it manually
            text = str(soup)

        return text

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            # Step 1: remove all markup with special care for JATS / MML / ??
            text = convert_markup(str(doc[key]))
            text = HTML_TAGS_REGEX.sub(" ", text)

            # Step 2: cleanup paragraphs, if any
            text = "\n\n".join([
                HTML_TAGS_WHITESPACE_REGEX.sub(" ", line).strip()
                for p in text.split("\n\n") if (line := p.strip())
                ]).strip()

            doc[key] = text
            logger.info("[FIX] Removing HTML tags from key '%s'.", key)

        return fixer

    keys = papis.config.getlist("html-tags-keys", section="doctor")
    keys.extend(papis.config.getlist("html-tags-keys-extend", section="doctor"))

    from papis.document import describe

    for key in keys:
        value = doc.get(key)
        if value is None:
            logger.debug("Key '%s' not found in document: '%s'", key, describe(doc))
            continue

        if not isinstance(value, str):
            continue

        m = HTML_TAGS_REGEX.findall(value)
        if m:
            results.append(
                make_error(doc, HTML_TAGS_CHECK_NAME,
                           msg=f"Field '{key}' contains HTML tags: {m}",
                           fix_action=make_fixer(key),
                           payload=key))

    return results


EMPTY_FIELDS_CHECK_NAME = "empty-fields"


def empty_fields_check(doc: Document) -> list[Error]:
    """
    Checks for fields with empty values (``None``, ``""``, ``[]``, ``{}``).

    :returns: a :class:`list` of errors, one for each field with an empty value.
    """
    from papis.document import is_empty_value

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            del doc[key]
            logger.info("[FIX] Removing empty field '%s'.", key)

        return fixer

    return [
        make_error(doc, EMPTY_FIELDS_CHECK_NAME,
                   msg=f"Field '{key}' has an empty value ({doc[key]!r})",
                   fix_action=make_fixer(key),
                   payload=key)
        for key in doc if is_empty_value(doc[key])
    ]


STRING_CLEANER_CHECK_NAME = "string-cleaner"

# NOTE: matches all text with two or more consecutive whitespace characters
STRING_CLEANER_WHITESPACE_REGEX = re.compile(r"\s{2,}")
# NOTE: matches all text with "abstract" at the start
STRING_CLEANER_ABSTRACT_REGEX = re.compile(r"^\W*abstract\W*", re.IGNORECASE)
# NOTE: matches all text that is a single letter not followed by a dot
STRING_CLEANER_INITIALS_SPACE_REGEX = re.compile(r"\b(\w)(?!\.)\b")
# NOTE: matches all text that is a letter followed by dot and another letter
STRING_CLEANER_INITIALS_DOTS_REGEX = re.compile(r"(?<=\b\w\.)(?=\w)")
# NOTE: matches all text that is a single letter followed by a dot
STRING_CLEANER_INITIALS_UPPER_REGEX = re.compile(r"\b([^\W\d_])\.")


def _dotify_initials(text: str) -> str:
    # add dots
    text = STRING_CLEANER_INITIALS_SPACE_REGEX.sub(r"\1.", text)
    # add spaces
    text = STRING_CLEANER_INITIALS_DOTS_REGEX.sub(" ", text)
    # uppercase
    text = STRING_CLEANER_INITIALS_UPPER_REGEX.sub(
        lambda m: f"{m.group(1).upper()}.",
        text,
    )

    return text


def string_cleaner_check(doc: Document) -> list[Error]:
    """
    Check string keys in the document for various errors.

    This check goes through all the keys of the document that are known to be
    keys, according to :confval:`document-field-types`, and fixes any obvious
    errors. For example (not exhaustive):

    * Double spacing or any repeated whitespace.
    * Unexpected new line characters.
    * Non-standard initial formatting, e.g. "J R R Tolkien" should be
      "J. R. R. Tolkien". This is the formatting recommended in the
      `APA style <https://apastyle.apa.org/style-grammar-guidelines/references/elements-list-entry>`_,
      but many other (mostly Western) styles use it as well.

    :returns: a :class:`list` of errors, one for each string-based key that has
        unexpected formatting.
    """
    from papis.document import author_list_to_author

    def has_extra_newlines(key: str, value: str) -> bool:
        return "\n" in value

    def remove_newlines_fixer(key: str) -> FixFn:
        def fixer() -> None:
            doc[key] = doc[key].replace("\n", " ")
            logger.info("[FIX] Removing newline from '%s' key.", key)

        return fixer

    def has_abstract_issues(key: str, value: str) -> bool:
        return (
            key == "abstract"
            and STRING_CLEANER_ABSTRACT_REGEX.match(value) is not None
        )

    def remove_abstract_fixer() -> None:
        doc["abstract"] = (
            STRING_CLEANER_ABSTRACT_REGEX.sub(r"", doc["abstract"]).strip())
        if not doc["abstract"]:
            del doc["abstract"]
        logger.info("[FIX] Cleaning up 'abstract' key.")

    def has_extra_whitespace(key: str, value: str) -> bool:
        return STRING_CLEANER_WHITESPACE_REGEX.search(value) is not None

    def remove_whitespace_fixer(key: str) -> FixFn:
        def fixer() -> None:
            doc[key] = STRING_CLEANER_WHITESPACE_REGEX.sub(r" ", doc[key])
            logger.info("[FIX] Replacing repeated whitespace in key '%s'.", key)

        return fixer

    def has_author_initials(key: str, value: str, pattern: re.Pattern[str]) -> bool:
        if key != "author":
            return False

        if "author_list" not in doc:
            return False

        # NOTE: we only want to fix given names of an author (e.g. single letter
        # family names are allowed) and only if the author also has a family name
        # (e.g. an author like `{"given": "C Committee", "family": None}` should
        # be left alone)
        return any(pattern.search(author["given"])
                   for author in doc["author_list"]
                   if author.get("given") and author.get("family"))

    def author_initials_fixer() -> None:
        author_list = doc.get("author_list")
        if author_list is None:
            return

        for author in author_list:
            if author.get("given") and author.get("family"):
                author.update({"given": _dotify_initials(author["given"])})

        doc["author_list"] = author_list
        doc["author"] = author_list_to_author(doc)
        logger.info("[FIX] Cleaning 'author' key for missing dots and spaces.")

    from papis.document import get_document_field_types

    field_types = get_document_field_types()
    results = []

    for key, value in doc.items():
        if field_types.get(key) is not str:
            continue

        if not isinstance(value, str):
            results.append(
                make_error(doc, STRING_CLEANER_CHECK_NAME,
                           msg=(f"Key '{key}' should be of type 'str' "
                                f"but got {type(value).__name__!r}: {value!r}"),
                           payload=key))
            continue

        if has_abstract_issues(key, value):
            results.append(
                make_error(doc, STRING_CLEANER_CHECK_NAME,
                           msg="Key 'abstract' starts with 'Abstract'",
                           fix_action=remove_abstract_fixer,
                           payload=key))

        if (has_author_initials(key, value, STRING_CLEANER_INITIALS_SPACE_REGEX)
            or has_author_initials(key, value, STRING_CLEANER_INITIALS_DOTS_REGEX)):
            results.append(
                make_error(doc, STRING_CLEANER_CHECK_NAME,
                           msg=("Key 'author' contains initials that are not "
                                "followed by a dot+space (e.g. 'J R R' or 'J.R.R.')"),
                           fix_action=author_initials_fixer,
                           payload=key))

        if has_extra_newlines(key, value):
            results.append(
                make_error(doc, STRING_CLEANER_CHECK_NAME,
                           msg=f"Key '{key}' contains a newline",
                           fix_action=remove_newlines_fixer(key),
                           payload=key))

        if has_extra_whitespace(key, value):
            results.append(
                make_error(doc, STRING_CLEANER_CHECK_NAME,
                           msg=f"Key '{key}' contains repeated whitespace",
                           fix_action=remove_whitespace_fixer(key),
                           payload=key))

    return results


register_check(FILES_CHECK_NAME, files_check)
register_check(KEYS_MISSING_CHECK_NAME, keys_missing_check)
register_check(DUPLICATED_KEYS_NAME, duplicated_keys_check)
register_check(DUPLICATED_VALUES_NAME, duplicated_values_check)
register_check(BIBTEX_TYPE_CHECK_NAME, bibtex_type_check)
register_check(BIBLATEX_TYPE_ALIAS_CHECK_NAME, biblatex_type_alias_check)
register_check(BIBLATEX_KEY_ALIAS_CHECK_NAME, biblatex_key_alias_check)
register_check(BIBLATEX_REQUIRED_KEYS_CHECK_NAME, biblatex_required_keys_check)
register_check(BIBLATEX_KEY_CONVERT_CHECK_NAME, biblatex_key_convert_check)
register_check(REFS_CHECK_NAME, refs_check)
register_check(HTML_CODES_CHECK_NAME, html_codes_check)
register_check(HTML_TAGS_CHECK_NAME, html_tags_check)
register_check(FIELD_TYPE_CHECK_NAME, field_type_check)
register_check(EMPTY_FIELDS_CHECK_NAME, empty_fields_check)
register_check(STRING_CLEANER_CHECK_NAME, string_cleaner_check)

DEPRECATED_CHECK_NAMES = {
    "keys-exist": "keys-missing",
    "key-type": "field-type",
}


def gather_errors(documents: list[Document],
                  checks: list[str] | None = None) -> list[Error]:
    """Run all *checks* over the list of *documents*.

    Only checks registered with :func:`register_check` are supported and any
    unrecongnized checks are automatically skipped.

    :param checks: a list of checks to run over the documents. If not provided,
        the default :confval:`doctor-default-checks` are used.
    :returns: a list of all the errors gathered from the documents.
    """
    if not checks:
        checks = papis.config.getlist("default-checks", section="doctor")
        checks.extend(papis.config.getlist("default-checks-extend", section="doctor"))

    for check in checks:
        if check not in REGISTERED_CHECKS:
            logger.error("Unknown doctor check '%s' (skipping).", check)

    checks = [check for check in checks if check in REGISTERED_CHECKS]
    logger.debug("Running checks: '%s'.", "', '".join(checks))

    errors: list[Error] = []
    for doc in documents:
        for check in checks:
            errors.extend(REGISTERED_CHECKS[check].operate(doc))

    return errors


def fix_errors(doc: Document,
               checks: list[str] | None = None) -> None:
    """Fix errors in *doc* for the given *checks*.

    This function only applies existing auto-fixers to the document. This is
    not possible for many of the existing checks, but can be used to quickly
    clean up a document.
    """
    from papis.document import describe

    errors = gather_errors([doc], checks=checks)

    fixed = 0
    for error in errors:
        if not error.fix_action:
            logger.error("Cannot fix '%s' error for document '%s': %s",
                         error.name, describe(doc), error.msg)
            continue

        try:
            error.fix_action()
            fixed += 1
        except Exception as exc:
            logger.error("Failed to fix '%s' error for document '%s': %s",
                         error.name, describe(doc), error.msg,
                         exc_info=exc)

    if errors:
        logger.info("Auto-fixed %d / %d errors!", fixed, len(errors))

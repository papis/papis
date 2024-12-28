"""
The doctor command checks for the overall health of your library.

There are many checks implemented and some others that you
can add yourself through the Python configuration file (these cannot be added
through the static configuration file). Currently, the following checks are
implemented

* ``biblatex-key-alias``: checks that the document does not contain any known
  key (or field in BibLaTeX) from :data:`~papis.bibtex.bibtex_key_aliases`.
* ``biblatex-required-keys``: checks that the document contains all the required
  keys for its type. In BibLaTeX, each type (e.g. article) has a set of
  required (or at least strongly recommended) keys that it needs to be
  adequately shown in the bibliography.
* ``biblatex-type-alias``: checks that the BibLaTeX type of the document is not
  a known type alias (usually defined for backwards compatibility reasons), as
  defined by :data:`~papis.bibtex.bibtex_type_aliases`.
* ``bibtex-type``: checks that the document type matches a known BibLaTeX type
  from :data:`papis.bibtex.bibtex_types`.
* ``duplicated-keys``: checks that the keys provided by
  :confval:`doctor-duplicated-keys-keys` are not present in multiple
  documents. This is mainly meant to be used to check the ``ref`` key or other
  similar keys that are meant to be unique.
* ``duplicated-values``: checks if the keys provided by
  :confval:`doctor-duplicated-values-keys` have any duplicated
  values. The keys are expected to be lists, e.g. ``files``.
* ``files``: checks whether all the document files exist on the filesystem.
* ``html-codes``: checks that no HTML codes (e.g. ``&amp;``) appear in the keys
  provided by :confval:`doctor-html-codes-keys`.
* ``html-tags``: checks that no HTML or XML tags (e.g. ``<a>``) appear in the keys
  provided by :confval:`doctor-html-tags-keys`.
* ``key-type``: checks the type of keys provided by
  :confval:`doctor-key-type-keys`, e.g. year should be an ``int``.
  Lists can be automatically fixed (by splitting or joining) using the
  :confval:`doctor-key-type-separator` setting.
* ``keys-missing``: checks that the keys provided by
  :confval:`doctor-keys-missing-keys` exist in the document.
* ``refs``: checks that the document has a valid reference (i.e. one that would
  be accepted by BibTeX and only contains valid characters).

If any custom checks are implemented, you can get a complete list at runtime from

.. code:: sh

    papis list --doctors

Examples
^^^^^^^^

- To run all available checks over all available documents in the library use

    .. code:: sh

        papis doctor --all-checks --all

  This will likely generate too many results, but it can be useful to output in JSON

    .. code:: sh

        papis doctor --all-checks --all --json

- To check if all the files of a document are present, use

    .. code:: sh

        papis doctor --checks files einstein

- To check if any unwanted HTML tags are present in your documents (especially
  abstracts can be full of additional HTML or XML tags) use

    .. code:: sh

        papis doctor --explain --checks html-tags einstein

  The ``--explain`` flag can be used to give additional details of checks that
  failed. Some fixes such as this also have automatic fixers. Here, we can just
  remove all the HTML tags by writing

    .. code:: sh

        papis doctor --fix --checks html-tags einstein

- If an automatic fix is not possible, some checks also have suggested
  commands or tips to fix the issue that was found. For example, if a key
  does not exist in the document, it can suggest editing the file to add it.

    .. code:: sh

        papis doctor --suggestion --checks keys-missing einstein
        >> Suggestion: papis edit --doc-folder /path/to/folder

  If this is the case, you can also run the following to automatically open
  the ``info.yaml`` file for editing more complex changes

    .. code:: sh

        papis doctor --edit --checks keys-missing einstein


Implementing additional checks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A check is just a function that takes a document and returns a list of errors.
A skeleton implementation that gets added to ``config.py``
(see :ref:`config_py`) can be implemented as follows

.. code:: python

    from papis.commands.doctor import Error, register_check

    def my_custom_check(doc) -> List[Error]:
        ...

    register_check("my-custom-check", my_custom_check)

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.doctor:cli
    :prog: papis doctor
"""

import os
import re
import collections
from typing import Any, Optional, List, NamedTuple, Callable, Dict, Set, Tuple, Match

import click

import papis
import papis.cli
import papis.config
import papis.strings
import papis.database
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

#: Callable for automatic doctor fixers. This callable is constructed by a
#: check and is expected to wrap all the required data, so it takes no arguments.
FixFn = Callable[[], None]
#: Callable for doctor document checks.
CheckFn = Callable[[papis.document.Document], List["Error"]]


class Error(NamedTuple):
    """A detailed error error returned by a doctor check."""

    #: Name of the check generating the error.
    name: str
    #: Path to the document that generated the error.
    path: str
    #: A value that caused the error.
    payload: str
    #: A short message describing the error that can be displayed to the user.
    msg: str
    #: A command to run to fix the error that can be suggested to the user.
    suggestion_cmd: str
    #: A callable that can autofix the error (see :data:`FixFn`). Note that this
    #: will change the attached :attr:`doc`.
    fix_action: Optional[FixFn]
    #: The document that generated the error.
    doc: Optional[papis.document.Document]


class Check(NamedTuple):
    #: Name of the check
    name: str
    #: A callable that takes a document and returns a list of errors generated
    #: by the current check (see :data:`CheckFn`).
    operate: CheckFn


REGISTERED_CHECKS: Dict[str, Check] = {}


def error_to_dict(e: Error) -> Dict[str, Any]:
    return {
        "msg": e.payload,
        "path": e.path,
        "name": e.name,
        "suggestion": e.suggestion_cmd}


def register_check(name: str, check: CheckFn) -> None:
    """
    Register a new check.

    Registered checks are recognized by ``papis`` and can be used by users
    in their configuration files through :confval:`doctor-default-checks`
    or on the command line through the ``--checks`` flag.
    """
    REGISTERED_CHECKS[name] = Check(name=name, operate=check)


def registered_checks_names() -> List[str]:
    return list(REGISTERED_CHECKS.keys())


FILES_CHECK_NAME = "files"


def files_check(doc: papis.document.Document) -> List[Error]:
    """
    Check whether the files of a document actually exist in the filesystem.

    :returns: a :class:`list` of errors, one for each file that does not exist.
    """

    files = doc.get_files()
    folder = doc.get_main_folder() or ""

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
        error = [Error(name=FILES_CHECK_NAME,
                       path=folder,
                       msg="Use the 'files' key instead of 'file' to list files",
                       suggestion_cmd=f"papis edit --doc-folder {folder}",
                       fix_action=None,
                       payload="file",
                       doc=doc)]
    else:
        error = []

    return [Error(name=FILES_CHECK_NAME,
                  path=folder,
                  msg=f"File '{f}' declared but does not exist",
                  suggestion_cmd=f"papis edit --doc-folder {folder}",
                  fix_action=make_fixer(f),
                  payload=f,
                  doc=doc)
            for f in files if not os.path.exists(f)] + error


KEYS_MISSING_CHECK_NAME = "keys-missing"


def keys_missing_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks whether the keys provided in the configuration
    option :confval:`doctor-keys-missing-keys` exist in the document
    and are non-empty.

    :returns: a :class:`list` of errors, one for each missing key.
    """
    from papis.defaults import NOT_SET

    folder = doc.get_main_folder() or ""
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

    def make_fixer(key: str) -> Optional[FixFn]:
        def fixer_author_from_author_list() -> None:
            if "author_list" not in doc:
                return

            logger.info("[FIX] Parsing 'author_list' into 'author': '%s'.",
                        doc["author_list"])
            doc["author"] = papis.document.author_list_to_author(doc)

        def fixer_author_list_from_author() -> None:
            if "author" not in doc:
                return

            logger.info("[FIX] Parsing 'author' into 'author_list': '%s'.",
                        doc["author"])
            doc["author_list"] = papis.document.split_authors_name(doc["author"])

        if key == "author":
            return fixer_author_from_author_list
        elif key == "author_list":
            return fixer_author_list_from_author
        else:
            return None

    return [Error(name=KEYS_MISSING_CHECK_NAME,
                  path=folder,
                  msg=f"Key '{k}' does not exist",
                  suggestion_cmd=f"papis edit --doc-folder {folder}",
                  fix_action=make_fixer(k),
                  payload=k,
                  doc=doc)
            for k in keys if k not in doc]


REFS_BAD_SYMBOL_REGEX = re.compile(r"[ ,{}\[\]@#`']")

REFS_CHECK_NAME = "refs"


def refs_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks that a ref exists and if not it tries to create one
    according to the :confval:`ref-format` configuration option.

    :returns: an error if the reference does not exist or contains invalid
        characters (as required by BibTeX).
    """
    import papis.bibtex

    folder = doc.get_main_folder() or ""

    def create_ref_fixer() -> None:
        ref = papis.bibtex.create_reference(doc, force=True)
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
        return [Error(name=REFS_CHECK_NAME,
                      path=folder,
                      msg="Reference missing",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=create_ref_fixer,
                      payload="ref",
                      doc=doc)]

    m = REFS_BAD_SYMBOL_REGEX.findall(ref)
    if m:
        return [Error(name=REFS_CHECK_NAME,
                      path=folder,
                      msg=f"Bad characters ({set(m)}) found in reference",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=clean_ref_fixer,
                      payload="ref",
                      doc=doc)]

    return []


DUPLICATED_KEYS_SEEN: Dict[str, Set[str]] = collections.defaultdict(set)
DUPLICATED_KEYS_NAME = "duplicated-keys"


def duplicated_keys_check(doc: papis.document.Document) -> List[Error]:
    """
    Check for duplicated keys in the list given by the
    :confval:`doctor-duplicated-keys-keys` configuration option.

    :returns: a :class:`list` of errors, one for each key with a value that already
        exist in the documents from the current query.
    """
    folder = doc.get_main_folder() or ""

    keys = papis.config.getlist("duplicated-keys-keys", section="doctor")
    keys.extend(papis.config.getlist("duplicated-keys-keys-extend", section="doctor"))

    results: List[Error] = []
    for key in keys:
        value = doc.get(key)
        if value is None:
            continue

        value = str(value)
        seen = DUPLICATED_KEYS_SEEN[key]
        if value not in seen:
            seen.update({value})
            continue

        results.append(Error(name=DUPLICATED_KEYS_NAME,
                             path=folder,
                             msg=f"Key '{key}' is duplicated ({value})",
                             suggestion_cmd=f"papis edit {key}:'{value}'",
                             fix_action=None,
                             payload=key,
                             doc=doc))

    return results


DUPLICATED_VALUES_NAME = "duplicated-values"


def duplicated_values_check(doc: papis.document.Document) -> List[Error]:
    """
    Check if the keys given by :confval:`doctor-duplicated-values-keys`
    contain any duplicate entries. These keys are expected to be lists of items.

    :returns: a :class:`list` of errors, one for each key with a value that
        has duplicate entries.
    """
    keys = papis.config.getlist("duplicated-values-keys", section="doctor")
    keys.extend(papis.config.getlist("duplicated-values-keys-extend", section="doctor"))
    folder = doc.get_main_folder() or ""

    def make_fixer(key: str, entries: List[Any]) -> FixFn:
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

    results: List[Error] = []
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

        results.append(Error(name=DUPLICATED_VALUES_NAME,
                             path=folder,
                             msg=(
                                 "Key '{}' contains duplicate entries: '{}'"
                                 .format(key, "', '".join(str(d) for d in dupes))),
                             suggestion_cmd=f"papis edit --doc-folder {folder}",
                             fix_action=make_fixer(key, list(seen.values())),
                             payload=key,
                             doc=doc))

    return results


BIBTEX_TYPE_CHECK_NAME = "bibtex-type"


def bibtex_type_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that the document type is compatible with BibTeX or BibLaTeX type descriptors.

    :returns: an error if the types are not compatible.
    """
    from papis.bibtex import bibtex_types, bibtex_type_converter
    folder = doc.get_main_folder() or ""

    def make_fixer(bib_type: str) -> Optional[FixFn]:
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
        return [Error(name=BIBTEX_TYPE_CHECK_NAME,
                      path=folder,
                      msg="Document does not define a type",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=None,
                      payload="type",
                      doc=doc)]

    if bib_type not in bibtex_types:
        return [Error(name=BIBTEX_TYPE_CHECK_NAME,
                      path=folder,
                      msg=f"Document type '{bib_type}' is not a valid BibTeX type",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=make_fixer(bib_type),
                      payload=bib_type,
                      doc=doc)]

    return []


BIBLATEX_TYPE_ALIAS_CHECK_NAME = "biblatex-type-alias"


def biblatex_type_alias_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that the BibLaTeX type of the document is not a known alias.

    The aliases are described by :data:`~papis.bibtex.bibtex_type_aliases`.

    :returns: an error if the type of the document is an alias.
    """
    from papis.bibtex import bibtex_type_aliases
    folder = doc.get_main_folder() or ""

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
        return [Error(name=BIBLATEX_TYPE_ALIAS_CHECK_NAME,
                      path=folder,
                      msg=("Document type '{}' is an alias for '{}' in BibLaTeX"
                           .format(bib_type, bib_type_base)),
                      suggestion_cmd="papis edit --doc-folder {}".format(folder),
                      fix_action=make_fixer(bib_type_base),
                      payload=bib_type,
                      doc=doc)]

    return []


# NOTE: `journal` is a key that papis relies on and we do not want to rename it
BIBLATEX_KEY_ALIAS_IGNORED = {"journal"}
BIBLATEX_KEY_ALIAS_CHECK_NAME = "biblatex-key-alias"


def biblatex_key_alias_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that no BibLaTeX keys in the document are known aliases.

    The aliases are described by :data:`~papis.bibtex.bibtex_key_aliases`. Note
    that these keys can also be converted on export to BibLaTeX.

    :returns: an error for each key of the document that is an alias.
    """
    from papis.bibtex import bibtex_key_aliases
    folder = doc.get_main_folder() or ""

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            new_key = bibtex_key_aliases[key]
            logger.info("[FIX] Renaming BibLaTeX key '%s' to '%s'.", key, new_key)
            doc[new_key] = doc[key]
            del doc[key]

        return fixer

    return [Error(name=BIBLATEX_KEY_ALIAS_CHECK_NAME,
                  path=folder,
                  msg=("Document key '{}' is an alias for '{}' in BibLaTeX"
                       .format(key, bibtex_key_aliases[key])),
                  suggestion_cmd="papis edit --doc-folder {}".format(folder),
                  fix_action=make_fixer(key),
                  payload=key,
                  doc=doc)
            for key in doc
            if key not in BIBLATEX_KEY_ALIAS_IGNORED and key in bibtex_key_aliases]


BIBLATEX_REQUIRED_KEYS_CHECK_NAME = "biblatex-required-keys"


def biblatex_required_keys_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that required BibLaTeX keys are part of the document based on its type.

    The required keys are described by :data:`papis.bibtex.bibtex_type_required_keys`.
    Note that most BibLaTeX processors will be quite forgiving if these keys are
    missing.

    :returns: an error for each key of the document that is missing.
    """
    import papis.bibtex
    folder = doc.get_main_folder() or ""

    errors = bibtex_type_check(doc)
    if errors:
        return [e._replace(name=BIBLATEX_REQUIRED_KEYS_CHECK_NAME) for e in errors]

    # translate bibtex type
    bib_type = doc["type"]
    bib_type = papis.bibtex.bibtex_type_aliases.get(bib_type, bib_type)

    if bib_type not in papis.bibtex.bibtex_type_required_keys:
        bib_type = papis.bibtex.bibtex_type_required_keys_aliases.get(bib_type)

    required_keys = papis.bibtex.bibtex_type_required_keys[bib_type]
    aliases = {v: k for k, v in papis.bibtex.bibtex_key_aliases.items()}

    return [Error(name=BIBLATEX_REQUIRED_KEYS_CHECK_NAME,
                  path=folder,
                  msg=("Document of type '{}' requires one of the keys ['{}'] "
                       "to be compatible with BibLaTeX"
                       .format(bib_type, "', '".join(keys))),
                  suggestion_cmd="papis edit --doc-folder {}".format(folder),
                  fix_action=None,
                  payload=",".join(keys),
                  doc=doc)
            for keys in required_keys
            if not any(key in doc or aliases.get(key) in doc for key in keys)]


KEY_TYPE_CHECK_NAME = "key-type"


def get_key_type_check_keys() -> Dict[str, type]:
    """
    Check the `doctor-key-type-keys` configuration entry for correctness.

    The :confval:`doctor-key-type-keys` configuration entry
    defines a mapping of keys and their expected types. If the desired type is
    a list, the :confval:`doctor-key-type-separator` setting
    can be used to split an existing string (and, similarly, if the desired type
    is a string, it can be used to join a list of items).

    :returns: A dictionary mapping key names to types.
    """
    import builtins

    from papis.defaults import NOT_SET

    keys = papis.config.get("key-type-check-keys", section="doctor")
    if keys is NOT_SET:
        keys = papis.config.getlist("key-type-keys", section="doctor")
    else:
        keys = papis.config.getlist("key-type-check-keys", section="doctor")
        logger.warning("The configuration option 'doctor-key-type-check-keys' "
                       "is deprecated and will be removed in the next version. "
                       "Use 'doctor-key-type-keys' instead.")

    keys.extend(papis.config.getlist("key-type-keys-extend", section="doctor"))
    processed_keys: Dict[str, type] = {}
    for value in keys:
        if ":" not in value:
            logger.error("Invalid (key, type) pair: '%s'. Must be 'key:type'.",
                         value)
            continue
        key, cls_name = value.split(":")
        key, cls_name = key.strip(), cls_name.strip()

        cls = getattr(builtins, cls_name, None)
        if not isinstance(cls, type):
            logger.error(
                "Invalid type for key '%s': '%s'. Only builtin types are supported",
                key, cls_name)
            continue
        processed_keys[key] = cls

    return processed_keys


def key_type_check(doc: papis.document.Document) -> List[Error]:
    """
    Check document keys have expected types.

    :returns: a :class:`list` of errors, one for each key does not have the
        expected type (if it exists).
    """
    from papis.defaults import NOT_SET

    folder = doc.get_main_folder() or ""

    # NOTE: the separator can be quoted so that it can force whitespace
    separator = papis.config.get("key-type-check-separator", section="doctor")
    if separator is NOT_SET:
        separator = papis.config.get("key-type-separator", section="doctor")
    else:
        logger.warning("The configuration option 'doctor-key-type-check-separator' "
                       "is deprecated and will be removed in the next version. "
                       "Use 'doctor-key-type-separator' instead.")

    separator = separator.strip("'").strip('"') if separator else None

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
                             key, cls, papis.document.describe(doc), exc_info=exc)

        if cls is list:
            return fixer_convert_list
        if cls is str:
            return fixer_convert_str
        else:
            return fixer_convert_any

    results = []
    for key, cls in get_key_type_check_keys().items():

        doc_value = doc.get(key)
        if doc_value is not None and not isinstance(doc_value, cls):
            results.append(Error(name=KEY_TYPE_CHECK_NAME,
                                 path=folder,
                                 msg=(
                                     f"Key '{key}' should be of type '{cls.__name__}' "
                                     f"but got '{type(doc_value).__name__}': "
                                     f"{doc_value!r}"),
                                 suggestion_cmd=f"papis edit --doc-folder {folder}",
                                 fix_action=make_fixer(key, cls),
                                 payload=key,
                                 doc=doc))
    return results


# NOTE: https://www.w3schools.com/html/html_symbols.asp
HTML_CODES_REGEX = re.compile(r"&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-fA-F]{1,6});", re.I)
HTML_CODES_CHECK_NAME = "html-codes"


def html_codes_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks that the keys in :confval:`doctor-html-codes-keys`
    configuration options do not contain any HTML codes like ``&amp;`` etc.

    :returns: a :class:`list` of errors, one for each key that contains HTML codes.
    """
    from html import unescape

    results = []
    folder = doc.get_main_folder() or ""

    def make_fixer(key: str) -> FixFn:
        def lower(p: Match[str]) -> str:
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
            results.append(Error(name=HTML_CODES_CHECK_NAME,
                                 path=folder,
                                 msg=f"Field '{key}' contains HTML codes: '{codes}'",
                                 suggestion_cmd=f"papis edit --doc-folder {folder}",
                                 fix_action=make_fixer(key),
                                 payload=key,
                                 doc=doc))

    return results


HTML_TAGS_CHECK_NAME = "html-tags"
HTML_TAGS_REGEX = re.compile(r"<.*?>")
HTML_TAGS_WHITESPACE_REGEX = re.compile(r"\s+")


def html_tags_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks that the keys in :confval:`doctor-html-tags-keys`
    configuration options do not contain any HTML tags like ``<href>`` etc.

    :returns: a :class:`list` of errors, one for each key that contains HTML codes.
    """
    from bs4 import BeautifulSoup

    results = []
    folder = doc.get_main_folder() or ""

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
                if tag.text.strip() == "Abstract":
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

    for key in keys:
        value = doc.get(key)
        if value is None:
            logger.debug("Key '%s' not found in document: '%s'",
                         key, papis.document.describe(doc))
            continue

        if not isinstance(value, str):
            continue

        m = HTML_TAGS_REGEX.findall(value)
        if m:
            results.append(Error(name=HTML_TAGS_CHECK_NAME,
                                 path=folder,
                                 msg=f"Field '{key}' contains HTML tags: {m}",
                                 suggestion_cmd=f"papis edit --doc-folder {folder}",
                                 fix_action=make_fixer(key),
                                 payload=key,
                                 doc=doc))

    return results


register_check(FILES_CHECK_NAME, files_check)
register_check(KEYS_MISSING_CHECK_NAME, keys_missing_check)
register_check(DUPLICATED_KEYS_NAME, duplicated_keys_check)
register_check(DUPLICATED_VALUES_NAME, duplicated_values_check)
register_check(BIBTEX_TYPE_CHECK_NAME, bibtex_type_check)
register_check(BIBLATEX_TYPE_ALIAS_CHECK_NAME, biblatex_type_alias_check)
register_check(BIBLATEX_KEY_ALIAS_CHECK_NAME, biblatex_key_alias_check)
register_check(BIBLATEX_REQUIRED_KEYS_CHECK_NAME, biblatex_required_keys_check)
register_check(REFS_CHECK_NAME, refs_check)
register_check(HTML_CODES_CHECK_NAME, html_codes_check)
register_check(HTML_TAGS_CHECK_NAME, html_tags_check)
register_check(KEY_TYPE_CHECK_NAME, key_type_check)

DEPRECATED_CHECK_NAMES = {
    "keys-exist": "keys-missing",
}


def gather_errors(documents: List[papis.document.Document],
                  checks: Optional[List[str]] = None) -> List[Error]:
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

    errors: List[Error] = []
    for doc in documents:
        for check in checks:
            errors.extend(REGISTERED_CHECKS[check].operate(doc))

    return errors


def fix_errors(doc: papis.document.Document,
               checks: Optional[List[str]] = None) -> None:
    """Fix errors in *doc* for the given *checks*.

    This function only applies existing auto-fixers to the document. This is
    not possible for many of the existing checks, but can be used to quickly
    clean up a document.
    """
    errors = gather_errors([doc], checks=checks)

    fixed = 0
    for error in errors:
        if not error.fix_action:
            logger.error("Cannot fix '%s' error for document '%s': %s",
                         error.name, papis.document.describe(doc), error.msg)
            continue

        try:
            error.fix_action()
            fixed += 1
        except Exception as exc:
            logger.error("Failed to fix '%s' error for document '%s': %s",
                         error.name, papis.document.describe(doc), error.msg,
                         exc_info=exc)

    if errors:
        logger.info("Auto-fixed %d / %d errors!", fixed, len(errors))


def process_errors(errors: List[Error],
                   fix: bool = False,
                   explain: bool = False,
                   suggest: bool = False,
                   edit: bool = False) -> None:
    """Process a list of document errors from :func:`gather_errors`.

    :param fix: if *True*, any automatic fixes are applied to the document the
        error refers to.
    :param explain: if *True*, a short explanation of the error is shown.
    :param suggest: if *True*, a short suggestion for manual fixing of the
        error is shown.
    :param edit: if *True*, the document is opened for editing.
    """
    if not errors:
        return

    import colorama as c

    from papis.api import save_doc
    from papis.commands.edit import run as edit_run

    fixed = 0
    for i, error in enumerate(errors):
        if i != 0:
            click.echo()

        click.echo(
            f"{c.Style.BRIGHT}{c.Fore.RED}{error.name}{c.Style.RESET_ALL}"
            f"\t{c.Style.BRIGHT}{error.payload}{c.Style.RESET_ALL}"
            f"\t{c.Fore.YELLOW}{error.path}{c.Style.RESET_ALL}")

        if explain:
            click.echo(
                f"\t{c.Style.BRIGHT}{c.Fore.CYAN}Reason{c.Style.RESET_ALL}: "
                f"{error.msg}")

        if suggest:
            click.echo(
                f"\t{c.Style.BRIGHT}{c.Fore.GREEN}Suggestion{c.Style.RESET_ALL}: "
                f"{error.suggestion_cmd}")

        if fix and error.fix_action:
            try:
                error.fix_action()
                fixed += 1
            except Exception as exc:
                logger.error("Failed to fix '%s' for document '%s'.",
                             error.name,
                             papis.document.describe(error.doc)
                             if error.doc else "unknown",
                             exc_info=exc)

        if error.doc:
            if edit:
                # NOTE: ensure the document has been saved before editing
                error.doc.save()

                click.pause("Press any key to edit...")
                edit_run(error.doc)
            elif fix and error.fix_action:
                save_doc(error.doc)

    if fix and errors:
        logger.info("Auto-fixed %d / %d errors!", fixed, len(errors))


def run(doc: papis.document.Document,
        checks: Optional[List[str]] = None,
        fix: bool = True,
        explain: bool = False,
        suggest: bool = False,
        edit: bool = False) -> None:
    """
    Runner for ``papis doctor``.

    It runs all the checks given by the *checks* argument that have been
    registered through :func:`register_check`. It then proceeds with processing
    and fixing each error in turn.
    """
    errors = gather_errors([doc], checks=checks)
    process_errors(errors,
                   fix=fix,
                   explain=explain,
                   suggest=suggest,
                   edit=edit)


@click.command("doctor")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.sort_option()
@click.option("-t", "--checks", "_checks",
              default=lambda: (
                  papis.config.getlist("default-checks", section="doctor")
                  + papis.config.getlist("default-checks-extend", section="doctor")),
              multiple=True,
              type=click.Choice(registered_checks_names()
                                + list(DEPRECATED_CHECK_NAMES)),
              help="Checks to run on every document.")
@papis.cli.bool_flag("--json", "_json",
                     help="Output the results in JSON format")
@papis.cli.bool_flag("--fix",
                     help="Auto fix the errors with the auto fixer mechanism")
@papis.cli.bool_flag("-s", "--suggest",
                     help="Suggest commands to be run for resolution")
@papis.cli.bool_flag("-e", "--explain",
                     help="Give a short message for the reason of the error")
@papis.cli.bool_flag("--edit",
                     help="Edit every file with the edit command.")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
@papis.cli.bool_flag("--all-checks", "all_checks",
                     help="Run all available checks (ignores --checks)")
def cli(query: str,
        doc_folder: Tuple[str, ...],
        sort_field: Optional[str],
        sort_reverse: bool,
        _all: bool,
        fix: bool,
        edit: bool,
        explain: bool,
        _checks: List[str],
        _json: bool,
        suggest: bool,
        all_checks: bool) -> None:
    """Check for common problems in documents"""
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if all_checks:
        checks = list(REGISTERED_CHECKS)
    else:
        # NOTE: ensure uniqueness of the checks so we don't run the same ones
        checks = list(set(_checks))

    new_checks = []
    for check in checks:
        new_check = DEPRECATED_CHECK_NAMES.get(check)
        if new_check is not None:
            check = new_check
            logger.warning("Check '%s' is deprecated and has been replace by "
                           "'%s'. Please use this in the future.",
                           check, new_check)

        new_checks.append(check)
    checks = new_checks

    errors = gather_errors(documents, checks=checks)
    if errors:
        logger.warning("Found %s errors.", len(errors))
    else:
        logger.info("No errors found!")

    if _json:
        import json

        click.echo(json.dumps(
            list(map(error_to_dict, errors)),
            indent=2))
        return

    process_errors(errors,
                   fix=fix,
                   explain=explain,
                   suggest=suggest,
                   edit=edit)

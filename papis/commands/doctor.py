"""
The doctor command checks for the overall health of your library.

There are many checks implemented and some others that you
can add yourself through the Python configuration file (these cannot be added
through the static configuration file). Currently, the following checks are
implemented

* ``files``: checks whether all the document files exist on the filesystem.
* ``keys-exist``: checks that the keys provided by
  :ref:`config-settings-doctor-keys-exist-keys` exist in the document.
* ``duplicated-keys``: checks that the keys provided by
  :ref:`config-settings-doctor-duplicated-keys-keys` are not present in multiple
  documents. This is mainly meant to be used to check the ``ref`` key.
* ``bibtex-type``: checks that the document type matches a known BibTeX type.
* ``refs``: checks that the document has a valid reference.
* ``html-codes``: checks that no HTML codes (e.g. ``&amp;``) appear in the keys
  provided by :ref:`config-settings-doctor-html-codes-keys`.
* ``html-tags``: checks that no HTML tags (e.g. ``<a>``) appear in the keys
  provided by :ref:`config-settings-doctor-html-tags-keys`.
* ``key-type``: checks the type of keys provided by
  :ref:`config-settings-doctor-key-type-check-keys`, e.g.
  (year should be an ``int``).

If any custom checks are implemented, you can get a complete list at runtime from

.. code:: sh

    papis doctor --list-checks

Examples
^^^^^^^^

- To check if all the files of a document are present, use

    .. code:: sh

        papis doctor --check files einstein

- To check if any unwanted HTML tags are present in your documents (especially
  abstracts can be full of additional HTML or XML tags) use

    .. code:: sh

        papis doctor --explain --check html-tags einstein

  The ``--explain`` flag can be used to give additional details of checks that
  failed. Some fixes such as this also have automatic fixers. Here, we can just
  remove all the HTML tags by writing

    .. code:: sh

        papis doctor --fix --check html-tags einstein

- If an automatic fix is not possible, some checks also have suggested
  commands or tips to fix the issue that was found. For example, if a key
  does not exist in the document, it can suggest editing the file to add it.

    .. code:: sh

        papis doctor --suggestion --check keys-exist einstein
        >> Suggestion: papis edit --doc-folder /path/to/folder

  If this is the case, you can also run

        papis doctor --edit --check keys-exist einstein

  to automatically open the ``info.yaml`` file for editing.

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
from typing import Any, Optional, List, NamedTuple, Callable, Dict, Set, Tuple

import click

import papis
import papis.cli
import papis.config
import papis.strings
import papis.database
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

FixFn = Callable[[], None]
CheckFn = Callable[[papis.document.Document], List["Error"]]


class Error(NamedTuple):
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
    #: A callable that can autofix the error.
    fix_action: FixFn
    #: The document that generated the error.
    doc: Optional[papis.document.Document]


class Check(NamedTuple):
    #: Name of the check
    name: str
    #: A callable that takes a document and returns a list of errors generated
    #: by the current check.
    operate: CheckFn


REGISTERED_CHECKS: Dict[str, Check] = {}


def error_to_dict(e: Error) -> Dict[str, Any]:
    return {
        "msg": e.payload,
        "path": e.path,
        "name": e.name,
        "suggestion": e.suggestion_cmd}


def register_check(name: str, check_function: CheckFn) -> None:
    """
    Register a check.

    Registered checks are recognized by ``papis`` and can be used by users
    in their configuration files, for example.
    """
    REGISTERED_CHECKS[name] = Check(name=name, operate=check_function)


def registered_checks_names() -> List[str]:
    return list(REGISTERED_CHECKS.keys())


FILES_CHECK_NAME = "files"


def files_check(doc: papis.document.Document) -> List[Error]:
    """
    Check whether the files of a document actually exist in the filesystem.

    :returns: a :class:`list` of errors, one for each file that does not exist.
    """
    from papis.api import save_doc

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
                save_doc(doc)

        return fixer

    return [Error(name=FILES_CHECK_NAME,
                  path=folder,
                  msg=f"File '{f}' declared but does not exist",
                  suggestion_cmd=f"papis edit --doc-folder {folder}",
                  fix_action=make_fixer(f),
                  payload=f,
                  doc=doc)
            for f in files if not os.path.exists(f)]


KEYS_EXIST_CHECK_NAME = "keys-exist"


def keys_exist_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks whether the keys provided in the configuration
    option ``doctor-keys-exist-keys`` exit in the document and are non-empty.

    :returns: a :class:`list` of errors, one for each key that does not exist.
    """
    keys = papis.config.getlist("doctor-keys-exist-keys")
    folder = doc.get_main_folder() or ""

    return [Error(name=KEYS_EXIST_CHECK_NAME,
                  path=folder,
                  msg=f"Key '{k}' does not exist.",
                  suggestion_cmd=f"papis edit --doc-folder {folder}",
                  fix_action=lambda: None,
                  payload=k,
                  doc=doc)
            for k in keys if k not in doc]


REFS_BAD_SYMBOL_REGEX = re.compile(r"[ ,{}\[\]@#`']")

REFS_CHECK_NAME = "refs"


def refs_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks that a ref exists and if not it tries to create one according to
    the ``ref-format`` configuration option.

    :returns: an error if the reference does not exist or contains invalid
        characters (as required by BibTeX).
    """
    from papis.api import save_doc

    folder = doc.get_main_folder() or ""

    def create_ref_fixer() -> None:
        ref = papis.bibtex.create_reference(doc, force=True)
        logger.info("[FIX] Setting ref to '%s': '%s'.",
                    ref,
                    papis.document.describe(doc))

        doc["ref"] = ref
        save_doc(doc)

    def clean_ref_fixer() -> None:
        ref = REFS_BAD_SYMBOL_REGEX.sub("", doc["ref"]).strip()
        if not ref:
            create_ref_fixer()
        else:
            logger.info("[FIX] Cleaning ref from '%s' to '%s': '%s'.",
                        doc["ref"], ref,
                        papis.document.describe(doc))

            doc["ref"] = ref

    ref = doc.get("ref")
    ref = str(ref).strip() if ref is not None else ref

    if not ref:
        return [Error(name=REFS_CHECK_NAME,
                      path=folder,
                      msg="Reference missing.",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=create_ref_fixer,
                      payload="ref",
                      doc=doc)]

    m = REFS_BAD_SYMBOL_REGEX.findall(ref)
    if m:
        return [Error(name=REFS_CHECK_NAME,
                      path=folder,
                      msg=f"Bad characters ({set(m)}) found in reference.",
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
    ``doctor-duplicated-keys-keys`` configuration option.

    :returns: a :class:`list` of errors, one for each key with a value that already
        exist in the documents from the current query.
    """
    keys = papis.config.getlist("doctor-duplicated-keys-keys")
    folder = doc.get_main_folder() or ""

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
                             msg=f"Key '{key}' is duplicated ({value}).",
                             suggestion_cmd=f"papis edit {key}:'{value}'",
                             fix_action=lambda: None,
                             payload=key,
                             doc=doc))

    return results


BIBTEX_TYPE_CHECK_NAME = "bibtex-type"


def bibtex_type_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that the document type is compatible with BibTeX or BibLaTeX type
    descriptors.

    :returns: an error if the types are not compatible.
    """
    import papis.bibtex
    folder = doc.get_main_folder() or ""
    bib_type = doc.get("type")

    if bib_type is None:
        return [Error(name=BIBTEX_TYPE_CHECK_NAME,
                      path=folder,
                      msg="Document does not define a type.",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=lambda: None,
                      payload="type",
                      doc=doc)]

    if bib_type not in papis.bibtex.bibtex_types:
        return [Error(name=BIBTEX_TYPE_CHECK_NAME,
                      path=folder,
                      msg=f"Document type '{bib_type}' is not a valid BibTeX type.",
                      suggestion_cmd=f"papis edit --doc-folder {folder}",
                      fix_action=lambda: None,
                      payload=bib_type,
                      doc=doc)]

    return []


KEY_TYPE_CHECK_NAME = "key-type"


def key_type_check(doc: papis.document.Document) -> List[Error]:
    """
    Check document keys have expected types.

    The ``doctor-key-type-check-keys`` configuration entry defines a mapping
    of keys and their expected types.

    :returns: a :class:`list` of errors, one for each key does not have the
        expected type (if it exists).
    """
    folder = doc.get_main_folder() or ""

    results = []
    for value in papis.config.getlist("doctor-key-type-check-keys"):
        try:
            key, cls_name = eval(value)
        except Exception as exc:
            logger.error("Invalid (key, type) pair: '%s'.",
                         value, exc_info=exc)
            continue

        try:
            cls = eval(cls_name)
        except Exception as exc:
            logger.error("Invalid type for key '%s': '%s'.",
                         key, cls_name, exc_info=exc)
            continue

        doc_value = doc.get(key)
        if doc_value is not None and not isinstance(doc_value, cls):
            results.append(Error(name=KEY_TYPE_CHECK_NAME,
                                 path=folder,
                                 msg=(
                                     f"Key '{key}' ({doc_value}) should be of type "
                                     f"'{cls}' but got '{type(doc_value).__name__}'."),
                                 suggestion_cmd=f"papis edit --doc-folder {folder}",
                                 fix_action=lambda: None,
                                 payload=key,
                                 doc=doc))
    return results


# NOTE: https://www.w3schools.com/html/html_symbols.asp
HTML_CODES_REGEX = re.compile(r"&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-fA-F]{1,6});")
HTML_CODES_CHECK_NAME = "html-codes"


def html_codes_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks that the keys in ``doctor-html-code-keys`` configuration options do
    not contain any HTML codes like ``&amp;`` etc.

    :returns: a :class:`list` of errors, one for each key that contains HTML codes.
    """
    from html import unescape
    from papis.api import save_doc

    results = []
    folder = doc.get_main_folder() or ""

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            val = unescape(doc[key])
            doc[key] = val
            logger.info("[FIX] Setting '%s' to '%s'.", key, val)
            save_doc(doc)

        return fixer

    for key in papis.config.getlist("doctor-html-codes-keys"):
        value = doc.get(key)
        if value is None:
            continue

        m = HTML_CODES_REGEX.findall(str(value))
        if m:
            results.append(Error(name=HTML_CODES_CHECK_NAME,
                                 path=folder,
                                 msg=f"Field '{key}' contains HTML codes {m}",
                                 suggestion_cmd=f"papis edit --doc-folder {folder}",
                                 fix_action=make_fixer(key),
                                 payload=key,
                                 doc=doc))

    return results


HTML_TAGS_CHECK_NAME = "html-tags"
HTML_TAGS_REGEX = re.compile(r"<.*?>")


def html_tags_check(doc: papis.document.Document) -> List[Error]:
    """
    Checks that the keys in ``doctor-html-tags-keys`` configuration options do
    not contain any HTML tags like ``<href>`` etc.

    :returns: a :class:`list` of errors, one for each key that contains HTML codes.
    """
    from papis.api import save_doc

    results = []
    folder = doc.get_main_folder() or ""

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            old_value = str(doc[key])
            new_value = HTML_TAGS_REGEX.sub("", old_value).strip()

            logger.info("[FIX] Removing HTML tags from key '%s'.", key)
            doc[key] = new_value
            save_doc(doc)

        return fixer

    for key in papis.config.getlist("doctor-html-tags-keys"):
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
register_check(KEYS_EXIST_CHECK_NAME, keys_exist_check)
register_check(DUPLICATED_KEYS_NAME, duplicated_keys_check)
register_check(BIBTEX_TYPE_CHECK_NAME, bibtex_type_check)
register_check(REFS_CHECK_NAME, refs_check)
register_check(HTML_CODES_CHECK_NAME, html_codes_check)
register_check(HTML_TAGS_CHECK_NAME, html_tags_check)
register_check(KEY_TYPE_CHECK_NAME, key_type_check)


def run(doc: papis.document.Document, checks: List[str]) -> List[Error]:
    """
    Runner for ``papis doctor``.

    It runs all the checks given by the *checks* argument that have been
    registered through :func:`register_check`.
    """
    assert all(check in REGISTERED_CHECKS for check in checks)

    results: List[Error] = []
    for check in checks:
        results.extend(REGISTERED_CHECKS[check].operate(doc))

    return results


@click.command("doctor")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.sort_option()
@click.option("-t", "--checks", "_checks",
              default=lambda: papis.config.getlist("doctor-default-checks"),
              multiple=True,
              type=click.Choice(registered_checks_names()),
              help="Checks to run on every document.")
@papis.cli.bool_flag("--json", "_json",
                     help="Output the results in json format")
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
@papis.cli.bool_flag("--list-checks", "list_checks",
                     help="List available checks and their descriptions")
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
        list_checks: bool) -> None:
    """Check for common problems in documents"""

    if list_checks:
        click.echo("\n".join(papis.utils.dump_object_doc([
            (name, fn.operate) for name, fn in REGISTERED_CHECKS.items()
            ], sep="\n    ")))

        return

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    logger.debug("Running checks: '%s'.", "', '".join(_checks))

    errors: List[Error] = []
    for doc in documents:
        errors.extend(run(doc, _checks))

    if errors:
        logger.warning("Found %s errors.", len(errors))
    else:
        logger.info("No errors found!")

    if _json:
        import json

        click.echo(json.dumps(list(map(error_to_dict, errors))))
        return

    from papis.commands.edit import run as edit_run

    for error in errors:
        click.echo(f"{error.name}\t{error.payload}\t{error.path}")

        if explain:
            click.echo(f"\tReason: {error.msg}")

        if suggest:
            click.echo(f"\tSuggestion: {error.suggestion_cmd}")

        if fix:
            error.fix_action()

        if edit and error.doc:
            click.pause("Press any key to edit...")
            edit_run(error.doc)

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
  :ref:`config-settings-doctor-duplicated-keys-keys` are not present in multiple
  documents. This is mainly meant to be used to check the ``ref`` key or other
  similar keys that are meant to be unique.
* ``files``: checks whether all the document files exist on the filesystem.
* ``html-codes``: checks that no HTML codes (e.g. ``&amp;``) appear in the keys
  provided by :ref:`config-settings-doctor-html-codes-keys`.
* ``html-tags``: checks that no HTML or XML tags (e.g. ``<a>``) appear in the keys
  provided by :ref:`config-settings-doctor-html-tags-keys`.
* ``key-type``: checks the type of keys provided by
  :ref:`config-settings-doctor-key-type-check-keys`, e.g. year should be an ``int``.
  Lists can be automatically fixed (by splitting or joining) using the
  :ref:`config-settings-doctor-key-type-check-separator` setting.
* ``keys-exist``: checks that the keys provided by
  :ref:`config-settings-doctor-keys-exist-keys` exist in the document.
* ``refs``: checks that the document has a valid reference (i.e. one that would
  be accepted by BibTeX and only contains valid characters).

If any custom checks are implemented, you can get a complete list at runtime from

.. code:: sh

    papis doctor --list-checks

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

  If this is the case, you can also run the following to automatically open
  the ``info.yaml`` file for editing more complex changes

    .. code:: sh

        papis doctor --edit --check keys-exist einstein


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
    import papis.bibtex
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


BIBLATEX_TYPE_ALIAS_CHECK_NAME = "biblatex-type-alias"


def biblatex_type_alias_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that the BibLaTeX type of the document is not a known alias.

    The aliases are described by :data:`~papis.bibtex.bibtex_type_aliases`.

    :returns: an error if the type of the document is an alias.
    """
    import papis.bibtex
    from papis.api import save_doc
    folder = doc.get_main_folder() or ""

    def make_fixer(value: str) -> FixFn:
        def fixer() -> None:
            logger.info("[FIX] Setting 'type' to '%s'", value)
            doc["type"] = value
            save_doc(doc)

        return fixer

    errors = bibtex_type_check(doc)
    if errors:
        return errors

    bib_type = doc["type"]
    bib_type_base = papis.bibtex.bibtex_type_aliases.get(bib_type)
    if bib_type is not None and bib_type_base is not None:
        return [Error(name=BIBLATEX_TYPE_ALIAS_CHECK_NAME,
                      path=folder,
                      msg=("Document type '{}' is an alias for '{}' in BibLaTeX."
                           .format(bib_type, bib_type_base)),
                      suggestion_cmd="papis edit --doc-folder {}".format(folder),
                      fix_action=make_fixer(bib_type_base),
                      payload=bib_type,
                      doc=doc)]

    return []


BIBLATEX_KEY_ALIAS_CHECK_NAME = "biblatex-key-alias"


def biblatex_key_alias_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that no BibLaTeX keys in the document are known aliases.

    The aliases are described by :data:`~papis.bibtex.bibtex_key_aliases`. Note
    that these keys can also be converted on export to BibLaTeX.

    :returns: an error for each key of the document that is an alias.
    """
    import papis.bibtex
    from papis.api import save_doc
    folder = doc.get_main_folder() or ""

    def make_fixer(key: str) -> FixFn:
        def fixer() -> None:
            new_key = papis.bibtex.bibtex_key_aliases[key]
            logger.info("[FIX] Renaming key '%s' to '%s'", key, new_key)
            doc[new_key] = doc[key]
            del doc[key]
            save_doc(doc)

        return fixer

    # NOTE: `journal` is a key that papis relies on and we do not want to rename it
    aliases = papis.bibtex.bibtex_key_aliases.copy()
    del aliases["journal"]

    return [Error(name=BIBLATEX_KEY_ALIAS_CHECK_NAME,
                  path=folder,
                  msg=("Document key '{}' is an alias for '{}' in BibLaTeX."
                       .format(key, aliases[key])),
                  suggestion_cmd="papis edit --doc-folder {}".format(folder),
                  fix_action=make_fixer(key),
                  payload=key,
                  doc=doc)
            for key in doc if key in aliases]


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
        return errors

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
                       "to be compatible with BibLaTeX."
                       .format(bib_type, "', '".join(keys))),
                  suggestion_cmd="papis edit --doc-folder {}".format(folder),
                  fix_action=lambda: None,
                  payload=",".join(keys),
                  doc=doc)
            for keys in required_keys
            if not any(key in doc or aliases.get(key) in doc for key in keys)]


KEY_TYPE_CHECK_NAME = "key-type"


def key_type_check(doc: papis.document.Document) -> List[Error]:
    """
    Check document keys have expected types.

    The :ref:`config-settings-doctor-key-type-check-keys` configuration entry
    defines a mapping of keys and their expected types. If the desired type is
    a list, the :ref:`config-settings-doctor-key-type-check-separator` setting
    can be used to split an existing string (and, similarly, if the desired type
    is a string, it can be used to join a list of items).

    :returns: a :class:`list` of errors, one for each key does not have the
        expected type (if it exists).
    """
    from papis.api import save_doc
    folder = doc.get_main_folder() or ""

    # NOTE: the separator can be quoted so that it can force whitespace
    separator = papis.config.get("doctor-key-type-check-separator")
    separator = separator.strip("'").strip('"') if separator else None

    def make_fixer(key: str, cls: type) -> FixFn:
        def fixer_convert_list() -> None:
            value = doc[key]

            if isinstance(value, str) and separator:
                doc[key] = re.split(fr"\s*{separator}\s*", value)
            else:
                doc[key] = [value]

            save_doc(doc)

        def fixer_convert_str() -> None:
            value = doc[key]

            if isinstance(value, list) and separator:
                doc[key] = separator.join(value)
            else:
                doc[key] = str(value)

            save_doc(doc)

        def fixer_convert_any() -> None:
            value = doc[key]

            if isinstance(value, list) and len(value) == 1:
                value = value[0]

            try:
                doc[key] = cls(value)
                save_doc(doc)
            except Exception as exc:
                logger.error("Failed to convert key '%s' to '%s': '%s'.",
                             key, cls, papis.document.describe(doc), exc_info=exc)

        if cls is list:
            return fixer_convert_list
        if cls is str:
            return fixer_convert_str
        else:
            return fixer_convert_any

    import builtins

    results = []
    for value in papis.config.getlist("doctor-key-type-check-keys"):
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

        doc_value = doc.get(key)
        if doc_value is not None and not isinstance(doc_value, cls):
            results.append(Error(name=KEY_TYPE_CHECK_NAME,
                                 path=folder,
                                 msg=(
                                     f"Key '{key}' should be of type '{cls.__name__}' "
                                     f"but got '{type(doc_value).__name__}': "
                                     f"{doc_value!r}."),
                                 suggestion_cmd=f"papis edit --doc-folder {folder}",
                                 fix_action=make_fixer(key, cls),
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
register_check(BIBLATEX_TYPE_ALIAS_CHECK_NAME, biblatex_type_alias_check)
register_check(BIBLATEX_KEY_ALIAS_CHECK_NAME, biblatex_key_alias_check)
register_check(BIBLATEX_REQUIRED_KEYS_CHECK_NAME, biblatex_required_keys_check)
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
@papis.cli.bool_flag("--all-checks", "all_checks",
                     help="Run all available checks (ignores --checks)")
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
        all_checks: bool,
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

    if all_checks:
        _checks = list(REGISTERED_CHECKS)
    else:
        # NOTE: ensure uniqueness of the checks so we don't run the same ones
        _checks = list(set(_checks))

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

        click.echo(json.dumps(
            list(map(error_to_dict, errors)),
            indent=2))
        return

    import colorama as c

    from papis.commands.edit import run as edit_run

    for i, error in enumerate(errors):
        if i != 0 and (explain or suggest):
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

        if fix:
            error.fix_action()

        if edit and error.doc:
            click.pause("Press any key to edit...")
            edit_run(error.doc)

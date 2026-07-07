"""
The doctor command checks your library for common problems.

There are many checks implemented and some others that you
can add yourself through the Python configuration file (these cannot be added
through the static configuration file). Currently, the following checks are
implemented:

* ``biblatex-key-alias``: checks that the document does not contain any known
  key (or field in BibLaTeX) from :data:`~papis.bibtex.bibtex_key_aliases`.
* ``biblatex-required-keys``: checks that the document contains all the required
  keys for its type. In BibLaTeX, each type (e.g. article) has a set of
  required (or at least strongly recommended) keys that it needs to be
  adequately shown in the bibliography.
* ``biblatex-type-alias``: checks that the BibLaTeX type of the document is not
  a known type alias (usually defined for backwards compatibility reasons), as
  defined by :data:`~papis.bibtex.bibtex_type_aliases`.
* ``biblatex-key-convert``: checks if some known BibLaTeX keys should be converted
  based on their values (e.g. a numeric "issue" is better used as a "number").
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
* ``empty-fields``: checks that the document does not contain fields with
  empty values (``None``, ``""``, ``[]``, ``{}``).
* ``field-type``: checks the type of fields provided by :confval:`document-field-types`
  (and :confval:`document-field-types-extend`), e.g. year should be an ``int``.
  Lists can be automatically fixed (by splitting or joining) using the
  :confval:`doctor-field-type-separator` setting.
* ``keys-missing``: checks that the keys provided by
  :confval:`doctor-keys-missing-keys` exist in the document.
* ``refs``: checks that the document has a valid reference (i.e. one that would
  be accepted by BibTeX and only contains valid characters).
* ``string-cleaner``: checks that strings do contain various undesired characters
  (e.g. newlines in titles) and other general style issues (double whitespace).

If any custom checks are implemented, you can get a complete list at runtime from:

.. code:: sh

    papis list --doctors

Examples
^^^^^^^^

- To run all available checks over all available documents in the library use:

    .. code:: sh

        papis doctor --all-checks --all

  This will likely generate too many results, but it can be useful to output in JSON:

    .. code:: sh

        papis doctor --all-checks --all --json

- To check if all the files of a document are present, use:

    .. code:: sh

        papis doctor --checks files einstein

- To check if any unwanted HTML tags are present in your documents (especially
  abstracts can be full of additional HTML or XML tags) use:

    .. code:: sh

        papis doctor --explain --checks html-tags einstein

  The ``--explain`` flag can be used to give additional details of checks that
  failed. This check (and some others) also has automatic fixers. Here, we can
  just remove all the HTML tags by writing:

    .. code:: sh

        papis doctor --fix --checks html-tags einstein

- If an automatic fix is not possible, some checks also have suggested
  commands or tips to fix issues. For example, if a key does not exist
  in the document, it can suggest editing the file to add it:

    .. code:: sh

        papis doctor --suggestion --checks keys-missing einstein
        >> Suggestion: papis edit --doc-folder /path/to/folder

  If this is the case, you can also run the following to automatically open
  the ``info.yaml`` file for editing more complex changes:

    .. code:: sh

        papis doctor --edit --checks keys-missing einstein


Implementing additional checks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A check is just a function that takes a document and returns a list of errors.
A skeleton implementation that gets added to ``config.py``
(see :ref:`config_py`) can be implemented as follows:

.. code:: python

    from papis.doctor import Error, register_check

    def my_custom_check(doc) -> List[Error]:
        ...

    register_check("my-custom-check", my_custom_check)

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.doctor:cli
    :prog: papis doctor
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

import papis.cli
import papis.config
import papis.logging
from papis.doctor import (
    DEPRECATED_CHECK_NAMES,
    REGISTERED_CHECKS,
    Error,
    gather_errors,
    registered_checks_names,
)

if TYPE_CHECKING:
    from papis.document import Document

logger = papis.logging.get_logger(__name__)


def _suggestion_cmd(error: Error) -> str:
    """Build the CLI suggestion string for a given error."""
    if error.fix_action is not None:
        return f"papis doctor --fix -t {error.name} --doc-folder {error.path!r}"
    return f"papis edit --doc-folder {error.path!r}"


def _error_to_dict(error: Error) -> dict[str, Any]:
    """Convert an :class:`Error` to a JSON-serializable dictionary."""
    return {
        "msg": error.payload,
        "path": error.path,
        "name": error.name,
        "suggestion": _suggestion_cmd(error),
    }


def process_errors(errors: list[Error],
                   fix: bool = False,
                   explain: bool = False,
                   suggest: bool = False,
                   edit: bool = False) -> None:
    """Process a list of document errors from :func:`~papis.doctor.gather_errors`.

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
    from papis.document import describe

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
                f"{_suggestion_cmd(error)}")

        if fix and error.fix_action:
            try:
                error.fix_action()
                fixed += 1
            except Exception as exc:
                logger.error("Failed to fix '%s' for document '%s'.",
                             error.name,
                             describe(error.doc)
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


def run(doc: Document,
        checks: list[str] | None = None,
        fix: bool = True,
        explain: bool = False,
        suggest: bool = False,
        edit: bool = False) -> None:
    """
    Runner for ``papis doctor``.

    It runs all the checks given by the *checks* argument that have been
    registered through :func:`papis.doctor.register_check`. It then proceeds
    with processing and fixing each error in turn.
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
              default=(),
              multiple=True,
              type=str,
              help="Checks to run on every document.")
@papis.cli.bool_flag("--list-checks", help="List all supported checks.")
@papis.cli.bool_flag("--json", "_json",
                     help="Output the results in JSON format.")
@papis.cli.bool_flag("--fix",
                     help="Auto fix the errors with the auto fixer mechanism.")
@papis.cli.bool_flag("-s", "--suggest",
                     help="Suggest commands to be run for resolution.")
@papis.cli.bool_flag("-e", "--explain",
                     help="Give a short message for the reason of the error.")
@papis.cli.bool_flag("--edit",
                     help="Edit every file with the edit command.")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
@papis.cli.bool_flag("--all-checks", "all_checks",
                     help="Run all available checks (ignores --checks).")
def cli(query: str,
        doc_folder: tuple[str, ...],
        sort_field: str | None,
        sort_reverse: bool,
        _all: bool,
        fix: bool,
        edit: bool,
        explain: bool,
        _checks: list[str],
        list_checks: bool,
        _json: bool,
        suggest: bool,
        all_checks: bool) -> None:
    """Check for common problems in documents."""
    if list_checks:
        from papis.commands.list import list_plugins
        for o in list_plugins(show_doctor=True, verbose=True):
            click.echo(o)
        return

    if all_checks:
        checks = list(REGISTERED_CHECKS)
    else:
        if not _checks:
            checks = (
                papis.config.getlist("default-checks", section="doctor")
                + papis.config.getlist("default-checks-extend", section="doctor"))

        # NOTE: ensure uniqueness of the checks so we don't run the same ones
        checks = list(set(_checks))

        known_checks = registered_checks_names() + list(DEPRECATED_CHECK_NAMES)
        extra_checks = set(checks).difference(known_checks)
        if extra_checks:
            if _checks:
                logger.error("Unknown checks chosen with '--check': ['%s'].",
                             "', '".join(extra_checks))
            else:
                logger.error("Unknown checks found in the configuration file: ['%s'].",
                             "', '".join(extra_checks))

            logger.error("Supported checks are: ['%s'].", "', '".join(known_checks))
            return

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all)

    if not documents:
        from papis.strings import no_documents_retrieved_message

        logger.warning(no_documents_retrieved_message)
        return

    new_checks = []
    for check in checks:
        check_name = check
        new_check_name = DEPRECATED_CHECK_NAMES.get(check)
        if new_check_name is not None:
            logger.warning("Check '%s' is deprecated and has been replace by "
                           "'%s'. Please use this in the future.",
                           check_name, new_check_name)

            check_name = new_check_name

        new_checks.append(check_name)
    checks = new_checks

    errors = gather_errors(documents, checks=checks)
    if errors:
        logger.warning("Found %s errors.", len(errors))
    else:
        logger.info("No errors found!")

    if _json:
        import json

        click.echo(json.dumps(
            list(map(_error_to_dict, errors)),
            indent=2))
        return

    process_errors(errors,
                   fix=fix,
                   explain=explain,
                   suggest=suggest,
                   edit=edit)

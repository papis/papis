"""
The doctor command checks for the overall health of your
library.

There are many checks implemented and some others that you
can add yourself through the python configuration file.
"""

import logging
import os
import re
import json
from typing import Optional, List, NamedTuple, Callable, Dict
import collections

import click

import papis
import papis.utils
import papis.config
import papis.cli
import papis.pick
import papis.database
import papis.strings
import papis.document
from papis.commands.edit import run as edit_run


Error = NamedTuple("Error", [("name", str),
                             ("path", str),
                             ("payload", str),
                             ("msg", str),
                             ("suggestion_cmd", str),
                             ("fix_action", Callable[[], None]),
                             ("doc", Optional[papis.document.Document]),
                             ])
CheckFn = Callable[[papis.document.Document], List[Error]]
Check = NamedTuple("Check", [("name", str),
                             ("operate", CheckFn),
                             ])

logger = logging.getLogger("doctor")


def register_check(name: str, check_function: CheckFn) -> None:
    """
    Register a check.
    To be used by users in their configuration files
    for example.
    """
    REGISTERED_CHECKS[name] = Check(name=name, operate=check_function)


def files_check(doc: papis.document.Document) -> List[Error]:
    """
    It checks wether the files of a document actually exist in the
    filesystem.
    """
    files = doc.get_files()
    results = []  # type: List[Error]
    folder = doc.get_main_folder()

    def _fix(_file: str) -> Callable[[], None]:
        """
        Files fixer function, it will remove the bad file.
        Notice that for now it only works if the file name is not of
        the form 'subdirectory/file' but only 'file'.
        """

        def __fix() -> None:
            _db = papis.database.get()
            basename = os.path.basename(_file)
            if basename in doc["files"]:
                doc["files"].remove(basename)
            doc.save()
            _db.update(doc)

        return __fix

    for _f in files:
        if not os.path.exists(_f):
            results.append(Error(name="files",
                                 path=folder or "",
                                 msg=("File '{}' declared but does not exist"
                                      .format(_f)),
                                 suggestion_cmd=("papis edit --doc-folder {}"
                                                 .format(folder)),
                                 fix_action=_fix(_f),
                                 payload=_f,
                                 doc=doc))
    return results


def keys_check(doc: papis.document.Document) -> List[Error]:
    """
    It checks wether the keys provided in the configuration
    option ``doctor-keys-check`` exit in the document.
    """
    keys = papis.config.getlist("doctor-keys-check")
    folder = doc.get_main_folder()
    results = []  # type: List[Error]
    for k in keys:
        if k not in doc or len(doc[k]) == 0:
            results.append(Error(name="keys",
                                 path=folder or "",
                                 msg=("Key '{}' does not exist"
                                      .format(k)),
                                 suggestion_cmd=("papis edit --doc-folder {}"
                                                 .format(folder)),
                                 fix_action=lambda: None,
                                 payload=k,
                                 doc=doc))
    return results


def refs_check(doc: papis.document.Document) -> List[Error]:
    """
    It checks that a ref exists and if not it
    tries to create one according to the ref-format configuration
    if the user chooses to fix it.
    """
    folder = doc.get_main_folder()
    bad_symbols = re.compile(r"[ ,{}\[\]@#`']")

    def _fix() -> None:
        ref = papis.bibtex.create_reference(doc, force=True)
        _db = papis.database.get()
        logger.info("Setting ref '%s' in '%s'",
                    ref,
                    papis.document.describe(doc))
        doc["ref"] = ref
        doc.save()
        _db.update(doc)

    if not doc["ref"] or not str(doc["ref"]).strip():
        return [Error(name="refs",
                      path=folder or "",
                      msg="Reference missing.",
                      suggestion_cmd=("papis edit --doc-folder {}"
                                      .format(folder)),
                      fix_action=_fix,
                      payload="",
                      doc=doc)]
    m = bad_symbols.findall(str(doc["ref"]))
    if m:
        return [Error(name="refs",
                      path=folder or "",
                      msg=("Bad characters ({}) found in reference."
                           .format(set(list(m)))),
                      suggestion_cmd=("papis edit --doc-folder {}"
                                      .format(folder)),
                      fix_action=_fix,
                      payload="",
                      doc=doc)]
    return []


DUPLICATED_KEYS_SEEN \
    = collections.defaultdict(list)  # type: Dict[str, List[str]]


def duplicated_keys_check(doc: papis.document.Document) -> List[Error]:
    """
    Check for duplicated keys in `doctor-duplicated-keys-check`
    """
    keys = papis.config.getlist("doctor-duplicated-keys-check")
    folder = doc.get_main_folder()
    results = []  # type: List[Error]
    for key in keys:
        if doc[key] in DUPLICATED_KEYS_SEEN[key]:
            results.append(Error(name="duplicated-keys",
                                 msg=("Key '{}' is duplicated."
                                      .format(key)),
                                 suggestion_cmd="",
                                 payload=key,
                                 fix_action=lambda: None,
                                 path=folder or "",
                                 doc=doc))
        else:
            DUPLICATED_KEYS_SEEN[key].append(str(doc[key]))
    return results


def bibtex_type_check(doc: papis.document.Document) -> List[Error]:
    """
    Check that the types are compatible with bibtex or biblatex
    type descriptors.
    """
    types = papis.bibtex.bibtex_types
    folder = doc.get_main_folder()
    results = []
    if doc["type"] not in types:
        results.append(Error(name="bibtex_types",
                             path=folder or "",
                             msg=("Document type '{}' is not"
                                  " a valid bibtex type"
                                  .format(doc["type"])),
                             suggestion_cmd=("papis edit --doc-folder {}"
                                             .format(folder)),
                             fix_action=lambda: None,
                             payload=doc["type"],
                             doc=doc))
    return results


REGISTERED_CHECKS = {
    "files":
    Check(operate=files_check,
          name="check"),
    "keys":
    Check(operate=keys_check,
          name="keys"),
    "duplicated-keys":
    Check(operate=duplicated_keys_check,
          name="duplicated-keys"),
    "bibtex-type":
    Check(operate=bibtex_type_check,
          name="bibtex-type"),
    "refs":
    Check(operate=refs_check,
          name="refs"),
}  # type: Dict[str, Check]


def run(doc: papis.document.Document, checks: List[str]) -> List[Error]:
    """
    Runner for doctor. It runs all the checks given by the check
    argument, and it gets the check from the global REGISTERED_CHECKS
    dictionary.
    """
    results = []  # type: List[Error]
    for check in checks:
        results.extend(REGISTERED_CHECKS[check].operate(doc))
    return results


@click.command("doctor")
@click.help_option("--help", "-h")
@papis.cli.query_option()
@papis.cli.sort_option()
@click.option("-t", "--checks", "_checks",
              default=lambda: papis.config.getlist("doctor-default-checks"),
              multiple=True,
              help=("Checks to run on every document, possible values: {}"
                    .format(", ".join(REGISTERED_CHECKS.keys()))))
@click.option("--json", "_json",
              default=False, is_flag=True,
              help="Output the results in json format")
@click.option("--fix",
              default=False, is_flag=True,
              help="Auto fix the errors with the auto fixer mechanism")
@click.option("-s", "--suggest",
              default=False, is_flag=True,
              help="Suggest commands to be run for resolution")
@click.option("-e", "--explain",
              default=False, is_flag=True,
              help="Give a short message for the reason of the error")
@click.option("--edit",
              default=False, is_flag=True,
              help="Edit every file with the edit command.")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool,
        _all: bool,
        fix: bool,
        edit: bool,
        explain: bool,
        _checks: List[str],
        _json: bool,
        suggest: bool) -> None:
    """Check for common problems in documents"""

    # handle doc_folder
    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    if not _all:
        documents = [doc for doc in papis.pick.pick_doc(documents) if doc]

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    logger.debug("Running checks: %s", _checks)

    errors = []  # type: List[Error]
    for doc in documents:
        errors += run(doc, _checks)

    if errors:
        logger.warning("%s errors found", len(errors))

    if _json:
        print(json.dumps(list(map(lambda e:
                                  dict(msg=e.payload,
                                       path=e.path,
                                       name=e.name,
                                       suggestion=e.suggestion_cmd),
                                  errors))))
        return

    for error in errors:
        print("{e.name}\t{e.payload}\t{e.path}".format(e=error))
        if explain:
            print("\tReason: {}"
                  .format(error.msg))
        if suggest:
            print("\tSuggestion: {}"
                  .format(error.suggestion_cmd))
        if fix:
            logger.warning("Fixing...")
            error.fix_action()
        if edit:
            input("Press any key to edit...")
            if error.doc:
                edit_run(error.doc)

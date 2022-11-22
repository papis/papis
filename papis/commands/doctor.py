"""
The doctor command checks for the overall health of your
library.

There are many checks implemented and some others that you
can add yourself through the python configuration file.
"""

import logging
import os
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


Error = NamedTuple("Error", [("name", str),
                             ("path", str),
                             ("msg", str),
                             ])
CheckFn = Callable[[papis.document.Document], List[Error]]
Check = NamedTuple("Check", [("name", str),
                             ("operate", CheckFn),
                             ("suggest_cmd", Callable[[Error], str])])

logger = logging.getLogger("doctor")


def register_check(name: str, check: Check) -> None:
    """
    Register a check.
    To be used by users in their configuration files
    for example.
    """
    REGISTERED_CHECKS[name] = check


def files_check(doc: papis.document.Document) -> List[Error]:
    """
    It checks wether the files of a document actually exist in the
    filesystem.
    """
    files = doc.get_files()
    results = []  # type: List[Error]
    folder = doc.get_main_folder()
    for _f in files:
        if not os.path.exists(_f):
            results.append(Error(name="files",
                                 path=folder or "",
                                 msg=_f))
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
                                 msg=k))
    return results


DUPLICATED_KEYS_SEEN = collections.defaultdict(list)  # type: Dict[str, List[str]]


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
                                 msg=key,
                                 path=folder or ""))
        else:
            DUPLICATED_KEYS_SEEN[key].append(str(doc[key]))
    return results


REGISTERED_CHECKS = {
    "files": Check(operate=files_check,
                   name="check",
                   suggest_cmd=lambda e:
                   """
                   papis edit --doc-folder {}
                   """.format(e.path)),
    "keys": Check(operate=keys_check,
                  name="keys",
                  suggest_cmd=lambda e:
                  """
                  papis update --doc-folder {}
                  """.format(e.path)),
    "duplicated-keys": Check(operate=duplicated_keys_check,
                             name="duplicated-keys",
                             suggest_cmd=lambda e: ""),
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
@click.option("--json", "_json", default=False, is_flag=True,
              help="Output the results in json format")
@click.option("--suggest", "suggest", default=False, is_flag=True,
              help="Suggest commands to be run for resolution")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str, doc_folder: str,
        sort_field: Optional[str], sort_reverse: bool,
        _all: bool,
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
                                  dict(msg=e.msg,
                                       path=e.path,
                                       name=e.name,
                                       suggestion=REGISTERED_CHECKS[e.name]
                                       .suggest_cmd(e)),
                                  errors))))
        return

    for error in errors:
        print("{e.name} {e.msg} {e.path}".format(e=error))
        if suggest:
            print("Suggestion:\n\t{}\n"
                  .format(REGISTERED_CHECKS[error.name]
                          .suggest_cmd(error)))

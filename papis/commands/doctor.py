"""
The doctor command checks for the overall health of your
library.

There are many tests implemented and some others that you
can add yourself through the python configuration file.
"""

import logging
import os
import json
from typing import Optional, List, NamedTuple, Callable, Dict

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
TestFn = Callable[[papis.document.Document], List[Error]]
Test = NamedTuple("Test", [("name", str),
                           ("operate", TestFn),
                           ("suggest_cmd", Callable[[Error], str])])

logger = logging.getLogger("doctor")


def register_test(name: str, test: Test) -> None:
    """
    Register a test.
    To be used by users in their configuration files
    for example.
    """
    REGISTERED_TESTS[name] = test


def files_test(doc: papis.document.Document) -> List[Error]:
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


def keys_test(doc: papis.document.Document) -> List[Error]:
    """
    It checks wether the keys provided in the configuration
    option ``doctor-keys-test`` exit in the document.
    """
    keys = papis.config.getlist("doctor-keys-test")
    folder = doc.get_main_folder()
    results = []  # type: List[Error]
    for k in keys:
        if k not in doc or len(doc[k]) == 0:
            results.append(Error(name="keys",
                                 path=folder or "",
                                 msg=k))
    return results


REGISTERED_TESTS = {
    "files": Test(operate=files_test,
                  name="test",
                  suggest_cmd=lambda e:
                  """
                  papis edit --doc-folder {}
                  """.format(e.path)),
    "keys": Test(operate=keys_test,
                 name="keys",
                 suggest_cmd=lambda e:
                 """
                 papis update --doc-folder {}
                 """.format(e.path)),
}  # type: Dict[str, Test]


def run(doc: papis.document.Document, tests: List[str]) -> List[Error]:
    """
    Runner for doctor. It runs all the tests given by the test
    argument, and it gets the test from the global REGISTERED_TESTS
    dictionary.
    """
    results = []  # type: List[Error]
    for test in tests:
        results += REGISTERED_TESTS[test].operate(doc)
    return results


@click.command("doctor")
@click.help_option("--help", "-h")
@papis.cli.query_option()
@papis.cli.sort_option()
@click.option("-t", "--tests", "_tests",
              default=lambda: papis.config.getlist("doctor-default-tests"),
              multiple=True,
              help=("Tests to run on every document, possible values: {}"
                    .format(", ".join(t.name for t in REGISTERED_TESTS)))
@click.option("--json", "_json", default=False, is_flag=True,
              help="Output the results in json format")
@click.option("--suggest", "suggest", default=False, is_flag=True,
              help="Suggest commands to be run for resolution")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str, doc_folder: str,
        sort_field: Optional[str], sort_reverse: bool, _all: bool,
        _tests: List[str],
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

    logger.debug("Running tests: %s", _tests)

    errors = []  # type: List[Error]
    for doc in documents:
        errors += run(doc, _tests)

    if errors:
        logger.warning("%s errors found", len(errors))

    if _json:
        print(json.dumps(list(map(lambda e:
                                  dict(msg=e.msg,
                                       path=e.path,
                                       name=e.name,
                                       suggestion=REGISTERED_TESTS[e.name]
                                       .suggest_cmd(e)),
                                  errors))))
        return

    for error in errors:
        print("{e.name} {e.msg} {e.path}".format(e=error))
        if suggest:
            print("Suggestion:\n\t{}\n"
                  .format(REGISTERED_TESTS[error.name]
                          .suggest_cmd(error)))

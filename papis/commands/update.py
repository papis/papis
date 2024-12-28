"""
This command allows you to update the document metadata stored in the
``info.yaml`` file. With it, you can either change individual values manually
or update a document with information automatically retrieved from a variety
of sources.

When using it to add information, Papis formatting strings and Python
expressions can be used. See below examples for more information. The command
also tries to sanitise filenames so that they don't contain any problematic
characters.

Normally, ``papis update`` will abort on encountering an error. If you want to
skip errors and apply as many changes as possible, use the ``--batch`` flag.

Examples
^^^^^^^^

- Search among papers with the tag "classics" and update the author to
  "Einstein, Albert":

    .. code:: sh

        papis update --set author "Einstein, Albert" "tags:classics"

  This will open the picker containing all documents that match the query from
  where you can select the document you want to update.

- Update the journal to "Mass and Energy" for all documents with the journal
  "Energy and Mass":

    .. code:: sh

        papis update --all --set journal "Mass and Energy" "journal:'Energy and Mass'"


  The ``--all`` flag means that the tag is applied to all documents that match the
  query, rather than allowing you to pick one individual document to update.

- Update a document automatically and interactively (searching by DOI in
  Crossref or in other sources...)

    .. code:: sh

        papis update --auto "author:dyson"

- Update your library from a BibTeX file, where many entries may be listed:

    .. code:: sh

        papis update --from bibtex libraryfile.bib

  Papis will try to look for documents in your library that match these
  entries and will ask you for each entry whether you want to update it.

- Add the ", Albert" to the author string of a documents matching 'Einstein':

    .. code:: sh

        papis update --set author "{doc[author]}, Albert" Einstein

  The ``papis update`` command tries to format input strings using the configured
  formatter. Here, it is used to get the existing author "Albert" and then add
  the string ", Einstein" to end up with "Einstein, Albert"

- The above can also be achieved with the ``--append`` option:

    .. code:: sh

        papis update --append author ", Albert" Einstein

    This appends ", Einstein" to the existing author string.

- You can also append an item to a list:

    .. code:: sh

        papis update --append tags physics

    This adds the tag 'physics' to the existing list of tags. If the list
    doesn't yet exist, it will be created. All duplicate items will be removed
    from the list.

- To remove an item from a list, use ``--remove``:

    .. code:: sh

        papis update --remove tags physics

    If the tag "physics" is in the list of tags, this command removes it.

- To remove a key-value pair entirely, use ``--drop``:

    .. code:: sh

        papis update --drop tags

    This removes the all tags.

- There is also a convenience option ``--rename`` if you want to rename
  a list item. It's equivalent to doing ``--remove`` and ``--append`` sequentially.

    .. code:: sh

        papis update --rename tags physics philosophy

  This renames the tag 'physics' to 'philosophy'. Note that this option being a
  combination of ``--remove`` and ``--append``, it will append the desired values
  even if the value to be removed didn't exist. Thus, the above command will add
  the tag "philosophy" even if the tag "physics" didn't exist before the
  operation.

- As an advanced feature, ``papis update`` also supports the parsing of python
  expressions (such as lists or dictionaries). This can be used as follows:

    .. code:: sh

        papis update --set author_list "[{'family': 'Einstein', 'given': 'Albert'}]"

  Because the above string is a valid python expression, ``author_list`` is
  updated to a set that contains a dictionary.


Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.update:cli
    :prog: papis update
"""

import ast
from typing import Any, Dict, List, Optional, Sequence, Tuple

import click

import papis.cli
import papis.commands.doctor
import papis.config
import papis.document
import papis.format
import papis.git
import papis.importer
import papis.logging
import papis.strings
import papis.utils
from papis.strings import AnyString, process_formatted_string_pair

logger = papis.logging.get_logger(__name__)

KEY_TYPES = papis.commands.doctor.get_key_type_check_keys()


def try_parsing_str(key: str, value: str) -> str:
    """
    Tries to parse the input string as a python expression.

    :returns: The parsed input string if string is a python expression,
        otherwise an unchanged string.
    """
    try:
        value = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        logger.debug("Value '%s' of key '%s' is not a python expression.", value, key)
    return value


def run_set(
    document: papis.document.DocumentLike,
    to_set: Sequence[Tuple[str, AnyString]],
    key_types: Dict[str, type],
) -> None:
    """
    Processes a list of ``to_set`` tuples and applies the resulting changes to the
    input document. Each tuple is (KEY, VALUE) and results in setting the KEY to
    the VALUE in the document.
    """
    from papis.paths import normalize_path

    for key, value in to_set:
        key, value = process_formatted_string_pair(key, value)
        value = papis.format.format(value, document, default=str(value))
        value = try_parsing_str(key, value)

        if isinstance(value, int) and key_types.get(key) is str:
            value = str(value)
        if key == "notes" and isinstance(value, str):
            # TODO: handle renames/deletions of files on disk
            document[key] = normalize_path(value)
            logger.warning(
                "Document note renamed in the info.yaml file. This does not "
                "rename any files on disk."
            )
        elif key == "files" and isinstance(value, list):
            # TODO: handle renames/deletions of files on disk
            document[key] = []
            for file in value:
                if isinstance(file, str):
                    document[key].append(normalize_path(file))
                else:
                    document[key].append(value)
            logger.warning(
                "Document files renamed in the info.yaml file. This does not "
                "rename any files on disk."
            )
        elif key == "ref" and isinstance(value, str):
            document[key] = papis.bibtex.ref_cleanup(value)
        else:
            document[key] = value


def run_append(
    document: papis.document.DocumentLike,
    to_append: Sequence[Tuple[str, AnyString]],
    key_types: Dict[str, type],
    batch: bool,
) -> bool:
    """
    Processes a list of ``to_append`` tuples and applies the resulting changes
    to the input document. Each tuple is (KEY, VALUE) and results in appending
    the VALUE to the KEY item.

    :returns: A boolean indicating whether the update was successful.
    """
    from papis.paths import normalize_path

    success = True
    processed_lists = set()
    supported_keys = key_types.keys() | document
    for key, value in to_append:
        key, value = process_formatted_string_pair(key, value)

        if key in supported_keys:
            value = papis.format.format(value, document, default=str(value))
            type_doc = type(document.get(key))
            type_conf = key_types.get(key)
            if type_doc is str or (type_doc is type(None) and type_conf is str):
                document[key] = document.setdefault(key, "") + value
            elif type_doc is list or (type_doc is type(None) and type_conf is list):
                value = try_parsing_str(key, value)
                if key == "files":
                    value = normalize_path(str(value))
                document.setdefault(key, []).append(value)
                processed_lists.add(key)
            else:
                logger.error(
                    "Items of key '%s' have the type '%s', for which Papis "
                    "doesn't support the append operation.",
                    key,
                    type(document[key]).__name__
                    if document.get(key)
                    else key_types[key].__name__,
                )
                if not batch:
                    success = False
                    break
        else:
            logger.error(
                "We cannot append to key '%s', because we do not know the "
                "intended type. Please use `papis update --set` instead.",
                key,
            )
            if not batch:
                success = False
                break

    for key in processed_lists:
        document[key] = list(set(document[key]))

    return success


def run_remove(
    document: papis.document.DocumentLike,
    to_remove: Sequence[Tuple[str, AnyString]],
    batch: bool
) -> bool:
    """
    Processes a list of ``to_remove`` tuples and applies the resulting changes
    to the input document. Each tuple is (KEY, VALUE) and results in removing
    the VALUE from the KEY item.

    :returns: A boolean indicating whether the update was successful.
    """
    success = True
    for key, value in to_remove:
        key, value = process_formatted_string_pair(key, value)

        if key in document:
            if isinstance(document.get(key), list):
                try:
                    document[key].remove(value)
                except ValueError:
                    try:
                        document[key].remove(int(str(value)))
                    except ValueError:
                        pass  # do nothing if there is nothing to remove
            else:
                logger.error(
                    "You're trying to remove an item from '%s', which has the "
                    "type '%s'. `papis update --remove` only supports lists.",
                    key,
                    type(document.get(key)).__name__,
                )
                if not batch:
                    success = False
                    break
        else:
            logger.info(
                "Document doesn't have key '%s', cannot remove '%s' from it. "
                "Continuing...",
                key,
                value,
            )

    return success


def run_drop(document: papis.document.DocumentLike, to_remove: Sequence[str]) -> None:
    """
    Processes a list of ``to_drop`` strings and applies the resulting changes
    to the input document. Each string is a KEY whose value is set to None
    (and then later in ``run()`` dropped from the document entirely).

    """
    for key in to_remove:
        if key in document:
            document[key] = None
        else:
            logger.info(
                "Document doesn't have key '%s', cannot remove it. Continuing...", key
            )


def run_rename(
    document: papis.document.DocumentLike,
    to_rename: Sequence[Tuple[str, AnyString, AnyString]],
    batch: bool,
) -> bool:
    """
    Processes a list of ``to_rename`` tuples and applies the resulting changes
    to the input document. Each tuple is (KEY, VALUE_OLD, VALUE_NEW) and results in
    rename the KEY's VALUE_OLD to VALUE_NEW.


    :returns: A boolean indicating whether the update was successful.
    """
    to_remove = [x[:2] for x in to_rename]
    to_append = [x[::2] for x in to_rename]
    success = run_remove(document, to_remove, batch)
    if success:
        success = run_append(document, to_append, KEY_TYPES, batch)
    return success


def run(
    document: papis.document.Document,
    data: Optional[Dict[str, Any]] = None,
    git: bool = False,
    auto_doctor: bool = False,
) -> None:
    """
    Updates the document in the Papis library.

    :returns: None
    """
    if data is None:
        data = {}

    folder = document.get_main_folder()
    info = document.get_info_file()

    if not folder or not info:
        from papis.exceptions import DocumentFolderNotFound

        raise DocumentFolderNotFound(papis.document.describe(document))

    document.update(data)

    # delete all keys that do not have a value
    to_drop = [k for k, v in document.items() if not v]
    [document.pop(k) for k in to_drop]

    if auto_doctor:
        logger.info(
            "Running doctor auto-fixers on document: '%s'.",
            papis.document.describe(document),
        )
        papis.commands.doctor.fix_errors(document)

    from papis.api import save_doc

    save_doc(document)

    if git:
        papis.git.add_and_commit_resource(
            folder,
            info,
            "Update information for '{}'".format(papis.document.describe(document)),
        )


@click.command("update")
@click.help_option("--help", "-h")
@papis.cli.git_option()
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
@papis.cli.bool_flag("--auto", help="Try to parse information from different sources")
@papis.cli.bool_flag(
    "--auto-doctor/--no-auto-doctor",
    help="Apply papis doctor to newly added documents.",
    default=lambda: papis.config.getboolean("auto-doctor"),
)
@click.option(
    "--from",
    "from_importer",
    help="Add document from a specific importer ({})".format(
        ", ".join(papis.importer.available_importers())
    ),
    type=(click.Choice(papis.importer.available_importers()), str),
    nargs=2,
    multiple=True,
    default=(),
)
@click.option(
    "-s",
    "--set",
    "to_set",
    help="Set the key to the given value.",
    multiple=True,
    type=(str, papis.cli.FormattedStringParamType()),
)
@click.option(
    "-d",
    "--drop",
    "to_drop",
    help="Drop a key from the document.",
    multiple=True,
    type=str,
)
@click.option(
    "-p",
    "--append",
    "to_append",
    help="Append a value to a document key.",
    multiple=True,
    type=(str, papis.cli.FormattedStringParamType()),
)
@click.option(
    "-r",
    "--remove",
    "to_remove",
    help="Remove an item from a list.",
    multiple=True,
    type=(str, papis.cli.FormattedStringParamType()),
)
@click.option(
    "-n",
    "--rename",
    "to_rename",
    help="Rename an item in a list.",
    multiple=True,
    type=(str,
          papis.cli.FormattedStringParamType(),
          papis.cli.FormattedStringParamType()),
)
@papis.cli.bool_flag("-b", "--batch", help="Batch mode, do not prompt or otherwise")
def cli(
    query: str,
    git: bool,
    doc_folder: Tuple[str, ...],
    from_importer: List[Tuple[str, str]],
    batch: bool,
    auto: bool,
    auto_doctor: bool,
    _all: bool,
    sort_field: Optional[str],
    sort_reverse: bool,
    to_set: List[Tuple[str, str]],
    to_drop: List[str],
    to_append: List[Tuple[str, str]],
    to_remove: List[Tuple[str, str]],
    to_rename: List[Tuple[str, str, str]],
) -> None:
    """Update document metadata"""
    success = True

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all
    )
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    processed_documents = []
    for document in documents:
        ctx = papis.importer.Context()

        ctx.data.update(document)
        if to_set:
            run_set(ctx.data, to_set, KEY_TYPES)

        if to_append and success:
            success = run_append(ctx.data, to_append, KEY_TYPES, batch)

        if to_remove and success:
            success = run_remove(ctx.data, to_remove, batch)

        if to_drop and success:
            run_drop(ctx.data, to_drop)

        if to_rename:
            success = run_rename(ctx.data, to_rename, batch)

        if success:
            logger.info("Updating %s.", papis.document.describe(document))

            # NOTE: use 'papis addto' to add files, so this only adds data
            # by setting 'only_data' to True always
            matching_importers = papis.utils.get_matching_importer_by_name(
                from_importer, only_data=True
            )

            if not from_importer and auto:
                for importer_cls in papis.importer.get_importers():
                    try:
                        importer = importer_cls.match_data(document)
                        if importer:
                            try:
                                importer.fetch_data()
                            except NotImplementedError:
                                importer.fetch()
                    except NotImplementedError:
                        continue
                    except Exception as exc:
                        logger.exception("Failed to match document data.", exc_info=exc)
                    else:
                        if importer and importer.ctx:
                            matching_importers.append(importer)

            imported = papis.utils.collect_importer_data(
                matching_importers, batch=batch, use_files=False
            )
            if "ref" in imported.data:
                logger.debug(
                    "An importer set the 'ref' key. This is not allowed and will be "
                    "automatically removed. Check importers: '%s'",
                    "', '".join(importer.name for importer in matching_importers),
                )

                del imported.data["ref"]

            # TODO: add interactive merging to avoid overwriting user changes
            ctx.data.update(imported.data)

            processed_documents.append((document, ctx.data))

        if not success and not batch:
            processed_documents.clear()
            logger.error(
                "Aborting operation. No documents have been changed.",
            )
            break

    for document, data in processed_documents:
        run(document, data=data, git=git, auto_doctor=auto_doctor)

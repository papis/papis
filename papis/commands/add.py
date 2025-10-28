"""
The ``add`` command is one of the central commands of the ``papis``
command-line interface. It is a very versatile command with a fair amount of
options.

There are also a few customization settings available for this command, which
are described on the :ref:`configuration page <add-command-options>` for
``add``.

Examples
^^^^^^^^

- Add a document located in ``~/Documents/interesting.pdf`` and name the
  folder where it will be stored in the database ``interesting-paper-2021``:

    .. code:: sh

        papis add ~/Documents/interesting.pdf \\
            --folder-name interesting-paper-2021

  If you want to directly add some metadata, like author, title and tags,
  you can also run the following:

    .. code:: sh

        papis add ~/Documents/interesting.pdf \\
            --folder-name interesting-paper-2021 \\
            --set author 'John Smith' \\
            --set title 'The interesting life of bees' \\
            --set year 1985 \\
            --set tags 'biology interesting bees'

- Add a paper with a locally stored file and get the paper information
  through its DOI identifier (in this case ``10.10763/1.3237134`` as an
  example):

    .. code:: sh

        papis add ~/Documents/interesting.pdf --from doi 10.10763/1.3237134

- Add a paper from ``arxiv.org`` to a library named ``machine-learning``:

    .. code:: sh

        papis -l machine-learning add \\
            --from arxiv https://arxiv.org/abs/1712.03134

- If you do not want copy the original PDFs into the library, you can
  also tell Papis to just create a link to them, for example:

    .. code:: sh

        papis add --link ~/Documents/interesting.pdf \\
            --from doi 10.10763/1.3237134

  adds an entry to the Papis library, but the PDF document remains at
  ``~/Documents/interesting.pdf``. The document's folder will contain a link
  to ``~/Documents/interesting.pdf`` instead of the file itself. Make sure that
  the document at ``~/Documents/interesting.pdf`` does not disappear, or
  you will end up without a document file.

- Papis tries to make sense of the arguments with which it is provided.
  For instance, you could only provide a DOI, and Papis will verify that
  this is a valid DOI and download available metadata using Crossref.
  For example, you can try:

    .. code:: sh

        papis add 10.1103/PhysRevLett.123.156401

  Similarly, a wide array of known journals are recognized by URL, so you can
  try:

    .. code:: sh

        papis add journals.aps.org/prl/abstract/10.1103/PhysRevLett.123.156401
        papis add https://arxiv.org/abs/1712.03134

- You can also download citations alongside the information on the
  paper if the metadata contains a DOI identifier.  You can pass the
  ``--fetch-citations`` flag in order to create a ``citations.yaml`` file
  in the document's main folder with a list of citations. You can check out
  the ``papis citations`` command for more advanced usage.

- BibTeX can be imported directly as a string, or read from a local file or
  from a remote URL. The following all work:

    .. code:: sh

        papis add --from bibtex someFile.bib
        papis add --from bibtex "https://example.com/someFile.bib"
        papis add --from bibtex "@book{someReference,
            author = {John Doe},
            ...more fields...
            }"
        papis add --from bibtex "$(xclip -o)"

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.add:cli
    :prog: papis add
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import click

import papis.cli
import papis.config
import papis.logging

if TYPE_CHECKING:
    from papis.citations import Citations
    from papis.document import Document
    from papis.strings import AnyString

logger = papis.logging.get_logger(__name__)


def get_file_name(
        doc: Document,
        original_filepath: str,
        suffix: str = "",
        file_name_format: AnyString | None = None,
        base_name_limit: int = 150) -> str:
    from warnings import warn
    warn("'get_file_name' is deprecated and will be removed in the next "
         "version. Use 'papis.paths.get_document_file_name' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import get_document_file_name
    return get_document_file_name(doc, original_filepath, suffix,
                                  base_name_limit=base_name_limit)


def get_hash_folder(data: dict[str, Any], document_paths: list[str]) -> str:
    from warnings import warn
    warn("'get_hash_folder' is deprecated and will be removed in the next "
         "version. Use 'papis.paths.get_document_hash_folder' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import get_document_hash_folder
    return get_document_hash_folder(data, document_paths)


def ensure_new_folder(path: str) -> str:
    from warnings import warn
    warn("'ensure_new_folder' is deprecated and will be removed in the next "
         "version. Use 'papis.paths.get_document_unique_folder' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import _make_unique_folder
    return _make_unique_folder(path)


def run(paths: list[str],
        data: dict[str, Any] | None = None,
        folder_name: AnyString | None = None,
        file_name: AnyString | None = None,
        subfolder: str | None = None,
        base_path: str | None = None,
        batch: bool = False,
        confirm: bool = False,
        open_file: bool = False,
        edit: bool = False,
        git: bool = False,
        link: bool = False,
        move: bool = False,
        citations: Citations | None = None,
        auto_doctor: bool = False) -> None:
    """
    :param paths: Paths to the documents to be added.
    :param data: Data for the document to be added.
        If more data is to be retrieved from other sources, the data dictionary
        will be updated from these sources.
    :param folder_name: Name of the folder where the document will be stored.
    :param file_name: File name of the document's files to be stored.
    :param subfolder: Folder within the library where the document's folder
        should be stored.
    :param confirm: Whether or not to ask user for confirmation before adding.
    :param open_file: Whether or not to ask the user for opening the file
        before adding.
    :param edit: Whether or not to ask user for editing the info file
        before adding.
    :param git: Whether or not to ask user for committing before adding,
        in the case of course that the library is a git repository.
    """
    if data is None:
        data = {}

    if citations is None:
        citations = []

    for p in paths:
        if not os.path.exists(p):
            raise FileNotFoundError(f"File '{p}' not found")

    import tempfile

    in_document_paths = paths
    temp_dir = tempfile.mkdtemp()

    from papis.database import get as get_database

    db = get_database()

    from papis.document import Document, describe, dump

    tmp_document = Document(folder=temp_dir, data=data)
    db.maybe_compute_id(tmp_document)

    # reference building
    # NOTE: this needs to go before any papis.format calls, so that those can
    # potentially use the 'ref' key in the format patterns.
    from papis.bibtex import create_reference

    new_ref = create_reference(data, True)
    if new_ref:
        logger.info("Created reference '%s'.", new_ref)
        tmp_document["ref"] = new_ref

    if auto_doctor:
        from papis.commands.doctor import fix_errors

        logger.info("Running doctor auto-fixers on document: '%s'.",
                    describe(tmp_document))
        fix_errors(tmp_document)

    # create a nice folder name for the new document
    if base_path is None:
        base_path = os.path.expanduser(papis.config.get_lib_dirs()[0])

    if subfolder:
        base_path = os.path.join(base_path, subfolder)

    # rename all the given file names
    from papis.paths import rename_document_files, symlink

    renamed_file_list = rename_document_files(
        tmp_document, in_document_paths,
        file_name_format=file_name, allow_remote=False)

    import shutil

    from papis.tui.utils import confirm as ask_confirm, text_area
    from papis.utils import open_file as open_file_viewer

    document_file_list = []
    for in_file_path, out_file_name in (
            zip(in_document_paths, renamed_file_list, strict=True)):
        out_file_path = os.path.join(temp_dir, out_file_name)
        if os.path.exists(out_file_path):
            logger.warning("File '%s' already exists. Skipping...", out_file_path)
            continue

        if not batch and open_file:
            open_file_viewer(in_file_path)

        if not batch and confirm and not ask_confirm(
                f"Add file '{os.path.basename(in_file_path)}' "
                f"(renamed to '{os.path.basename(out_file_path)}') to document?"):
            continue

        if link:
            logger.info("[LN] '%s' to '%s'.", in_file_path, out_file_name)
            symlink(in_file_path, out_file_path)
        elif move:
            logger.info("[MV] '%s' to '%s'.", in_file_path, out_file_name)
            shutil.copy(in_file_path, out_file_path)
        else:
            logger.info("[CP] '%s' to '%s'.", in_file_path, out_file_name)
            shutil.copy(in_file_path, out_file_path)

        document_file_list.append(out_file_name)

    tmp_document["files"] = document_file_list
    tmp_document.save()

    from papis.paths import get_document_unique_folder

    base_path = os.path.normpath(base_path)
    out_folder_path = get_document_unique_folder(
        tmp_document, base_path,
        folder_name_format=folder_name)

    logger.info("Document folder is '%s'.", out_folder_path)
    logger.debug("Document includes files: '%s'.", "', '".join(document_file_list))

    # Check if the user wants to edit before submitting the doc
    # to the library
    if edit:
        from papis.api import edit_file
        logger.info("Editing file before adding it.")

        edit_file(tmp_document.get_info_file(), wait=True)
        tmp_document.load()

    from papis.hooks import run as run_hook
    run_hook("on_add_done", tmp_document)

    # Duplication checking
    logger.info("Checking if this document is already in the library. "
                "This uses the keys ['%s'] to determine uniqueness.",
                "', '".join(papis.config.getlist("unique-document-keys")))

    from papis.utils import locate_document_in_lib

    has_duplicate = False
    try:
        found_document = locate_document_in_lib(tmp_document)
    except IndexError:
        logger.info("No document matching the new metadata found in the '%s' library.",
                    papis.config.get_lib_name())
    else:
        text_area(
            dump(found_document),
            title="This document is already in your library",
            lexer_name="yaml")

        logger.warning("Duplication Warning")
        logger.warning(
            "A document (shown above) in the '%s' library seems to match the "
            "one to be added.", papis.config.get_lib())

        if batch:
            logger.warning(
                "No new document is created! Add this document in "
                "interactive mode (no '--batch') or use 'papis update' instead.")
            return

        logger.warning(
            "Hint: Use the 'papis update' command instead to update the "
            "existing document.")

        # NOTE: we always want the user to confirm if a duplicate is found!
        confirm = True
        has_duplicate = True

    if citations:
        from papis.citations import save_citations
        save_citations(tmp_document, citations)

    if not batch and confirm:
        dup_text = " (duplicate) " if has_duplicate else " "
        text_area(
            dump(tmp_document),
            title=f"This{dup_text}document will be added to your library",
            lexer_name="yaml")

    if confirm:
        if not ask_confirm("Do you want to add the new document?"):
            return

    from papis.document import move as move_doc

    logger.info("[MV] '%s' to '%s'.", tmp_document.get_main_folder(), out_folder_path)
    move_doc(tmp_document, out_folder_path)
    db.add(tmp_document)

    if git:
        from papis.git import add_and_commit_resource
        add_and_commit_resource(
            out_folder_path, ".",
            f"Add document '{describe(tmp_document)}'")

    if move:
        for in_file_path in in_document_paths:
            try:
                os.remove(in_file_path)
            except Exception as exc:
                logger.error("Failed to move file: '%s'.", in_file_path, exc_info=exc)


@click.command(
    "add",
    help="Add a document into a given library."
)
@click.help_option("--help", "-h")
@click.argument("files", type=click.Path(), nargs=-1)
@click.option(
    "-s", "--set", "set_list",
    help="Set some information before.",
    multiple=True,
    type=(str, str))
@click.option(
    "-d", "--subfolder",
    help="Subfolder in the library.",
    default=lambda: papis.config.getstring("add-subfolder"))
@papis.cli.bool_flag(
    "-p", "--pick-subfolder",
    help="Pick from existing subfolders.")
@click.option(
    "--folder-name",
    help="Name format for the document main folder.",
    type=papis.cli.FormatPatternParamType(),
    default=lambda: papis.config.getformatpattern("add-folder-name"))
@click.option(
    "--file-name",
    help="File name format for the document.",
    type=papis.cli.FormatPatternParamType(),
    default=None)
@click.option(
    "--from", "from_importer",
    help="Add document from a specific importer.",
    type=str,
    nargs=2,
    multiple=True,
    default=(),)
@papis.cli.bool_flag("--list-importers", help="List all supported importers.")
@papis.cli.bool_flag(
    "-b", "--batch",
    help="Batch mode, do not prompt or otherwise.")
@papis.cli.bool_flag(
    "--confirm/--no-confirm",
    help="Ask to confirm before adding to the collection.",
    default=lambda: papis.config.getboolean("add-confirm"))
@papis.cli.bool_flag(
    "--open/--no-open", "open_file",
    help="Open files before adding them to the document.",
    default=lambda: papis.config.getboolean("add-open"))
@papis.cli.bool_flag(
    "--edit/--no-edit",
    help="Edit info file before adding document.",
    default=lambda: papis.config.getboolean("add-edit"))
@papis.cli.bool_flag(
    "--link/--no-link",
    help="Instead of copying the file to the library, create a link to "
         "its original location.",
    default=False)
@papis.cli.bool_flag(
    "--move/--no-move",
    help="Instead of copying the file to the library, "
         "move it from its original location.",
    default=False)
@papis.cli.bool_flag(
    "--auto-doctor/--no-auto-doctor",
    help="Apply papis doctor to newly added documents.",
    default=lambda: papis.config.getboolean("auto-doctor"))
@papis.cli.git_option(help="Git add and commit the new document.")
@papis.cli.bool_flag(
    "--download-files/--no-download-files",
    help="Download file with importer if available or not.",
    default=lambda: papis.config.getboolean("add-download-files"))
@papis.cli.bool_flag(
    "--fetch-citations/--no-fetch-citations",
    help="Fetch citations from a DOI (Digital Object Identifier).",
    default=lambda: papis.config.getboolean("add-fetch-citations"))
def cli(files: list[str],
        set_list: list[tuple[str, str]],
        subfolder: str,
        pick_subfolder: bool,
        folder_name: AnyString,
        file_name: AnyString | None,
        from_importer: list[tuple[str, str]],
        list_importers: bool,
        batch: bool,
        confirm: bool,
        open_file: bool,
        edit: bool,
        auto_doctor: bool,
        git: bool,
        link: bool,
        move: bool,
        download_files: bool,
        fetch_citations: bool) -> None:
    """
    Command line interface for papis-add.
    """

    if batch:
        edit = False
        confirm = False
        open_file = False

    # gather importers / downloaders
    from papis.importer import (
        collect_from_importers,
        fetch_importers,
        get_available_importers,
        get_matching_importers_by_name,
        get_matching_importers_by_uri,
    )

    if list_importers:
        from papis.commands.list import list_plugins
        for o in list_plugins(show_importers=True, verbose=True):
            click.echo(o)
        return

    known_importers = get_available_importers()
    extra_importers = {name for name, _ in from_importer}.difference(known_importers)
    if extra_importers:
        logger.error("Unknown importers chosen with '--from': ['%s'].",
                     "', '".join(extra_importers))
        logger.error("Supported importers are: ['%s'].", "', '".join(known_importers))
        return

    if from_importer:
        importers = get_matching_importers_by_name(from_importer)
    elif files:
        from itertools import chain

        importers = list(
            chain.from_iterable(
                get_matching_importers_by_uri(f, include_downloaders=True)
                for f in files))

        if importers and not batch:
            from papis.tui.utils import select_range

            logger.info("These importers where automatically matched. "
                        "Select the ones you want to use.")

            matching_indices = select_range(
                ["{} (files: {}) ".format(
                    imp.name,
                    ", ".join(imp.ctx.files) if imp.ctx.files else "none")
                 for imp in importers],
                "Select matching importers (for instance 0, 1, 3-10, a, all...)")

            importers = [importers[i] for i in matching_indices]
    else:
        importers = []

    # merge importer data + commandline data into a single set
    importers = fetch_importers(importers, download_files=download_files)
    imported = collect_from_importers(importers, batch=batch, use_files=download_files)

    from papis.importer import Context

    ctx = Context()
    ctx.data = imported.data
    ctx.files = [f for f in files if os.path.exists(f)] + imported.files

    if set_list:
        if batch or not ctx.data:
            ctx.data.update(set_list)
        else:
            from papis.utils import update_doc_from_data_interactively
            update_doc_from_data_interactively(
                ctx.data,
                dict(set_list),
                "command-line")

    if not ctx:
        logger.error("No document is created, since no data or files have been "
                     "found. Try providing a filename, an URL or use "
                     "`--from [importer] [uri]` to extract metadata for the "
                     "document.")
        return

    if papis.config.getboolean("time-stamp"):
        from papis.strings import get_timestamp
        ctx.data["time-added"] = get_timestamp()

    from papis.pick import pick_subfolder_from_lib
    base_path = (
        pick_subfolder_from_lib(papis.config.get_lib_name())[0]
    ) if pick_subfolder else None

    if fetch_citations:
        from papis.citations import fetch_citations as fetch_citations_for_doc
        from papis.document import from_data

        try:
            logger.info("Fetching citations for document.")
            citations = fetch_citations_for_doc(from_data(ctx.data))
        except ValueError as exc:
            logger.warning("Could not fetch any citations.", exc_info=exc)
            citations = []
    else:
        citations = []

    run(ctx.files,
        data=ctx.data,
        folder_name=folder_name,
        file_name=file_name,
        subfolder=subfolder,
        base_path=base_path,
        batch=batch,
        confirm=confirm,
        open_file=open_file,
        edit=edit,
        git=git,
        link=link,
        move=move,
        citations=citations,
        auto_doctor=auto_doctor)

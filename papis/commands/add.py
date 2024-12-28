"""
The ``add`` command is one of the central commands of the ``papis``
command-line interface It is a very versatile command with a fair amount of
options.

There are also a few customization settings available for this command, which
are described on the :ref:`configuration page <add-command-options>` for add.

Examples
^^^^^^^^

- Add a document located in ``~/Documents/interesting.pdf`` and name the
  folder where it will be stored in the database ``interesting-paper-2021``

    .. code:: sh

        papis add ~/Documents/interesting.pdf \\
            --folder-name interesting-paper-2021

  if you want to directly add some metadata, like author, title and tags,
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

- Add paper to a library named ``machine-learning`` from ``arxiv.org``

    .. code:: sh

        papis -l machine-learning add \\
            --from arxiv https://arxiv.org/abs/1712.03134

- If you do not want copy the original PDFs into the library, you can
  also tell Papis to just create a link to them, for example

    .. code:: sh

        papis add --link ~/Documents/interesting.pdf \\
            --from doi 10.10763/1.3237134

  will add an entry into the Papis library, but the PDF document will remain
  at ``~/Documents/interesting.pdf``. In the document's folder
  there will be a link to ``~/Documents/interesting.pdf`` instead of the
  file itself. Of course you always have to be sure that the
  document at ``~/Documents/interesting.pdf`` does not disappear, otherwise
  you will end up without a document file.

- Papis also tries to make sense of the inputs that you have passed
  on the command-line. For instance you could provide only a DOI and
  Papis will figure out if this is indeed a DOI and download available metadata
  using Crossref. For example, you can try

    .. code:: sh

        papis add 10.1103/PhysRevLett.123.156401

  Similarly, a wide array of known journal are recognized by URL, so you can try:

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

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.add:cli
    :prog: papis add
"""

import os
from typing import List, Any, Optional, Dict, Tuple
from warnings import warn

import click

import papis.api
import papis.pick
import papis.utils
import papis.hooks
import papis.tui.utils
import papis.filetype
import papis.config
import papis.document
import papis.importer
import papis.cli
import papis.strings
import papis.downloaders
import papis.git
import papis.format
import papis.citations
import papis.id
import papis.logging
import papis.commands.doctor


logger = papis.logging.get_logger(__name__)


class FromFolderImporter(papis.importer.Importer):

    """Importer that gets files and data from a valid papis folder"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name="folder", **kwargs)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        return FromFolderImporter(uri=uri) if os.path.isdir(uri) else None

    def fetch(self) -> None:
        self.logger.info("Importing from folder '%s'.", self.uri)

        doc = papis.document.from_folder(self.uri)
        del doc[papis.id.key_name()]
        self.ctx.data = papis.document.to_dict(doc)
        self.ctx.files = doc.get_files()


class FromLibImporter(papis.importer.Importer):

    """Importer that queries a valid Papis library (also paths) and adds files
    and data
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name="lib", **kwargs)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        try:
            papis.config.get_lib_from_name(uri)
        except Exception:
            return None
        else:
            return FromLibImporter(uri=uri)

    def fetch(self) -> None:
        docs = papis.pick.pick_doc(
            papis.api.get_all_documents_in_lib(self.uri))
        if not docs:
            return
        importer = FromFolderImporter(uri=docs[0].get_main_folder())
        importer.fetch()
        self.ctx = importer.ctx


def get_file_name(
        doc: papis.document.Document,
        original_filepath: str,
        suffix: str = "",
        file_name_format: Optional[papis.strings.AnyString] = None,
        base_name_limit: int = 150) -> str:
    warn("'get_file_name' is deprecated and will be removed in the next "
         "version. Use 'papis.paths.get_document_file_name' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import get_document_file_name
    return get_document_file_name(doc, original_filepath, suffix,
                                  base_name_limit=base_name_limit)


def get_hash_folder(data: Dict[str, Any], document_paths: List[str]) -> str:
    warn("'get_hash_folder' is deprecated and will be removed in the next "
         "version. Use 'papis.paths.get_document_hash_folder' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import get_document_hash_folder
    return get_document_hash_folder(data, document_paths)


def ensure_new_folder(path: str) -> str:
    warn("'ensure_new_folder' is deprecated and will be removed in the next "
         "version. Use 'papis.paths.get_document_unique_folder' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.paths import _make_unique_folder
    return _make_unique_folder(path)


def run(paths: List[str],
        data: Optional[Dict[str, Any]] = None,
        folder_name: Optional[papis.strings.AnyString] = None,
        file_name: Optional[papis.strings.AnyString] = None,
        subfolder: Optional[str] = None,
        base_path: Optional[str] = None,
        batch: bool = False,
        confirm: bool = False,
        open_file: bool = False,
        edit: bool = False,
        git: bool = False,
        link: bool = False,
        move: bool = False,
        citations: Optional[papis.citations.Citations] = None,
        auto_doctor: bool = False) -> None:
    """
    :param paths: Paths to the documents to be added
    :param data: Data for the document to be added.
        If more data is to be retrieved from other sources, the data dictionary
        will be updated from these sources.
    :param folder_name: Name of the folder where the document will be stored
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
    tmp_document = papis.document.Document(folder=temp_dir, data=data)
    papis.database.get().maybe_compute_id(tmp_document)

    # reference building
    # NOTE: this needs to go before any papis.format calls, so that those can
    # potentially use the 'ref' key in the formatted strings.
    if "ref" not in data:
        new_ref = papis.bibtex.create_reference(data)
        if new_ref:
            logger.info("Created reference '%s'.", new_ref)
            tmp_document["ref"] = new_ref

    if auto_doctor:
        logger.info("Running doctor auto-fixers on document: '%s'.",
                    papis.document.describe(tmp_document))
        papis.commands.doctor.fix_errors(tmp_document)

    # create a nice folder name for the new document
    if base_path is None:
        base_path = os.path.expanduser(papis.config.get_lib_dirs()[0])

    if subfolder:
        base_path = os.path.join(base_path, subfolder)

    # rename all the given file names
    from papis.paths import symlink, rename_document_files

    renamed_file_list = rename_document_files(
        tmp_document, in_document_paths,
        file_name_format=file_name)

    import shutil

    document_file_list = []
    for in_file_path, out_file_name in zip(in_document_paths, renamed_file_list):
        out_file_path = os.path.join(temp_dir, out_file_name)
        if os.path.exists(out_file_path):
            logger.warning("File '%s' already exists. Skipping...", out_file_path)
            continue

        if not batch and open_file:
            papis.utils.open_file(in_file_path)

        if not batch and confirm and not papis.tui.utils.confirm(
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
        logger.info("Editing file before adding it.")

        papis.api.edit_file(tmp_document.get_info_file(), wait=True)
        tmp_document.load()

    papis.hooks.run("on_add_done", tmp_document)

    # Duplication checking
    logger.info("Checking if this document is already in the library. "
                "This uses the keys ['%s'] to determine uniqueness.",
                "', '".join(papis.config.getlist("unique-document-keys")))

    has_duplicate = False
    try:
        found_document = papis.utils.locate_document_in_lib(tmp_document)
    except IndexError:
        logger.info("No document matching the new metadata found in the '%s' library.",
                    papis.config.get_lib_name())
    else:
        papis.tui.utils.text_area(papis.document.dump(found_document),
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
        papis.citations.save_citations(tmp_document, citations)

    if not batch and confirm:
        dup_text = " (duplicate) " if has_duplicate else " "
        papis.tui.utils.text_area(
            papis.document.dump(tmp_document),
            title=f"This{dup_text}document will be added to your library",
            lexer_name="yaml")

    if confirm:
        if not papis.tui.utils.confirm("Do you want to add the new document?"):
            return

    logger.info("[MV] '%s' to '%s'.", tmp_document.get_main_folder(), out_folder_path)
    papis.document.move(tmp_document, out_folder_path)

    papis.database.get().add(tmp_document)

    if git:
        papis.git.add_and_commit_resource(
            out_folder_path, ".",
            f"Add document '{papis.document.describe(tmp_document)}'")

    if move:
        for in_file_path in in_document_paths:
            try:
                os.remove(in_file_path)
            except Exception as exc:
                logger.error("Failed to move file: '%s'.", in_file_path, exc_info=exc)


@click.command(
    "add",
    help="Add a document into a given library"
)
@click.help_option("--help", "-h")
@click.argument("files", type=click.Path(), nargs=-1)
@click.option(
    "-s", "--set", "set_list",
    help="Set some information before",
    multiple=True,
    type=(str, str))
@click.option(
    "-d", "--subfolder",
    help="Subfolder in the library",
    default=lambda: papis.config.getstring("add-subfolder"))
@papis.cli.bool_flag(
    "-p", "--pick-subfolder",
    help="Pick from existing subfolders")
@click.option(
    "--folder-name",
    help="Name format for the document main folder",
    type=papis.cli.FormattedStringParamType(),
    default=lambda: papis.config.getformattedstring("add-folder-name"))
@click.option(
    "--file-name",
    help="File name format for the document",
    type=papis.cli.FormattedStringParamType(),
    default=None)
@click.option(
    "--from", "from_importer",
    help="Add document from a specific importer",
    type=(click.Choice(papis.importer.available_importers()), str),
    nargs=2,
    multiple=True,
    default=(),)
@papis.cli.bool_flag(
    "-b", "--batch",
    help="Batch mode, do not prompt or otherwise")
@papis.cli.bool_flag(
    "--confirm/--no-confirm",
    help="Ask to confirm before adding to the collection",
    default=lambda: papis.config.getboolean("add-confirm"))
@papis.cli.bool_flag(
    "--open/--no-open", "open_file",
    help="Open files before adding them to the document",
    default=lambda: papis.config.getboolean("add-open"))
@papis.cli.bool_flag(
    "--edit/--no-edit",
    help="Edit info file before adding document",
    default=lambda: papis.config.getboolean("add-edit"))
@papis.cli.bool_flag(
    "--link/--no-link",
    help="Instead of copying the file to the library, create a link to "
         "its original location",
    default=False)
@papis.cli.bool_flag(
    "--move/--no-move",
    help="Instead of copying the file to the library, "
         "move it from its original location",
    default=False)
@papis.cli.bool_flag(
    "--auto-doctor/--no-auto-doctor",
    help="Apply papis doctor to newly added documents.",
    default=lambda: papis.config.getboolean("auto-doctor"))
@papis.cli.git_option(help="Git add and commit the new document")
@papis.cli.bool_flag(
    "--download-files/--no-download-files",
    help="Download file with importer if available or not",
    default=lambda: papis.config.getboolean("add-download-files"))
@papis.cli.bool_flag(
    "--fetch-citations/--no-fetch-citations",
    help="Fetch citations from a DOI (Digital Object Identifier)",
    default=lambda: papis.config.getboolean("add-fetch-citations"))
def cli(files: List[str],
        set_list: List[Tuple[str, str]],
        subfolder: str,
        pick_subfolder: bool,
        folder_name: papis.strings.AnyString,
        file_name: Optional[papis.strings.AnyString],
        from_importer: List[Tuple[str, str]],
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
    matching_importers = papis.utils.get_matching_importer_by_name(
        from_importer, download_files=download_files)

    if not from_importer and files:
        from itertools import chain

        matching_importers = list(
            chain.from_iterable(
                papis.utils.get_matching_importer_or_downloader(
                    f, download_files=download_files)
                for f in files))

        if matching_importers and not batch:
            logger.info("These importers where automatically matched. "
                        "Select the ones you want to use.")

            matching_indices = papis.tui.utils.select_range(
                ["{} (files: {}) ".format(
                    imp.name,
                    ", ".join(imp.ctx.files) if imp.ctx.files else "no")
                 for imp in matching_importers],
                "Select matching importers (for instance 0, 1, 3-10, a, all...)")

            matching_importers = [matching_importers[i] for i in matching_indices]

    # merge importer data + commandline data into a single set
    imported = papis.utils.collect_importer_data(
        matching_importers, batch=batch, use_files=download_files
    )

    ctx = papis.importer.Context()
    ctx.data = imported.data
    ctx.files = [f for f in files if os.path.exists(f)] + imported.files

    if set_list:
        if batch or not ctx.data:
            ctx.data.update(set_list)
        else:
            papis.utils.update_doc_from_data_interactively(
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
        import time
        ctx.data["time-added"] = time.strftime(papis.strings.time_format)

    base_path = (
        papis.pick.pick_subfolder_from_lib(papis.config.get_lib_name())[0]
    ) if pick_subfolder else None

    if fetch_citations:
        try:
            logger.info("Fetching citations for document.")
            citations = papis.citations.fetch_citations(
                papis.document.from_data(ctx.data))
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

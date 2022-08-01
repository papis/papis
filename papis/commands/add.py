"""
The add command is one of the central commands of the papis command line
interface. It is a very versatile command with a fair amount of options.

There are also customization settings available for this command, check out
the :ref:`configuration page <add-command-options>` for add.

Examples
^^^^^^^^

- Add a document located in ``~/Documents/interesting.pdf`` and name the
  folder where it will be stored in the database ``interesting-paper-2021``

    .. code::

        papis add ~/Documents/interesting.pdf \\
            --folder-name interesting-paper-2021

  if you want to add directly some key values, like ``author``, ``title``
  and ``tags``, you can also run the following:

    .. code::

        papis add ~/Documents/interesting.pdf \\
            --folder-name interesting-paper-2021 \\
            --set author 'John Smith' \\
            --set title 'The interesting life of bees' \\
            --set year 1985 \\
            --set tags 'biology interesting bees'

- Add a paper that you have locally in a file and get the paper information
  through its ``doi`` identifier (in this case ``10.10763/1.3237134`` as an
  example):

    .. code::

        papis add ~/Documents/interesting.pdf --from doi 10.10763/1.3237134

- Add paper to a library named ``machine-learning`` from ``arxiv.org``

    .. code::

        papis -l machine-learning add \\
            --from arxiv https://arxiv.org/abs/1712.03134

- If you do not want copy the original pdfs into the library, you can
  also tell papis to just create a link to them, for example

    .. code::

        papis add --link ~/Documents/interesting.pdf \\
            --from doi 10.10763/1.3237134

  will add an entry into the papis library, but the pdf document will remain
  at ``~/Documents/interesting.pdf``, and in the document's folder
  there will be a link to ``~/Documents/interesting.pdf`` instead of the
  file itself. Of course you always have to be sure that the
  document at ``~/Documents/interesting.pdf`` does not disappear, otherwise
  you will end up without a document to open.

- Papis also tries to make sense of the inputs that you have passed
  to the command, for instance you could provide only a ``doi`` and
  papis will try to know if this is indeed a ``doi``

    .. code::

        papis add 10.1103/PhysRevLett.123.156401

  or from a ``url``

    .. code::

        papis add journals.aps.org/prl/abstract/10.1103/PhysRevLett.123.156401
        papis add https://arxiv.org/abs/1712.03134


Examples in python
^^^^^^^^^^^^^^^^^^

There is a python function in the add module that can be used to interact
in a more effective way in python scripts,

.. autofunction:: papis.commands.add.run

Cli
^^^
.. click:: papis.commands.add:cli
    :prog: papis add

"""
import os
import re
import logging
import pathlib
from typing import List, Any, Optional, Dict, Tuple

import click

import papis.api
import papis.pick
import papis.utils
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

logger = logging.getLogger('add')  # type: logging.Logger


class FromFolderImporter(papis.importer.Importer):

    """Importer that gets files and data from a valid papis folder"""

    def __init__(self, **kwargs: Any):
        papis.importer.Importer.__init__(self, name='folder', **kwargs)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        return FromFolderImporter(uri=uri) if os.path.isdir(uri) else None

    def fetch(self) -> None:
        self.logger.info("Importing from folder '%s'", self.uri)

        doc = papis.document.from_folder(self.uri)
        self.ctx.data = papis.document.to_dict(doc)
        self.ctx.files = doc.get_files()


class FromLibImporter(papis.importer.Importer):

    """Importer that queries a valid papis library (also paths) and adds files
    and data
    """

    def __init__(self, **kwargs: Any):
        papis.importer.Importer.__init__(self, name='lib', **kwargs)

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
        data: Dict[str, Any],
        original_filepath: str,
        suffix: str = "") -> str:
    """Generates file name for the document

    :param data: Data parsed for the actual document
    :type  data: dict
    :param original_filepath: The full path to the original file
    :type  original_filepath: str
    :param suffix: Possible suffix to be appended to the file without
        its extension.
    :type  suffix: str
    :returns: New file name
    :rtype:  str

    """

    basename_limit = 150
    file_name_opt = papis.config.get('add-file-name')
    ext = papis.filetype.get_document_extension(original_filepath)

    if file_name_opt is None:
        file_name_opt = os.path.basename(original_filepath)

    # Get a file name from the format `add-file-name`
    file_name_base = papis.format.format(file_name_opt,
                                         papis.document.from_data(data))

    if len(file_name_base) > basename_limit:
        logger.warning(
            "Shortening the file name '%s' for portability", file_name_base)
        file_name_base = file_name_base[0:basename_limit]

    # Remove extension from file_name_base, if any
    file_name_base = re.sub(
        r"([.]{0})?$".format(ext),
        '',
        file_name_base
    )

    # Adding some extra suffixes, if any, and cleaning up document name
    filename_basename = papis.utils.clean_document_name(
        "{}{}".format(
            file_name_base,
            "-" + suffix if len(suffix) > 0 else ""
        )
    )

    # Adding the recognised extension
    filename = filename_basename + '.' + ext

    return filename


def get_hash_folder(data: Dict[str, Any], document_paths: List[str]) -> str:
    """Folder name where the document will be stored.

    :data: Data parsed for the actual document
    :document_paths: Path of the document

    """
    import random
    author = "-{:.20}".format(data["author"])\
             if "author" in data.keys() else ""

    document_strings = b''
    for docpath in document_paths:
        with open(docpath, 'rb') as fd:
            document_strings += fd.read(2000)

    import hashlib
    md5 = hashlib.md5(
        ''.join(document_paths).encode()
        + str(data).encode()
        + str(random.random()).encode()
        + document_strings
    ).hexdigest()

    result = md5 + author
    result = papis.utils.clean_document_name(result)

    return result


def run(paths: List[str],
        data: Dict[str, Any] = dict(),
        folder_name: Optional[str] = None,
        file_name: Optional[str] = None,
        subfolder: Optional[str] = None,
        confirm: bool = False,
        open_file: bool = False,
        edit: bool = False,
        git: bool = False,
        link: bool = False
        ) -> None:
    """
    :param paths: Paths to the documents to be added
    :type  paths: []
    :param data: Data for the document to be added.
        If more data is to be retrieved from other sources, the data dictionary
        will be updated from these sources.
    :type  data: dict
    :param folder_name: Name of the folder where the document will be stored
    :type  folder_name: str
    :param file_name: File name of the document's files to be stored.
    :type  file_name: str
    :param subfolder: Folder within the library where the document's folder
        should be stored.
    :type  subfolder: str
    :param confirm: Whether or not to ask user for confirmation before adding.
    :type  confirm: bool
    :param open_file: Whether or not to ask the user for opening the file
        before adding.
    :type  open_file: bool
    :param edit: Whether or not to ask user for editing the info file
        before adding.
    :type  edit: bool
    :param git: Whether or not to ask user for committing before adding,
        in the case of course that the library is a git repository.
    :type  git: bool
    """
    import tempfile
    logger = logging.getLogger('add:run')

    # The folder name of the new document that will be created
    out_folder_name = None
    # The real paths of the documents to be added
    in_documents_paths = paths
    # The basenames of the documents to be added
    in_documents_names = []
    # The folder name of the temporary document to be created
    temp_dir = tempfile.mkdtemp()

    for p in in_documents_paths:
        if not os.path.exists(p):
            raise IOError('Document %s not found' % p)

    in_documents_names = [
        papis.utils.clean_document_name(doc_path)
        for doc_path in in_documents_paths
    ]

    tmp_document = papis.document.Document(temp_dir)

    base_path = pathlib.Path(papis.config.get_lib_dirs()[0]).expanduser()
    out_folder_path = base_path

    if subfolder:
        out_folder_path /= pathlib.Path(subfolder)

    if not folder_name:
        out_folder_name = get_hash_folder(data, in_documents_paths)
        logger.info("Got an automatic folder name")
    else:
        temp_doc = papis.document.Document(data=data)
        temp_path = out_folder_path / pathlib.Path(folder_name)
        components: List[str] = []
        assert temp_path.is_relative_to(out_folder_path)
        while temp_path != out_folder_path and temp_path.is_relative_to(out_folder_path):
            path_component = temp_path.name
            component_formatted = papis.format.format(path_component, temp_doc)
            component_cleaned = papis.utils.clean_document_name(component_formatted)
            components.insert(0, component_cleaned)
            # continue with parent path component
            temp_path = temp_path.parent
        # components are formatted in reverse order, so we add then now in the
        # right order to the path
        for c in components:
            out_folder_path /= c

        del temp_doc

    if not out_folder_path.is_relative_to(base_path):
        raise ValueError("formatting produced path outside of library")

    data["files"] = in_documents_names

    logger.info("The folder name is '%s'", out_folder_name)
    logger.debug("Folder path: '%s'", out_folder_path)
    logger.debug("File(s): %s", in_documents_paths)

    # First prepare everything in the temporary directory
    from string import ascii_lowercase
    g = papis.utils.create_identifier(ascii_lowercase)
    string_append = ''
    if file_name is not None:  # Use args if set
        papis.config.set("add-file-name", file_name)
    new_file_list = []

    for in_file_path in in_documents_paths:

        # Rename the file in the staging area
        new_filename = papis.utils.clean_document_name(
            get_file_name(
                data,
                in_file_path,
                suffix=string_append))
        new_file_list.append(new_filename)

        tmp_end_filepath = os.path.join(
            temp_dir,
            new_filename)
        string_append = next(g)

        if link:
            in_file_abspath = os.path.abspath(in_file_path)
            logger.debug(
                "[SYMLINK] '%s' to '%s'", in_file_abspath, tmp_end_filepath)
            os.symlink(in_file_abspath, tmp_end_filepath)
        else:
            logger.debug(
                "[CP] '%s' to '%s'", in_file_path, tmp_end_filepath)

            import shutil
            shutil.copy(in_file_path, tmp_end_filepath)

    data['files'] = new_file_list

    # reference building
    if data.get('ref') is None:
        data['ref'] = papis.bibtex.create_reference(data)
        logger.info("Created reference '%s'", data['ref'])

    tmp_document.update(data)
    tmp_document.save()

    # Check if the user wants to edit before submitting the doc
    # to the library
    if edit:
        logger.info("Editing file before adding it")
        papis.api.edit_file(tmp_document.get_info_file(), wait=True)
        logger.info("Loading the changes made by editing")
        tmp_document.load()

    # Duplication checking
    logger.info("Checking if this document is already in the library")
    try:
        found_document = papis.utils.locate_document_in_lib(tmp_document)
    except IndexError:
        logger.info("No document matching found already in the library")
    else:
        logger.warning("{c.Fore.RED}DUPLICATION WARNING{c.Style.RESET_ALL}")
        logger.warning(
            "A document in the library seems to match the added one.")
        logger.warning(
            "(Hint) Use the 'papis update' command to just update the info.")

        papis.tui.utils.text_area(
            'The following document is already in your library',
            papis.document.dump(found_document),
            lexer_name='yaml',
            height=20)
        confirm = True

    if open_file:
        for d_path in tmp_document.get_files():
            papis.utils.open_file(d_path)
    if confirm:
        if not papis.tui.utils.confirm('Really add?'):
            return

    logger.info(
        "[MV] '%s' to '%s'", tmp_document.get_main_folder(), out_folder_path)

    # This also sets the folder of tmp_document
    papis.document.move(tmp_document, out_folder_path)
    papis.database.get().add(tmp_document)
    if git:
        papis.git.add_and_commit_resource(
            str(tmp_document.get_main_folder()), '.',
            "Add document '{0}'".format(papis.document.describe(tmp_document)))


@click.command(
    "add",
    help="Add a document into a given library"
)
@click.help_option('--help', '-h')
@click.argument("files", type=str, nargs=-1)
@click.option(
    "-s", "--set", "set_list",
    help="Set some information before",
    multiple=True,
    type=(str, str))
@click.option(
    "-d", "--subfolder",
    help="Subfolder in the library",
    default=lambda: papis.config.getstring('add-subfolder'))
@click.option(
    "--folder-name",
    help="Name for the document's folder (papis format)",
    default=lambda: papis.config.getstring('add-folder-name'))
@click.option(
    "--file-name",
    help="File name for the document (papis format)",
    default=None)
@click.option(
    "--from", "from_importer",
    help="Add document from a specific importer ({0})".format(
        ", ".join(papis.importer.available_importers())
    ),
    type=(click.Choice(papis.importer.available_importers()), str),
    nargs=2,
    multiple=True,
    default=(),)
@click.option(
    "-b", "--batch",
    help="Batch mode, do not prompt or otherwise",
    default=False, is_flag=True)
@click.option(
    "--confirm/--no-confirm",
    help="Ask to confirm before adding to the collection",
    default=lambda: True if papis.config.get('add-confirm') else False)
@click.option(
    "--open/--no-open", "open_file",
    help="Open file before adding document",
    default=lambda: True if papis.config.get('add-open') else False)
@click.option(
    "--edit/--no-edit",
    help="Edit info file before adding document",
    default=lambda: True if papis.config.get('add-edit') else False)
@click.option(
    "--link/--no-link",
    help="Instead of copying the file to the library, create a link to"
         "its original location",
    default=False)
@papis.cli.git_option(help="Git add and commit the new document")
@click.option(
    "--list-importers", "--li", "list_importers",
    help="List all available papis importers",
    default=False,
    is_flag=True)
@click.option(
    "--force-download", "--fd", "force_download",
    help="Download file with importer even if local file is passed",
    default=False,
    is_flag=True)
def cli(
        files: List[str],
        set_list: List[Tuple[str, str]],
        subfolder: str,
        folder_name: str,
        file_name: Optional[str],
        from_importer: List[Tuple[str, str]],
        batch: bool,
        confirm: bool,
        open_file: bool,
        edit: bool,
        git: bool,
        link: bool,
        list_importers: bool,
        force_download: bool) -> None:

    if list_importers:
        import_mgr = papis.importer.get_import_mgr()
        for n in import_mgr.names():
            print("{name}\n\t{text}".format(
                name=n,
                text=re.sub(r"[ \n]+", " ", import_mgr[n].plugin.__doc__)))
        return

    from_importer = list(from_importer)
    logger = logging.getLogger('cli:add')

    data = dict()
    for data_set in set_list:
        data[data_set[0]] = data_set[1]

    files = list(files)
    ctx = papis.importer.Context()
    ctx.files = [f for f in files if os.path.exists(f)]
    ctx.data.update(data)

    if batch:
        edit = False
        confirm = False
        open_file = False

    import_mgr = papis.importer.get_import_mgr()
    matching_importers = []  # type: List[papis.importer.Importer]

    if not from_importer and not batch and files:
        matching_importers = sum((
            papis.utils.get_matching_importer_or_downloader(f)
            for f in files), [])
        logger.info("These importers where automatically matched, "
                    "select the ones you want to use")
        _range = papis.tui.utils.select_range(
            ["{0} (files: {1}) ".format(imp.name, ", ".join(imp.ctx.files))
                for imp in matching_importers],
            "Select matching importers (for instance 0, 1, 3-10, a, all...)")
        matching_importers = [matching_importers[i] for i in _range]

    for importer_tuple in from_importer:
        try:
            importer_name = importer_tuple[0]
            resource = importer_tuple[1]
            importer = import_mgr[importer_name].plugin(uri=resource)
            importer.fetch()
            if importer.ctx:
                matching_importers.append(importer)
        except Exception as e:
            logger.exception(e)

    if matching_importers:
        logger.info('There are %d possible matchings', len(matching_importers))

        for importer in matching_importers:
            if importer.ctx.data:
                logger.info('Merging data from importer %s', importer.name)
                if batch:
                    ctx.data.update(importer.ctx.data)
                else:
                    papis.utils.update_doc_from_data_interactively(
                        ctx.data,
                        importer.ctx.data,
                        str(importer))
            if importer.ctx.files and (not files or force_download):
                logger.info(
                        "Got files %s from importer '%s'",
                        importer.ctx.files, importer.name)
                for f in importer.ctx.files:
                    papis.utils.open_file(f)
                    _msg = "Use this file? (from {0})".format(importer.name)
                    if batch or papis.tui.utils.confirm(_msg):
                        ctx.files.append(f)

    if not ctx:
        logger.error('There is nothing to be added')
        return

    if papis.config.getboolean("time-stamp"):
        import time
        ctx.data['time-added'] = time.strftime(papis.strings.time_format)

    return run(
        ctx.files,
        data=ctx.data,
        folder_name=folder_name,
        file_name=file_name,
        subfolder=subfolder,
        confirm=confirm,
        open_file=open_file,
        edit=edit,
        git=git,
        link=link)

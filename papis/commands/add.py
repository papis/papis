"""
The add command is one of the central commands of the papis command line
interface. It is a very versatile command with a fair amount of options.

There are also customization settings availabe for this command, check out
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
            --from url https://arxiv.org/abs/1712.03134

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

        papis add https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.123.156401


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
import logging
from string import ascii_lowercase
import os
import re
import tempfile
import hashlib
import shutil
import papis.api
import papis.pick
import papis.utils
import papis.config
import papis.document
import papis.importer
import papis.cli
import click
import colorama
import papis.downloaders
import papis.git

logger = logging.getLogger('add')


class FromFolderImporter(papis.importer.Importer):

    """Importer that gets files and data from a valid papis folder"""

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(self, name='folder', **kwargs)

    @classmethod
    def match(cls, uri):
        return FromFolderImporter(uri=uri) if os.path.isdir(uri) else None

    def fetch(self):
        doc = papis.document.from_folder(self.uri)
        self.logger.info('importing from folder {0}'.format(self.uri))
        self.ctx.data = papis.document.to_dict(doc)
        self.ctx.files = doc.get_files()


class FromLibImporter(papis.importer.Importer):

    """Importer that queries a valid papis library (also paths) and adds files
    and data
    """

    def __init__(self, **kwargs):
        papis.importer.Importer.__init__(self, name='lib', **kwargs)

    @classmethod
    def match(cls, uri):
        try:
            papis.config.get_lib_from_name(uri)
        except Exception:
            return None
        else:
            return FromLibImporter(uri=uri)

    def fetch(self):
        doc = papis.pick.pick_doc(papis.api.get_all_documents_in_lib(self.uri))
        importer = FromFolderImporter(uri=doc.get_main_folder())
        importer.fetch()
        self.ctx = importer.ctx


def get_file_name(data, original_filepath, suffix=""):
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
    ext = papis.utils.get_document_extension(original_filepath)

    if file_name_opt is None:
        file_name_opt = os.path.basename(original_filepath)

    # Get a file name from the format `add-file-name`
    file_name_base = papis.utils.format_doc(
        file_name_opt,
        papis.document.from_data(data)
    )

    if len(file_name_base) > basename_limit:
        logger.warning(
            "Shortening the name {0} for portability".format(file_name_base)
        )
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


def get_hash_folder(data, document_paths):
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

    md5 = hashlib.md5(
        ''.join(document_paths).encode() +
        str(data).encode() +
        str(random.random()).encode() +
        document_strings
    ).hexdigest()

    result = md5 + author
    result = papis.utils.clean_document_name(result)

    return result


def run(
        paths,
        data=dict(),
        folder_name=None,
        file_name=None,
        subfolder=None,
        confirm=False,
        open_file=False,
        edit=False,
        git=False,
        link=False
        ):
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
    :param confirm: Wether or not to ask user for confirmation before adding.
    :type  confirm: bool
    :param open_file: Wether or not to ask user for opening file before adding.
    :type  open_file: bool
    :param edit: Wether or not to ask user for editing the infor file
        before adding.
    :type  edit: bool
    :param git: Wether or not to ask user for committing before adding,
        in the case of course that the library is a git repository.
    :type  git: bool
    """

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

    if not folder_name:
        out_folder_name = get_hash_folder(data, in_documents_paths)
        logger.info("Got an automatic folder name")
    else:
        temp_doc = papis.document.Document(data=data)
        out_folder_name = papis.utils.format_doc(folder_name, temp_doc)
        out_folder_name = papis.utils.clean_document_name(out_folder_name)
        del temp_doc

    data["files"] = in_documents_names
    out_folder_path = os.path.expanduser(
        os.path.join(
            papis.config.get_lib_dirs()[0],
            subfolder or '',
            out_folder_name))

    logger.info("The folder name is {0}".format(out_folder_name))
    logger.debug("Folder path: {0}".format(out_folder_path))
    logger.debug("File(s): {0}".format(in_documents_paths))

    # First prepare everything in the temporary directory
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
            tmp_document.get_main_folder(),
            new_filename)
        string_append = next(g)

        if link:
            in_file_abspath = os.path.abspath(in_file_path)
            logger.debug(
                "[SYMLINK] '%s' to '%s'" %
                (in_file_abspath, tmp_end_filepath))
            os.symlink(in_file_abspath, tmp_end_filepath)
        else:
            logger.debug(
                "[CP] '%s' to '%s'" %
                (in_file_path, tmp_end_filepath))
            shutil.copy(in_file_path, tmp_end_filepath)

    data['files'] = new_file_list
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
        logger.warning(
            colorama.Fore.RED +
            "DUPLICATION WARNING" +
            colorama.Style.RESET_ALL)
        logger.warning(
            "The document beneath is in your library and it seems to match")
        logger.warning(
            "the one that you're trying to add, "
            "I will prompt you for confirmation")
        logger.warning(
            "(Hint) Use the update command if you just want to update"
            " the info.")
        papis.utils.text_area(
            'The following document is already in your library',
            papis.document.dump(found_document),
            lexer_name='yaml',
            height=20)
        confirm = True

    if open_file:
        for d_path in tmp_document.get_files():
            papis.utils.open_file(d_path)
    if confirm:
        if not papis.utils.confirm('Really add?'):
            return

    logger.info(
        "[MV] '%s' to '%s'" %
        (tmp_document.get_main_folder(), out_folder_path)
    )
    # This also sets the folder of tmp_document
    papis.document.move(tmp_document, out_folder_path)
    papis.database.get().add(tmp_document)
    if git:
        papis.git.add_and_commit_resource(
            tmp_document.get_main_folder(), '.',
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
    default="")
@click.option(
    "--folder-name",
    help="Name for the document's folder (papis format)",
    default=lambda: papis.config.get('add-folder-name'))
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
def cli(files, set_list, subfolder, folder_name, file_name, from_importer,
        batch, confirm, open_file, edit, git, link, list_importers):

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
    matching_importers = []

    if not from_importer and not batch and files:
        matching_importers = sum((
            papis.utils.get_matching_importer_or_downloader(f)
            for f in files), [])

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
        logger.info(
            'There are {0} possible matchings'.format(len(matching_importers)))

        for importer in matching_importers:
            if importer.ctx.data:
                logger.info(
                    'Merging data from importer {0}'.format(importer.name))
                if batch:
                    ctx.data.update(importer.ctx.data)
                else:
                    papis.utils.update_doc_from_data_interactively(
                        ctx.data,
                        importer.ctx.data,
                        str(importer))
            if importer.ctx.files:
                logger.info(
                    'Got files {0} from importer {1}'
                    .format(importer.ctx.files, importer.name))
                for f in importer.ctx.files:
                    papis.utils.open_file(f)
                    if batch or papis.utils.confirm("Use this file?"):
                        ctx.files.append(f)

    if not ctx:
        logger.error('there is nothing to be added')
        return

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

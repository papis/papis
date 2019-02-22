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

        papis add ~/Documents/interesting.pdf --name interesting-paper-2021

  if you want to add directly some key values, like ``author``, ``title``
  and ``tags``, you can also run the following:

    .. code::

        papis add ~/Documents/interesting.pdf \\
            --name interesting-paper-2021 \\
            --set author 'John Smith' \\
            --set title 'The interesting life of bees' \\
            --set year 1985 \\
            --set tags 'biology interesting bees'

- Add a paper that you have locally in a file and get the paper information
  through its ``doi`` identifier (in this case ``10.10763/1.3237134`` as an
  example):

    .. code::

        papis add ~/Documents/interesting.pdf --from-doi 10.10763/1.3237134

- Add paper to a library named ``machine-learning`` from ``arxiv.org``

    .. code::

        papis -l machine-learning add \\
            --from-url https://arxiv.org/abs/1712.03134

- If you do not want copy the original pdfs into the library, you can
  also tell papis to just create a link to them, for example

    .. code::

        papis add --link ~/Documents/interesting.pdf \\
            --from-doi 10.10763/1.3237134

  will add an entry into the papis library, but the pdf document will remain
  at ``~/Documents/interesting.pdf``, and in the document's folder
  there will be a link to ``~/Documents/interesting.pdf`` instead of the
  file itself. Of course you always have to be sure that the
  document at ``~/Documents/interesting.pdf`` does not disappear, otherwise
  you will end up without a document to open.


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
import papis
from string import ascii_lowercase
import os
import re
import tempfile
import hashlib
import shutil
import subprocess
import papis.api
from papis.api import status
import papis.utils
import papis.config
import papis.bibtex
import papis.document
import papis.downloaders.utils
import papis.cli
import click
import builtins
import colorama

logger = logging.getLogger('add')


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
    file_name_opt = papis.config.get('file-name')

    if file_name_opt is None:
        file_name_opt = os.path.basename(original_filepath)

    file_name_base = papis.utils.format_doc(
        file_name_opt,
        papis.document.from_data(data)
    )

    if len(file_name_base) > basename_limit:
        logger.warning(
            'Shortening the documents\' {} name for portability'.format(
                original_filepath
            )
        )
        file_name_base = file_name_base[0:basename_limit]

    filename_basename = papis.utils.clean_document_name(
        "{}{}".format(
            file_name_base,
            "-" + suffix if len(suffix) > 0 else ""
        )
    )

    filename = "{}.{}".format(
        filename_basename,
        papis.utils.get_document_extension(original_filepath)
    )

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


def get_document_extension(document_path):
    """Get document extension

    :document_path: Path of the document
    :returns: Extension (string)

    """
    import filetype
    filetype.guess(document_path)
    kind = filetype.guess(document_path)
    if kind is None:
        m = re.match(r"^.*\.([^.]+)$", os.path.basename(document_path))
        return m.group(1) if m else 'data'
    else:
        return kind.extension


def get_default_title(data, document_path, interactive=False):
    """
    >>> get_default_title({'title': 'hello world'}, 'whatever.pdf')
    'hello world'
    >>> open('Luces-de-bohemia.pdf', 'w+').close()
    >>> get_default_title(dict(), 'Luces-de-bohemia.pdf')
    'Luces de bohemia'
    """
    if "title" in data.keys():
        return data["title"]
    extension = get_document_extension(document_path)
    title = os.path.basename(document_path)\
        .replace("."+extension, "")\
        .replace("_", " ")\
        .replace("-", " ")
    if interactive:
        title = papis.utils.input(
            'Title?', title
        )
    return title


def get_default_author(data, document_path, interactive=False):
    """
    >>> get_default_author({'author': 'Garcilaso de la vega'}, 'whatever.pdf')
    'Garcilaso de la vega'
    >>> get_default_author(dict(), 'Luces-de-bohemia.pdf')
    'Unknown'
    """
    if "author" in data.keys():
        return data["author"]
    author = "Unknown"
    if interactive:
        author = papis.utils.input(
            'Author?', author
        )
    return author


def run(
        paths,
        data=dict(),
        name=None,
        file_name=None,
        subfolder=None,
        interactive=False,
        confirm=False,
        open_file=False,
        edit=False,
        commit=False,
        link=False
        ):
    """
    :param paths: Paths to the documents to be added
    :type  paths: []
    :param data: Data for the document to be added.
        If more data is to be retrieved from other sources, the data dictionary
        will be updated from these sources.
    :type  data: dict
    :param name: Name of the folder where the document will be stored
    :type  name: str
    :param file_name: File name of the document's files to be stored.
    :type  file_name: str
    :param subfolder: Folder within the library where the document's folder
        should be stored.
    :type  subfolder: str
    :param interactive: Wether or not interactive functionality of this command
        should be activated.
    :type  interactive: bool
    :param confirm: Wether or not to ask user for confirmation before adding.
    :type  confirm: bool
    :param open_file: Wether or not to ask user for opening file before adding.
    :type  open_file: bool
    :param edit: Wether or not to ask user for editing the infor file
        before adding.
    :type  edit: bool
    :param commit: Wether or not to ask user for committing before adding,
        in the case of course that the library is a git repository.
    :type  commit: bool
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

    if not name:
        logger.info("Getting an automatic name")
        out_folder_name = get_hash_folder(data, in_documents_paths)
    else:
        temp_doc = papis.document.Document(data=data)
        out_folder_name = papis.utils.format_doc(name, temp_doc)
        out_folder_name = papis.utils.clean_document_name(out_folder_name)
        del temp_doc

    data["files"] = in_documents_names
    out_folder_path = os.path.expanduser(os.path.join(
        papis.config.get('dir'), subfolder or '',  out_folder_name
    ))

    logger.debug("Folder name = % s" % out_folder_name)
    logger.debug("Folder path = % s" % out_folder_path)
    logger.debug("File(s)     = % s" % in_documents_paths)

    # First prepare everything in the temporary directory
    g = papis.utils.create_identifier(ascii_lowercase)
    string_append = ''
    if file_name is not None:  # Use args if set
        papis.config.set("file-name", file_name)
    new_file_list = []

    for in_file_path in in_documents_paths:

        # Rename the file in the staging area
        new_filename = papis.utils.clean_document_name(
            get_file_name(
                data,
                in_file_path,
                suffix=string_append
            )
        )
        new_file_list.append(new_filename)

        tmp_end_filepath = os.path.join(
            tmp_document.get_main_folder(),
            new_filename
        )
        string_append = next(g)

        if link:
            in_file_abspath = os.path.abspath(in_file_path)
            logger.debug(
                "[SYMLINK] '%s' to '%s'" %
                (in_file_abspath, tmp_end_filepath)
            )
            os.symlink(in_file_abspath, tmp_end_filepath)
        else:
            logger.debug(
                "[CP] '%s' to '%s'" %
                (in_file_path, tmp_end_filepath)
            )
            shutil.copy(in_file_path, tmp_end_filepath)

    data['files'] = new_file_list
    tmp_document.update(data, force=True)
    tmp_document.save()

    # Check if the user wants to edit before submitting the doc
    # to the library
    if edit:
        logger.info("Editing file before adding it")
        papis.api.edit_file(tmp_document.get_info_file(), wait=True)
        logger.info("Loading the changes made by editing")
        tmp_document.load()
        data = papis.document.to_dict(tmp_document)

    # Duplication checking
    logger.info("Check if the added document is already existing")
    try:
        found_document = papis.utils.locate_document_in_lib(tmp_document)
    except IndexError:
        logger.info("Document not found in library")
    else:
        logger.warning(
            colorama.Fore.RED +
            "DUPLICATION WARNING" +
            colorama.Style.RESET_ALL
        )
        logger.warning(
            "The document beneath is in your library and it seems to match"
        )
        logger.warning(
            "the one that you're trying to add, "
            "I will prompt you for confirmation"
        )
        logger.warning(
            "(Hint) Use the update command if you just want to update"
            " the info."
        )
        papis.utils.text_area(
            'The following document is already in your library',
            papis.document.dump(found_document),
            lexer_name='yaml',
            height=20
        )
        confirm = True

    if open_file:
        for d_path in tmp_document.get_files():
            papis.api.open_file(d_path)
    if confirm:
        if not papis.utils.confirm('Really add?'):
            return status.success

    logger.info(
        "[MV] '%s' to '%s'" %
        (tmp_document.get_main_folder(), out_folder_path)
    )
    # This also sets the folder of tmp_document
    papis.document.move(tmp_document, out_folder_path)
    papis.database.get().add(tmp_document)
    if commit:
        subprocess.call(["git", "-C", out_folder_path, "add", "."])
        subprocess.call(
            ["git", "-C", out_folder_path, "commit", "-m", "Add document"]
        )
    return status.success


@click.command(
    "add",
    help="Add a document into a given library"
)
@click.help_option('--help', '-h')
@click.argument("files", type=click.Path(exists=True), nargs=-1)
@click.option(
    "-s", "--set", "set_list",
    help="Set some information before",
    multiple=True,
    type=(str, str)
)
@click.option(
    "-d", "--dir", "directory",
    help="Subfolder in the library",
    default=""
)
@click.option(
    "-i", "--interactive/--no-interactive",
    help="Do some of the actions interactively",
    default=lambda: True if papis.config.get('add-interactive') else False
)
@click.option(
    "--name",
    help="Name for the document's folder (papis format)",
    default=lambda: papis.config.get('add-name')
)
@click.option(
    "--file-name",
    help="File name for the document (papis format)",
    default=None
)
@click.option(
    "--from-bibtex",
    help="Parse information from a bibtex file",
    default=""
)
@click.option(
    "--from-yaml",
    help="Parse information from a yaml file",
    default=""
)
@click.option(
    "--from-folder",
    help="Add document from folder being a valid papis document"
         " (containing info.yaml)",
    default=""
)
@click.option(
    "--from-url",
    help="Get document and information from a"
    "given url, a parser must be implemented",
    default=""
)
@click.option(
    "--from-doi",
    help="Doi to try to get information from",
    default=None
)
@click.option(
    "--from-pmid",
    help="PMID to try to get information from",
    default=None
)
@click.option(
    "--from-lib",
    help="Add document from another library",
    default=""
)
@click.option(
    "--confirm/--no-confirm",
    help="Ask to confirm before adding to the collection",
    default=lambda: True if papis.config.get('add-confirm') else False
)
@click.option(
    "--open/--no-open", "open_file",
    help="Open file before adding document",
    default=lambda: True if papis.config.get('add-open') else False
)
@click.option(
    "--edit/--no-edit",
    help="Edit info file before adding document",
    default=lambda: True if papis.config.get('add-edit') else False
)
@click.option(
    "--commit/--no-commit",
    help="Commit document if library is a git repository",
    default=False
)
@click.option(
    "--link/--no-link",
    help="Instead of copying the file to the library, create a link to"
         "its original location",
    default=False
)
@click.option(
    #TODO: REMOVE IT AT SOME POINT
    "--no-document",
    default=False,
    is_flag=True,
    help="DEPRECATION NOTICE: This option is no longer valid, "
         "it will be removed in future releases"
)
def cli(
        files,
        set_list,
        directory,
        interactive,
        name,
        file_name,
        from_bibtex,
        from_yaml,
        from_folder,
        from_url,
        from_doi,
        from_pmid,
        from_lib,
        confirm,
        open_file,
        edit,
        commit,
        link,
        no_document
        ):
    """
    :param from_folder: Filepath where to find a papis document (folder +
        info file) to be added to the library.
    :type  from_folder: str
    :param from_doi: doi number to try to download information from.
    :type  from_doi: str
    :param from_pmid: pmid number to try to download information from.
    :type  from_pmid: str
    :param from_url: Url to try to download information and files from.
    :type  from_url: str
    :param from_bibtex: Filepath where to find a file containing bibtex info.
    :type  from_bibtex: str
    :param from_yaml: Filepath where to find a file containing yaml info.
    :type  from_yaml: str
    """
    data = dict()
    files = list(files)

    for data_set in set_list:
        data[data_set[0]] = data_set[1]

    logger = logging.getLogger('cli:add')

    if from_lib:
        doc = papis.api.pick_doc(
            papis.api.get_all_documents_in_lib(from_lib)
        )
        if doc:
            from_folder = doc.get_main_folder()

    try:
        # Try getting title if title is an argument of add
        data["title"] = data.get('title') or get_default_title(
            data,
            files[0],
            interactive
        )
        logger.debug("Title = % s" % data["title"])
    except:
        pass

    try:
        # Try getting author if author is an argument of add
        data["author"] = data.get('author') or get_default_author(
            data,
            files[0],
            interactive
        )
        logger.debug("Author = % s" % data["author"])
    except:
        pass

    if from_folder:
        original_document = papis.document.Document(from_folder)
        from_yaml = original_document.get_info_file()
        files.extend(original_document.get_files())

    if from_url:
        logger.info("Attempting to retrieve from url")
        url_data = papis.downloaders.utils.get(from_url)
        data.update(url_data["data"])
        files.extend(url_data["documents_paths"])
        # If no data was retrieved and doi was found, try to get
        # information with the document's doi
        if not data and url_data["doi"] is not None and\
                not from_doi:
            logger.warning(
                "I could not get any data from %s" % from_url
            )
            from_doi = url_data["doi"]

    if from_pmid:
        logger.info("Using PMID %s via HubMed" % from_pmid)
        hubmed_url = "http://pubmed.macropus.org/articles/"\
                     "?format=text%%2Fbibtex&id=%s" % from_pmid
        bibtex_data = papis.downloaders.utils.get_downloader(
            hubmed_url,
            "get"
        ).get_document_data().decode("utf-8")
        bibtex_data = papis.bibtex.bibtex_to_dict(bibtex_data)
        if len(bibtex_data):
            data.update(bibtex_data[0])
            if "doi" in data and not from_doi:
                from_doi = data["doi"]
        else:
            logger.error("PMID %s not found or invalid" % from_pmid)

    if from_doi:
        logger.info("I'll try using doi %s" % from_doi)
        data.update(papis.utils.doi_to_data(from_doi))
        if len(files) == 0 and \
                papis.config.get('doc-url-key-name') in data.keys():

            doc_url = data[papis.config.get('doc-url-key-name')]
            logger.info(
                'You did not provide any files, but I found a possible '
                'url where the file might be'
            )
            logger.info(
                'I am trying to download the document from %s' % doc_url
            )
            down = papis.downloaders.utils.get_downloader(doc_url, 'get')
            assert(down is not None)
            tmp_filepath = tempfile.mktemp()
            logger.debug("Saving in %s" % tmp_filepath)

            with builtins.open(tmp_filepath, 'wb+') as fd:
                fd.write(down.get_document_data())

            logger.info('Opening the file')
            papis.api.open_file(tmp_filepath)
            if papis.utils.confirm('Do you want to use this file?'):
                files.append(tmp_filepath)

    if from_yaml:
        logger.info("Reading yaml input file = %s" % from_yaml)
        data.update(papis.utils.yaml_to_data(from_yaml))

    if from_bibtex:
        logger.info("Reading bibtex input file = %s" % from_bibtex)
        bib_data = papis.bibtex.bibtex_to_dict(from_bibtex)
        if len(bib_data) > 1:
            logger.warning(
                'Your bibtex file contains more than one entry,'
                ' I will be taking the first entry'
            )
        data.update(bib_data[0])

    assert(isinstance(data, dict))

    return run(
        list(files),
        data=data,
        name=name,
        file_name=file_name,
        subfolder=directory,
        interactive=interactive,
        confirm=confirm,
        open_file=open_file,
        edit=edit,
        commit=commit,
        link=link
    )

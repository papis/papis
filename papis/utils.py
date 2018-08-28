# -*- coding: utf-8 -*-
from subprocess import call
import logging
from itertools import count, product

logger = logging.getLogger("utils")
logger.debug("importing")

import os
import re
import papis.api
import papis.config
import papis.commands
import papis.document
import papis.crossref
import papis.bibtex
import papis.exceptions


def general_open(fileName, key, default_opener=None, wait=True):
    """Wraper for openers


    >>> import tempfile; path = tempfile.mktemp()
    >>> general_open(path, 'nonexistent-key', wait=False).stdin == None
    True
    >>> general_open(path, 'nonexistent-key') > 0
    True
    >>> general_open([path], 'nonexistent-key', default_opener=lambda path: 42)
    42
    >>> general_open([path], 'nonexistent-key', default_opener=tempfile)
    Traceback (most recent call last):
    ...
    Warning: How should I use the opener ...?
    >>> papis.config.set('editor', 'echo')
    >>> general_open([path], 'editor', wait=False)
    <subprocess.Popen...>
    """
    try:
        opener = papis.config.get(key)
    except papis.exceptions.DefaultSettingValueMissing:
        if default_opener is None:
            default_opener = papis.config.get_default_opener()
        opener = default_opener
    if isinstance(fileName, list):
        fileName = papis.api.pick(fileName)
    if isinstance(opener, str):
        import subprocess
        import shlex
        cmd = shlex.split("{0} '{1}'".format(opener, fileName))
        logger.debug("cmd:  %s" % cmd)
        if wait:
            logger.debug("Waiting for process to finsih")
            return subprocess.call(cmd)
        else:
            logger.debug("Not waiting for process to finish")
            return subprocess.Popen(
                cmd, shell=False,
                stdin=None, stdout=None, stderr=None, close_fds=True
            )
    elif hasattr(opener, '__call__'):
        return opener(fileName)
    else:
        raise Warning("How should I use the opener %s?" % opener)


def format_doc(python_format, document, key=""):
    """Construct a string using a pythonic format string and a document.

    :param python_format: Python-like format string.
        (`see <
            https://docs.python.org/2/library/string.html#format-string-syntax
        >`_)
    :type  python_format: str
    :param document: Papis document
    :type  document: papis.document.Document
    :returns: Formated string
    :rtype: str
    """
    doc = key or papis.config.get("format-doc-name")
    if papis.config.getboolean('format-jinja2-enable') is True:
        try:
            import jinja2
        except ImportError:
            logger.error("""
            You're trying to format strings using jinja2
            Jinja2 is not installed by default, so just install it

                pip3 install jinja2

            """)
        else:
            return jinja2.Template(python_format).render(**{doc: document})
    return python_format.format(**{doc: document})


def get_folders(folder):
    """This is the main indexing routine. It looks inside ``folder`` and crawls
    the whole directory structure in search for subfolders containing an info
    file.

    :param folder: Folder to look into.
    :type  folder: str
    :returns: List of folders containing an info file.
    :rtype: list
    """
    logger.debug("Indexing folders")
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(os.path.join(root, get_info_file_name())):
            folders.append(root)
    return folders


def create_identifier(input_list):
    """This creates a generator object capable of iterating over lists to
    create combinations of that list that result in unique strings.
    Ideally for use in modifying an existing string to make it unique.

    Example:
    >>> import string
    >>> m = create_identifier(string.ascii_lowercase)
    >>> next(m)
    'a'

    (`see <
        https://stackoverflow.com/questions/14381940/
        >`_)

    :param input_list: list to iterate over
    :type  input_list: list

    """
    for n in count(1):
        for s in product(input_list, repeat=n):
            yield ''.join(s)


def get_info_file_name():
    """Get the name of the general info file for any document

    :returns: Name of the file.
    :rtype: str
    """
    return papis.config.get("info-name")


def doi_to_data(doi):
    """Try to get from a DOI expression a dictionary with the document's data
    using the crossref module.

    :param doi: DOI expression.
    :type  doi: str
    :returns: Document's data
    :rtype: dict
    """
    return papis.crossref.doi_to_data(doi)


def yaml_to_data(yaml_path):
    """Convert a yaml file into a dictionary using the yaml module.

    :param yaml_path: Path to a yaml file
    :type  yaml_path: str
    :returns: Dictionary containing the info of the yaml file
    :rtype:  dict
    """
    import yaml
    return yaml.load(open(yaml_path))


def confirm(prompt, yes=True, bottom_toolbar=None):
    """Confirm with user input

    :param prompt: Question or text that the user gets.
    :type  prompt: str
    :param yes: If yes should be the default.
    :type  yes: bool
    :returns: True if go ahead, False if stop
    :rtype:  bool

    """
    result = papis.utils.input(
        prompt,
        bottom_toolbar=bottom_toolbar,
        default='Y/n' if yes else 'y/N',
        validator_function=lambda x: x in 'YyNn',
        dirty_message='Please, write either "y" or "n" to confirm'
    )
    if yes:
        return result not in 'Nn'
    else:
        return result not in 'Yy'


def input(prompt, default="", bottom_toolbar=None, multiline=False, 
        validator_function=None, dirty_message=""):
    """Prompt user for input

    :param prompt: Question or text that the user gets.
    :type  prompt: str
    :param default: Default value to give if the user does not input anything
    :type  default: str
    :returns: User input or default
    :rtype:  bool

    """
    import prompt_toolkit
    from prompt_toolkit.validation import Validator
    if validator_function is not None:
        validator = Validator.from_callable(
            validator_function,
            error_message=dirty_message,
            move_cursor_to_end=True
        )
    else:
        validator = None

    fragments = [
        ('', prompt),
        ('fg:red', ' ({0})'.format(default)),
        ('', ': '),
    ]

    result = prompt_toolkit.prompt(
        fragments,
        validator=validator,
        multiline=multiline,
        bottom_toolbar=bottom_toolbar,
        validate_while_typing=True
    )

    return result if result else default


def clean_document_name(doc_path):
    """Get a file path and return the basename of the path cleaned.

    It will also turn chinese, french, russian etc into ascii characters.

    :param doc_path: Path of a document.
    :type  doc_path: str
    :returns: Basename of the path cleaned
    :rtype:  str

    >>> clean_document_name('{{] __ }}albert )(*& $ß $+_ einstein (*]')
    'albert-ss-einstein'
    >>> clean_document_name('/ashfd/df/  #$%@#$ }{_+"[ ]hello öworld--- .pdf')
    'hello-oworld-.pdf'
    """
    from slugify import slugify
    regex_pattern = r'[^a-z0-9.]+'
    return slugify(
        os.path.basename(doc_path),
        word_boundary=True,
        regex_pattern=regex_pattern
    )


def git_commit(path="", message=""):
    """Commits changes in the path with a message.
    If the path is not given, then the lib path is used.

    :param path: Folder where a git repo exists.
    :type  path: str
    :param message: Commit message
    :type  message: str
    :returns: None

    """
    logger.debug('Commiting...')
    path = path or os.path.expanduser(papis.config.get('dir'))
    message = '-m "%s"' % message if len(message) > 0 else ''
    cmd = ['git', '-C', path, 'commit', message]
    logger.debug(cmd)
    message = '-m "%s"' % message if len(message) > 0 else ''
    call(cmd)


def locate_document(document, documents):
    """Try to figure out if a document is already within a list of documents.

    :param document: Document to be searched for
    :type  document: papis.document.Document
    :param documents: Documents to search in
    :type  documents: list
    :returns: papis document if it is found

    """
    # if these keys exist in the documents, then check those first
    # TODO: find a way to really match well titles and author
    comparing_keys = eval(papis.config.get('unique-document-keys'))
    for d in documents:
        for key in comparing_keys:
            if key in document.keys() and key in d.keys():
                if re.match(document[key], d[key], re.I):
                    return d


def guess_file_extension(filename):
    for ext in ["pdf", "djvu", "epub", "mobi"]:
        if re.match(r".*\.{0}$".format(ext), filename):
            return ext
    return "txt"

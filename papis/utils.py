# -*- coding: utf-8 -*-
import subprocess
import multiprocessing
import time
import copy
from itertools import count, product
import os
import re
import papis.pick
import papis.config
import papis.commands
import papis.document
import papis.bibtex
import papis.exceptions
import logging
import papis.importer
import papis.downloaders
import colorama

logger = logging.getLogger("utils")
logger.debug("importing")


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
        fileName = papis.pick.pick(fileName)
    if isinstance(opener, str):
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


def open_file(file_path, wait=True):
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    :param wait: Wait for the completion of the opener program to continue
    :type  wait: bool

    """
    general_open(fileName=file_path, key="opentool", wait=wait)


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
    fdoc = papis.document.Document()
    fdoc.update(document)
    try:
        return python_format.format(**{doc: fdoc})
    except Exception as e:
        return str(e)


def get_folders(folder):
    """This is the main indexing routine. It looks inside ``folder`` and crawls
    the whole directory structure in search for subfolders containing an info
    file.

    :param folder: Folder to look into.
    :type  folder: str
    :returns: List of folders containing an info file.
    :rtype: list
    """
    logger.debug("Indexing folders in '{0}'".format(folder))
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(os.path.join(root, papis.config.get('info-name'))):
            folders.append(root)
    logger.debug("{0} valid folders retrieved".format(len(folders)))
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
        return result in 'Yy'


def text_area(title, text, lexer_name="", height=10, full_screen=False):
    """
    Small implementation of an editor/pager for small pieces of text.

    :param title: Title of the text_area
    :type  title: str
    :param text: Editable text
    :type  text: str
    :param lexer_name: If the editable text should be highlighted with
        some kind of grammar, examples are ``yaml``, ``python`` ...
    :type  lexer_name: str
    :param height: Max height of the text area
    :type  height: int
    :param full_screen: Wether or not the text area should be full screen.
    :type  full_screen: bool
    """
    from prompt_toolkit import Application
    from prompt_toolkit.enums import EditingMode
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
    from prompt_toolkit.layout.controls import (
        BufferControl, FormattedTextControl
    )
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.layout import Dimension
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import PygmentsLexer
    from pygments.lexers import find_lexer_class_by_name
    assert(type(title) == str)
    assert(type(text) == str)
    assert(type(lexer_name) == str)
    assert(type(height) == int)
    assert(type(full_screen) == bool)

    kb = KeyBindings()
    buffer1 = Buffer()
    buffer1.text = text

    @kb.add('c-q')
    def exit_(event):
        event.app.exit(0)

    @kb.add('c-s')
    def save_(event):
        event.app.return_text = buffer1.text

    class App(Application):
        return_text = None

    text_height = Dimension(min=0, max=height) if height is not None else None

    pygment_lexer = find_lexer_class_by_name(lexer_name)
    lexer = PygmentsLexer(pygment_lexer)
    text_window = Window(
        height=text_height,
        style='bg:black fg:ansiwhite',
        content=BufferControl(buffer=buffer1, lexer=lexer)
    )

    root_container = HSplit([
        Window(
            align=WindowAlign.LEFT,
            style='bg:ansiwhite',
            height=1,
            content=FormattedTextControl(
                text=[('fg:ansiblack bg:ansiwhite', title)]
            ),
            always_hide_cursor=True
        ),

        text_window,

        Window(
            height=1,
            width=None,
            align=WindowAlign.LEFT,
            style='bg:ansiwhite',
            content=FormattedTextControl(
                text=[(
                    'fg:ansiblack bg:ansiwhite',
                    "Quit [Ctrl-q]  Save [Ctrl-s]"
                )]
            )
        ),
    ])

    layout = Layout(root_container)

    layout.focus(text_window)

    app = App(
        editing_mode=(
            EditingMode.EMACS
            if papis.config.get('editmode', section='tui') == 'emacs'
            else EditingMode.VI
        ), layout=layout, key_bindings=kb, full_screen=full_screen
    )
    app.run()
    return app.return_text


def yes_no_dialog(title, text):
    from prompt_toolkit.shortcuts import yes_no_dialog
    from prompt_toolkit.styles import Style

    example_style = Style.from_dict({
        'dialog': 'bg:#88ff88',
        'dialog frame-label': 'bg:#ffffff #000000',
        'dialog.body': 'bg:#000000 #00ff00',
        'dialog shadow': 'bg:#00aa00',
    })

    return yes_no_dialog(
        title=title,
        text=text,
        style=example_style
    )


def input(
        prompt, default="", bottom_toolbar=None, multiline=False,
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
    import prompt_toolkit.validation
    if validator_function is not None:
        validator = prompt_toolkit.validation.Validator.from_callable(
            validator_function,
            error_message=dirty_message,
            move_cursor_to_end=True
        )
    else:
        validator = None
    if isinstance(prompt, str):
        fragments = [
            ('', prompt),
            ('fg:red', ' ({0})'.format(default)),
            ('', ': '),
        ]
    else:
        fragments = prompt

    result = prompt_toolkit.prompt(
        fragments,
        validator=validator,
        multiline=multiline,
        bottom_toolbar=bottom_toolbar,
        validate_while_typing=True
    )

    return result if result else default


def update_doc_from_data_interactively(document, data, data_name):
    import papis.tui.widgets.diff
    docdata = copy.copy(document)
    # do not compare some entries
    docdata.pop('files', None)
    docdata.pop('tags', None)
    document.update(
        papis.tui.widgets.diff.diffdict(
            docdata,
            data,
            namea=papis.document.describe(document), nameb=data_name))


def clean_document_name(doc_path):
    """Get a file path and return the basename of the path cleaned.

    It will also turn chinese, french, russian etc into ascii characters.

    :param doc_path: Path of a document.
    :type  doc_path: str
    :returns: Basename of the path cleaned
    :rtype:  str

    """
    import slugify
    regex_pattern = r'[^a-z0-9.]+'
    return slugify.slugify(
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
    dirs = papis.config.get_lib_dirs()
    path = path or os.path.expanduser(dirs[0])
    message = '-m "%s"' % message if len(message) > 0 else ''
    cmd = ['git', '-C', path, 'commit', message]
    logger.debug(cmd)
    subprocess.call(cmd)


def locate_document_in_lib(document, library=None):
    """Try to figure out if a document is already in a library

    :param document: Document to be searched for
    :type  document: papis.document.Document
    :param library: Name of a valid papis library
    :type  library: str
    :returns: Document in library if found
    :rtype:  papis.document.Document
    :raises IndexError: Whenever document is not found in the library
    """
    db = papis.database.get(library=library)
    comparing_keys = eval(papis.config.get('unique-document-keys'))

    for k in comparing_keys:
        if not document.has(k):
            continue
        docs = db.query_dict({k: document[k]})
        if docs:
            return docs[0]

    raise IndexError("Document not found in library")


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


def folders_to_documents(folders):
    """Turn folders into documents, this is done in a multiprocessing way, this
    step is quite critical for performance.

    :param folders: List of folder paths.
    :type  folders: list
    :returns: List of document objects.
    :rtype:  list
    """
    logger = logging.getLogger("utils:dir2doc")
    np = multiprocessing.cpu_count()
    logger.debug("converting folder into documents on {0} cores".format(np))
    pool = multiprocessing.Pool(np)
    begin_t = time.time()
    result = pool.map(papis.document.from_folder, folders)
    pool.close()
    pool.join()
    logger.debug("done in %.1f ms" % (1000*time.time()-1000*begin_t))
    return result


def get_cache_home():
    """Get folder where the cache files are stored, it retrieves the
    ``cache-dir`` configuration setting. It is ``XDG`` standard compatible.

    :returns: Full path for cache main folder
    :rtype:  str

    """
    user_defined = papis.config.get('cache-dir')
    if user_defined is not None:
        path = os.path.expanduser(user_defined)
    else:
        path = os.path.expanduser(
            os.path.join(os.environ.get('XDG_CACHE_HOME'), 'papis')
        ) if os.environ.get(
            'XDG_CACHE_HOME'
        ) else os.path.expanduser(
            os.path.join('~', '.cache', 'papis')
        )
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def geturl(url):
    """Quick and dirty file get request utility.
    """
    assert(isinstance(url, str))
    import requests
    session = requests.Session()
    session.headers = {'User-Agent': papis.config.get('user-agent')}
    return session.get(url).content


def get_matching_importer_or_downloader(matching_string):
    importers = []
    logger = logging.getLogger("utils:matcher")
    for importer_cls in (papis.importer.get_importers() +
                         papis.downloaders.get_downloaders()):
        importer = importer_cls.match(matching_string)
        logger.debug(
            "trying with importer {c.Back.BLACK}{c.Fore.YELLOW}{name}"
            "{c.Style.RESET_ALL}".format(
                c=colorama, name=importer_cls))
        if importer:
            logger.info(
                "{f} {c.Back.BLACK}{c.Fore.GREEN}matches {name}"
                "{c.Style.RESET_ALL}".format(
                    f=matching_string, c=colorama, name=importer.name))
            try:
                importer.fetch()
            except Exception as e:
                logger.error(e)
            else:
                importers.append(importer)
    return importers

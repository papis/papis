from itertools import count, product
from typing import Optional, List, Iterator, Callable, Any, Dict, Union
import copy
import logging
import multiprocessing
import os
import re
import shlex
import subprocess
import time

import colorama

import papis.config
import papis.exceptions
import papis.importer
import papis.downloaders
import papis.document
import papis.database

LOGGER = logging.getLogger("utils")
LOGGER.debug("importing")


def general_open(
        file_name: str, key: str,
        default_opener: Optional[str] = None,
        wait: bool = True) -> None:
    """Wraper for openers
    """
    try:
        opener = papis.config.get(key)
    except papis.exceptions.DefaultSettingValueMissing:
        if default_opener is None:
            default_opener = papis.config.get_default_opener()
        opener = default_opener
    cmd = shlex.split("{0} '{1}'".format(opener, file_name))
    LOGGER.debug("cmd:  %s", cmd)
    if wait:
        LOGGER.debug("Waiting for process to finsih")
        subprocess.call(cmd)
    else:
        LOGGER.debug("Not waiting for process to finish")
        subprocess.Popen(
            cmd, shell=False,
            stdin=None, stdout=None, stderr=None, close_fds=True)


def open_file(file_path: str, wait: bool = True) -> None:
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    :param wait: Wait for the completion of the opener program to continue
    :type  wait: bool

    """
    general_open(file_name=file_path, key="opentool", wait=wait)


def get_folders(folder: str) -> List[str]:
    """This is the main indexing routine. It looks inside ``folder`` and crawls
    the whole directory structure in search for subfolders containing an info
    file.

    :param folder: Folder to look into.
    :type  folder: str
    :returns: List of folders containing an info file.
    :rtype: list
    """
    LOGGER.debug("Indexing folders in '{0}'".format(folder))
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(
                os.path.join(root, papis.config.getstring('info-name'))):
            folders.append(root)
    LOGGER.debug("{0} valid folders retrieved".format(len(folders)))
    return folders


def create_identifier(input_list: str) -> Iterator[str]:
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


def confirm(
        prompt: str,
        yes: bool = True,
        bottom_toolbar: Optional[str] = None) -> bool:
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
        dirty_message='Please, write either "y" or "n" to confirm')
    if yes:
        return result not in 'Nn'
    return result in 'Yy'


def text_area(
        title: str,
        text: str,
        lexer_name: str = "",
        height: int = 10,
        full_screen: bool = False) -> str:
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
    from prompt_toolkit.utils import Event
    from prompt_toolkit.layout import Dimension
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import PygmentsLexer
    from pygments.lexers import find_lexer_class_by_name

    kb = KeyBindings()
    buffer1 = Buffer()
    buffer1.text = text

    @kb.add('c-q')  # type: ignore
    def exit_(event: Event) -> None:
        event.app.exit(0)

    @kb.add('c-s')  # type: ignore
    def save_(event: Event) -> None:
        event.app.return_text = buffer1.text

    class App(Application):  # type: ignore
        # TODO: add stubs to be able to remove type ignore above
        return_text = ""  # type: str

    text_height = Dimension(min=0, max=height) if height is not None else None

    pygment_lexer = find_lexer_class_by_name(lexer_name)
    lexer = PygmentsLexer(pygment_lexer)
    text_window = Window(
        height=text_height,
        style='bg:black fg:ansiwhite',
        content=BufferControl(buffer=buffer1, lexer=lexer))

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


def yes_no_dialog(title: str, text: str) -> Any:
    from prompt_toolkit.shortcuts import yes_no_dialog
    from prompt_toolkit.styles import Style

    example_style = Style.from_dict({
        'dialog': 'bg:#88ff88',
        'dialog frame-label': 'bg:#ffffff #000000',
        'dialog.body': 'bg:#000000 #00ff00',
        'dialog shadow': 'bg:#00aa00',
    })

    return yes_no_dialog(title=title, text=text, style=example_style)


def input(
        prompt: str,
        default: str = "",
        bottom_toolbar: Optional[str] = None,
        multiline: bool = False,
        validator_function: Optional[Callable[[str], bool]] = None,
        dirty_message: str = "") -> str:
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
        validate_while_typing=True)

    return str(result) if result else default


def update_doc_from_data_interactively(
        document: Union[papis.document.Document, Dict[str, Any]],
        data: Dict[str, Any], data_name: str) -> None:
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


def clean_document_name(doc_path: str) -> str:
    """Get a file path and return the basename of the path cleaned.

    It will also turn chinese, french, russian etc into ascii characters.

    :param doc_path: Path of a document.
    :type  doc_path: str
    :returns: Basename of the path cleaned
    :rtype:  str

    """
    import slugify
    regex_pattern = r'[^a-z0-9.]+'
    return str(slugify.slugify(
        os.path.basename(doc_path),
        word_boundary=True,
        regex_pattern=regex_pattern))


def locate_document_in_lib(
        document: papis.document.Document,
        library: Optional[str] = None) -> papis.document.Document:
    """Try to figure out if a document is already in a library

    :param document: Document to be searched for
    :type  document: papis.document.Document
    :param library: Name of a valid papis library
    :type  library: str
    :returns: Document in library if found
    :rtype:  papis.document.Document
    :raises IndexError: Whenever document is not found in the library
    """
    db = papis.database.get(library_name=library)
    comparing_keys = papis.config.getlist('unique-document-keys')
    assert comparing_keys is not None

    for k in comparing_keys:
        if not document.has(k):
            continue
        docs = db.query_dict({k: document[k]})
        if docs:
            return docs[0]

    raise IndexError("Document not found in library")


def locate_document(
        document: papis.document.Document,
        documents: List[papis.document.Document]
        ) -> Optional[papis.document.Document]:
    """Try to figure out if a document is already within a list of documents.

    :param document: Document to be searched for
    :type  document: papis.document.Document
    :param documents: Documents to search in
    :type  documents: list
    :returns: papis document if it is found

    """
    # if these keys exist in the documents, then check those first
    # TODO: find a way to really match well titles and author
    comparing_keys = papis.config.getlist('unique-document-keys')
    assert comparing_keys is not None
    for d in documents:
        for key in comparing_keys:
            if key in document.keys() and key in d.keys():
                if re.match(document[key], d[key], re.I):
                    return d
    return None


def folders_to_documents(folders: List[str]) -> List[papis.document.Document]:
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


def get_cache_home() -> str:
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
            os.path.join(str(os.environ.get('XDG_CACHE_HOME')), 'papis')
        ) if os.environ.get(
            'XDG_CACHE_HOME'
        ) else os.path.expanduser(
            os.path.join('~', '.cache', 'papis')
        )
    if not os.path.exists(path):
        os.makedirs(path)
    return str(path)


def get_matching_importer_or_downloader(
        matching_string: str
        ) -> List[papis.importer.Importer]:
    importers = []  # type: List[papis.importer.Importer]
    logger = logging.getLogger("utils:matcher")
    _imps = papis.importer.get_importers()
    _downs = papis.downloaders.get_available_downloaders()
    _all_importers = list(_imps) + list(_downs)
    for importer_cls in _all_importers:
        logger.debug(
            "trying with importer {c.Back.BLACK}{c.Fore.YELLOW}{name}"
            "{c.Style.RESET_ALL}".format(c=colorama, name=importer_cls))
        importer = importer_cls.match(
            matching_string)  # type: Optional[papis.importer.Importer]
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

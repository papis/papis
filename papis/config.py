"""General
*******

.. papis-config:: local-config-file

    Name AND relative path of the local configuration file that papis
    will additionally read if the file is present in the current
    directory or in the base directory of a given library.

    This is useful for instance if you have a library somewhere
    for which you want special configuration settings to be set
    but you do not want these settings to cluster in your configuration
    file. It is also useful if you're sharing a library with someone
    else and you want them to have the same settings in that library as
    you. Imagine you're sharing a library of datasheets with your friend
    Fulano. You have your library at

    ::

        ~/Documents/lib-with-fulano

    and you've set a local configuration file there

    ::

        ~/Documents/lib-with-fulano/.papis.config

    then whenever Fulano uses that library and the file is also present,
    his papis program will also read the configuration settings at
    the path above.

.. papis-config:: dir-umask

    This is the default ``umask`` that will be used to create the new
    documents' directories.

.. papis-config:: use-git

    Some commands will issue git commands if this option is set to ``True``.
    For example in ``mv`` or ``rename``.

.. papis-config:: browse-query-format

    The query string that is to be searched for in the ``browse`` command
    whenever a search engine is used.

.. papis-config:: search-engine

    Search engine to be used by some commands like ``browse``.

.. papis-config:: user-agent

    User agent used by papis whenever it obtains information from external
    servers.

.. papis-config:: default-gui

    Default gui to be used by papis, it can have the values given
    by ``papis gui --help``.

.. papis-config:: scripts-short-help-regex

    This is the format of the short help indicator in external papis
    commands.

.. papis-config:: info-name

    The default name of the information files.

.. papis-config:: doc-url-key-name

    Some documents might have associated apart from an url also a file url,
    the key name appearing in the information file is defined by
    this setting.

.. papis-config:: default-library

    The name of the library that is to be searched when ``papis``
    is run without library arguments.

.. papis-config:: export-text-format

    The default output papis format for ``papis export --text``.

.. papis-config:: format-doc-name

    This setting controls the name of the document in the papis format strings
    like in format strings such as ``match-format`` or ``header-format``.
    For instance, if you are managing videos, you might want to
    set this option to ``vid`` in order to set  the ``header-format`` to
    ``{doc[title]} - {doc[director]} - {doc[duration]}``.

.. papis-config:: match-format

    Default format that is used to match a document against in order to select
    it. For example if the ``match-format`` is equal to
    ``{doc[year]} {doc[author]}`` then title of a document will not work
    to match a document, only the year and author.

.. papis-config:: header-format

    Default format that is used to show a document in order to select it.

.. papis-config:: info-allow-unicode

    This flag is to be set if you want to allow unicode characters
    in your info file or not. If it is set to false then a representation
    for the unicode characters will be written in its place.
    Since we should be living in an unicode world, it is set to ``True``
    by default.

.. papis-config:: sync-command

    Command that is to be used when ``papis sync`` is run.

Tools options
^^^^^^^^^^^^^

.. papis-config:: opentool

    This is the general program that will be used to open documents.
    As for now papis is not intended to detect the type of document to be open
    and decide upon it how to open the document. You should set this
    to the right program for the tool. If you are in linux you might want
    to take a look at `ranger <http://ranger.nongnu.org>`_ or let
    the default handle it in your system.
    For mac users you might set this to ``open``.

.. papis-config:: browser
    :default: $BROWSER

    Program to be used for opening websites, the default is the environment
    variable ``$BROWSER``.

.. papis-config:: picktool

    This is the program used whenever papis asks you to pick a document
    or options in general.

    Possible options are:
        - papis.pick
        - rofi
        - vim
        - dmenu

.. papis-config:: editor
    :default: $EDITOR

    Editor used to edit files in papis, for instance for the ``papis edit``
    command. It defaults to the ``$EDITOR`` environment variable, if this is
    not set then it will default to the ``$VISUAL`` environment variable.
    Otherwise the default editor in your system will be used.

.. papis-config:: xeditor

    Sometimes papis might use an editor that uses a windowing system
    (GUI Editor), you can set this to your preferred gui based editor, e.g.
    ``gedit``, ``xemacs``, ``gvim`` to name a few.


.. papis-config:: file-browser

    File browser to be used when opening a directory, it defaults to the
    default file browser in your system, however you can set it to different
    file browsers such as ``dolphin``, ``thunar``, ``ranger`` to name a few.


Bibtex options
^^^^^^^^^^^^^^

.. papis-config:: extra-bibtex-keys

    When exporting documents in bibtex format, you might want to add
    non-standard bibtex keys such as ``doc_url`` or ``tags``, you can add
    these here as comma separated values, for example
    ``extra-bibtex-keys = tags, doc_url``.

.. papis-config:: extra-bibtex-types

    Allow non-standard bibtex types to be recognized, e.g,
    ``extra-bibtex-types = wikipedia, video, song``.
    See `bibtex reference
        <http://mirror.easyname.at/ctan/biblio/bibtex/base/btxdoc.pdf>`_.

.. papis-config:: multiple-authors-format

    When retrieving automatic author information from services like
    crossref.org, papis usually builds the ``author`` field for the
    given document. The format how every single author name is built
    is given by this setting, for instance you could customize it
    by the following:

    ::

        multiple-authors-format = {au[surname]} -- {au[given_name]}

    which would given in the case of Albert Einstein the string
    ``Einstein -- Albert``.

.. papis-config:: multiple-authors-separator

    Similarly to ``multiple-authors-format``, this is the string that
    separates single authors in the ``author`` field. If it is set to
    `` and `` then you would have ``<author 1> and <author 2> and ....``
    in the ``author`` field.

.. _add-command-options:

Add command options
^^^^^^^^^^^^^^^^^^^

.. papis-config:: ref-format

    This flag is set to change the ``ref`` flag in the info.yaml file
    when a document is imported. For example: I prefer the format
    FirstAuthorYear e.g. Plews2019. This would be achieved by the
    following:

    ::

        ref-format = {doc[author_list][0][surname]}{doc[year]}

    The default behavior is to set the doi as the ref.

.. papis-config:: add-confirm

    If set to ``True``, everytime you run ``papis add``
    the flag ``--confirm`` will be added automatically. If is set to ``True``
    and you add it, i.e., you run ``papis add --confirm``, then it will
    fave the contrary effect, i.e., it will not ask for confirmation.

.. papis-config:: add-name
    :default: empty string

    Default name for the folder of newly added documents. For example, if you
    the folder of your documents to be named after the format
    ``author-title`` then you should set it to
    the papis format: ``{doc[author]}-{doc[title]}``.
    Per default a hash followed by the author name is created.

.. papis-config:: file-name

    Same as ``add-name``, but for files, not folders. If it is not set,
    the names of the files will be cleaned and taken `as-is`.

.. papis-config:: add-interactive

    If set to ``True``, everytime you run ``papis add``
    the flag ``--interactive`` will be added automatically. If is set to
    ``True`` and you add it, i.e., you run ``papis add --interactive``, then it
    will fave the contrary effect, i.e., it will not run in interactive mode.

.. papis-config:: add-edit

    If set to ``True``, everytime you run ``papis add``
    the flag ``--edit`` will be added automatically. If is set to
    ``True`` and you add it, i.e., you run ``papis add --edit``, then it
    will fave the contrary effect, i.e., it will not prompt to edit the info
    file.

.. papis-config:: add-open

    If set to ``True``, everytime you run ``papis add``
    the flag ``--open`` will be added automatically. If is set to
    ``True`` and you add it, i.e., you run ``papis add --open``, then it
    will fave the contrary effect, i.e., it will not open the attached files
    before adding the document to the library.

.. papis-config:: add-default-fields

    This is the default values that are settable in the add command.
    For instance if you would like to set ``title``, ``author`` and
    ``year`` directly from the command line, you can set
    ::

        add-default-fields = ['title', 'author', 'year']

    and you will be able to do
    ::

        papis add doc.pdf --author 'Bohm' --title 'Super book' --year 1928

.. _check-command-options:

Check command options
^^^^^^^^^^^^^^^^^^^^^

.. papis-config:: check-keys

    Python list key values to be checked by default by the command
    ``check``. E.g: ``check-keys = ["author", "doi"]``.
    It is important that it is a valid python list.

.. _edit-command-options:

Edit command options
^^^^^^^^^^^^^^^^^^^^

.. papis-config:: notes-name

    In ``papis edit`` you can edit notes about the document. ``notes-name``
    is the default name of the notes file, which by default is supposed
    to be a TeX file.

.. _marks-options:

Marks
^^^^^

.. papis-config:: open-mark

    If this option is set to ``True``, then every time that papis opens
    a document it will ask to open a mark first.
    If it is set to ``False``, then doing

    .. code::

        papis open --mark

    will avoid opening a mark.

.. papis-config:: mark-key-name

    This is the default key name for the marks in the info file, for
    example if you set ``mark-key-name = bookmarks`` then you would have
    in your ``info.yaml`` file

    .. code::

        author: J. Krishnamurti
        bookmarks:
        - name: Chapter 1
          value: 120

.. papis-config:: mark-format-name

    This is the name of the mark to be passed to the options
    ``mark-header-format`` etc... E.g. if you set ``mark-format-name = m``
    then you could set ``mark-header-format = {m[value]} - {m[name]}``.

.. papis-config:: mark-header-format

    This is the format in which the mark will appear whenever the user
    has to pick one, you can change this in order to make ``marks`` work
    in the way you like. Per default it is assumed that every mark
    has a ``name`` and a ``value`` key, but this you can change.

.. papis-config:: mark-match-format

    Format in which the mark name has to match the user input.

.. papis-config:: mark-opener-format

    Due to the difficulty to generalize opening a general document
    at a given bookmark, the user should set this in whichever way
    it suits their needs. For example

    - If you are using the pdf viewer ``evince`` and you want to open a
      mark, you would use

        ::

            mark-opener-format = evince -p {mark[value]}

    - If you are using ``okular`` you would use

        ::

            mark-opener-format = okular -p {mark[value]}

    - If you are using ``zathura``, do

        ::

            mark-opener-format = zathura -P {mark[value]}

Databases
=========

.. papis-config:: default-query-string

    This is the default query that a command will take if no
    query string is typed in the command line. For example this is
    the query that is passed to the command open whenever no search
    string is typed:

    ::

        papis open

    Imagine you want to have all your papers whenever you do not
    specify an input query string, then you would set

    ::

        default-query-string = author="John Smith"

    and whenever you typed ``papis open``, onlye the ``John Smith`` authored
    papers would appear. Notice that the current example has been
    done assuming the ``database-backend = papis``.

.. papis-config:: database-backend

    The backend to use in the database. As for now papis supports
    the own database system ``papis`` and
    `whoosh <https://whoosh.readthedocs.io/en/latest/>`_.

.. papis-config:: use-cache

    Set to ``False`` if you do not want to use the ``cache``
    for the given library. This is only effective if you're using the
    ``papis`` database-backend.

.. papis-config:: cache-dir

.. papis-config:: whoosh-schema-fields

    Python list with the ``TEXT`` fields that should be included in the
    whoosh database schema. For instance say that you want to be able
    to search for the ``doi`` and ``ref`` of the documents, then you could
    include

    ::

        whoosh-schema-fields = ['doi', 'ref']

.. papis-config:: whoosh-schema-prototype

    This is the model for the whoosh schema, check
    `the documentation <https://whoosh.readthedocs.io/en/latest/schema.html/>`_
    for more information.


"""
import logging

logger = logging.getLogger("config")
logger.debug("importing")

import os
import configparser
import papis.exceptions


CONFIGURATION = None  #: Global configuration object variable.
DEFAULT_SETTINGS = None  #: Default settings for the whole papis.
OVERRIDE_VARS = {
    "folder": None,
    "cache": None,
    "file": None,
    "scripts": None
}


def get_default_opener():
    """Get the default file opener for the current system
    """
    import sys
    if sys.platform.startswith('darwin'):
        return "open"
    elif os.name == 'nt':
        return "start"
    elif os.name == 'posix':
        return "xdg-open"


general_settings = {
    "local-config-file": ".papis.config",
    "database-backend": "papis",
    "default-query-string": ".",

    "opentool": get_default_opener(),
    "dir-umask": 0o755,
    "browser": os.environ.get('BROWSER') or get_default_opener(),
    "picktool": "papis.pick",
    "mvtool": "mv",
    "editor": os.environ.get('EDITOR')
                        or os.environ.get('VISUAL')
                        or get_default_opener(),
    "xeditor": get_default_opener(),
    "sync-command": "git -C {lib[dir]} pull origin master",
    "notes-name": "notes.tex",
    "use-cache": True,
    "cache-dir": None,
    "use-git": False,

    "add-confirm": False,
    "add-name": "",
    "file-name": None,
    "add-interactive": False,
    "add-edit": False,
    "add-open": False,
    "add-default-fields": '["title", "author"]',

    "check-keys": '["files"]',
    "browse-query-format": "{doc[title]} {doc[author]}",
    "search-engine": "https://duckduckgo.com",
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)',
    "default-gui": "vim",
    "scripts-short-help-regex": ".*papis-short-help: *(.*)",
    "info-name": "info.yaml",
    "doc-url-key-name": "doc_url",

    "open-mark": False,
    "mark-key-name": "marks",
    "mark-format-name": "mark",
    "mark-header-format": "{mark[name]} - {mark[value]}",
    "mark-match-format": "{mark[name]} - {mark[value]}",
    "mark-opener-format": get_default_opener(),

    "file-browser": get_default_opener(),
    "extra-bibtex-keys": "",
    "extra-bibtex-types": "",
    "default-library": "papers",
    "export-text-format":
        "{doc[author]}. {doc[title]}. {doc[journal]} {doc[pages]}"
        " {doc[month]} {doc[year]}",
    "format-doc-name": "doc",
    "match-format":
        "{doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}",
    "header-format":
        "{doc[title]:<70.70}|{doc[author]:<20.20} ({doc[year]:-<4})",

    "info-allow-unicode": True,
    "ref-format": "{doc[doi]}",
    "multiple-authors-separator": " and ",
    "multiple-authors-format": "{au[surname]}, {au[given_name]}",

    "whoosh-schema-fields": "['doi']",
    "whoosh-schema-prototype":
    '{\n'
    '"author": TEXT(stored=True),\n'
    '"title": TEXT(stored=True),\n'
    '"year": TEXT(stored=True),\n'
    '"tags": TEXT(stored=True),\n'
    '}',

}


def get_general_settings_name():
    """Get the section name of the general settings
    :returns: Section's name
    :rtype:  str
    >>> get_general_settings_name()
    'settings'
    """
    return "settings"


def get_default_settings(section="", key=""):
    """Get the default settings for all non-user variables
    in papis.

    If section and key are given, then the setting
    for the given section and the given key are returned.

    If only ``key`` is given, then the setting
    for the ``general`` section is returned.

    :param section: Particular section of the default settings
    :type  section: str
    :param key: Setting's name to be queried for.
    :type  key: str

    >>> import collections
    >>> type(get_default_settings()) is collections.OrderedDict
    True
    >>> get_default_settings(key='mvtool')
    'mv'
    >>> get_default_settings(key='help-key', section='vim-gui')
    'h'
    """
    global DEFAULT_SETTINGS
    import papis.gui
    # We use an OrderedDict so that the first entry will always be the general
    # settings, also good for automatic documentation
    from collections import OrderedDict
    if DEFAULT_SETTINGS is None:
        DEFAULT_SETTINGS = OrderedDict()
        DEFAULT_SETTINGS.update({
            get_general_settings_name(): general_settings,
        })
        DEFAULT_SETTINGS.update(
            papis.gui.get_default_settings()
        )
    if not section and not key:
        return DEFAULT_SETTINGS
    elif not section:
        return DEFAULT_SETTINGS[get_general_settings_name()][key]
    else:
        return DEFAULT_SETTINGS[section][key]


def get_config_home():
    """Returns the base directory relative to which user specific configuration
    files should be stored.

    :returns: Configuration base directory
    :rtype:  str
    >>> import os; os.environ['XDG_CONFIG_HOME'] = '/tmp'
    >>> get_config_home()
    '/tmp'
    """
    return os.environ.get('XDG_CONFIG_HOME') or os.path.join(
        os.path.expanduser('~'), '.config'
    )


def get_config_dirs():
    """
    >>> import os; os.environ['XDG_CONFIG_DIRS'] = ''
    >>> os.environ['XDG_CONFIG_HOME'] = '/tmp'
    >>> get_config_dirs()
    ['/tmp/papis', ...]
    """
    dirs = []
    if os.environ.get('XDG_CONFIG_DIRS'):
        # get_config_home should also be included on top of XDG_CONFIG_DIRS
        dirs += [
            os.path.join(d, 'papis') for d in
            os.environ.get('XDG_CONFIG_DIRS').split(':')
        ]
    # Take XDG_CONFIG_HOME and $HOME/.papis for backwards
    # compatibility
    dirs += [
        os.path.join(get_config_home(), 'papis'),
        os.path.join(os.path.expanduser('~'), '.papis')
    ]
    return dirs


def get_config_folder():
    """Get folder where the configuration files are stored,
    e.g. ``/home/user/.papis``. It is XDG compatible, which means that if the
    environment variable ``XDG_CONFIG_HOME`` is defined it will use the
    configuration folder ``XDG_CONFIG_HOME/papis`` instead.

    >>> import os; os.environ['XDG_CONFIG_HOME'] = '/tmp'
    >>> newpath = os.path.join(os.environ['XDG_CONFIG_HOME'], 'papis')
    >>> if not os.path.exists(newpath): os.mkdir(newpath)
    >>> get_config_folder()
    '/tmp/papis'
    """
    config_dirs = get_config_dirs()
    for config_dir in config_dirs:
        if os.path.exists(config_dir):
            return config_dir
    # If no folder is found, then get the config home
    return os.path.join(get_config_home(), 'papis')


def get_config_file():
    """Get the path of the main configuration file,
    e.g. /home/user/.papis/config

    >>> import os; os.environ['XDG_CONFIG_HOME'] = '/tmp'
    >>> newpath = os.path.join(os.environ['XDG_CONFIG_HOME'], 'papis')
    >>> if not os.path.exists(newpath): os.mkdir(newpath)
    >>> get_config_file()
    '/tmp/papis/config'
    """
    global OVERRIDE_VARS
    if OVERRIDE_VARS["file"] is not None:
        config_file = OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(
            get_config_folder(), "config"
        )
    logger.debug("Getting config file %s" % config_file)
    return config_file


def set_config_file(filepath):
    """Override the main configuration file path
    """
    global OVERRIDE_VARS
    if filepath is not None:
        logger.debug("Setting config file to %s" % filepath)
        OVERRIDE_VARS["file"] = filepath


def get_scripts_folder():
    """Get folder where the scripts are stored,
    e.g. /home/user/.papis/scripts
    """
    return os.path.join(
        get_config_folder(), "scripts"
    )


def set(key, val, section=None):
    """Set a key to val in some section and make these changes available
    everywhere.
    >>> set('picktool', 'rofi')
    >>> get('picktool')
    'rofi'
    """
    config = get_configuration()
    if not config.has_section(section or "settings"):
        config.add_section(section or "settings")
    # FIXME: Right now we can only save val in string form
    # FIXME: It would be nice to be able to save also int and booleans
    config.set(section or get_general_settings_name(), key, str(val))


def general_get(key, section=None, data_type=None):
    """General getter method that will be specialized for different modules.

    :param data_type: The data type that should be expected for the value of
        the variable.
    :type  data_type: DataType, e.g. int, src ...
    :param default: Default value for the configuration variable if it is not
        set.
    :type  default: It should be the same that ``data_type``
    :param extras: List of tuples containing section and prefixes
    """
    # Init main variables
    method = None
    value = None
    config = get_configuration()
    lib = get_lib()
    global_section = get_general_settings_name()
    specialized_key = section + "-" + key if section is not None else key
    extras = [(section, key)] if section is not None else []
    sections = [(global_section, specialized_key)] +\
        extras + [(lib, specialized_key)]
    default_settings = get_default_settings()

    # Check data type for setting getter method
    if data_type == int:
        method = config.getint
    elif data_type == float:
        method = config.getfloat
    elif data_type == bool:
        method = config.getboolean
    else:
        method = config.get

    # Try to get key's value from configuration
    for extra in sections:
        sec = extra[0]
        whole_key = extra[1]
        if sec not in config.keys():
            continue
        if whole_key in config[sec].keys():
            value = method(sec, whole_key)

    if value is None:
        try:
            default = default_settings[
                section or global_section
            ][
                specialized_key if section is None else key
            ]
        except KeyError as e:
            raise papis.exceptions.DefaultSettingValueMissing(key)
        else:
            return default
    return value


def get(*args, **kwargs):
    """String getter
    """
    return general_get(*args, **kwargs)


def getint(*args, **kwargs):
    """Integer getter
    >>> set('something', 42)
    >>> getint('something')
    42
    """
    return general_get(*args, data_type=int, **kwargs)


def getfloat(*args, **kwargs):
    """Float getter
    >>> set('something', 0.42)
    >>> getfloat('something')
    0.42
    """
    return general_get(*args, data_type=float, **kwargs)


def getboolean(*args, **kwargs):
    """Bool getter
    >>> set('add-open', True)
    >>> getboolean('add-open')
    True
    """
    return general_get(*args, data_type=bool, **kwargs)


def get_configuration():
    """Get the configuration object, if no papis configuration has ever been
    initialized, it initializes one. Only one configuration per process should
    ever be configured.

    :returns: Configuration object
    :rtype:  papis.config.Configuration
    """
    global CONFIGURATION
    if CONFIGURATION is None:
        logger.debug("Creating configuration")
        CONFIGURATION = Configuration()
        # Handle local configuration file, and merge it if it exists
        local_config_file = papis.config.get("local-config-file")
        merge_configuration_from_path(local_config_file, CONFIGURATION)
    return CONFIGURATION


def merge_configuration_from_path(path, configuration):
    """
    Merge information of a configuration file found in `path`
    to the information of the configuration object stored in `configuration`.
    The function checks for the existence of path.

    :param path: Path to the configuration file
    :type  path: str
    :param configuration: Configuration object
    :type  configuration: papis.config.Configuration
    """
    if os.path.exists(path):
        logger.debug(
            "Merging configuration from " + path
        )
        configuration.read(path)
        configuration.handle_includes()


def set_lib(library):
    """Set library, notice that in principle library can be a full path.

    :param library: Library name or path to a papis library
    :type  library: str

    >>> import os
    >>> if not os.path.exists('/tmp/setlib-test'): os.makedirs(\
            '/tmp/setlib-test'\
        )
    >>> set_lib('/tmp/setlib-test')
    >>> get_lib()
    '/tmp/setlib-test'
    """
    config = get_configuration()
    if library not in config.keys():
        if os.path.exists(library):
            # Check if the path exists, then use this path as a new library
            logger.debug("Using library %s" % library)
            config[library] = dict(dir=library)
        else:
            raise Exception(
                "Path or library '%s' does not seem to exist" % library
            )
    try:
        args = papis.commands.get_args()
        args.lib = library
    except AttributeError:
        os.environ["PAPIS_LIB"] = library


def get_lib():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str
    >>> set_lib('papers')
    >>> get_lib()
    'papers'
    """
    import papis.commands
    try:
        lib = papis.commands.get_args().lib
    except AttributeError:
        try:
            lib = os.environ["PAPIS_LIB"]
        except KeyError:
            # Do not put papis.config.get because get is a special function
            # that also needs the library to see if some key was overridden!
            lib = papis.config.get_default_settings(key="default-library")
    return lib


def reset_configuration():
    """Destroys existing configuration and returns a new one.

    :returns: Configuration object
    :rtype:  papis.config.Configuration
    """
    global CONFIGURATION
    if CONFIGURATION is not None:
        logger.warning("Overwriting previous configuration")
    CONFIGURATION = None
    logger.debug("Resetting configuration")
    return get_configuration()


class Configuration(configparser.ConfigParser):

    default_info = {
      "papers": {
        'dir': '~/Documents/papers'
      },
      get_general_settings_name(): {
        'default-library': 'papers'
      }
    }

    logger = logging.getLogger("Configuration")

    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.dir_location = get_config_folder()
        self.scripts_location = get_scripts_folder()
        self.file_location = get_config_file()
        self.initialize()

    def handle_includes(self):
        if "include" in self.keys():
            for name in self["include"]:
                self.logger.debug("including %s" % name)
                self.read(os.path.expanduser(self.get("include", name)))

    def initialize(self):
        if not os.path.exists(self.dir_location):
            self.logger.warning(
                'Creating configuration folder in %s' % self.dir_location
            )
            os.makedirs(self.dir_location)
        if not os.path.exists(self.scripts_location):
            os.makedirs(self.scripts_location)
        if os.path.exists(self.file_location):
            self.read(self.file_location)
            self.handle_includes()
        else:
            for section in self.default_info:
                self[section] = {}
                for field in self.default_info[section]:
                    self[section][field] = self.default_info[section][field]
            with open(self.file_location, "w") as configfile:
                self.write(configfile)

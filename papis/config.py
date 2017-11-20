"""
General
*******


.. papis-config:: mode

    Papis is a modal program and it can be configured to support different
    operating modes. The default is considering that every papis document
    or entry is a 'document'.

.. papis-config:: opentool

    This is the general program that will be used to open documents.
    As for now papis is not intended to detect the type of document to be open
    and decide upon it how to open the document. You should set this
    to the right program for the tool. If you are in linux you might want
    to take a look at `ranger <http://ranger.nongnu.org>`_ or let
    the default handle it in your system.
    For mac users you might set this to ``open``.

.. papis-config:: dir-umask

.. papis-config:: browser
    :default: $BROWSER

.. papis-config:: picktool

.. papis-config:: mvtool

.. papis-config:: editor
    :default: $EDITOR

.. papis-config:: xeditor

.. papis-config:: sync-command

.. papis-config:: notes-name

.. papis-config:: format-doc-name

.. papis-config:: use-cache

.. papis-config:: cache-dir

.. papis-config:: use-git

.. papis-config:: add-confirm

.. papis-config:: add-name

.. papis-config:: add-interactive

.. papis-config:: add-edit

.. papis-config:: add-open

.. papis-config:: check-keys

.. papis-config:: browse-query-format

.. papis-config:: search-engine

.. papis-config:: user-agent

.. papis-config:: default-gui

.. papis-config:: scripts-short-help-regex

.. papis-config:: info-name

.. papis-config:: doc-url-key-name

.. papis-config:: file-browser

.. papis-config:: extra-bibtex-keys

.. papis-config:: extra-bibtex-types

.. papis-config:: default-library

.. papis-config:: export-text-format

.. papis-config:: match-format

.. papis-config:: header-format

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
          mark, you would use ``mark-opener-format = evince -p {mark[value]}``.
        - If you are using ``zathura``, do ``mark-opener-format = zathura -P
          {mark[value]}``.

"""
import logging

logger = logging.getLogger("config")
logger.debug("importing")

import os
import configparser
import papis.exceptions


CONFIGURATION = None #: Global configuration object variable.
DEFAULT_SETTINGS = None #: Default settings for the whole papis.
DEFAULT_MODE = "document" #: Default mode in the modal architecture.
OVERRIDE_VARS = {
    "folder": None,
    "cache": None,
    "file": None,
    "scripts": None
}


general_settings = {
    "mode"            : "document",
    "opentool"        : "xdg-open",
    "dir-umask"       : 0o755,
    "browser"         : os.environ.get('BROWSER') or 'xdg-open',
    "picktool"        : "papis.pick",
    "mvtool"          : "mv",
    "editor"          : os.environ.get('EDITOR')
                        or os.environ.get('VISUAL')
                        or 'xdg-open',
    "xeditor"         : "xdg-open",
    "sync-command"    : "git -C {lib[dir]} pull origin master",
    "notes-name"      : "notes.tex",
    "format-doc-name" : "doc",
    "use-cache"       : True,
    "cache-dir"       : \
        os.path.join(os.environ.get('XDG_CACHE_HOME'), 'papis') if
        os.environ.get('XDG_CACHE_HOME') else \
        os.path.join(os.path.expanduser('~'), '.cache', 'papis'),
    "use-git"         : False,

    "add-confirm"     : False,
    "add-name"        : "",
    "add-interactive" : False,
    "add-edit"        : False,
    "add-open"        : False,

    "check-keys"      : 'files',
    "browse-query-format"   : "{doc[title]} {doc[author]}",
    "search-engine"   : "https://duckduckgo.com",
    "user-agent"      : \
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)',
    "default-gui"     : "vim",
    "scripts-short-help-regex": ".*papis-short-help: *(.*)",
    "info-name"       : "info.yaml",
    "doc-url-key-name": "doc_url",

    "open-mark": False,
    "mark-key-name": "marks",
    "mark-format-name": "mark",
    "mark-header-format": "{mark[name]} - {mark[value]}",
    "mark-match-format": "{mark[name]} - {mark[value]}",
    "mark-opener-format": "xdg-open",

    "file-browser"    : "xdg-open",
    "extra-bibtex-keys" : "",
    "extra-bibtex-types" : "",
    "default-library" : "papers",
    "export-text-format" : \
        "{doc[author]}. {doc[title]}. {doc[journal]} {doc[pages]}"
        " {doc[month]} {doc[year]}",
    "match-format"    : \
        "{doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}",
    "header-format"   : \
        "{doc[title]:<70.70}|{doc[author]:<20.20} ({doc[year]:-<4})",
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
    """
    return os.environ.get('XDG_CONFIG_HOME') or \
        os.path.join(os.path.expanduser('~'), '.config')


def get_config_dirs():
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
    """General getter method that will be specialised for different modules.

    :param data_type: The data type that should be expected for the value of
        the variable.
    :type  data_type: DataType, e.g. int, src ...
    :param default: Default value for the configuration variable if it is not set.
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


def in_mode(mode):
    """Get mode of the library. In principle every library can have a mode,
    and depending on the mode some extra options can be offered.

    :param mode: Name of the mode used.
    :type  mode: str
    :returns: Return true if mode matches
    :rtype: bool
    """
    current_mode = get("mode")
    logger.debug("current_mode = %s" % current_mode)
    return mode == current_mode


def get_configuration():
    """Get the configuratoin object, if no papis configuration has ever been
    initialized, it initializes one. Only one configuration per process should
    ever be configurated.

    :returns: Configuration object
    :rtype:  papis.config.Configuration
    """
    global CONFIGURATION
    if CONFIGURATION is None:
        logger.debug("Creating configuration")
        CONFIGURATION = Configuration()
    return CONFIGURATION


def get_lib():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str
    >>> papis.api.set_lib('hello-world')
    >>> get_lib()
    'hello-world'
    """
    import papis.commands
    try:
        lib = papis.commands.get_args().lib
    except AttributeError:
        try:
            lib = os.environ["PAPIS_LIB"]
        except KeyError:
            # Do not put papis.config.get because get is a special function
            # that also needs the library to see if some key was overriden!
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
    logger.debug("Reseting configuration")
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

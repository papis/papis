import sys
import os
import configparser
import papis.exceptions
import logging
from collections import OrderedDict

logger = logging.getLogger("config")
logger.debug("importing")


_EXTERNAL_PICKER = None  #: Picker to set externally
_CONFIGURATION = None  #: Global configuration object variable.
_DEFAULT_SETTINGS = None  #: Default settings for the whole papis.
_OVERRIDE_VARS = {
    "folder": None,
    "cache": None,
    "file": None,
    "scripts": None
}


def get_default_opener():
    """Get the default file opener for the current system
    """
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

    "browse-key": 'url',
    "browse-query-format": "{doc[title]} {doc[author]}",
    "search-engine": "https://duckduckgo.com",
    "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)',
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
    "bibtex-journal-key": 'journal',
    "extra-bibtex-keys": "[]",
    "extra-bibtex-types": "[]",
    "default-library": "papers",
    "export-text-format":
        "{doc[author]}. {doc[title]}. {doc[journal]} {doc[pages]}"
        " {doc[month]} {doc[year]}",
    "format-doc-name": "doc",
    "match-format":
        "{doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}",
    "format-jinja2-enable": False,
    "header-format-file": None,
    "header-format": (
        "<ansired>{doc.html_escape[title]}</ansired>\n"
        " <ansigreen>{doc.html_escape[author]}</ansigreen>\n"
        "  <blue>({doc.html_escape[year]})</blue> "
        "[<ansiyellow>{doc.html_escape[tags]}</ansiyellow>]"
    ),

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

    "citation-string": "*",
    'unique-document-keys': "['doi','ref','isbn','isbn10','url','doc_url']",

    "downloader-proxy": None,
    "bibtex-unicode": False,

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

    """
    global _DEFAULT_SETTINGS
    # We use an OrderedDict so that the first entry will always be the general
    # settings, also good for automatic documentation
    if _DEFAULT_SETTINGS is None:
        _DEFAULT_SETTINGS = OrderedDict()
        _DEFAULT_SETTINGS.update({
            get_general_settings_name(): general_settings,
        })
        import papis.tui
        _DEFAULT_SETTINGS.update(papis.tui.get_default_settings())
    if not section and not key:
        return _DEFAULT_SETTINGS
    elif not section:
        return _DEFAULT_SETTINGS[get_general_settings_name()][key]
    else:
        return _DEFAULT_SETTINGS[section][key]


def register_default_settings(settings_dictionary):
    """Register configuration settings into the global configuration registry.

    Notice that you can define sections or global options. For instance,
    let us suppose that a script called ``hubation`` defines some
    configuration options. In the script there could be the following defined

    ::

        import papis.config
        options = {'hubation': { 'command': 'open'}}
        papis.config.register_default_settings(options)

    and later on the script can use these options as:

    ::

        papis.config.get('command', section='hubation')

    :param settings_dictionary: A dictionary with settings
    :type  settings_dictionary: dict
    """
    default_settings = get_default_settings()
    # we do a for loop because apparently the OrderedDict removes all
    # key-val fields after updating, so we have to do it by hand
    for section in settings_dictionary.keys():
        if section in default_settings.keys():
            default_settings[section].update(settings_dictionary[section])
        else:
            default_settings[section] = settings_dictionary[section]


def get_config_home():
    """Returns the base directory relative to which user specific configuration
    files should be stored.

    :returns: Configuration base directory
    :rtype:  str
    """
    xdg_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_home:
        return os.path.expanduser(xdg_home)
    else:
        return os.path.join(os.path.expanduser('~'), '.config')


def get_config_dirs():
    """Get papis configuration directories where the configuration
    files might be stored
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
    global _OVERRIDE_VARS
    if _OVERRIDE_VARS["file"] is not None:
        config_file = _OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(
            get_config_folder(), "config"
        )
    logger.debug("Getting config file %s" % config_file)
    return config_file


def set_config_file(filepath):
    """Override the main configuration file path
    """
    global _OVERRIDE_VARS
    logger.debug("Setting config file to %s" % filepath)
    _OVERRIDE_VARS["file"] = filepath


def set_external_picker(picker):
    global _EXTERNAL_PICKER
    _EXTERNAL_PICKER = picker


def get_external_picker():
    global _EXTERNAL_PICKER
    return _EXTERNAL_PICKER


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
    """
    config = get_configuration()
    if not config.has_section(section or "settings"):
        config.add_section(section or "settings")
    config[section or get_general_settings_name()][key] = str(val)


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
        except KeyError:
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


def getlist(key, **kwargs):
    """Bool getter

    :returns: A python list
    :rtype:  list
    :raises SyntaxError: Whenever the parsed syntax is either not a valid
        python object or a valid python list.
    """
    rawvalue = general_get(key, **kwargs)
    if isinstance(rawvalue, list):
        return rawvalue
    try:
        value = eval(rawvalue)
    except Exception as e:
        raise SyntaxError(
            "The key '{0}' must be a valid python object\n\t{1}".format(key, e)
        )
    else:
        if not isinstance(value, list):
            raise SyntaxError(
                "The key '{0}' must be a valid python list".format(key)
            )
        return value


def get_configuration():
    """Get the configuration object, if no papis configuration has ever been
    initialized, it initializes one. Only one configuration per process should
    ever be configured.

    :returns: Configuration object
    :rtype:  papis.config.Configuration
    """
    global _CONFIGURATION
    if _CONFIGURATION is None:
        logger.debug("Creating configuration")
        _CONFIGURATION = Configuration()
        # Handle local configuration file, and merge it if it exists
        local_config_file = papis.config.get("local-config-file")
        merge_configuration_from_path(local_config_file, _CONFIGURATION)
    return _CONFIGURATION


def merge_configuration_from_path(path, configuration):
    """
    Merge information of a configuration file found in `path`
    to the information of the configuration object stored in `configuration`.

    :param path: Path to the configuration file
    :type  path: str
    :param configuration: Configuration object
    :type  configuration: papis.config.Configuration
    """
    logger.debug("Merging configuration from " + path)
    configuration.read(path)
    configuration.handle_includes()


def set_lib(library):
    """Set library, notice that in principle library can be a full path.

    :param library: Library name or path to a papis library
    :type  library: str

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
    os.environ["PAPIS_LIB"] = library
    os.environ["PAPIS_LIB_DIR"] = get('dir')


def get_lib():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str
    """
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
    global _CONFIGURATION
    if _CONFIGURATION is not None:
        logger.warning("Overwriting previous configuration")
    _CONFIGURATION = None
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

    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.dir_location = get_config_folder()
        self.scripts_location = get_scripts_folder()
        self.file_location = get_config_file()
        self.logger = logging.getLogger("Configuration")
        self.initialize()

    def handle_includes(self):
        if "include" in self.keys():
            for name in self["include"]:
                self.logger.debug("including %s" % name)
                fullpath = os.path.expanduser(self.get("include", name))
                if os.path.exists(fullpath):
                    self.read(fullpath)
                else:
                    self.logger.warn(
                        "{0} not included because it does not exist".format(
                            fullpath
                        )
                    )

    def initialize(self):
        if not os.path.exists(self.dir_location):
            self.logger.warning(
                'Creating configuration folder in %s' % self.dir_location
            )
            os.makedirs(self.dir_location)
        if not os.path.exists(self.scripts_location):
            os.makedirs(self.scripts_location)
        if os.path.exists(self.file_location):
            self.logger.debug(
                'Reading configuration from {0}'.format(self.file_location)
            )
            self.read(self.file_location)
            self.handle_includes()
        else:
            for section in self.default_info:
                self[section] = {}
                for field in self.default_info[section]:
                    self[section][field] = self.default_info[section][field]
            with open(self.file_location, "w") as configfile:
                self.write(configfile)

import sys
import os
from os.path import expanduser
import configparser
import papis.exceptions
import papis.library
import logging
from typing import Dict, Any, List, Optional, Callable  # noqa: ignore

PapisConfigType = Dict[str, Dict[str, Any]]

logger = logging.getLogger("config")
logger.debug("importing")

_CURRENT_LIBRARY = None  #: Current library in use
_CONFIGURATION = None  # type: Optional[Configuration]
_DEFAULT_SETTINGS = None  # type: Optional[PapisConfigType]
_OVERRIDE_VARS = {
    "folder": None,
    "file": None,
    "scripts": None
}  # type: Dict[str, Optional[str]]


def get_default_opener() -> str:
    """Get the default file opener for the current system
    """
    if sys.platform.startswith('darwin'):
        return "open"
    elif os.name == 'nt':
        return "start"
    else:
        return "xdg-open"


general_settings = {
    "local-config-file": ".papis.config",
    "database-backend": "papis",
    "default-query-string": ".",
    "sort-field": None,

    "opentool": get_default_opener(),
    "dir-umask": 0o755,
    "browser": os.environ.get('BROWSER') or get_default_opener(),
    "picktool": "papis",
    "mvtool": "mv",
    "editor": os.environ.get('EDITOR')
                        or os.environ.get('VISUAL')
                        or get_default_opener(),
    "notes-name": "notes.tex",
    "use-cache": True,
    "cache-dir": None,
    "use-git": False,

    "add-confirm": False,
    "add-folder-name": "",
    "add-file-name": None,
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
    "format-doc-name": "doc",
    "match-format":
        "{doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}",
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
    "multiple-authors-format": "{au[family]}, {au[given]}",

    "whoosh-schema-fields": "['doi']",
    "whoosh-schema-prototype":
    '{\n'
    '"author": TEXT(stored=True),\n'
    '"title": TEXT(stored=True),\n'
    '"year": TEXT(stored=True),\n'
    '"tags": TEXT(stored=True),\n'
    '}',

    'unique-document-keys': "['doi','ref','isbn','isbn10','url','doc_url']",

    "downloader-proxy": None,
    "bibtex-unicode": False,

    "time-stamp": True,

    "document-description-format": '{doc[title]} - {doc[author]}',
    "formater": "python",

}


def get_general_settings_name() -> str:
    """Get the section name of the general settings
    :returns: Section's name
    :rtype:  str
    >>> get_general_settings_name()
    'settings'
    """
    return "settings"


class Configuration(configparser.ConfigParser):

    def __init__(self) -> None:
        configparser.ConfigParser.__init__(self)
        self.dir_location = get_config_folder()
        self.scripts_location = get_scripts_folder()
        self.file_location = get_config_file()
        self.logger = logging.getLogger("Configuration")
        self.default_info = {
          "papers": {
            'dir': '~/Documents/papers'
          },
          get_general_settings_name(): {
            'default-library': 'papers'
          }
        }  # type: PapisConfigType
        self.initialize()

    def handle_includes(self) -> None:
        if "include" in self.keys():
            for name in self["include"]:
                self.logger.debug("including %s" % name)
                fullpath = os.path.expanduser(self.get("include", name))
                if os.path.exists(fullpath):
                    self.read(fullpath)
                else:
                    self.logger.warning(
                        "{0} not included because it does not exist"
                        .format(fullpath))

    def initialize(self) -> None:
        if not os.path.exists(self.dir_location):
            self.logger.warning(
                'Creating configuration folder in {0}'
                .format(self.dir_location))
            os.makedirs(self.dir_location)
        if not os.path.exists(self.scripts_location):
            os.makedirs(self.scripts_location)
        if os.path.exists(self.file_location):
            self.logger.debug(
                'Reading configuration from {0}'.format(self.file_location))
            self.read(self.file_location)
            self.handle_includes()
        else:
            for section in self.default_info:
                self[section] = {}
                for field in self.default_info[section]:
                    self[section][field] = self.default_info[section][field]
            with open(self.file_location, "w") as configfile:
                self.logger.info('Creating config file at {0}'
                                 .format(self.file_location))
                self.write(configfile)
        configpy = get_configpy_file()
        if os.path.exists(configpy):
            self.logger.debug('Executing {0}'.format(configpy))
            with open(configpy) as fd:
                exec(fd.read())


def get_default_settings() -> PapisConfigType:
    """Get the default settings for all non-user variables
    in papis.

    """
    global _DEFAULT_SETTINGS
    # We use an OrderedDict so that the first entry will always be the general
    # settings, also good for automatic documentation
    if _DEFAULT_SETTINGS is None:
        _DEFAULT_SETTINGS = dict()
        _DEFAULT_SETTINGS.update({
            get_general_settings_name(): general_settings,
        })
        import papis.tui
        _DEFAULT_SETTINGS.update(papis.tui.get_default_settings())
    return _DEFAULT_SETTINGS


def register_default_settings(settings_dictionary: PapisConfigType) -> None:
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


def get_config_home() -> str:
    """Returns the base directory relative to which user specific configuration
    files should be stored.

    :returns: Configuration base directory
    :rtype:  str
    """
    xdg_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_home:
        return expanduser(xdg_home)
    else:
        return os.path.join(expanduser('~'), '.config')


def get_config_dirs() -> List[str]:
    """Get papis configuration directories where the configuration
    files might be stored
    """
    dirs = []  # type: List[str]
    # get_config_home should also be included on top of XDG_CONFIG_DIRS
    if os.environ.get('XDG_CONFIG_DIRS') is not None:
        dirs += [
            os.path.join(d, 'papis') for d in
            os.environ.get('XDG_CONFIG_DIRS', '').split(':')]
    # Take XDG_CONFIG_HOME and $HOME/.papis for backwards
    # compatibility
    dirs += [
        os.path.join(get_config_home(), 'papis'),
        os.path.join(expanduser('~'), '.papis')]
    return dirs


def get_config_folder() -> str:
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


def get_config_file() -> str:
    """Get the path of the main configuration file,
    e.g. /home/user/.papis/config
    """
    global _OVERRIDE_VARS
    if _OVERRIDE_VARS["file"] is not None:
        config_file = _OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(get_config_folder(), "config")
    logger.debug("Getting config file %s" % config_file)
    return config_file


def get_configpy_file() -> str:
    """Get the path of the main python configuration file,
    e.g. /home/user/config/.papis/config.py
    """
    return os.path.join(get_config_folder(), "config.py")


def set_config_file(filepath: str) -> None:
    """Override the main configuration file path
    """
    global _OVERRIDE_VARS
    logger.debug("Setting config file to %s" % filepath)
    _OVERRIDE_VARS["file"] = filepath


def get_scripts_folder() -> str:
    """Get folder where the scripts are stored,
    e.g. /home/user/.papis/scripts
    """
    return os.path.join(get_config_folder(), "scripts")


def set(key: str, val: Any, section: Optional[str] = None) -> None:
    """Set a key to val in some section and make these changes available
    everywhere.
    """
    config = get_configuration()
    if not config.has_section(section or "settings"):
        config.add_section(section or "settings")
    config[section or get_general_settings_name()][key] = str(val)


def general_get(key: str, section: Optional[str] = None,
                data_type: Optional[Any] = None) -> Optional[Any]:
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
    method = None  # type: Optional[Callable[[Any, Any], Any]]
    value = None  # type: Optional[Any]
    config = get_configuration()
    libname = get_lib_name()
    global_section = get_general_settings_name()
    specialized_key = section + "-" + key if section is not None else key
    extras = [(section, key)] if section is not None else []
    sections = [(global_section, specialized_key)] +\
        extras + [(libname, specialized_key)]
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


def get(key: str, section: Optional[str] = None) -> Optional[Any]:
    """String getter
    """
    return general_get(key, section=section)


def getint(key: str, section: Optional[str] = None) -> Optional[int]:
    """Integer getter
    >>> set('something', 42)
    >>> getint('something')
    42
    """
    return general_get(key, section=section, data_type=int)


def getfloat(key: str, section: Optional[str] = None) -> Optional[float]:
    """Float getter
    >>> set('something', 0.42)
    >>> getfloat('something')
    0.42
    """
    return general_get(key, section=section, data_type=float)


def getboolean(key: str, section: Optional[str] = None) -> Optional[bool]:
    """Bool getter
    >>> set('add-open', True)
    >>> getboolean('add-open')
    True
    """
    return general_get(key, section=section, data_type=bool)


def getstring(key: str, section: Optional[str] = None) -> str:
    """String getter
    >>> set('add-open', "hello world")
    >>> getstring('add-open')
    'hello world'
    """
    result = general_get(key, section=section, data_type=str)
    if not isinstance(result, str):
        raise ValueError("Key {0} should be a string".format(key))
    return str(result)


def getlist(key: str, section: Optional[str] = None) -> List[str]:
    """List getter

    :returns: A python list
    :rtype:  list
    :raises SyntaxError: Whenever the parsed syntax is either not a valid
        python object or a valid python list.
    """
    rawvalue = general_get(key, section=section)  # type: Any
    if isinstance(rawvalue, list):
        return list(map(str, rawvalue))
    try:
        rawvalue = eval(rawvalue)
    except Exception as e:
        raise SyntaxError(
            "The key '{0}' must be a valid python object\n\t{1}"
            .format(key, e))
    else:
        if not isinstance(rawvalue, list):
            raise SyntaxError(
                "The key '{0}' must be a valid python list".format(key))
        return list(map(str, rawvalue))


def get_configuration() -> Configuration:
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


def merge_configuration_from_path(path: Optional[str],
                                  configuration: Configuration) -> None:
    """
    Merge information of a configuration file found in `path`
    to the information of the configuration object stored in `configuration`.

    :param path: Path to the configuration file
    :type  path: str
    :param configuration: Configuration object
    :type  configuration: papis.config.Configuration
    """
    if path is None or not os.path.exists(path):
        return
    logger.debug("Merging configuration from " + path)
    configuration.read(path)
    configuration.handle_includes()


def set_lib(library: papis.library.Library) -> None:
    """Set library

    :param library: Library object
    :type  library: papis.library.Library

    """
    global _CURRENT_LIBRARY
    config = get_configuration()
    if library.name not in config.keys():
        config[library.name] = dict(dirs=str(library.paths))
    _CURRENT_LIBRARY = library


def set_lib_from_name(libname: str) -> None:
    """Set library, notice that in principle library can be a full path.

    :param libname: Name of the library or some path to a folder
    :type  libname: str
    """
    set_lib(get_lib_from_name(libname))


def get_lib_from_name(libname: str) -> papis.library.Library:
    config = get_configuration()
    if libname not in config.keys():
        if os.path.isdir(libname):
            # Check if the path exists, then use this path as a new library
            logger.warning("Since the path '{0}' exists, "
                           "I'm interpreting it as a library"
                           .format(libname))
            library_obj = papis.library.from_paths([libname])
            name = library_obj.path_format()
            # the configuration object can only store strings
            config[name] = dict(dirs=str(library_obj.paths))
        else:
            raise Exception("Library '{0}' does not seem to exist"
                            "\n\n"
                            "To add a library simply write the following"
                            "in your configuration file located at '{cpath}'"
                            "\n\n"
                            "\t[{0}]\n"
                            "\tdir = path/to/your/{0}/folder"
                            .format(libname, cpath=get_config_file()))
    else:
        try:
            paths = [expanduser(config[libname]['dir'])]
        except KeyError:
            try:
                paths = eval(expanduser(config[libname].get('dirs')))
            except Exception as e:
                raise Exception("To define a library you have to set either"
                                " dir or dirs in the configuration file.\n"
                                "\tdir must be a path to a single folder.\n"
                                "\tdirs must be a python list of "
                                "paths to folders.\n\n"
                                "Error: ({0})"
                                .format(e))
        library_obj = papis.library.Library(libname, paths)
    return library_obj


def get_lib_dirs() -> List[str]:
    """Get the directories of the current library

    :returns: A list of paths
    :rtype:  list
    """
    return get_lib().paths


def get_lib_name() -> str:
    return get_lib().name


def get_lib() -> papis.library.Library:
    """Get current library, if there is no library set before,
    the default library will be retrieved.
    If the `PAPIS_LIB` environment variable is defined, this is the
    library name (or path) that will be taken as a default.

    :returns: Current library
    :rtype:  papis.library.Library
    """
    global _CURRENT_LIBRARY
    if os.environ.get('PAPIS_LIB'):
        set_lib_from_name(os.environ['PAPIS_LIB'])
    if _CURRENT_LIBRARY is None:
        # Do not put papis.config.get because get is a special function
        # that also needs the library to see if some key was overridden!
        default_settings = get_default_settings()[get_general_settings_name()]
        lib = default_settings['default-library']
        set_lib_from_name(lib)
    assert(isinstance(_CURRENT_LIBRARY, papis.library.Library))
    return _CURRENT_LIBRARY


def reset_configuration() -> Configuration:
    """Destroys existing configuration and returns a new one.

    :returns: Configuration object
    :rtype:  papis.config.Configuration
    """
    global _CONFIGURATION
    _CONFIGURATION = None
    logger.debug("Resetting configuration")
    return get_configuration()

import os
import configparser
from typing import Dict, Any, List, Optional, Callable  # noqa: F401

import papis.exceptions
import papis.library
import papis.logging

logger = papis.logging.get_logger(__name__)

PapisConfigType = Dict[str, Dict[str, Any]]

_CURRENT_LIBRARY = None  #: Current library in use
_CONFIGURATION = None  # type: Optional[Configuration]
_DEFAULT_SETTINGS = None  # type: Optional[PapisConfigType]
_OVERRIDE_VARS = {
    "folder": None,
    "file": None,
    "scripts": None
}  # type: Dict[str, Optional[str]]


def get_general_settings_name() -> str:
    """Get the section name of the general settings
    :returns: Section's name
    >>> get_general_settings_name()
    'settings'
    """
    return "settings"


class Configuration(configparser.ConfigParser):

    def __init__(self) -> None:
        super().__init__()

        self.dir_location = get_config_folder()
        self.scripts_location = get_scripts_folder()
        self.file_location = get_config_file()
        self.default_info = {
            "papers": {
                "dir": "~/Documents/papers"
            },
            get_general_settings_name(): {
                "default-library": "papers"
            }
        }  # type: PapisConfigType
        self.initialize()

    def handle_includes(self) -> None:
        if "include" in self:
            for name in self["include"]:
                fullpath = os.path.expanduser(self.get("include", name))
                if os.path.exists(fullpath):
                    logger.debug("Including file '%s'.", name)
                    self.read(fullpath)
                else:
                    logger.warning(
                        "'%s' not included because it does not exist.",
                        fullpath)

    def initialize(self) -> None:
        # ensure all configuration directories exist
        if not os.path.exists(self.dir_location):
            logger.warning("Creating configuration folder in '%s'.", self.dir_location)
            os.makedirs(self.dir_location)

        if not os.path.exists(self.scripts_location):
            logger.warning(
                "Creating scripts folder in '%s'", self.scripts_location)
            os.makedirs(self.scripts_location)

        # load settings
        if os.path.exists(self.file_location):
            logger.debug("Reading configuration from '%s'.", self.file_location)
            try:
                self.read(self.file_location)
                self.handle_includes()
            except configparser.DuplicateOptionError as exc:
                logger.error("%s: %s", type(exc).__name__, exc, exc_info=exc)
                raise SystemExit(1)

        # if no sections were actually read, add default ones
        if not self.sections():
            logger.warning(
                "No sections were found in the configuration file. "
                "Adding default ones (with a default library named 'papers')!")

            for section in self.default_info:
                self[section] = {}
                for field in self.default_info[section]:
                    self[section][field] = self.default_info[section][field]

            with open(self.file_location, "w") as configfile:
                logger.info("Creating configuration file at '%s'.", self.file_location)
                self.write(configfile)

        # ensure the general section and default-library exist in the config
        general_section = get_general_settings_name()
        if general_section not in self:
            libs = get_libs_from_config(self)
            default_library = (
                libs[0] if libs else
                self.default_info[general_section]["default-library"])

            logger.warning(
                "No main '%s' section found in the configuration file. "
                "Setting '%s' as the default library!",
                general_section, default_library)

            self[general_section] = {"default-library": default_library}

        # evaluate the python config
        configpy = get_configpy_file()
        if os.path.exists(configpy):
            logger.debug("Executing configuration script '%s'.", configpy)
            with open(configpy) as fd:
                exec(fd.read())


def get_default_settings() -> PapisConfigType:
    """Get the default settings for all non-user variables
    in papis.

    """
    import papis.defaults
    global _DEFAULT_SETTINGS
    # We use an OrderedDict so that the first entry will always be the general
    # settings, also good for automatic documentation
    if _DEFAULT_SETTINGS is None:
        _DEFAULT_SETTINGS = {}
        _DEFAULT_SETTINGS.update({
            get_general_settings_name(): papis.defaults.settings,
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
    """
    default_settings = get_default_settings()
    # we do a for loop because apparently the OrderedDict removes all
    # key-val fields after updating, so we have to do it by hand
    for section in settings_dictionary:
        if section in default_settings:
            default_settings[section].update(settings_dictionary[section])
        else:
            default_settings[section] = settings_dictionary[section]


def get_config_home() -> str:
    """Returns the base directory relative to which user specific configuration
    files should be stored.

    :returns: Configuration base directory
    """
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return os.path.expanduser(xdg_home)
    else:
        return os.path.join(os.path.expanduser("~"), ".config")


def get_config_dirs() -> List[str]:
    """Get papis configuration directories where the configuration
    files might be stored
    """
    dirs = []  # type: List[str]
    # get_config_home should also be included on top of XDG_CONFIG_DIRS
    if os.environ.get("XDG_CONFIG_DIRS") is not None:
        dirs += [
            os.path.join(d, "papis") for d in
            os.environ.get("XDG_CONFIG_DIRS", "").split(":")]
    # Take XDG_CONFIG_HOME and $HOME/.papis for backwards
    # compatibility
    dirs += [
        os.path.join(get_config_home(), "papis"),
        os.path.join(os.path.expanduser("~"), ".papis")]
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
    return os.path.join(get_config_home(), "papis")


def get_config_file() -> str:
    """Get the path of the main configuration file,
    e.g. /home/user/.papis/config
    """
    global _OVERRIDE_VARS
    if _OVERRIDE_VARS["file"] is not None:
        config_file = _OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(get_config_folder(), "config")
    logger.debug("Getting config file '%s'.", config_file)
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
    logger.debug("Setting config file to '%s'.", filepath)
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
    :param extras: List of tuples containing section and prefixes
    """
    config = get_configuration()
    libname = get_lib_name()
    global_section = get_general_settings_name()
    default_settings = get_default_settings()

    # Check data type for setting getter method
    method = None  # type: Optional[Callable[[Any, Any], Any]]
    if data_type == int:
        method = config.getint
    elif data_type == float:
        method = config.getfloat
    elif data_type == bool:
        method = config.getboolean
    else:
        method = config.get

    # NOTE: configuration settings are given in two formats (where <section>
    # and <key> are given as arguments)
    #
    # 1. As a key under the `global_section`
    #
    #   [settings]
    #   <section>-<key> = value
    #
    # 2. In a separate section
    #
    #   [<section>]
    #   <key> = value
    #
    # 3. As a key under the current library section
    #
    #   [lib]
    #   <section>-<key> = value
    #
    # If the <section> is not given, then only the general and library settings
    # are checked.

    qualified_key = key if section is None else "{}-{}".format(section, key)
    candidate_sections = (
        # NOTE: these are in overwriting order: general < custom < lib
        [(global_section, qualified_key)]
        + ([] if section is None else [(section, key)])
        + [(libname, qualified_key)]
        )

    # Try to get key's value from configuration
    value = None  # type: Optional[Any]
    for section_name, key_name in candidate_sections:
        if section_name not in config:
            continue

        if key_name in config[section_name]:
            value = method(section_name, key_name)

    if value is None:
        try:
            return default_settings[section or global_section][key]
        except KeyError as exc:
            raise papis.exceptions.DefaultSettingValueMissing(qualified_key) from exc

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
    try:
        return general_get(key, section=section, data_type=int)
    except ValueError:
        value = general_get(key, section=section)
        raise ValueError("Key '{}' should be an integer: '{}' is of type '{}'"
                         .format(key, value, type(key).__name__))


def getfloat(key: str, section: Optional[str] = None) -> Optional[float]:
    """Float getter
    >>> set('something', 0.42)
    >>> getfloat('something')
    0.42
    """
    try:
        return general_get(key, section=section, data_type=float)
    except ValueError:
        value = general_get(key, section=section)
        raise ValueError("Key '{}' should be a float: '{}' is of type '{}'"
                         .format(key, value, type(key).__name__))


def getboolean(key: str, section: Optional[str] = None) -> Optional[bool]:
    """Bool getter
    >>> set('add-open', True)
    >>> getboolean('add-open')
    True
    """
    try:
        return general_get(key, section=section, data_type=bool)
    except ValueError:
        value = general_get(key, section=section)
        raise ValueError("Key '{}' should be a boolean: '{}' is of type '{}'"
                         .format(key, value, type(key).__name__))


def getstring(key: str, section: Optional[str] = None) -> str:
    """String getter
    >>> set('add-open', "hello world")
    >>> getstring('add-open')
    'hello world'
    """
    result = general_get(key, section=section, data_type=str)
    if not isinstance(result, str):
        raise ValueError("Key '{}' should be a string: '{}' is of type '{}'"
                         .format(key, result, type(key).__name__))

    return str(result)


def getlist(key: str, section: Optional[str] = None) -> List[str]:
    """List getter

    :returns: A python list
    :raises SyntaxError: Whenever the parsed syntax is either not a valid
        python object or a valid python list.
    """
    rawvalue = general_get(key, section=section)  # type: Any
    if isinstance(rawvalue, list):
        return list(map(str, rawvalue))
    try:
        rawvalue = eval(rawvalue)
    except Exception:
        raise SyntaxError(
            "The key '{}' must be a valid Python object: {}"
            .format(key, rawvalue))
    else:
        if not isinstance(rawvalue, list):
            raise SyntaxError(
                "The key '{}' must be a valid Python list. Got: {} (type {!r})"
                .format(key, rawvalue, type(rawvalue).__name__))

        return list(map(str, rawvalue))


def get_configuration() -> Configuration:
    """Get the configuration object, if no papis configuration has ever been
    initialized, it initializes one. Only one configuration per process should
    ever be configured.

    :returns: Configuration object
    """
    global _CONFIGURATION
    if _CONFIGURATION is None:
        logger.debug("Creating configuration.")
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
    :param configuration: Configuration object
    """
    if path is None or not os.path.exists(path):
        return
    logger.debug("Merging configuration from '%s'.", path)
    configuration.read(path)
    configuration.handle_includes()


def set_lib(library: papis.library.Library) -> None:
    """Set library

    :param library: Library object
    """
    global _CURRENT_LIBRARY
    config = get_configuration()
    if library.name not in config:
        config[library.name] = {"dirs": str(library.paths)}
    _CURRENT_LIBRARY = library


def set_lib_from_name(libname: str) -> None:
    """Set library, notice that in principle library can be a full path.

    :param libname: Name of the library or some path to a folder
    """
    set_lib(get_lib_from_name(libname))


def get_lib_from_name(libname: str) -> papis.library.Library:
    config = get_configuration()
    if libname not in config:
        if os.path.isdir(libname):
            # Check if the path exists, then use this path as a new library
            logger.warning("Setting path '%s' as the main library folder.", libname)
            library_obj = papis.library.from_paths([libname])
            name = library_obj.path_format()
            # the configuration object can only store strings
            config[name] = {"dirs": str(library_obj.paths)}
        else:
            raise RuntimeError("Library '{0}' does not seem to exist"
                               "\n\n"
                               "To add a library simply write the following"
                               " in your configuration file located at '{cpath}'"
                               "\n\n"
                               "\t[{0}]\n"
                               "\tdir = path/to/your/{0}/folder"
                               .format(libname, cpath=get_config_file()))
    else:
        try:
            paths = [os.path.expanduser(config[libname]["dir"])]
        except KeyError:
            try:
                paths = eval(os.path.expanduser(config[libname].get("dirs")))
            except Exception as e:
                raise RuntimeError(
                    "To define a library you have to set either 'dir' or 'dirs' "
                    "in the configuration file.\n"
                    "\t'dir' must be a path to an existing folder.\n"
                    "\t'dirs' must be a python list of paths.\n\n"
                    "Error: {}".format(e))
        library_obj = papis.library.Library(libname, paths)
    return library_obj


def get_lib_dirs() -> List[str]:
    """Get the directories of the current library

    :returns: A list of paths
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
    """
    global _CURRENT_LIBRARY
    if os.environ.get("PAPIS_LIB"):
        set_lib_from_name(os.environ["PAPIS_LIB"])
    if _CURRENT_LIBRARY is None:
        # NOTE: this cannot use `general_get` (cyclic dependency), so we have
        # to handle the `default-library` not being present in the user config
        config = papis.config.get_configuration()
        settings_name = get_general_settings_name()

        settings = config[settings_name]
        if "default-library" in settings:
            lib = settings["default-library"]
        else:
            default_settings = get_default_settings()[settings_name]
            lib = default_settings["default-library"]

        set_lib_from_name(lib)
    assert isinstance(_CURRENT_LIBRARY, papis.library.Library)
    return _CURRENT_LIBRARY


def get_libs() -> List[str]:
    return get_libs_from_config(get_configuration())


def get_libs_from_config(config: Configuration) -> List[str]:
    libs = []
    for section in config:
        sec = config[section]
        if "dir" in sec or "dirs" in sec:
            libs.append(section)

    return libs


def reset_configuration() -> Configuration:
    """Destroys existing configuration and returns a new one.

    :returns: Configuration object
    """
    global _CONFIGURATION
    _CONFIGURATION = None
    logger.debug("Resetting configuration.")
    return get_configuration()

import os
import configparser
from typing import Dict, Any, List, Optional, Callable  # noqa: F401

import papis.exceptions
import papis.library
import papis.logging

logger = papis.logging.get_logger(__name__)

PapisConfigType = Dict[str, Dict[str, Any]]

CURRENT_LIBRARY = None
CURRENT_CONFIGURATION: Optional["Configuration"] = None

DEFAULT_SETTINGS: Optional[PapisConfigType] = None
OVERRIDE_VARS: Dict[str, Optional[str]] = {
    "folder": None,
    "file": None,
    "scripts": None
}

GENERAL_SETTINGS_NAME = "settings"


def get_general_settings_name() -> str:
    """Get the section name of the general settings.

        >>> get_general_settings_name()
        'settings'
    """

    return GENERAL_SETTINGS_NAME


class Configuration(configparser.ConfigParser):
    """A subclass of :class:`configparser.ConfigParser` with custom defaults.

    This class automatically reads the configuration file and imports any
    required scripts. If no file exists, a default one is created.

    Use :func:`get_configuration` to instantiate this class instead of calling it
    directly.
    """

    def __init__(self) -> None:
        super().__init__()

        self.dir_location: str = get_config_folder()
        self.scripts_location: str = get_scripts_folder()
        self.file_location: str = get_config_file()
        self.default_info: PapisConfigType = {
            "papers": {
                "dir": "~/Documents/papers"
            },
            GENERAL_SETTINGS_NAME: {
                "default-library": "papers"
            }
        }
        self.initialize()

    def handle_includes(self) -> None:
        if "include" not in self:
            return

        for name in self["include"]:
            fullpath = os.path.expanduser(self.get("include", name))
            if os.path.exists(fullpath):
                logger.debug("Including file '%s'.", name)
                self.read(fullpath)
            else:
                logger.warning("'%s' not included because it does not exist.",
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
        if GENERAL_SETTINGS_NAME not in self:
            libs = get_libs_from_config(self)
            default_library = (
                libs[0] if libs else
                self.default_info[GENERAL_SETTINGS_NAME]["default-library"])

            logger.warning(
                "No main '%s' section found in the configuration file. "
                "Setting '%s' as the default library!",
                GENERAL_SETTINGS_NAME, default_library)

            self[GENERAL_SETTINGS_NAME] = {"default-library": default_library}

        # evaluate the python config
        configpy = get_configpy_file()
        if os.path.exists(configpy):
            logger.debug("Executing configuration script '%s'.", configpy)
            with open(configpy) as fd:
                exec(fd.read())


def get_default_settings() -> PapisConfigType:
    """Get the default settings for all non-user variables.

    Additional user variables can be registered using
    :func:`register_default_settings` and will be included in this
    dictionary.
    """

    global DEFAULT_SETTINGS

    if DEFAULT_SETTINGS is None:
        DEFAULT_SETTINGS = {}

        import papis.defaults
        DEFAULT_SETTINGS.update({
            GENERAL_SETTINGS_NAME: papis.defaults.settings,
        })

        import papis.tui
        DEFAULT_SETTINGS.update(papis.tui.get_default_settings())

    return DEFAULT_SETTINGS


def register_default_settings(settings_dictionary: PapisConfigType) -> None:
    """Register configuration settings into the global configuration registry.

    Notice that you can define sections or global options. For instance,
    let us suppose that a script called ``foobar`` defines some
    configuration options. In the script there could be the following defined

    .. code:: python

        import papis.config

        options = {"foobar": { "command": "open"}}
        papis.config.register_default_settings(options)

    which can then be accessed globally through

    .. code:: python

        papis.config.get("command", section="foobar")

    :param settings_dictionary: a dictionary of configuration settings, where
        the first level of keys defines the sections and the second level
        defines the actual configuration settings.
    """
    default_settings = get_default_settings()

    # NOTE: this updates existing sections in place
    for section, settings in settings_dictionary.items():
        if section in default_settings:
            default_settings[section].update(settings)
        else:
            default_settings[section] = settings


def get_config_home() -> str:
    """
    :returns: the base directory relative to which user specific configuration
        files should be stored.
    """
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return os.path.expanduser(xdg_home)
    else:
        return os.path.join(os.path.expanduser("~"), ".config")


def get_config_dirs() -> List[str]:
    """
    :returns: a list of directories where the configuration files might be stored.
    """
    dirs: List[str] = []

    # get_config_home should also be included on top of XDG_CONFIG_DIRS
    config_dirs = os.environ.get("XDG_CONFIG_DIRS")
    if config_dirs:
        dirs += [os.path.join(d, "papis") for d in config_dirs.split(":")]

    # NOTE: Take XDG_CONFIG_HOME and $HOME/.papis for backwards compatibility
    dirs += [
        os.path.join(get_config_home(), "papis"),
        os.path.join(os.path.expanduser("~"), ".papis")]

    return dirs


def get_config_folder() -> str:
    """Get the main configuration folder.

    :returns: the folder where the configuration files are stored, e.g.
        ``$HOME/.config/papis``, by looking in the directories returned by
        :func:`get_config_dirs`.
    """
    config_dirs = get_config_dirs()

    for config_dir in config_dirs:
        if os.path.exists(config_dir):
            return config_dir

    # NOTE: If no folder is found, then get the config home
    return os.path.join(get_config_home(), "papis")


def get_config_file() -> str:
    """Get the main configuration file.

    This file can be changed by :func:`set_config_file`.

    :returns: the path of the main configuration file, e.g. ``$CONFIG_FOLDER/config``,
        in the directory returned by :func:`get_config_folder`.
    """

    global OVERRIDE_VARS
    if OVERRIDE_VARS["file"] is not None:
        config_file = OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(get_config_folder(), "config")

    logger.debug("Getting config file '%s'.", config_file)
    return config_file


def set_config_file(filepath: str) -> None:
    """Override the main configuration file."""
    global OVERRIDE_VARS

    logger.debug("Setting config file to '%s'.", filepath)
    OVERRIDE_VARS["file"] = filepath


def get_configpy_file() -> str:
    """
    :returns: the path of the main Python configuration file, e.g.
        ``$CONFIG_FOLDER/config.py``.
    """
    return os.path.join(get_config_folder(), "config.py")


def get_scripts_folder() -> str:
    """
    :returns: the folder where the scripts are stored, e.g. ``$CONFIG_FOLDER/scripts``.
    """
    return os.path.join(get_config_folder(), "scripts")


def set(key: str, value: Any, section: Optional[str] = None) -> None:
    """Set a key in the configuration.

    :param key: the name of the key to set.
    :param value: the value to set it to, which can be any value understood
        by the :class:`Configuration`.
    :param section: the name of the section to set the key in.
    """
    config = get_configuration()
    section = GENERAL_SETTINGS_NAME if section is None else section

    if not config.has_section(section):
        config.add_section(section)

    config[section][key] = str(value)


def general_get(key: str,
                section: Optional[str] = None,
                data_type: Optional[type] = None) -> Optional[Any]:
    """Get the value for a given *key* in *section*.

    This function is a bit more general than the get from :class:`Configuration`
    (see :meth:`configparser.ConfigParser.get`). In particular it supports

    * Providing the *key* and *section*, in which case it will retrieve the
      key from that section directly.

    * The *key* has the format ``<section>-<key>`` and no section is specified.
      In this case, the full key is expected to be in the general settings
      section or a library section.

    The priority of the search is given by

    1. The key is retrieved from a library section.
    2. The key is retrieved from the given *section*, if any.
    3. The key is retrieved from the general section.

    :param key: a key in the configuration file to retrieve.
    :param section: a section from which to retrieve the key, which defaults to
        :func:`get_general_settings_name`.
    :param data_type: the data type that should be expected for the value of
        the variable.
    """
    config = get_configuration()
    libname = get_lib_name()
    global_section = get_general_settings_name()
    default_settings = get_default_settings()

    # Check data type for setting getter method
    method: Callable[[Any, Any], Any]
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
    value: Any = None
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
    """Retrieve a general value (can be *None*) from the configuration file."""
    return general_get(key, section=section)


def getint(key: str, section: Optional[str] = None) -> Optional[int]:
    """Retrieve an integer value from the configuration file.

        >>> set("something", 42)
        >>> getint("something")
        42
    """
    try:
        return general_get(key, section=section, data_type=int)
    except ValueError:
        value = general_get(key, section=section)
        raise ValueError("Key '{}' should be an integer: '{}' is of type '{}'"
                         .format(key, value, type(key).__name__))


def getfloat(key: str, section: Optional[str] = None) -> Optional[float]:
    """Retrieve an floating point value from the configuration file.

        >>> set("something", 0.42)
        >>> getfloat("something")
        0.42
    """
    try:
        return general_get(key, section=section, data_type=float)
    except ValueError:
        value = general_get(key, section=section)
        raise ValueError("Key '{}' should be a float: '{}' is of type '{}'"
                         .format(key, value, type(key).__name__))


def getboolean(key: str, section: Optional[str] = None) -> Optional[bool]:
    """Retrieve a boolean value from the configuration file.

        >>> set("add-open", True)
        >>> getboolean("add-open")
        True
    """
    try:
        return general_get(key, section=section, data_type=bool)
    except ValueError:
        value = general_get(key, section=section)
        raise ValueError("Key '{}' should be a boolean: '{}' is of type '{}'"
                         .format(key, value, type(key).__name__))


def getstring(key: str, section: Optional[str] = None) -> str:
    """Retrieve a string value from the configuration file.

        >>> set("add-open", "hello world")
        >>> getstring("add-open")
        'hello world'
    """
    result = general_get(key, section=section, data_type=str)
    if not isinstance(result, str):
        raise ValueError("Key '{}' should be a string: '{}' is of type '{}'"
                         .format(key, result, type(key).__name__))

    return str(result)


def getlist(key: str, section: Optional[str] = None) -> List[str]:
    """Retrieve a list value from the configuration file.

    This function uses :func:`eval` to execute a the string present in the
    configuration file into a Python list. This can be unsafe if the list
    contains unknown code.

        >>> set("tags", "['a', 'b', 'c']")
        >>> getlist("tags")
        ['a', 'b', 'c']

    :raises SyntaxError: Whenever the parsed syntax is either not a valid
        python object or not a valid python list.
    """
    rawvalue: Any = general_get(key, section=section)
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
    """Get the configuration object,

    If no configuration has been initialized, it initializes one. Only one
    configuration per process should ever be configured.
    """
    global CURRENT_CONFIGURATION

    if CURRENT_CONFIGURATION is None:
        logger.debug("Creating configuration.")
        CURRENT_CONFIGURATION = Configuration()

        # Handle local configuration file, and merge it if it exists
        local_config_file = papis.config.get("local-config-file")
        merge_configuration_from_path(local_config_file, CURRENT_CONFIGURATION)

    return CURRENT_CONFIGURATION


def merge_configuration_from_path(path: Optional[str],
                                  configuration: Configuration) -> None:
    """Merge information of a configuration file found in *path* into *configuration*.

    :param path: a path to a configuration file.
    :param configuration: an existing :class:`Configuration` object.
    """

    if path is None or not os.path.exists(path):
        return

    logger.debug("Merging configuration from '%s'.", path)
    configuration.read(path)
    configuration.handle_includes()


def set_lib(library: papis.library.Library) -> None:
    """Set the current library."""

    global CURRENT_LIBRARY
    config = get_configuration()

    if library.name not in config:
        # NOTE: can't use set(...) here due to cyclic dependencies
        config[library.name] = {"dirs": str(library.paths)}

    CURRENT_LIBRARY = library


def set_lib_from_name(libname: str) -> None:
    """Set the current library from a name.

    :param libname: the name of a library in the configuration file or a path
        to an existing folder that should be considered a library.
    """
    set_lib(get_lib_from_name(libname))


def get_lib_from_name(libname: str) -> papis.library.Library:
    """Get a library object from a name.

    :param libname: the name of a library in the configuration file or a path
        to an existing folder that should be considered a library.
    """
    config = get_configuration()

    if libname not in config:
        if os.path.isdir(libname):
            logger.warning("Setting path '%s' as the main library folder.", libname)

            lib = papis.library.from_paths([libname])
            # NOTE: can't use set(...) here due to cyclic dependencies
            config[lib.name] = {"dirs": str(lib.paths)}
        else:
            raise RuntimeError(
                "Library '{lib}' does not seem to exist. "
                "To add a library simply write the following "
                "in your configuration file located at '{config}'\n\n"
                "\t[{lib}]\n"
                "\tdir = path/to/your/{lib}/folder"
                .format(lib=libname, config=get_config_file()))
    else:
        try:
            # NOTE: can't use `getstring(...)` due to cyclic dependency
            paths = [os.path.expanduser(config[libname]["dir"])]
        except KeyError:
            try:
                # NOTE: can't use `getlist(...)` due to cyclic dependency
                paths = eval(config[libname]["dirs"])
                paths = [os.path.expanduser(d) for d in paths]
            except Exception as exc:
                raise RuntimeError(
                    "To define a library you have to set either 'dir' or 'dirs' "
                    "in the configuration file.\n"
                    "\t'dir' must be a path to an existing folder.\n"
                    "\t'dirs' must be a list of paths.") from exc

        lib = papis.library.Library(libname, paths)

    return lib


def get_lib_dirs() -> List[str]:
    """Get the directories of the current library."""
    return get_lib().paths


def get_lib_name() -> str:
    """Get the name of the current library."""
    return get_lib().name


def get_lib() -> papis.library.Library:
    """Get current library.

    If there is no library set before, the default library will be retrieved.
    If the ``PAPIS_LIB`` environment variable is defined, this is the
    library name (or path) that will be taken as a default.
    """
    global CURRENT_LIBRARY

    libname = os.environ.get("PAPIS_LIB")
    if libname:
        set_lib_from_name(libname)

    if CURRENT_LIBRARY is None:
        # NOTE: this cannot use `general_get` (cyclic dependency), so we have
        # to handle the `default-library` not being present in the user config
        config = get_configuration()
        settings = config[GENERAL_SETTINGS_NAME]

        if "default-library" in settings:
            lib = settings["default-library"]
        else:
            default_settings = get_default_settings()[GENERAL_SETTINGS_NAME]
            lib = default_settings["default-library"]

        set_lib_from_name(lib)

    assert isinstance(CURRENT_LIBRARY, papis.library.Library)
    return CURRENT_LIBRARY


def get_libs() -> List[str]:
    """Get all the library names from the configuration file."""
    return get_libs_from_config(get_configuration())


def get_libs_from_config(config: Configuration) -> List[str]:
    """Get all library names from the given *configuration*.

    In the configuration file, any sections that contain a ``"dir"`` or a
    ``"dirs"`` key are considered to be libraries.
    """

    libs = []
    for section in config:
        sec = config[section]
        if "dir" in sec or "dirs" in sec:
            libs.append(section)

    return libs


def reset_configuration() -> Configuration:
    """Resets the existing configuration and returns a new one without any
    user settings.
    """

    global CURRENT_CONFIGURATION
    CURRENT_CONFIGURATION = None

    logger.debug("Resetting configuration.")
    return get_configuration()

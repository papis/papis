import os
import configparser
from typing import Dict, Any, List, Optional, Callable

import click
import platformdirs

import papis.exceptions
import papis.library
import papis.logging
from papis.strings import FormattedString

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
                "dir": os.path.join(platformdirs.user_documents_dir(), "papers")
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
                self.read(fullpath)

    def include_defaults(self) -> None:
        for section in self.default_info:
            self[section] = {}
            for field in self.default_info[section]:
                self[section][field] = self.default_info[section][field]

    def initialize(self) -> None:
        deprecated_config = _get_deprecated_config_folder()
        has_deprecated_config = (
            self.dir_location != deprecated_config
            and os.path.exists(deprecated_config))

        # ensure all configuration directories exist
        if os.path.exists(self.dir_location):
            if has_deprecated_config:
                click.echo(
                    f"The configuration is loaded from '{self.dir_location}'. A "
                    "deprecated configuration folder was found at "
                    f"'{deprecated_config}' and skipped. Please remove it to "
                    "avoid seeing this warning in the future.")
        else:
            if has_deprecated_config:
                click.echo(
                    "A deprecated configuration folder was found at "
                    f"'{deprecated_config}' and has been copied to the new "
                    f"location '{self.dir_location}'. Please remove the deprecated "
                    "folder to avoid seeing this warning in the future.")

                import shutil
                shutil.copytree(deprecated_config, self.dir_location)
            else:
                self.include_defaults()
                return

        # load settings
        if os.path.exists(self.file_location):
            try:
                self.read(self.file_location)
                self.handle_includes()
            except configparser.DuplicateOptionError as exc:
                click.echo("Failed to read configuration file "
                           f"'{self.file_location}'.")
                click.echo(f"Error: Duplicate option '{exc.option}' "
                           f"in section {exc.section}")
                raise SystemExit(1) from None

        # if no sections were actually read, add default ones
        if not self.sections():
            self.include_defaults()

        # ensure the general section and default-library exist in the config
        if GENERAL_SETTINGS_NAME not in self:
            libs = get_libs_from_config(self)
            default_library = (
                libs[0] if libs else
                self.default_info[GENERAL_SETTINGS_NAME]["default-library"])

            self[GENERAL_SETTINGS_NAME] = {"default-library": default_library}

        # evaluate the python config
        configpy = get_configpy_file()
        if os.path.exists(configpy):
            with open(configpy, encoding="utf-8") as fd:
                # NOTE: this includes the `globals()` so that the user config.py
                # can add entries to the global namespace. This was motivated
                # by adding filters to `Jinja2Formatter.env`, which may be separated
                # into multiple functions that would not be found otherwise.
                #   https://github.com/papis/papis/pull/930
                exec(fd.read(), globals())


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


def _get_deprecated_config_folder() -> str:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        xdg_config_home = os.path.expanduser(xdg_config_home)
    else:
        xdg_config_home = os.path.join(os.path.expanduser("~"), ".config")

    # NOTE: configuration directories are search in the following order
    # 1. user config in `~/.config/papis` (see XDG_CONFIG_HOME)
    # 2. site config in `/etc/papis` (see XDG_CONFIG_DIRS)
    # 3. deprecated config in `~/.papis`
    config_dirs = [os.path.join(xdg_config_home, "papis")]

    xdg_config_dirs = os.environ.get("XDG_CONFIG_DIRS")
    if xdg_config_dirs:
        config_dirs += [os.path.join(d, "papis") for d in xdg_config_dirs.split(":")]

    config_dirs += [os.path.join(os.path.expanduser("~"), ".papis")]

    for config_dir in config_dirs:
        if os.path.exists(config_dir):
            return config_dir

    # NOTE: If no folder is found, then get the config home
    return os.path.join(xdg_config_home, "papis")


def get_config_home() -> str:
    """
    :returns: a (platform dependent) base directory relative to which user
        specific configuration files should be stored.
    """
    # NOTE: this environment variable is added mainly for testing purposes, so
    # we don't have to monkeypatch platformdirs in an awkward way
    home = os.environ.get("PAPIS_CONFIG_DIR")
    if home is None:
        home = platformdirs.user_config_dir()
    else:
        home = os.path.dirname(home)

    return home


def get_config_folder() -> str:
    """Get the main configuration folder.

    :returns: a (platform dependent) folder where the configuration files are
        stored, e.g. ``$HOME/.config/papis`` on POSIX platforms.
    """
    folder = os.environ.get("PAPIS_CONFIG_DIR")
    if folder is None:
        # FIXME: should also check XDG_CONFIG_DIRS as we did before
        folder = platformdirs.user_config_dir("papis")

    return folder


def get_config_file() -> str:
    """Get the main configuration file.

    :returns: the path of the main configuration file, which by default is in
        :func:`get_config_folder`, but can be overwritten using
        :func:`set_config_file`.
    """
    if OVERRIDE_VARS["file"] is not None:
        config_file = OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(get_config_folder(), "config")

    logger.debug("Getting config file '%s'.", config_file)
    return config_file


def set_config_file(filepath: str) -> None:
    """Override the main configuration file."""
    logger.debug("Setting config file to '%s'.", filepath)
    OVERRIDE_VARS["file"] = filepath


def get_configpy_file() -> str:
    r"""Get the main Python configuration file.

    This is a file that will get automatically :func:`eval`\ ed if it exists
    and allows for more dynamic configuration.

    :returns: the path of the main Python configuration file, which by default
        is in :func:`get_config_folder`.
    """
    return os.path.join(get_config_folder(), "config.py")


def get_scripts_folder() -> str:
    """
    :returns: the folder where additional scripts are stored, which by default
        is in :func:`get_config_folder`.
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

    try:
        config[section][key] = str(value)
    except ValueError as exc:
        logger.error("Failed to set the key '%s' in section '%s' with value '%s'.",
                     key, section, value)
        logger.error("If the value contains a '%', this should be properly "
                     "escaped (using a double percent '%%') or the proper "
                     "interpolation syntax should be used (i.e. '%(other_key)').",
                     exc_info=exc)


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
    if data_type is int:
        method = config.getint
    elif data_type is float:
        method = config.getfloat
    elif data_type is bool:
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

    qualified_key = key if section is None else f"{section}-{key}"
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
        if section is not None:
            section_settings = default_settings.get(section, {})
            if key in section_settings:
                return section_settings[key]

        general_settings = default_settings.get(global_section, {})
        if qualified_key in general_settings:
            return general_settings[qualified_key]

        raise papis.exceptions.DefaultSettingValueMissing(qualified_key)

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
    except ValueError as exc:
        value = general_get(key, section=section)
        raise ValueError(f"Key '{key}' should be an integer: '{value}'") from exc


def getfloat(key: str, section: Optional[str] = None) -> Optional[float]:
    """Retrieve an floating point value from the configuration file.

        >>> set("something", 0.42)
        >>> getfloat("something")
        0.42
    """
    try:
        return general_get(key, section=section, data_type=float)
    except ValueError as exc:
        value = general_get(key, section=section)
        raise ValueError(f"Key '{key}' should be a float: '{value}'") from exc


def getboolean(key: str, section: Optional[str] = None) -> Optional[bool]:
    """Retrieve a boolean value from the configuration file.

        >>> set("add-open", True)
        >>> getboolean("add-open")
        True
    """
    try:
        return general_get(key, section=section, data_type=bool)
    except ValueError as exc:
        value = general_get(key, section=section)
        raise ValueError(f"Key '{key}' should be a boolean: '{value}'") from exc


def getstring(key: str, section: Optional[str] = None) -> str:
    """Retrieve a string value from the configuration file.

        >>> set("add-open", "hello world")
        >>> getstring("add-open")
        'hello world'
    """
    result = general_get(key, section=section, data_type=str)
    if not isinstance(result, str):
        raise ValueError(f"Key '{key}' should be a string: {result!r}")

    return str(result)


def getformattedstring(key: str, section: Optional[str] = None) -> FormattedString:
    """Retrieve a formatted string value from the configuration file.

    Formatted strings use the :class:`~papis.strings.FormattedString` class to
    define a string that should be formatted by a specific
    :class:`~papis.format.Formatter`. For configuration options, such strings
    can be defined in the configuration file as::

        [settings]
        multiple-authors-format = {au[family]}, {au[given]}
        multiple-authors-format.python = {au[family]}, {au[given]}
        multiple-authors-format.jinja2 = {{ au[family] }}, {{ au[given] }}

    i.e. like ``key[.formatter]``. If no formatter is provided in the key name,
    the default formatter is used, as defined by :confval:`formatter`.
    Formatters are checked in alphabetical order and the last one is returned.

        >>> set("add-open", "hello world")
        >>> r = getformattedstring("add-open")
        >>> r.formatter
        'python'

        >>> set("add-open", FormattedString("python", "hello world"))
        >>> r = getformattedstring("add-open")
        >>> r.formatter
        'python'

        >>> set("add-open.python", "hello world")
        >>> r = getformattedstring("add-open")
        >>> r.formatter
        'python'
    """
    from papis.format import get_available_formatters, get_default_formatter

    formatter = get_default_formatter()
    result: Optional[str] = None

    for f in get_available_formatters():
        try:
            tmp = general_get(f"{key}.{f}", section=section, data_type=str)
        except papis.exceptions.DefaultSettingValueMissing:
            pass
        else:
            result, formatter = tmp, f

    if result is None:
        result = general_get(key, section=section, data_type=str)

    if isinstance(result, FormattedString):
        return result
    elif isinstance(result, str):
        return FormattedString(formatter, result)
    else:
        raise ValueError(f"Key '{key}' should be a string: '{result}'")


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
    except Exception as exc:
        raise SyntaxError(
            f"The key '{key}' must be a valid Python object: {rawvalue}"
            ) from exc
    else:
        if not isinstance(rawvalue, list):
            raise SyntaxError(
                f"The key '{key}' must be a valid Python list. "
                f"Got: {rawvalue} (type {type(rawvalue)})")

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
        paths = [escape_interp(path) for path in library.paths]
        config[library.name] = {"dirs": str(paths)}

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
    default_settings = get_default_settings()
    libs = get_libs_from_config(config)

    if libname not in libs:
        if os.path.isdir(libname):
            logger.warning("Setting path '%s' as the main library folder.", libname)

            lib = papis.library.from_paths([libname])
            # NOTE: can't use set(...) here due to cyclic dependencies
            config[lib.name] = {"dirs": str([escape_interp(libname)])}
        else:
            raise RuntimeError(
                f"Library '{libname}' does not seem to exist. "
                "To add a library simply write the following "
                f"in your configuration file located at '{get_config_file()}'\n\n"
                f"\t[{libname}]\n"
                f"\tdir = path/to/your/{libname}/folder"
                )
    else:
        if libname in default_settings and libname not in config:
            config[libname] = default_settings[libname]

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

    # NOTE: also look through default settings in case they were registered
    # in `config.py` using `register_default_settings`.
    default_settings = get_default_settings()
    for name, values in default_settings.items():
        if name in config:
            continue

        if "dir" in values or "dirs" in values:
            libs.append(name)

    return sorted(libs)


def reset_configuration() -> Configuration:
    """Resets the existing configuration and returns a new one without any
    user settings.
    """

    global CURRENT_CONFIGURATION
    CURRENT_CONFIGURATION = None

    logger.debug("Resetting configuration.")
    return get_configuration()


def escape_interp(path: str) -> str:
    """Escape paths added to the configuration file.

    By default, the :class:`papis.config.Configuration` enables string interpolation
    in the key values (e.g. using ``key = %(other_key)s-suffix)``). Any paths
    added to the configuration should then be escaped so that they do not
    interfere with the interpolation.
    """
    import re

    # FIXME: this should be smart enough to not double quote valid interpolation
    # paths? Would need a regex to skip things like `%\(\w+\)`?
    return re.sub(r"([^%])%([^%(])", r"\1%%\2", path)

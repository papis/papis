
import os
import configparser
import papis.utils
import logging

logger = logging.getLogger("config")

CONFIGURATION = None
DEFAULT_MODE = "document"
OVERRIDE_VARS = {
    "folder": None,
    "cache": None,
    "file": None,
    "scripts": None
}


def get_config_folder():
    return os.path.join(
        os.path.expanduser("~"), ".papis"
    )


def get_cache_folder():
    return os.path.join(
        get_config_folder(), "cache"
    )


def get_config_file():
    if OVERRIDE_VARS["file"] is not None:
        config_file = OVERRIDE_VARS["file"]
    else:
        config_file = os.path.join(
            get_config_folder(), "config"
        )
    logger.debug("Getting config file %s" % config_file)
    return config_file


def set_config_file(filepath):
    global OVERRIDE_VARS
    if filepath is not None:
        logger.debug("Setting config file to %s" % filepath)
        OVERRIDE_VARS["file"] = filepath


def get_scripts_folder():
    return os.path.join(
        get_config_folder(), "scripts"
    )


def general_get(*args, data_type="", default=None, extras=[]):
    """
    :param: extras: List of tuples containing section and prefixes
    """
    method = None
    lib = papis.utils.get_lib()
    config = get_configuration()
    if len(args) == 1:
        key = args[0]
    elif len(args) == 2:
        lib = args[0]
        key = args[1]
    else:
        raise Exception("Problem with args parsing")
    if data_type == int:
        method = config.getint
    elif data_type == float:
        method = config.getfloat
    elif data_type == bool:
        method = config.getboolean
    else:
        method = config.get
    global_section = "settings"
    extras = [(global_section, "")] + extras + [(lib, "")]
    value = None
    for extra in extras:
        section = extra[0]
        prefix = extra[1]
        whole_key = extra[2] if len(extra) == 3 else prefix+key
        if section not in config.keys():
            continue
        if whole_key in config[section].keys():
            value = method(section, whole_key)
    if value is None:
        if default is not None:
            return default
        else:
            raise KeyError("No key %s found in the configuration" % key)
    return value


def get(*args, **kwargs):
    return general_get(*args, **kwargs)


def getint(*args, **kwargs):
    return general_get(*args, data_type=int, **kwargs)


def getfloat(*args, **kwargs):
    return general_get(*args, data_type=float, **kwargs)


def getboolean(*args, **kwargs):
    return general_get(*args, data_type=bool, **kwargs)


def inMode(mode):
    current_mode = get("mode", default=DEFAULT_MODE)
    logger.debug("current_mode = %s" % current_mode)
    return mode == current_mode


def get_configuration():
    global CONFIGURATION
    if CONFIGURATION is None:
        logger.debug("Creating configuration")
        CONFIGURATION = Configuration()
    return CONFIGURATION


def reset_configuration():
    global CONFIGURATION
    if CONFIGURATION is not None:
        logger.warning("Overwriting previous configuration")
    CONFIGURATION = None
    logger.debug("Reseting configuration")
    return get_configuration()


def get_default_match_format():
    return "{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}"


def get_default_header_format():
    return "{doc[title]:<70.70}|{doc[author]:<20.20} ({doc[year]:-<4})"


def get_header_format(key="header_format"):
    try:
        header_format = get(key)
    except:
        header_format = get_default_header_format()
    return header_format


def get_match_format():
    try:
        match_format = get("match_format")
    except:
        match_format = get_default_match_format()
    return match_format


class Configuration(configparser.ConfigParser):

    default_info = {
      "papers": {
        'dir': '~/Documents/papers'
      },
      "settings": {
        'default': 'papers'
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

    def save(self):
        fd = open(self.file_location, "w")
        self.write(fd)
        fd.close()

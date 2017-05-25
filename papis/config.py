
import os
import configparser
import papis.utils
import logging

logger = logging.getLogger("config")

CONFIGURATION = None
DEFAULT_MODE = "document"


def get_config_folder():
    return os.path.join(
        os.path.expanduser("~"), ".papis"
    )


def get_config_file():
    return os.path.join(
        get_config_folder(), "config"
    )


def get_scripts_folder():
    return os.path.join(
        get_config_folder(), "scripts"
    )


def general_get(*args, data_type=""):
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
    if key in config[lib].keys():
        return method(lib, key)
    elif key in config[global_section].keys():
        return method(global_section, key)
    else:
        raise KeyError("No key %s found in the configuration" % key)


def get(*args):
    return general_get(*args)


def getint(*args):
    return general_get(*args, data_type=int)


def getfloat(*args):
    return general_get(*args, data_type=float)


def getboolean(*args):
    return general_get(*args, data_type=bool)


def inMode(mode):
    current_mode = get("mode")
    logger.debug("current_mode = %s" % current_mode)
    return mode == current_mode


def get_configuration():
    global CONFIGURATION
    if CONFIGURATION is None:
        CONFIGURATION = Configuration()
    return CONFIGURATION


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

    DEFAULT_DIR_LOCATION = get_config_folder()

    DEFAULT_SCRIPTS_LOCATION = get_scripts_folder()

    DEFAULT_FILE_LOCATION = get_config_file()

    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.initialize()

    def initialize(self):
        if not os.path.exists(self.DEFAULT_DIR_LOCATION):
            os.makedirs(self.DEFAULT_DIR_LOCATION)
        if not os.path.exists(self.DEFAULT_SCRIPTS_LOCATION):
            os.makedirs(self.DEFAULT_SCRIPTS_LOCATION)
        if os.path.exists(self.DEFAULT_FILE_LOCATION):
            self.read(self.DEFAULT_FILE_LOCATION)
        else:
            for section in self.default_info:
                self[section] = {}
                for field in self.default_info[section]:
                    self[section][field] = self.default_info[section][field]
            with open(self.DEFAULT_FILE_LOCATION, "w") as configfile:
                self.write(configfile)

    def save(self):
        fd = open(self.DEFAULT_FILE_LOCATION, "w")
        self.write(fd)
        fd.close()

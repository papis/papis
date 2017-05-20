
import os
import configparser

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

    DEFAULT_FILE_LOCATION = get_config_file()

    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.initialize()

    def initialize(self):
        if not os.path.exists(self.DEFAULT_DIR_LOCATION):
            os.makedirs(self.DEFAULT_DIR_LOCATION)
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

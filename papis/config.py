
import os
import configparser

class Configuration(configparser.ConfigParser):

    default_info={
      "papers": {
        'dir'  : '~/Documents/papers'
      },
      "settings": {
        'default': 'papers'
      }
    }

    DEFAULT_FILE_LOCATION= os.path.join(os.path.expanduser("~"), ".papis.conf")
    def __init__(self):
        configparser.ConfigParser.__init__(self)
        self.initialize()
    def initialize(self):
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
        """
        :f: TODO
        :returns: TODO
        """
        fd = open(self.DEFAULT_FILE_LOCATION, "w")
        self.write(fd)
        fd.close()

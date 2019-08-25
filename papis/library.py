import os
import glob
import logging
import sys

logger = logging.getLogger("library")

class Library:

    def __init__(self, name, paths):
        assert(isinstance(name, str)), '`name` must be a string'
        assert(isinstance(paths, list)), '`paths` must be a list'
        self.name = name

        # If any of the paths do not exist, warn the user.
        for path in paths:
            if not os.path.exists(path):
                logger.warn("Warning: library " + name + " at path '" + path +
                            "' doesn't exist.  Please create it before " +
                            "continuing.")

        self.paths = sum(
            [glob.glob(os.path.expanduser(p)) for p in paths],
            []
        )

        if len(self.paths) == 0:
            logger.error("No existing paths found for library " + name +
                         ".  Exiting.")
            sys.exit(1)

    def path_format(self):
        return ":".join(self.paths)

    def __str__(self):
        return self.name


def from_paths(paths):
    name = ":".join(paths)
    return Library(name, paths)

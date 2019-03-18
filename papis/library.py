import os
import glob


class Library:

    def __init__(self, name, paths):
        assert(isinstance(name, str)), '`name` must be a string'
        assert(isinstance(paths, list)), '`paths` must be a list'
        self.name = name
        self.paths = sum(
            [glob.glob(os.path.expanduser(p)) for p in paths],
            []
        )

    def path_format(self):
        return ":".join(self.paths)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


def from_paths(paths):
    name = ":".join(paths)
    return Library(name, paths)

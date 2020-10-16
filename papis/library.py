import os
import glob
from typing import List


class Library:

    def __init__(self, name: str, paths: List[str]):
        """Create a Library object."""
        self.name = name
        self.paths = sum(
            [glob.glob(os.path.expanduser(p)) for p in paths],
            [])  # type: List[str]

    def path_format(self) -> str:
        return ":".join(self.paths)

    def __str__(self) -> str:
        """Get the name of the library when formatting"""
        return self.name


def from_paths(paths: List[str]) -> Library:
    name = ":".join(paths)
    return Library(name, paths)

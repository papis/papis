import os
import glob
from itertools import chain
from typing import List, Sequence


class Library:
    """A class containing library information."""

    def __init__(self, name: str, paths: Sequence[str]) -> None:
        #: The name of the library, as it appears in the configuration file if
        #: defined there.
        self.name: str = name
        #: A list of paths with documents that form the library.
        self.paths: List[str] = list(
            chain.from_iterable(glob.glob(os.path.expanduser(p)) for p in paths)
            )

    def path_format(self) -> str:
        """
        :return: a string containing all the paths in the library concatenated
            using a colon.
        """
        return ":".join(self.paths)

    def __str__(self) -> str:
        return self.name


def from_paths(paths: Sequence[str]) -> Library:
    """Create a library from a list of paths."""

    name = ":".join(paths)
    return Library(name, paths)

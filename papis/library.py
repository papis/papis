from __future__ import annotations

import os


class Library:
    """A class containing library information."""

    def __init__(self, name: str, path: str) -> None:
        #: The name of the library, as it appears in the configuration file if
        #: defined there.
        self.name: str = name
        #: The path with documents that form the library.
        self.path: str = os.path.abspath(os.path.expanduser(path))

    def __str__(self) -> str:
        return self.name

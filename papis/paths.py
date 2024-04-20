import os
import pathlib
import sys
from typing import Iterator, Optional, Union

import papis.config

#: A union type for allowable paths.
PathLike = Union[os.PathLike, str]

# NOTE: private error codes for Windows
WIN_ERROR_PRIVILEGE_NOT_HELD = 1314


def unique_suffixes(chars: Optional[str] = None, skip: int = 0) -> Iterator[str]:
    """Creates an infinite list of suffixes based on *input_list*.

    This creates a generator object capable of iterating over lists to
    create unique products of increasing cardinality
    (see `here <https://stackoverflow.com/questions/14381940/python-pair-alphabets-after-loop-is-completed>`__).
    This is mainly intended to create suffixes for existing strings, e.g. file names,
    to ensure uniqueness.

    :param chars: list to iterate over
    :param skip: number of suffices to skip (negative integers are set to 0).

    >>> import string
    >>> m = make_suffix(string.ascii_lowercase)
    >>> next(m)
    'a'
    """  # noqa: E501

    import string
    from itertools import count, product, islice

    def ids() -> Iterator[str]:
        inputs = string.ascii_lowercase if chars is None else chars

        for n in count(1):
            for s in product(inputs, repeat=n):
                yield "".join(s)

    yield from islice(ids(), max(skip, 0), None)


def normalize_path(path: str, *,
                   lowercase: Optional[bool] = None,
                   extra_chars: Optional[str] = None,
                   separator: Optional[str] = None) -> str:
    """Clean a path to only contain visible ASCII characters.

    This function will create ASCII strings that can be safely used as file names
    or printed to consoles that do not necessarily support full unicode.

    :arg lowercase: if *True*, the resulting string will always be lowercased
        (defaults to :confval:`doc-paths-lowercase`).
    :arg extra_chars: extra characters that are allowed in the
        output path besides the default ASCII alphanumeric characters
        (defaults to :confval:`doc-paths-extra-chars`).
    :arg separator: word separator used to replace any non-allowed characters
        in the path (defaults to :confval:`doc-paths-separator`).
    :returns: a cleaned ASCII string.
    """
    if lowercase is None:
        lowercase = papis.config.getboolean("doc-paths-lowercase")

    if extra_chars is None:
        extra_chars = papis.config.getstring("doc-paths-extra-chars")

    if separator is None:
        separator = papis.config.getstring("doc-paths-word-separator")

    if lowercase is None:
        lowercase = True

    if lowercase:
        regex_pattern = fr"[^a-z0-9.{extra_chars}]+"
    else:
        regex_pattern = fr"[^a-zA-Z0-9.{extra_chars}]+"

    import slugify

    return str(slugify.slugify(
        path,
        word_boundary=True,
        separator=separator,
        regex_pattern=regex_pattern,
        lowercase=lowercase))


def is_relative_to(path: PathLike, other: PathLike) -> bool:
    """Check if paths are relative to each other.

    This is equivalent to :meth:`pathlib.PurePath.is_relative_to`.

    :returns: *True* if *path* is relative to the *other* path.
    """
    try:
        return pathlib.Path(path).is_relative_to(other)
    except AttributeError:
        try:
            return not os.path.relpath(path, start=other).startswith("..")
        except ValueError:
            return False


def symlink(src: PathLike, dst: PathLike) -> None:
    """Create a symbolic link pointing to *src* named *dst*.

    This is a simple wrapper around :func:`os.symlink` that attempts to give
    better error messages on different platforms. For example, it offers
    suggestions for some missing priviledge issues.

    :param src: the existing file that *dst* points to.
    :param dst: the name of the new symbolic link, pointing to *src*.
    """
    try:
        os.symlink(src, dst)
    except OSError as exc:
        if sys.platform == "win32" and exc.winerror == WIN_ERROR_PRIVILEGE_NOT_HELD:
            # https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--1300-1699-
            raise OSError(exc.errno,
                          "Failed to link due to insufficient permissions. You "
                          "can try again after enabling the 'Developer mode' "
                          "and restarting.", exc.filename, exc.winerror, exc.filename2)

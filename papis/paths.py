from typing import Iterator, Optional

import papis.config


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

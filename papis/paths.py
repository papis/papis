from typing import Optional

import papis.config


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

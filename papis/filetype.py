import os
import re
from typing import Optional

import filetype


def guess_content_extension(content: bytes) -> Optional[str]:
    """Guess the extension from (potential) file contents.

    This method attempts to look at known file signatures to determine the file
    type. This is not always possible, as it is hard to determine a unique type.

    :param content: contents of a file.
    :returns: an extension string (e.g. "pdf" without the dot) or *None* if the
        file type cannot be determined.
    """
    kind = filetype.guess(content)
    return str(kind.extension) if kind is not None else None


def guess_document_extension(document_path: str) -> Optional[str]:
    """Guess the extension of a given file at *document_path*.

    :param document_path: path to an existing file.
    :returns: an extension string (e.g. "pdf" without the dot) or *None* if the
        file type cannot be determined.
    """

    document_path = os.path.expanduser(document_path)
    kind = filetype.guess(document_path)

    if kind is not None:
        return str(kind.extension)

    m = re.match(r"^.*\.([^.]+)$", os.path.basename(document_path))
    return m.group(1) if m else None


def get_document_extension(document_path: str) -> str:
    """Get an extension for the file at *document_path*.

    This uses :func:`guess_document_extension` and returns a default extension
    `"data"` if no specific type can be determined from the file.

    :param document_path: path to an existing file.
    :returns: an extension string.
    """

    extension = guess_document_extension(document_path)
    return extension if extension is not None else "data"

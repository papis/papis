import os
import re
from typing import Optional

import filetype


class DjVu(filetype.Type):      # type: ignore[misc]
    """
    Implements a custom DjVu type matcher for ``filetype``.
    """

    MIME = "image/vnd.djvu"
    EXTENSION = "djvu"

    def __init__(self) -> None:
        super().__init__(mime=self.MIME, extension=self.EXTENSION)

    def match(self, buf: bytes) -> bool:  # noqa: PLR6301
        # https://en.wikipedia.org/wiki/List_of_file_signatures
        # magic: AT&TFORMXXXXDJV[UM]
        return (
            len(buf) >= 16
            and buf[0] == 0x41 and buf[1] == 0x54
            and buf[2] == 0x26 and buf[3] == 0x54
            and buf[4] == 0x46 and buf[5] == 0x4F
            and buf[6] == 0x52 and buf[7] == 0x4D
            # and buf[8:11] == ??
            and buf[12] == 0x44 and buf[13] == 0x4A
            and buf[14] == 0x56
            and (buf[15] == 0x55 or buf[15] == 0x4D)
            )


if filetype.get_type(DjVu.MIME) is None:
    filetype.add_type(DjVu())


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

import re
import os
import filetype


def get_document_extension(document_path: str) -> str:
    """Get document extension

    :document_path: Path of the document
    :returns: Extension (string)

    """
    filetype.guess(document_path)
    kind = filetype.guess(document_path)
    if kind is None:
        m = re.match(r"^.*\.([^.]+)$", os.path.basename(document_path))
        return m.group(1) if m else 'data'
    else:
        assert isinstance(kind.extension, str)
        return kind.extension

"""
This module controls the notes for every Papis document.
"""
import os
from typing import TYPE_CHECKING

import papis.config
import papis.logging

if TYPE_CHECKING:
    import papis.document

logger = papis.logging.get_logger(__name__)


def has_notes(doc: "papis.document.Document") -> bool:
    """Checks if the document has notes."""
    return "notes" in doc


def notes_path(doc: "papis.document.Document") -> str:
    """Get the path to the notes file corresponding to *doc*.

    If the document does not have attached notes, a filename is constructed (using
    the :confval:`notes-name` setting) in the document's main folder.

    :returns: a absolute filename that corresponds to the attached notes for
        *doc* (this file does not necessarily exist).
    """
    if not has_notes(doc):
        from papis.format import format
        notes_name = format(
            papis.config.getformatpattern("notes-name"), doc,
            default="notes.tex")

        from papis.paths import normalize_path
        doc["notes"] = normalize_path(notes_name)

        from papis.api import save_doc
        save_doc(doc)

    return os.path.join(doc.get_main_folder() or "", doc["notes"])


def notes_path_ensured(doc: "papis.document.Document") -> str:
    """Get the path to the notes file corresponding to *doc* or create it if
    it does not exist.

    If the notes do not exist, a new file is created using :func:`notes_path`
    and filled with the contents of the template given by the
    :confval:`notes-template` configuration option.

    :returns: an absolute filename that corresponds to the attached notes for *doc*.
    """
    notespath = notes_path(doc)

    if not os.path.exists(notespath):
        templatepath = os.path.expanduser(papis.config.getstring("notes-template"))

        template = ""
        if os.path.exists(templatepath):
            from papis.format import FormatFailedError, format

            with open(templatepath, encoding="utf-8") as fd:
                try:
                    template = format(fd.read(), doc)
                except FormatFailedError as exc:
                    logger.error("Failed to format notes template at '%s'.",
                                 templatepath, exc_info=exc)

        with open(notespath, "w+", encoding="utf-8") as fd:
            fd.write(template)

    return notespath

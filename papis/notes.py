"""
This module controls the notes for every papis document.
"""
import os

import papis.config
import papis.api
import papis.format
import papis.document
import papis.utils
import papis.hooks


def has_notes(doc: papis.document.Document) -> bool:
    """
    Checks if the document has the notes key.
    """
    return "notes" in doc


def notes_path(doc: papis.document.Document) -> str:
    """
    It returns the notes path of a document even if this
    document did not have a notes field.

    If it did not have a notes filed, it creates it
    and it saves it to the database.
    """
    if has_notes(doc):
        return os.path.join(doc.get_main_folder() or "",
                            doc["notes"])
    notes_name = papis.config.getstring("notes-name")
    notes_name = papis.format.format(notes_name, doc)
    doc["notes"] = papis.utils.clean_document_name(notes_name)
    papis.api.save_doc(doc)
    return notes_path(doc)


def notes_path_ensured(doc: papis.document.Document) -> str:
    """
    It returns a file descriptor for the notes.
    If the notes file does not exist it creates one with the content of
    ``notes-template`` file included.
    """
    _notes_path = notes_path(doc)
    if not os.path.exists(_notes_path):
        templ_path = (os.path.expanduser(papis.config
                                         .getstring("notes-template")))
        templ_out = ""
        if os.path.exists(templ_path):
            with open(templ_path, "r") as f:
                templ_src = f.read()
                templ_out = papis.format.format(templ_src, doc)
        with open(_notes_path, "w+") as _fd:
            _fd.write(templ_out)
    return _notes_path

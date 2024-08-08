"""Module defining the main document type."""

import os
import re
import enum
from typing import (
    Any, Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple,
    TypedDict, Union,
    )

import papis
import papis.config
import papis.logging

logger = papis.logging.get_logger(__name__)

#: A union of types that can be converted to a document.
DocumentLike = Union["Document", Dict[str, Any]]


# NOTE: rankings used in papis.document.sort:
#   date:       0 (date type -- comes first)
#   int:        1 (integer type)
#   other:      2 (other types)
#   none:       3 (missing key)
class _SortPriority(enum.IntEnum):
    Date = 0
    Int = 1
    Other = 2
    Missing = 3


class KeyConversion(TypedDict):
    """A :class:`dict` that contains a *key* and an *action*."""

    #: Name of a key in a foreign dictionary to convert.
    key: Optional[str]
    #: Action to apply to the value at :attr:`key` for pre-processing.
    action: Optional[Callable[[Any], Any]]


#: A default :class:`KeyConversion`.
EmptyKeyConversion = KeyConversion(key=None, action=None)


class KeyConversionPair(NamedTuple):
    #: A string denoting the key in the input data.
    from_key: str
    #: A :class:`list` of :class:`KeyConversion` key mapping rules used to
    #: rename and post-process the :attr:`from_key` and its value.
    rules: List[KeyConversion]


def keyconversion_to_data(conversions: Sequence[KeyConversionPair],
                          data: Dict[str, Any],
                          keep_unknown_keys: bool = False) -> Dict[str, Any]:
    r"""Function to convert between dictionaries.

    This can be used to define a fixed set of translation rules between, e.g.,
    JSON data obtained from a website API and standard ``papis`` key names and
    formatting. The implementation is completely generic.

    For example, we have the simple dictionary

    .. code:: python

        data = {"id": "10.1103/physrevb.89.140501"}

    which contains the DOI of a document with the wrong key. We can then write
    the following rules

    .. code:: python

        conversions = [
            KeyConversionPair("id", [
                {"key": "doi", "action": None},
                {"key": "url": "action": lambda x: "https://doi.org/{}".format(x)}
            ])
        ]

        new_data = keyconversion_to_data(conversions, data)

    to rename the ``"id"`` key to the standard ``"doi"`` key used by ``papis``
    and a URL. Any number of such rules can be written, depending on the
    complexity of the incoming data. Note that any errors raised on the
    application of the *action* will be silently ignored and the corresponding
    key will be skipped.

    :param conversions: a sequence of :class:`KeyConversionPair`\ s used to
        convert the *data*.
    :param data: a :class:`dict` to be convert according to *conversions*.
    :param keep_unknown_keys: if *True* unknown keys from *data* are kept in the
        resulting dictionary. Otherwise, only keys from *conversions* are
        present.

    :returns: a new :class:`dict` containing the entries from *data* converted
        according to *conversions*.
    """

    new_data = {}

    for key_pair in conversions:

        from_key = key_pair.from_key
        if from_key not in data:
            continue

        for rule in key_pair.rules:
            papis_key = str(rule.get("key") or from_key)
            papis_value = data[from_key]

            action = rule.get("action")
            if action:
                try:
                    new_value = action(papis_value)
                except Exception as exc:
                    logger.debug(
                        "Error converting value from key '%s' to '%s': %r.",
                        from_key, papis_key, papis_value, exc_info=exc
                    )
                    new_value = None
            else:
                new_value = papis_value

            if isinstance(new_value, str):
                new_value = new_value.strip()

            if new_value:
                new_data[papis_key] = new_value

    if keep_unknown_keys:
        from_keys = {c.from_key for c in conversions}
        for key, value in data.items():
            if key in from_keys:
                continue
            new_data[key] = value

    if "author_list" in new_data:
        new_data["author"] = author_list_to_author(new_data)

    return new_data


def author_list_to_author(data: Dict[str, Any]) -> str:
    """Convert a list of authors into a single author string.

    This uses the :confval:`multiple-authors-separator` and the
    :confval:`multiple-authors-format` settings to construct the
    concatenated authors.

    :param data: a :class:`dict` that contains an ``"author_list"`` key to
        be converted into a single author string.

    >>> author1 = {"given": "Some", "family": "Author"}
    >>> author2 = {"given": "Other", "family": "Author"}
    >>> author_list_to_author({"author_list": [author1, author2]})
    'Author, Some and Author, Other'
    """
    if "author_list" not in data:
        return ""

    separator = papis.config.getstring("multiple-authors-separator")
    fmt = papis.config.getstring("multiple-authors-format")

    if separator is None or fmt is None:
        raise ValueError(
            "Cannot join the author list if the settings 'multiple-authors-separator' "
            "and 'multiple-authors-format' are not present in the configuration")

    return separator.join([
        fmt.format(au=author) for author in data["author_list"]
        ])


# NOTE: matches "Sanger, F. and Nicklen, S. and Coulson, A. R."
_AUTHOR_FAMILY_FIRST_RE = re.compile(r"\S+\s*,\s*\S+\s+and\s+\S+\s*,")
# NOTE: matches "F. Sanger and S. Nicklen and A. R. Coulson"
_AUTHOR_AND_AS_SEP_RE = re.compile(r"[^,\s]\s+and\s+\S")
# NOTE: matches "F. Sanger, and S. Nicklen, and A. R. Coulson"
_AUTHOR_AND_COMMA_SEP_RE = re.compile(r",\s+and\s+\S")
# NOTE: matches "Turing, A. M." or "Liddel Hart, Basil"
_AUTHOR_SINGLE_AUTHOR_FAMILY_FIRST_RE = \
    re.compile(r"^(\S+\s*,\s*[^,]+)|([^,]+\s*,\s*\S+)$")


def guess_authors_separator(authors: str) -> str:
    """Attempt to determine the separator for various non-BibTeX author lists.

    :param authors: author string to determine the separator for.
    :returns: a regex that can be used to split the authors string.

    For example:

    >>> s = "Sanger, F. and Nicklen, S. and Coulson, A. R."
    >>> assert guess_authors_separator(s) == "and"
    >>> s = "Fabian Sanger and Steven Nicklen and Alexander R. Coulson"
    >>> assert guess_authors_separator(s) == "and"
    >>> s = "Fabian Sanger, Steven Nicklen, Alexander R. Coulson"
    >>> assert guess_authors_separator(s) == ","
    >>> s = "Fabian Sanger, and Steven Nicklen, and Alexander R. Coulson"
    >>> import re
    >>> sep = guess_authors_separator(s)
    >>> assert re.match(sep, ", and")
    >>> s = "Dagobert Duck and von Beethoven, Ludwig and Ford, Jr., Henry"
    >>> assert guess_authors_separator(s) == "and"
    >>> s = "Turing, A. M."
    >>> assert guess_authors_separator(s) == "and"
    """
    authors = authors.strip()
    if not authors:
        return "and"

    if _AUTHOR_FAMILY_FIRST_RE.match(authors):
        # found something like "Last, First and Last, First"
        sep = "and"
    elif _AUTHOR_AND_AS_SEP_RE.search(authors):
        # found "Name and Name"
        sep = "and"
    elif _AUTHOR_AND_COMMA_SEP_RE.search(authors):
        # found something like "Name, and Name": use a regex to capture all variants
        sep = r",\s*(?:and)?"
    elif _AUTHOR_SINGLE_AUTHOR_FAMILY_FIRST_RE.match(authors):
        # found a single author "Last, First"
        sep = "and"
    elif "," in authors and " and " not in authors:
        # found something like "Name, Name, Name"
        sep = ","
    else:
        sep = "and"

    return sep


def split_author_name(author: str) -> Dict[str, Any]:
    """Split an author name into a given and family name.

    This uses :func:`bibtexparser.customization.splitname` to correctly
    split and determine the first and last names of an author in the list.
    Note that this is just a heuristic and can give incorrect results for
    certain author names.

    :param author: a string containing an author name.
    :returns: a :class:`dict` with the family and given name of the author.
    """
    from bibtexparser.customization import splitname

    parts = splitname(author)
    given = " ".join(parts["first"])
    family = " ".join(parts["von"] + parts["last"] + parts["jr"])

    return {"family": family, "given": given}


def split_authors_name(authors: Union[str, List[str]],
                       separator: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convert list of authors to a fixed format.

    Uses :func:`split_author_name` to construct the individual authors and the
    *separator* to split the authors in the list.

    :param authors: a list of author names, where each entry can consists of
        multiple authors separated by *separator*.
    :param separator: a separator for entries in *authors* that contain
        multiple authors. If *None*, a separator is guessed using
        :func:`guess_authors_separator`.
    """

    if isinstance(authors, str):
        authors = [authors]

    author_list = []
    for subauthors in authors:
        sep = separator if separator else guess_authors_separator(subauthors)
        author_list.extend([
            split_author_name(author)
            for author in re.split(fr"\s*{sep}\s+", subauthors)
        ])

    return author_list


class DocHtmlEscaped(Dict[str, Any]):
    """Small helper class to escape HTML elements in a document.

    >>> DocHtmlEscaped(from_data({"title": '> >< int & "" "'}))['title']
    '&gt; &gt;&lt; int &amp; &quot;&quot; &quot;'
    """

    def __init__(self, doc: "Document") -> None:
        self.doc = doc

    def __getitem__(self, key: str) -> str:
        return (
            str(self.doc[key])
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


class Document(Dict[str, Any]):
    """An abstract document in a ``papis`` library.

    This class inherits from a standard :class:`dict` and implements some
    additional functionality.

    .. attribute:: html_escape

        A :class:`DocHtmlEscaped` instance that can be used to escape keys
        in the document for use in HTML documents.
    """

    subfolder: str = ""
    _info_file_path: str = ""

    def __init__(self,
                 folder: Optional[str] = None,
                 data: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()

        self._folder: Optional[str] = None

        if folder is not None:
            self.set_folder(folder)
            self.load()

        if data is not None:
            self.update(data)

    def has(self, key: str) -> bool:
        """Check if *key* is in the document."""
        return key in self

    def __missing__(self, key: str) -> str:
        """
        If key is not defined, return empty string
        """
        return ""

    def copy(self) -> "Document":
        """Make a shallow copy of the :class:`Document`."""
        doc = Document(data=dict(self))

        folder = self.get_main_folder()
        if folder:
            doc.set_folder(folder)

        return doc

    @property
    def html_escape(self) -> DocHtmlEscaped:
        return DocHtmlEscaped(self)

    def set_folder(self, folder: str) -> None:
        """Set the document's main folder.

        This also updates the location of the info file and other attributes.
        Note, however, that it will not load any data from the given folder
        even if it contains another info file (see :func:`from_folder` for
        this functionality).

        :param folder: an absolute path to a new main folder for the document.
        """
        self._folder = os.path.expanduser(folder)
        self._info_file_path = os.path.join(folder, papis.config.getstring("info-name"))
        self.subfolder = (
            self._folder
            .replace(os.path.expanduser("~"), "")
            .replace("/", " "))

    def get_main_folder(self) -> Optional[str]:
        """
        :returns: the root path in the filesystem where the document is stored,
            if any.
        """
        return self._folder

    def get_main_folder_name(self) -> Optional[str]:
        """
        :returns: the folder name of the document, i.e. the basename of
            the path returned by :meth:`get_main_folder`.
        """
        folder = self.get_main_folder()
        return os.path.basename(folder) if folder else None

    def get_info_file(self) -> str:
        """
        :returns: path to the info file, which can also be an empty string if
            no such file has been created.
        """
        return self._info_file_path

    def _get_absolute_paths(self, key: str) -> List[str]:
        folder = self.get_main_folder()
        if folder is None:
            return []

        relative_files = self.get(key)
        if relative_files is None:
            return []

        files = relative_files if isinstance(relative_files, list) else [relative_files]
        return [os.path.join(folder, f) for f in files]

    def get_files(self) -> List[str]:
        """Get the files linked to the document.

        The files in a document are stored relative to its main folder. If no
        main folder is set on the document (see :meth:`set_folder`), then this
        function will not return any files. To retrieve the relative file paths
        only, access ``doc["files"]`` directly.

        :returns: a :class:`list` of absolute file paths in the document's
            main folder, if any.
        """
        return self._get_absolute_paths("files")

    def get_notes(self) -> List[str]:
        """Get all notes linked to the document.

        :returns: a :class:`list` of absolute file paths in the document's
            main folder, if any, similar to :meth:`get_files`.
        """
        return self._get_absolute_paths("notes")

    def save(self) -> None:
        """Saves the current document fields into the info file."""

        if not self._folder or not os.path.exists(self._folder):
            from papis.exceptions import DocumentFolderNotFound
            raise DocumentFolderNotFound(describe(self))

        import papis.yaml

        allow_unicode = papis.config.getboolean("info-allow-unicode")
        papis.yaml.data_to_yaml(self.get_info_file(),
                                dict(self),
                                allow_unicode=allow_unicode)

    def load(self) -> None:
        """Load information from the info file."""
        import papis.yaml
        info_file = self.get_info_file()
        if not info_file or not os.path.exists(info_file):
            return

        try:
            data = papis.yaml.yaml_to_data(info_file, raise_exception=True)
        except Exception as exc:
            logger.error(
                "Error reading info file at '%s'. Please check it!",
                self.get_info_file(), exc_info=exc)
        else:
            self.clear()
            self.update(data)


def from_data(data: Dict[str, Any]) -> Document:
    """Construct a :class:`Document` from a dictionary.

    :param data: a dictionary to be made into a new document.
    """
    return Document(data=data)


def from_folder(folder_path: str) -> Document:
    """Construct a :class:`Document` from a folder.

    :param folder_path: absolute path to a valid ``papis`` folder.
    """
    return Document(folder=folder_path)


def to_json(document: Document) -> str:
    """Export the document to JSON.

    :returns: a JSON string corresponding to all the entries in the document.
    """
    import json
    return json.dumps(to_dict(document))


def to_dict(document: Document) -> Dict[str, Any]:
    """Convert a document back into a standard :class:`dict`.

    :returns: a :class:`dict` corresponding to all the entries in the document.
    """
    return {key: document[key] for key in document}


def dump(document: Document) -> str:
    """Dump the document into a formatted string.

    The format of the string is not fixed and is meant to be used to display the
    document entries in a consistent way across ``papis``.

    :returns: a string containing all the entries in the document.

    >>> doc = from_data({'title': 'Hello World'})
    >>> dump(doc)
    'title: Hello World'
    """
    import yaml
    from papis.yaml import Dumper   # type: ignore[attr-defined]

    data = dict(document)

    # NOTE: popping some usually very long and unhelpful fields
    data.pop("citations", None)
    data.pop("abstract", None)
    data.pop("papis_id", None)

    return str(yaml.dump(data,
                         Dumper=Dumper,
                         allow_unicode=True,
                         default_flow_style=False)).strip()


def delete(document: Document) -> None:
    """Delete a document from the filesystem.

    This function delete the main folder of the document (recursively), but it
    does not delete the in-memory version of the document.
    """
    folder = document.get_main_folder()
    if folder:
        import shutil
        shutil.rmtree(folder)


def describe(document: Union[Document, Dict[str, Any]]) -> str:
    """
    :returns: a string description of the current document using
        :confval:`document-description-format`.
    """
    return papis.format.format(
        papis.config.getstring("document-description-format"),
        document, default=document.get("title", str(document)))


def move(document: Document, path: str) -> None:
    """Move the *document* to a new main folder at *path*.

    This supposes that the document exists in the location
    ``document.get_main_folder()`` and will change the folder in the input
    *document* as a result.

    :param path: absolute path where the document should be moved to. This
        path is expected to not exist yet and will be created by this function.

    >>> doc = from_data({'title': 'Hello World'})
    >>> doc.set_folder('path/to/folder')
    >>> import tempfile; newfolder = tempfile.mkdtemp()
    >>> move(doc, newfolder)
    Traceback (most recent call last):
    ...
    FileExistsError: There is already...
    """
    folder = document.get_main_folder()
    if not folder:
        return

    path = os.path.expanduser(path)
    if os.path.exists(path):
        raise FileExistsError(
            "There is already a document at '{}' that should be checked. A temporary"
            "document has been stored at '{}'"
            .format(path, folder)
        )

    import shutil
    shutil.move(folder, path)

    # Let us chmod it because it might come from a temp folder
    # and temp folders are per default 0o600
    os.chmod(path, papis.config.getint("dir-umask") or 0o600)
    document.set_folder(path)


def sort(docs: Sequence[Document], key: str, reverse: bool = False) -> List[Document]:
    """Sort a list of documents by the given *key*.

    The sort is performed on the key with a priority given to the type of the
    value. If the key does not exist in the document, this is given the lowest
    priority and left at the end of the list.

    :param docs: a sequence of documents.
    :param key: a key in the documents by which to sort.
    :param reverse: if *True*, the sorting is done in reverse order (descending
        instead of ascending).

    :returns: a list of documents sorted by *key*.
    """
    from datetime import datetime
    default_sort_key = (
        _SortPriority.Missing, datetime.fromtimestamp(0), 0, "")

    from contextlib import suppress

    def document_sort_key(doc: Document) -> Tuple[int, datetime, int, str]:
        priority, date, int_value, str_value = default_sort_key

        value = doc.get(key, None)
        if value is not None:
            str_value = str(value)

            if key == "time-added":
                with suppress(ValueError):
                    date = datetime.strptime(str_value, papis.strings.time_format)
                    priority = _SortPriority.Date
            else:
                try:
                    int_value = int(str_value)
                    priority = _SortPriority.Int
                except ValueError:
                    priority = _SortPriority.Other

        return (
            -priority.value if reverse else priority.value,
            date, int_value, str_value)

    logger.debug("Sorting %d documents.", len(docs))
    return sorted(docs, key=document_sort_key, reverse=reverse)


def new(folder_path: str,
        data: Dict[str, Any],
        files: Optional[Sequence[str]] = None) -> Document:
    """Creates a complete document with data and existing files.

    The document is saved to the filesystem at *folder_path* and all the given
    files are copied over to the main folder.

    :param folder_path: a main folder for the document.
    :param data: a :class:`dict` with key and values to be used as metadata
        in the document.
    :param files: a sequence of files to add to the document.
    :raises FileExistsError: if *folder_path* already exists.
    """

    if files is None:
        files = []

    os.makedirs(folder_path)

    import shutil
    doc = Document(folder=folder_path, data=data)
    doc["files"] = []

    for f in files:
        shutil.copy(f, os.path.join(folder_path))
        doc["files"].append(os.path.basename(f))

    doc.save()
    return doc

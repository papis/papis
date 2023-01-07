"""Module defining the main document type.
"""
import os
import re
from typing import (
    List, Dict, Any, Optional, Union, NamedTuple, Callable, Tuple)

from typing_extensions import TypedDict

import papis
import papis.config
import papis.logging

logger = papis.logging.get_logger(__name__)

KeyConversion = TypedDict(
    "KeyConversion", {"key": Optional[str],
                      "action": Optional[Callable[[Any], Any]]}
)
EmptyKeyConversion = {"key": None, "action": None}  # type: KeyConversion
KeyConversionPair = NamedTuple(
    "KeyConversionPair",
    [("foreign_key", str), ("list", List[KeyConversion])]
)


def keyconversion_to_data(conversion_list: List[KeyConversionPair],
                          data: Dict[str, Any],
                          keep_unknown_keys: bool = False) -> Dict[str, Any]:
    """Function to convert general dictionaries into a papis document.

    This can be used for instance when parsing a website and
    writing a KeyConversionPair to be input to this function.
    """

    new_data = {}

    for key_pair in conversion_list:

        foreign_key = key_pair.foreign_key
        if foreign_key not in data:
            continue

        for conv_data in key_pair.list:
            papis_key = conv_data.get("key") or foreign_key  # type: str
            papis_value = data[foreign_key]

            action = conv_data.get("action")
            if action:
                try:
                    new_value = action(papis_value)
                except Exception as ex:
                    logger.debug("Error while trying to parse '%s' (%s)",
                                 papis_key, ex)
                    new_value = None
            else:
                new_value = papis_value

            if isinstance(new_value, str):
                new_value = new_value.strip()

            if new_value:
                new_data[papis_key] = new_value

    if keep_unknown_keys:
        for key, value in data.items():
            if key in [c.foreign_key for c in conversion_list]:
                continue
            new_data[key] = value

    if "author_list" in new_data:
        new_data["author"] = author_list_to_author(new_data)

    return new_data


def author_list_to_author(data: Dict[str, Any]) -> str:
    """Convert a list of authors into a single author string.
    """
    author = ""
    separator = papis.config.get("multiple-authors-separator")
    separator_fmt = papis.config.get("multiple-authors-format")
    if separator is None or separator_fmt is None:
        raise Exception(
            "You have to define 'multiple-author-separator'"
            " and 'multiple-author-format'")
    if "author_list" in data:
        author = (
            separator.join([
                separator_fmt.format(au=author)
                for author in data["author_list"]
            ])
        )
    return author


def split_authors_name(
        authors: List[str], separator: str = "and") -> List[Dict[str, str]]:
    """
    Convert a list of authors to papis formatted data.

    :arg authors: A list of single author names or multiple authors separated
        by *separator*.
    """
    from bibtexparser.customization import splitname

    author_list = []
    for subauthors in authors:
        for author in re.split(r"\s+{}\s+".format(separator), subauthors):
            parts = splitname(author)
            given = " ".join(parts["first"])
            family = " ".join(parts["von"] + parts["last"] + parts["jr"])

            author_list.append({"family": family, "given": given})

    return author_list


class DocHtmlEscaped(Dict[str, Any]):
    """
    Small helper class to escape html elements.

    >>> DocHtmlEscaped(from_data({"title": '> >< int & "" "'}))['title']
    '&gt; &gt;&lt; int &amp; &quot;&quot; &quot;'
    """

    def __init__(self, doc: Any) -> None:
        self.__doc = doc

    def __getitem__(self, key: str) -> str:
        return (
            str(self.__doc[key])
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


class Document(Dict[str, Any]):

    """Class implementing the entry abstraction of a document in a library.
    It is basically a python dictionary with more methods.
    """

    subfolder = ""  # type: str
    _info_file_path = ""  # type: str

    def __init__(self, folder: Optional[str] = None,
                 data: Optional[Dict[str, Any]] = None) -> None:
        self._folder = None  # type: Optional[str]

        if folder is not None:
            self.set_folder(folder)
            self.load()

        if data is not None:
            self.update(data)

    def __missing__(self, key: str) -> str:
        """
        If key is not defined, return empty string
        """
        return ""

    @property
    def html_escape(self) -> DocHtmlEscaped:
        return DocHtmlEscaped(self)

    def get_main_folder(self) -> Optional[str]:
        """Get full path for the folder where the document and the information
        is stored.
        :returns: Folder path
        """
        return self._folder

    def set_folder(self, folder: str) -> None:
        """Set document's folder. The info_file path will be accordingly set.

        :param folder: Folder where the document will be stored, full path.
        """
        self._folder = folder
        self._info_file_path = os.path.join(
            folder,
            papis.config.getstring("info-name"))
        self.subfolder = (self._folder
                              .replace(os.path.expanduser("~"), "")
                              .replace("/", " "))

    def get_main_folder_name(self) -> Optional[str]:
        """Get main folder name where the document and the information is
        stored.
        :returns: Folder name
        """
        folder = self.get_main_folder()
        return os.path.basename(folder) if folder else None

    def has(self, key: str) -> bool:
        """Check if the information file has some key defined.

        :param key: Key name to be checked
        :returns: True/False

        """
        return key in self

    def save(self) -> None:
        """Saves the current document's information into the info file.
        """
        # FIXME: fix circular import in papis.yaml
        import papis.yaml
        papis.yaml.data_to_yaml(self.get_info_file(),
                                {key: self[key] for key in self if self[key]})

    def get_info_file(self) -> str:
        """Get full path for the info file
        :returns: Full path for the info file
        """
        return self._info_file_path

    def get_files(self) -> List[str]:
        """Get the files linked to the document, if any.

        :returns: List of full file paths
        """
        if not self.has("files"):
            return []
        files = (self["files"]
                 if isinstance(self["files"], list)
                 else [self["files"]])
        folder = self.get_main_folder()
        return [os.path.join(folder, fl) for fl in files] if folder else []

    def load(self) -> None:
        """Load information from info file
        """
        import papis.yaml
        if not os.path.exists(self.get_info_file()):
            return
        try:
            data = papis.yaml.yaml_to_data(self.get_info_file(),
                                           raise_exception=True)
        except Exception as ex:
            logger.error(
                "Error reading yaml file in '%s'. Please check it!\n%s",
                self.get_info_file(), ex)
        else:
            for key in data:
                self[key] = data[key]


def from_folder(folder_path: str) -> Document:
    """Construct a document object from a folder

    :param folder_path: Full path to a valid papis folder
    :returns: A papis document
    """
    return Document(folder=folder_path)


def to_json(document: Document) -> str:
    """Export information into a json string

    :param document: Papis document
    :returns: Json formatted info file
    """
    import json
    return json.dumps(to_dict(document))


def to_dict(document: Document) -> Dict[str, Any]:
    """Gets a python dictionary with the information of the document

    :param document: Papis document
    :returns: Python dictionary
    """
    return {key: document[key] for key in document}


def dump(document: Document) -> str:
    """Return information string without any obvious format

    :param document: Papis document
    :returns: String with document's information

    >>> doc = from_data({'title': 'Hello World'})
    >>> dump(doc)
    'title:     Hello World'
    """
    # NOTE: this tries to align all the values to the next multiple of 4 of the
    # longest key length, for a minimum of visual consistency
    width = max(len(key) for key in document)
    width = (width // 4 + 2) * 4 - 1

    return "\n".join([
        "{:{}}{}".format("{}:".format(key), width, value)
        for key, value in sorted(document.items())
        ])


def delete(document: Document) -> None:
    """This function deletes a document from disk.

    :param document: Papis document
    """
    folder = document.get_main_folder()
    if folder:
        import shutil
        shutil.rmtree(folder)


def describe(document: Union[Document, Dict[str, Any]]) -> str:
    """Return a string description of the current document
    using the document-description-format
    """
    return papis.format.format(
        papis.config.getstring("document-description-format"),
        document)


def move(document: Document, path: str) -> None:
    """This function moves a document to path, it supposes that
    the document exists in the location ``document.get_main_folder()``.
    Warning: This method will change the folder in the document object too.

    :param document: Papis document
    :param path: Full path where the document will be moved to

    >>> doc = from_data({'title': 'Hello World'})
    >>> doc.set_folder('path/to/folder')
    >>> import tempfile; newfolder = tempfile.mkdtemp()
    >>> move(doc, newfolder)
    Traceback (most recent call last):
    ...
    Exception: There is already...
    """
    path = os.path.expanduser(path)
    if os.path.exists(path):
        raise Exception(
            "There is already a document in {0}, please check it,\n"
            "a temporary papis document has been stored in {1}".format(
                path, document.get_main_folder()
            )
        )
    folder = document.get_main_folder()
    if folder:
        import shutil
        shutil.move(folder, path)
        # Let us chmod it because it might come from a temp folder
        # and temp folders are per default 0o600
        os.chmod(path, papis.config.getint("dir-umask") or 0o600)
        document.set_folder(path)


def from_data(data: Union[Document, Dict[str, Any]]) -> Document:
    """Construct a document object from a dictionary.

    :param data: A dictionary to be copied to a new document. If this is already
        a document, a (deep) copy is performed.
    """
    if isinstance(data, Document):
        return Document(folder=data.get_main_folder(), data=data)
    else:
        return Document(data=data)


def sort(docs: List[Document], key: str, reverse: bool) -> List[Document]:
    # The tuple returned by the _sort_for_key function represents:
    # (ranking, integer value, string value)
    # Rankings are:
    #   date:   0 (come first)
    #   integers:    2 (come after integers)
    #   strings:    3 (come after integers)
    #   None:       4 (come last)
    sort_rankings = {
        "date": 0,
        "int": 1,
        "string": 2,
        "None": 3
    }

    # Preserve the ordering of types even if --reverse is used.
    if reverse:
        for sort_type in sort_rankings:
            sort_rankings[sort_type] = -sort_rankings[sort_type]

    import datetime
    zero_date = datetime.datetime.fromtimestamp(0)

    def _sort_for_key(key: str, doc: Document
                      ) -> Tuple[int, datetime.datetime, int, str]:
        from contextlib import suppress
        if key in doc:
            if key == "time-added":
                with suppress(ValueError):
                    date_value = \
                        datetime.datetime.strptime(str(doc[key]),
                                                   papis.strings.time_format)
                    return (sort_rankings["date"],
                            date_value, 0, str(doc[key]))

            if str(doc[key]).isdigit():
                return (sort_rankings["int"],
                        zero_date,
                        int(doc[key]),
                        str(doc[key]))
            else:
                return (sort_rankings["string"],
                        zero_date,
                        0,
                        str(doc[key]))
        else:
            # The key does not appear in the document, ensure
            # it comes last.
            return (sort_rankings["None"], zero_date, 0, "")
    logger.debug("Sorting %d documents", len(docs))
    return sorted(docs, key=lambda d: _sort_for_key(key, d), reverse=reverse)


def new(folder_path: str, data: Dict[str, Any],
        files: Optional[List[str]] = None) -> Document:
    """
    Creates a document at a given folder with data and
    some existing files.

    :param folder_path: A folder path, if non existing it will be created
    :param data: Dictionary with key and values to be updated
    :param files: Existing paths for files
    :raises FileExistsError: If folder_path exists
    """
    if files is None:
        files = []

    os.makedirs(folder_path)

    import shutil
    doc = Document(folder=folder_path, data=data)
    doc["files"] = []
    for _file in files:
        shutil.copy(_file, os.path.join(folder_path))
        doc["files"].append(os.path.basename(_file))
    doc.save()
    return doc

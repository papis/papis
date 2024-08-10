import os
import pathlib
import sys
from typing import Iterable, Iterator, Literal, List, Optional, Union
from warnings import warn

import papis.config
import papis.logging
from papis.document import DocumentLike
from papis.document import from_data

logger = papis.logging.get_logger(__name__)

#: A union type for allowable paths.
PathLike = Union[pathlib.Path, str]

# NOTE: private error codes for Windows
WIN_ERROR_PRIVILEGE_NOT_HELD = 1314


def unique_suffixes(chars: Optional[str] = None, skip: int = 0) -> Iterator[str]:
    """Creates an infinite list of suffixes based on *chars*.

    This creates a generator object capable of iterating over lists to
    create unique products of increasing cardinality
    (see `here <https://stackoverflow.com/questions/14381940/python-pair-alphabets-after-loop-is-completed>`__).
    This is mainly intended to create suffixes for existing strings, e.g. file names,
    to ensure uniqueness.

    :param chars: list to iterate over
    :param skip: number of suffices to skip (negative integers are set to 0).

    >>> import string
    >>> s = unique_suffixes(string.ascii_lowercase)
    >>> next(s)
    'a'
    >>> s = unique_suffixes(skip=3)
    >>> next(s)
    'd'
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
        in the path (defaults to :confval:`doc-paths-word-separator`).
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
    if sys.version_info >= (3, 9):
        return pathlib.Path(path).is_relative_to(other)

    # NOTE: this should give the same result as above for older versions
    try:
        return not os.path.relpath(path, start=other).startswith("..")
    except ValueError:
        return False


def symlink(src: PathLike, dst: PathLike) -> None:
    """Create a symbolic link pointing to *src* named *dst*.

    This is a simple wrapper around :func:`os.symlink` that attempts to give
    better error messages on different platforms. For example, it offers
    suggestions for some missing privilege issues.

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


def get_document_file_name(
        doc: DocumentLike,
        orig_path: PathLike,
        suffix: str = "", *,
        file_name_format: Optional[Union[str, Literal[False]]] = None,
        base_name_limit: int = 150) -> str:
    """Generate a file name based on *orig_path* for the document *doc*.

    This function will generate a file name for the given file *path* (that
    does not necessarily exist) based on the document data. If the document
    data does not provide the necessary keys for *file_name_format*, then the
    original path will be preserved.

    If resulting path will have the same extension as *orig_path* and will be
    modified by :func:`normalize_path`. The extension is determined using
    :func:`~papis.filetype.get_document_extension`.

    :param orig_path: an input file path
    :param suffix: a suffix to be appended to the end of the new file name.
    :param file_name_format: a format string used to construct a new file name
        from the document data (see :func:`papis.format.format`). This value
        defaults to :confval:`add-file-name` if not provided.
    :param base_name_limit: a maximum character length of the file name. This
        is important on operating systems of filesystems that do not support
        long file names.
    :returns: a new path based on the document data and the *orig_path*.
    """
    orig_path = pathlib.Path(orig_path)

    if file_name_format is None:
        file_name_format = papis.config.get("add-file-name")

    if not file_name_format:
        file_name_format = orig_path.name

    assert isinstance(file_name_format, str)

    from papis.filetype import get_document_extension

    # get formatted file name
    ext = get_document_extension(str(orig_path))
    file_name_base = papis.format.format(file_name_format, doc, default="")

    # ensure the file name is valid and within limits
    file_name_base = normalize_path(file_name_base)
    if not file_name_base:
        file_name_base = normalize_path(orig_path.name)

    if len(file_name_base) > base_name_limit:
        logger.warning(
            "Shortening file name for portability: '%s'.", file_name_base)
        file_name_base = file_name_base[:base_name_limit]

    # ensure we do not add the extension twice
    file_name_path = pathlib.Path(file_name_base)
    if file_name_path.suffix == f".{ext}":
        stem = file_name_path.stem
    else:
        stem = str(file_name_path)

    return "{}{}.{}".format(stem, f"-{suffix}" if suffix else "", ext)


def get_document_hash_folder(
        doc: DocumentLike,
        paths: Optional[Iterable[str]] = None, *,
        file_read_limit: int = 2000,
        seed: Optional[str] = None) -> str:
    warn("'get_document_hash_folder' is deprecated and will be removed. "
         "Use 'papis.paths.get_document_folder' instead.",
         DeprecationWarning, stacklevel=2)

    from papis.id import compute_an_id
    return compute_an_id(from_data(dict(doc)), seed)


def get_document_folder(
        doc: DocumentLike,
        dirname: PathLike, *,
        folder_name_format: Optional[str] = None) -> str:
    """Generate a folder name for the document at *dirname*.

    This function uses :confval:`add-folder-name` to generate a folder name for
    the *doc* at *dirname*. If no folder can be constructed from the format, then
    the document's ``papis_id`` is used instead as a subfolder of *dirname*. The
    ``papis_id`` is guaranteed to be unique.

    :arg doc: the document used on the *folder_name_format*.
    :arg dirname: the base directory in which to generate the document main folder.
    :arg folder_name_format: a format to use for the folder name that will be
        filled in using the given *doc*. If no format is given, we default to
        :confval:`add-folder-name`. This format can have additional subfolders.

    :returns: a folder name for *doc* with the root at *dirname*.
    """
    dirname = os.path.normpath(dirname)
    out_folder_path = dirname

    if folder_name_format is None:
        folder_name_format = papis.config.get("add-folder-name")

    # try to get a folder name from folder_name_format
    if folder_name_format:
        tmp_path = os.path.normpath(os.path.join(dirname, folder_name_format))

        # NOTE: the folder_name_format can contain subfolders, so we go through
        # them one by one and expand them here to get the full path
        # NOTE: we need to go through them one by one because e.g. doc[title]
        # could contain a backslash and ruin the hierarchy -- instead we clean it
        # and remove any such characters from messing up the folder name

        components: List[str] = []
        while tmp_path != dirname and is_relative_to(tmp_path, dirname):
            tmp_component = os.path.basename(tmp_path)

            try:
                tmp_component = papis.format.format(tmp_component, doc)
            except papis.format.FormatFailedError as exc:
                logger.error("Could not format path for document.", exc_info=exc)
                components.clear()
                break
            else:
                components.append(normalize_path(tmp_component))

            tmp_path = os.path.dirname(tmp_path)

        out_folder_path = os.path.normpath(os.path.join(dirname, *components[::-1]))

    # if no folder name could be obtained from the format use papis_id
    if out_folder_path == dirname:
        if folder_name_format:
            logger.error(
                "Could not produce a folder path from the provided data:\n"
                "\tdata: %s", doc)

        logger.info("Falling back to 'papis_id' as a reference folder name.")
        out_folder_path = os.path.join(dirname, doc["papis_id"])

    if not is_relative_to(out_folder_path, dirname):
        raise ValueError(
            "Formatting produced a path outside the root directory: "
            f"'{dirname}' not relative to '{out_folder_path}'")

    return out_folder_path


def _make_unique_folder(out_folder_path: PathLike) -> str:
    """Add a suffix to *out_folder_path* until it is unique."""

    if not os.path.exists(out_folder_path):
        return str(out_folder_path)

    suffix = unique_suffixes()

    out_folder_path_suffix = f"{out_folder_path}-{next(suffix)}"
    while os.path.exists(out_folder_path_suffix):
        out_folder_path_suffix = f"{out_folder_path}-{next(suffix)}"

    return out_folder_path_suffix


def get_document_unique_folder(
        doc: DocumentLike,
        dirname: PathLike, *,
        folder_name_format: Optional[str] = None) -> str:
    """A wrapper around :func:`get_document_folder` that ensures that the
    folder is unique by adding suffixes.

    :returns: a folder name for *doc* with the root at *dirname* that does not
        yet exist on the filesystem.
    """
    out_folder_path = get_document_folder(
        doc, dirname,
        folder_name_format=folder_name_format)

    return _make_unique_folder(out_folder_path)


def _is_remote(uri: str) -> bool:
    return uri.startswith("http://") or uri.startswith("https://")


def rename_document_files(
        doc: DocumentLike,
        in_document_paths: Iterable[str], *,
        file_name_format: Optional[Union[str, Literal[False]]] = None,
        allow_remote: bool = True,
        ) -> List[str]:
    """Rename *in_document_paths* according to *file_name_format* and ensure
    uniqueness.

    Uniqueness is required with respect to the files in *in_document_paths*
    and those in the *doc* itself (under the *files* key). If a repeated file
    name is found, a suffix is generated using :func:`unique_suffixes` and
    appended to the new file.

    :param file_name_format: a format string used to construct a new file name
        from the document data (see :func:`papis.format.format`). This value
        defaults to :confval:`add-file-name` if not provided.
    :param allow_remote: if *True*, *in_document_paths* can also be remote
        URL, that will be downloaded to local files.
    :returns: a list of modified file names form *in_document_paths* that
        are renamed based on *file_name_format* and suffixed for uniqueness.
    """
    if file_name_format is None:
        file_name_format = papis.config.get("add-file-name")

    from collections import Counter

    # find next suffix for each extension
    known_files = set(doc.get("files", []))
    exts = Counter([pathlib.Path(d).suffix for d in known_files])
    suffixes = {ext: unique_suffixes(skip=n - 1) for ext, n in exts.items()}

    from papis.downloaders import download_document

    new_files = []
    for in_file_path in in_document_paths:
        if not in_file_path:
            continue

        if _is_remote(in_file_path):
            if allow_remote:
                local_in_file_path = download_document(in_file_path)
            else:
                local_in_file_path = ""
        else:
            local_in_file_path = in_file_path

        if not local_in_file_path:
            logger.info("Skipping renaming file: '%s'.", in_file_path)
            continue

        # get suffix
        _, ext = os.path.splitext(local_in_file_path)
        isuffix = suffixes.get(ext)
        if not isuffix:
            suffixes[ext] = isuffix = unique_suffixes()

        # ensure a unique file name
        new_filename = get_document_file_name(
            doc, local_in_file_path,
            file_name_format=file_name_format)

        while new_filename in known_files:
            new_filename = get_document_file_name(
                doc, local_in_file_path,
                suffix=next(isuffix),
                file_name_format=file_name_format)

        new_files.append(new_filename)
        known_files.add(new_filename)

    return new_files

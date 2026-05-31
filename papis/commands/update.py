"""
This command allows you to update the document metadata stored in the
``info.yaml`` file. With it, you can either change individual values manually
or update a document with information automatically retrieved from a variety
of sources.

When using it to add information, Papis formatting patterns and Python
expressions can be used. See below examples for more information. The command
also tries to sanitise filenames so that they don't contain any problematic
characters.

Normally, ``papis update`` will prompt you when it encounters an error. If you
want to continue errors without input and apply as many changes as possible,
use the ``--batch`` flag. With this in mind, the command is mostly meant to be
used to apply sweeping changes to a larger number of documents. If you just
want to update a single document, ``papis edit`` might be more appropriate.

Examples
^^^^^^^^

- Search among papers with the tag "classics" and update the author to
  "Einstein, Albert":

    .. code:: sh

        papis update --set author "Einstein, Albert" "tags:classics"

  This will open the picker containing all documents that match the query from
  where you can select the document you want to update.

- Update the journal to "Mass and Energy" for all documents with the journal
  "Energy and Mass":

    .. code:: sh

        papis update --all --set journal "Mass and Energy" "journal:'Energy and Mass'"


  The ``--all`` flag means that the operation is applied to all documents that
  match the query, rather than allowing you to pick one individual document to
  update.

- Update a document automatically and interactively (searching by DOI in
  Crossref or in other sources...):

    .. code:: sh

        papis update --auto "author:dyson"

- Update your document from a DOI using the importer functionality as

    .. code:: sh

        papis update --from doi '10.1103/PhysRev.47.777' 'author:einstein'

  For a list of all supported importers use ``papis update --list-importers``.

- Add the ", Albert" to the author string of a documents matching 'Einstein':

    .. code:: sh

        papis update --set author "{doc[author]}, Albert" Einstein

  The ``papis update`` command tries to format input strings using the configured
  formatter. Here, it is used to get the existing author "Albert" and then add
  the string ", Einstein" to end up with "Einstein, Albert".

- Reset keys to their default values using:

    .. code:: sh

        papis update --reset ref Einstein

  This will reset the value to the default value defined for the key. In the
  above case the "ref" is set to the format described by :confval:`ref-format`.
  Other supported keys are: "author" (gets updated from ``author_list`` and
  :confval:`multiple-authors-format`), "notes" (using :confval:`notes-name`),
  and "files" (using :confval:`add-file-name`). Other keys do not support this
  as they do not have any well-defined default.

- The ``--append`` option can be used to append a string to an existing key:

    .. code:: sh

        papis update --append author ", Albert" Einstein

  This appends ", Albert" to the existing author value. Note that it will be
  appended to the existing value only if it does not already end with that
  exact string (case-sensitive). This avoids appending duplicates by mistake, as
  in the case of lists (below).

- You can also append an item to a list:

    .. code:: sh

        papis update --append tags physics 'author:einstein'

    This adds the tag "physics" to the existing list of tags. If the list
    doesn't yet exist, it will be created. The new tag will only be appended to
    the list if the tag does not already exist (as an exact case-sensitive match).

    The ``--append`` flag needs to know the type of the key it is appending to.
    If the key exists in the document, then the value set in the document
    determines the type. If the key doesn't exist in the document, the command
    looks at the list of types defined in the :confval:`document-field-types`
    (and :confval:`document-field-types-extend`) configuration option. If the
    type cannot be determined in either of these two ways, the command will
    fail.

- To remove an item from a list, use ``--remove``. For example, to remove the
  "physics" tag from the list of document tags, use

    .. code:: sh

        papis update --remove tags physics 'author:einstein'

- To remove a key-value pair entirely, use ``--drop``. For example, to remove all
  tags from documents use

    .. code:: sh

        papis update --drop tags 'author:einstein'

- There is also a convenience option ``--rename`` if you want to rename
  a list item. It's equivalent to doing ``--remove`` and ``--append``, but as
  a single operation:

    .. code:: sh

        papis update --rename tags physics philosophy

  This renames the tag "physics" to "philosophy". Note that the new tag will
  not be added to the list if the original tag doesn't exist.

- The ``--batch`` flag suppresses interactive prompts and skips any document
  that cannot be fully updated. This is useful when applying the same operation
  across many documents where some may not have the expected keys or values:

    .. code:: sh

        papis update --all --batch --remove tags obsolete "tags:obsolete"

  Without ``--batch``, if a document does not have "obsolete" in its tag list
  (or has no ``tags`` key at all), the command pauses and asks whether to
  continue. With ``--batch``, an error is logged, the document is skipped and the
  command moves on to the next one.

  More specifically, ``--batch`` suppresses prompts for the following errors:

  * An operation on a key fails (e.g. trying to ``--remove`` a value that is
    not in the list, ``--append`` to a key of unknown type, or a type
    conversion error from ``--set``). The affected key retains its original
    value and the remaining keys for that document are still processed.
  * A file rename fails (e.g. the file on disk is missing or cannot be moved).
    The whole document is skipped.

  In all cases the command exits with a non-zero status if any document was
  skipped.

Advanced Examples
^^^^^^^^^^^^^^^^^

- When you update the ``files`` or ``notes`` keys, the corresponding files on
  disk are also renamed to match the new value:

    .. code:: sh

        papis update --set notes "my-new-notes.tex" Einstein

  This renames the ``notes`` file on disk from its current name to
  ``my-new-notes.tex`` and updates the ``info.yaml`` file accordingly. The same
  applies when updating ``files``:

    .. code:: sh

        papis update --set files 0:einstein-new.pdf Einstein

  This renames the first file in the document's file list to ``einstein-new.pdf``
  on disk. If the rename fails (e.g. the file does not exist or there is a
  permissions error), the metadata is not updated and an error is reported.

  Note that the ``--reset`` option also triggers a rename when used with
  ``notes`` or ``files``. It renames the files to the names derived from the
  configured :confval:`notes-name` and :confval:`add-file-name` formats
  respectively.

- As an advanced feature, ``papis update`` also supports the parsing of Python
  expressions (such as lists or dictionaries). This can be used as follows:

    .. code:: sh

        papis update --set author_list "[{'family': 'Einstein', 'given': 'Albert'}]"

  Because the above string is a valid Python expression, ``author_list`` is
  updated to a list that contains a dictionary.

- You can use ``--set`` to set a value into a list at a given position:

    .. code:: sh

        papis update --set files 0:some-new-file.pdf Einstein

  This special syntax for ``--set`` only works with keys that are known to be
  lists (as before, based on :confval:`document-field-types` and
  :confval:`document-field-types-extend`). If the key is not a list, then the
  value is treated as a string. This might be unexpected, so make sure you are
  using it for list keys only.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.update:cli
    :prog: papis update
"""
from __future__ import annotations

import ast
import enum
import os
from typing import TYPE_CHECKING, Any, NamedTuple

import click

import papis.cli
import papis.config
import papis.logging

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from papis.document import Document
    from papis.strings import AnyString, FormatPattern

logger = papis.logging.get_logger(__name__)


class OperationError(Exception):
    """Error occurring during validation or application of an operation."""


@enum.unique
class OperationType(enum.Enum):
    """Supported types of operations on document keys."""
    Set = enum.auto()
    Reset = enum.auto()
    Drop = enum.auto()
    Append = enum.auto()
    Remove = enum.auto()
    Rename = enum.auto()


class Operation(NamedTuple):
    """Operation on document keys."""
    optype: OperationType
    key: str
    value: FormatPattern

    to_value: FormatPattern


def _try_eval_value(key: str, value: str) -> Any:
    """Try to use :func:`ast.literal_eval` to evaluate the given string.

    :returns: *value* if the evaluation gives an error, and the evaluated value
        otherwise.
    """
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        logger.debug("Value for key '%s' is not a Python expression: '%s'", key, value)
        return value


def _try_parse_list_element(key: str, value: str) -> tuple[int | None, Any]:
    """Parse a string of the form ``n:list_element`` from *value*.

    :returns: a tuple ``(index, list_element)`` if the parsing succeeded or
        a dummy value of ``(None, value)`` otherwise.
    """
    if ":" not in value:
        return None, value

    index, value = value.split(":", maxsplit=1)
    if not index.isdigit():
        return None, value

    return int(index), _try_eval_value(key, value)


def _apply_operation_set(
        data: dict[str, Any], key: str, vformat: FormatPattern, *,
        field_types: dict[str, type]
    ) -> None:
    """Update the *key* with the given *vformat* in *data* (in place).

    This function also supports some custom behavior:

    * If setting the ``ref`` key, then :func:`papis.bibtex.ref_cleanup` is
      automatically called to clean up the value.
    * If the *key* has a known type (defined by :confval:`document-field-types`),
      then the *value* is automatically converted to that type. This operation
      can fail and an :exc:`OperationError` is raised.
    * If the *value* has the special form ``n:element``, then this is used as an
      indication to insert the ``element`` into the n-th position of the list
      given by *key*.

    The value is always evaluated to a Python expression using :func:`ast.literal_eval`
    if possible.

    :raises OperationError: if any of these operations is not possible or fails
        in some way.
    """
    from papis.format import format
    value: Any = format(vformat, data, default=str(vformat))

    if key == "ref":
        from papis.bibtex import ref_cleanup
        value = ref_cleanup(value)
    else:
        eval_value = _try_eval_value(key, value)
        if (cls := field_types.get(key)) is not None:
            # NOTE: special syntax for lists: `n:value`, where `n` denotes
            # the list index to insert this value at
            doc_value = data.get(key)
            if issubclass(cls, list):
                index, list_value = _try_parse_list_element(key, value)
                if index is not None:
                    if not isinstance(doc_value, list):
                        raise OperationError(
                            f"cannot use list syntax 'n:value' for document key "
                            f"'{key}' that is not a list ({type(doc_value)})")

                    if not 0 <= index < len(doc_value):
                        raise OperationError(
                            f"list index out of bounds for key '{key}' "
                            f"in value '{value}' (length {len(doc_value)})"
                        )

                    eval_value = list(doc_value)
                    eval_value[index] = list_value

            if type(eval_value) is cls:
                value = eval_value
            else:
                # TODO: this assumes that the constructor for cls is sufficiently
                # simple to allow directly converting the value. Better way?
                try:
                    value = cls(value)
                except Exception:
                    try:
                        value = cls(eval_value)
                    except Exception:
                        raise OperationError(
                            f"failed to convert '{key}' value to {cls}: {value}"
                        ) from None
        else:
            # TODO: do we want to do this? It seems a bit too smart for its own
            # good. Maybe we should let the user decide using a `type:value`
            # sort of syntax if they really want to do that.
            value = eval_value

    logger.debug("Setting key '%s': %s (%s)", key, value, type(value))
    data[key] = value


def _apply_operation_reset(
        data: dict[str, Any], key: str, *,
        folder: str
    ) -> None:
    """Reset the *key* to its default value (in place).

    Most keys do not have a predefined default value. The following keys are
    supported:
    * ``ref``: the reference is recreated using :func:`papis.bibtex.create_reference`.
    * ``author``: the author is regenerated from ``author_list``, if available.
    * ``notes``: the notes file is renamed using :confval:`notes-name`.
    * ``files``: all files are renamed using :confval:`add-file-name`

    :raises OperationError: if any of these operations is not possible or fails
        in some way.
    """
    from papis.format import format

    if key == "ref":
        from papis.bibtex import create_reference
        value: Any = create_reference(data, force=True)
    elif key == "author":
        from papis.document import author_list_to_author
        value = author_list_to_author(data)
    elif key == "notes":
        # NOTE: we do not check if the notes file exists, since it is usually
        # created on demand using the name from the document
        notes_name_format = papis.config.getformatpattern("notes-name")
        value = format(notes_name_format, data)
    elif key == "files":
        # NOTE: we pop the document files so that `rename_document_files` thinks
        # the new set we give is is brand new and starts the suffixes at 0
        files = data.pop("files", None)
        if files:
            files = [os.path.join(folder, filename) for filename in files]
            for filename in files:
                if not os.path.exists(filename):
                    raise OperationError(
                        f"file '{os.path.basename(filename)}' does not exist")

            from papis.paths import rename_document_files
            file_name_format = papis.config.getformatpattern("add-file-name")
            if not file_name_format:
                raise OperationError(
                    "cannot reset 'files' ('add-file-name' not defined in config)")

            value = rename_document_files(
                data, files, file_name_format=file_name_format
            )
        else:
            value = None
    else:
        raise OperationError(f"cannot reset key '{key}' (no known default)")

    data[key] = value


def _apply_operation_drop(
        data: dict[str, Any], key: str
    ) -> None:
    """Remove the *key* from *data* (in place)."""
    if key not in data:
        raise OperationError(f"key '{key}' not in document")

    _ = data.pop(key)


def _apply_operation_append(
        data: dict[str, Any], key: str, vformat: FormatPattern, *,
        field_types: dict[str, type],
    ) -> None:
    """Append a *value* to the *key* in *data* (in place).

    A key can only be appended to if its type is known through
    :confval:`document-field-types`. This type must then match the actual type
    of the value in *data*. If they match, then
    * If the type is :class:`str`, then the *value* is simply concatenated at the
      end of the string (no separator is added) if the string does not already
      end with *value*.
    * If the type is :class:`list`, then the *value* is appended to the list if
      it does not exist in the list already.

    The value is always evaluated to a Python expression using :func:`ast.literal_eval`
    if possible.

    :raises OperationError: if any of these operations is not possible or fails
        in some way.
    """
    if key not in field_types and key not in data:
        logger.info(
            "Please use `papis update --set` instead or add the key type "
            "to the `document-field-types` configuration setting "
            "(or `document-field-types-extend`)."
        )
        raise OperationError(f"cannot append to key '{key}' of unknown type")

    from papis.format import format
    value: Any = format(vformat, data, default=str(vformat))

    field_type = field_types.get(key)
    doc_type = type(data[key]) if key in data else None
    if doc_type and field_type and doc_type is not field_type:
        raise OperationError(
            f"key '{key}' does not have expected type '{field_type.__name__}': "
            f"{doc_type.__name__}"
        )

    field_type = field_type or doc_type
    assert field_type is not None

    if issubclass(field_type, str):
        doc_value = data.get(key, "")
        if not doc_value.endswith(value):
            value = f"{doc_value}{value}"
    elif issubclass(field_type, list):
        doc_value = data.get(key, [])

        # NOTE: ensure we do not add duplicates to the list, but if there are any
        # just leave them alone (maybe a job for `papis doctor`)
        if value in doc_value:
            value = doc_value
        else:
            value = _try_eval_value(key, value)
            if value in doc_value:
                value = doc_value
            else:
                value = [*doc_value, value]
    else:
        raise OperationError(
            f"cannot append to key '{key}' of type '{field_type.__name__}'")

    data[key] = value


def _apply_operation_remove(
    data: dict[str, Any], key: str, vformat: FormatPattern
    ) -> int:
    """Remove the *value* from the *key* in *data* (in place).

    This operation removes a given value from a list in *data*. If the given
    key is not a list, then the operation is not allowed.

    :raises OperationError: if any of these operations is not possible or fails
        in some way.
    """

    if key not in data:
        raise OperationError(f"cannot remove from non-existent key '{key}'")

    doc_value = data[key]
    if not isinstance(doc_value, list):
        raise OperationError(f"key '{key}' is not a list: {type(doc_value)}")

    from papis.format import format
    value = format(vformat, data, default=str(vformat))

    try:
        idx = doc_value.index(value)
    except ValueError:
        value = _try_eval_value(key, value)
        try:
            idx = doc_value.index(value)
        except ValueError:
            raise OperationError(f"key '{key}' does not contain '{value}'") from None

    data[key].pop(idx)
    return idx


def _apply_operation_rename(
        data: dict[str, Any],
        key: str, from_vformat: FormatPattern, to_vformat: FormatPattern
    ) -> None:
    """Rename an element from a list in *data* (in place).

    If the given *key* is not a list, then this operation is not allowed. Also,
    if the value to be removed from the list does not exist, it will not be
    added.

    :raises OperationError: if any of these operations is not possible or fails
        in some way.
    """
    from papis.format import format

    idx = _apply_operation_remove(data, key, from_vformat)

    # NOTE: if we get here, it means that the value was in the document, so we
    # can proceed to insert it back in.
    to_value: Any = format(to_vformat, data, default=str(to_vformat))
    to_value = _try_eval_value(key, to_value)

    data[key].insert(idx, to_value)


def _process_command_line_operations(
        options: Sequence[_Option], *,
        to_set: Iterable[tuple[str, AnyString]],
        to_reset: Iterable[str],
        to_drop: Iterable[str],
        to_append: Iterable[tuple[str, AnyString]],
        to_remove: Iterable[tuple[str, AnyString]],
        to_rename: Iterable[tuple[str, AnyString, AnyString]],
    ) -> Sequence[tuple[str, Sequence[Operation]]]:
    """
    :returns: a sequence of ``(key, ops)`` aggregated from the input iterables.
    """
    from papis.strings import process_format_pattern_pair

    to_set = iter(to_set)
    to_reset = iter(to_reset)
    to_drop = iter(to_drop)
    to_append = iter(to_append)
    to_remove = iter(to_remove)
    to_rename = iter(to_rename)

    ops: dict[str, list[Operation]] = {}
    for option in options:
        if option.name == "to_set":
            key, value = next(to_set)
            key, value = process_format_pattern_pair(key, value)

            ops.setdefault(key, []).append(
                Operation(OperationType.Set, key, value, value))
        elif option.name == "to_reset":
            key = next(to_reset)
            key, value = process_format_pattern_pair(key, "")

            ops.setdefault(key, []).append(
                Operation(OperationType.Reset, key, value, value))
        elif option.name in {"to_drop", "drop"}:
            # NOTE: "drop" is added to handle `papis tag`, which just has a
            # --drop flag, but not a `--drop key` type option
            key = next(to_drop)
            key, value = process_format_pattern_pair(key, "")

            ops.setdefault(key, []).append(
                Operation(OperationType.Drop, key, value, value))
        elif option.name == "to_append":
            key, value = next(to_append)
            key, value = process_format_pattern_pair(key, value)

            ops.setdefault(key, []).append(
                Operation(OperationType.Append, key, value, value))
        elif option.name == "to_remove":
            key, value = next(to_remove)
            key, value = process_format_pattern_pair(key, value)

            ops.setdefault(key, []).append(
                Operation(OperationType.Remove, key, value, value))
        elif option.name == "to_rename":
            key, from_value, to_value = next(to_rename)
            key, from_value = process_format_pattern_pair(key, from_value)
            key, to_value = process_format_pattern_pair(key, to_value)

            ops.setdefault(key, []).append(
                Operation(OperationType.Rename, key, from_value, to_value))
        else:
            logger.debug("Unsupported option: %s.", option.name)

    return tuple((key, tuple(value)) for key, value in ops.items())


def _apply_operations(
        document: Document,
        key_ops: Sequence[tuple[str, Sequence[Operation]]], *,
        field_types: dict[str, type] | None = None,
        continue_on_error: bool = False,
    ) -> dict[str, Any]:
    if field_types is None:
        field_types = {}

    # NOTE: we need to make a deepcopy here, since the document can have nested
    # lists and dictionaries and we do not want to worry about it when applying
    from copy import deepcopy
    new_data = deepcopy(dict(document))

    from papis.document import describe
    folder = document.get_main_folder()

    if not folder:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(document))

    from papis.tui.utils import confirm as ask_confirm

    for key, ops in key_ops:
        orig_value = new_data.get(key)

        for op in ops:
            try:
                if op.optype == OperationType.Set:
                    _apply_operation_set(
                        new_data, op.key, op.value, field_types=field_types)
                elif op.optype == OperationType.Reset:
                    _apply_operation_reset(
                        new_data, op.key, folder=folder)
                elif op.optype == OperationType.Drop:
                    _apply_operation_drop(new_data, op.key)
                elif op.optype == OperationType.Append:
                    _apply_operation_append(
                        new_data, op.key, op.value, field_types=field_types)
                elif op.optype == OperationType.Remove:
                    _apply_operation_remove(new_data, op.key, op.value)
                elif op.optype == OperationType.Rename:
                    _apply_operation_rename(new_data, op.key, op.value, op.to_value)
                else:
                    raise TypeError(f"unknown operation type: {type(op)}")
            except OperationError as exc:
                logger.error("Failed '%s' operation on key '%s': %s (doc: %s).",
                             op.optype.name, key, exc,
                             describe(document))

                if continue_on_error:
                    # restore value and move on to the next key
                    if orig_value is None:
                        new_data.pop(key, None)
                    else:
                        new_data[key] = orig_value

                    break
                else:
                    if ask_confirm(
                        "Updating document failed with the above error. Continue?"
                    ):
                        break
                    else:
                        raise

    return new_data


def _rename_files_safely(folder: str,
                         from_files: Sequence[str],
                         to_files: Sequence[str]) -> None:
    import shutil
    import tempfile

    # NOTE: this does a two-phase rename that is safe-ish against collisions
    #
    # Phase 1: move every original file into a temporary directory.
    #   On error, if any of the moves fail, we roll back everything.
    #
    # Phase 2: move each file from the temp directory to its final destination.
    #   On error, if any of the moves fails, we roll back everything.
    #
    # NOTE: the rollbacks can still fail, in which case we're in trouble. However,
    # this is meant to guard against overwriting files, not against power blackouts
    # or other catastrophic failures..

    with tempfile.TemporaryDirectory(prefix="papis-update-tmp-") as tmpdirname:
        to_rename: list[tuple[str, str]] = []

        # Phase 1: move original out of the folder into temp
        try:
            for from_file, to_file in zip(from_files, to_files, strict=True):
                if from_file == to_file:
                    continue

                orig_path = os.path.join(folder, from_file)
                if not os.path.exists(orig_path):
                    raise FileNotFoundError(f"document file not found: {from_file}")

                tmp_path = os.path.join(tmpdirname, from_file)
                shutil.move(orig_path, tmp_path)

                to_rename.append((tmp_path, os.path.join(folder, to_file)))
        except Exception:
            # if an error occurred, just move back the files we've handled so far
            for from_path, _ in to_rename:
                from_file = os.path.basename(from_path)
                to_path = os.path.join(folder, from_file)
                shutil.move(from_path, to_path)

            raise

        # Phase 2: move from temp to final destinations.
        renamed: list[tuple[str, str]] = []
        try:
            while to_rename:
                from_path, to_path = to_rename[-1]
                shutil.move(from_path, to_path)

                to_rename.pop()
                renamed.append((from_path, to_path))
        except Exception:
            # move back the files that got renamed into *folder*
            for from_path, to_path in reversed(renamed):
                from_file = os.path.basename(from_path)
                orig_path = os.path.join(folder, from_file)
                shutil.move(to_path, orig_path)

            # move back the files still in the tmpdir back to *folder*
            for from_path, _ in to_rename:
                from_file = os.path.basename(from_path)
                orig_path = os.path.join(folder, from_file)
                shutil.move(from_path, orig_path)

            raise


def run(
    document: Document,
    data: dict[str, Any] | None = None, *,
    git: bool = False,
    auto_doctor: bool = False,
    overwrite: bool = False,
) -> None:
    """Updates a document in the Papis library with the given *data*.

    The entries in *data* can be further modified or not ignored when updating
    the *document*. The following rules apply:

    * If a value in *data* is *None*, then it will be removed from the *document*.
    * If *auto_doctor* is *True*, then all the default auto-fixers
      (see :confval:`doctor-default-checks`) will be applied to the document. This
      can modify keys that are not in *data*.
    * If the *notes* or *files* keys are updated, any paths in *data* will be
      further normalized using :func:`~papis.paths.normalize_path_part`.
    """
    from papis.document import describe

    if data is None:
        data = {}

    folder = document.get_main_folder()
    info = document.get_info_file()

    if not folder or not info:
        from papis.exceptions import DocumentFolderNotFound

        raise DocumentFolderNotFound(describe(document))

    from papis.paths import normalize_path_part

    # normalize new document files
    if "files" in data:
        data["files"] = [normalize_path_part(filename) for filename in data["files"]]

    if "notes" in data:
        data["notes"] = normalize_path_part(data["notes"])

    # gather all files to rename
    from_files = list(document.get("files", []))
    to_files = list(data.get("files", []))

    if to_files and len(set(to_files)) != len(to_files):
        raise ValueError(f"updated files are not unique: {to_files}")

    if from_files and len(set(from_files)) != len(from_files):
        raise ValueError(f"existing files are not unique: {from_files}")

    # NOTE: if they're not the same length, we do not want to rename files. This
    # is done here, so that adding notes works as expected and they're all renamed
    # atomically if possible. Note that this can never happen when calling from cli()
    if len(from_files) != len(to_files):
        from_files.clear()
        to_files.clear()

    if (to_notes := data.get("notes")) and (from_notes := document.get("notes")):
        if os.path.exists(os.path.join(folder, from_notes)):
            from_files.append(from_notes)
            to_files.append(to_notes)

    # rename files
    # FIXME: this is not great, since len == len is a bad heuristic to figure out
    # if files are renamed. Ideally, we would get a `update_files: dict[str, str]`
    # argument to let us know exactly what needs renaming.
    if from_files and len(from_files) == len(to_files):
        _rename_files_safely(folder, from_files, to_files)

    # update document metadata
    if overwrite:
        document.clear()
    document.update(data)

    # delete all keys that do not have a value
    for key in list(document):
        value = document[key]

        # NOTE: remove any False-y keys from the document, but not:
        # * 0 as an integer
        # * False as a boolean
        if (
                value is None
                or (isinstance(value, str) and not value)
                or (isinstance(value, (list, dict)) and not value)):
            del document[key]

    if auto_doctor:
        from papis.doctor import fix_errors

        logger.info(
            "Running doctor auto-fixers on document: '%s'.", describe(document),
        )
        fix_errors(document)

    from papis.api import save_doc
    save_doc(document)

    if git:
        from papis.git import GitError, add_and_commit as git_add_and_commit

        try:
            git_add_and_commit(
                folder,
                info,
                f"Update information for '{describe(document)}'",
            )
        except GitError as exc:
            logger.error("%s", exc)


# NOTE: these classes are a hack to allow us to recover the real argument order
# from click. By default, when using `multiple=True`, click aggregates all the
# flags into lists for the same type, so any order is lost. Only the parser
# seems to know the original order, so we get it from there.

class _Option(NamedTuple):
    """A :class:`click.Option` look-alike that remembers the argument name."""
    name: str | None


class _TrackingOptionParser(click.parser._OptionParser):
    """A modified option parser that remembers the argument order."""

    def parse_args(self, args: list[str]) -> Any:
        opts, args, order = super().parse_args(args)
        if self.ctx is not None:
            self.ctx.ensure_object(dict)
            self.ctx.obj["param"] = [_Option(param.name) for param in order]

        return opts, args, order


class _OrderedCommand(click.Command):
    """A modified command that uses ``_TrackingOptionParser``."""

    def make_parser(self, ctx: click.Context) -> Any:
        parser = _TrackingOptionParser(ctx)
        for param in self.get_params(ctx):
            param.add_to_parser(parser, ctx)

        return parser


@click.command("update", cls=_OrderedCommand)
@click.help_option("--help", "-h")
@papis.cli.git_option()
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
@papis.cli.bool_flag(
    "--auto",
    help="Automatically select importers and downloaders based on document metadata."
)
@papis.cli.bool_flag(
    "--auto-doctor/--no-auto-doctor",
    help="Apply automatic doctor fixes to newly added documents.",
    default=lambda: papis.config.getboolean("auto-doctor"),
)
@click.option(
    "--from",
    "from_importer",
    help="Add document from a specific importer.",
    type=(str, str),
    nargs=2,
    multiple=True,
    default=(),
)
@papis.cli.bool_flag("--list-importers", help="List all supported importers.")
@click.option(
    "-s", "--set", "to_set",
    help="Set the key to the given value.",
    multiple=True,
    type=(papis.cli.KeyParamType(), papis.cli.FormatPatternParamType()),
)
@click.option(
    "--reset", "to_reset",
    help="Reset keys to their default values.",
    multiple=True,
    type=papis.cli.KeyParamType(),
)
@click.option(
    "-d", "--drop", "to_drop",
    help="Drop a key from the document.",
    multiple=True,
    type=papis.cli.KeyParamType(),
)
@click.option(
    "-p", "--append", "to_append",
    help="Append a value to a document key.",
    multiple=True,
    type=(papis.cli.KeyParamType(), papis.cli.FormatPatternParamType()),
)
@click.option(
    "-r", "--remove", "to_remove",
    help="Remove an item from a list.",
    multiple=True,
    type=(papis.cli.KeyParamType(), papis.cli.FormatPatternParamType()),
)
@click.option(
    "-n", "--rename", "to_rename",
    help="Rename an item in a list.",
    multiple=True,
    type=(papis.cli.KeyParamType(),
          papis.cli.FormatPatternParamType(),
          papis.cli.FormatPatternParamType()),
)
@papis.cli.bool_flag(
    "-b",
    "--batch",
    help="Do not prompt, and skip documents containing errors."
)
@click.pass_context
def cli(
    ctx: click.Context,
    query: str,
    git: bool,
    doc_folder: tuple[str, ...],
    from_importer: list[tuple[str, str]],
    list_importers: bool,
    batch: bool,
    auto: bool,
    auto_doctor: bool,
    to_set: list[tuple[str, AnyString]],
    to_reset: list[str],
    to_drop: list[str],
    to_append: list[tuple[str, AnyString]],
    to_remove: list[tuple[str, AnyString]],
    to_rename: list[tuple[str, AnyString, AnyString]],
    _all: bool,
    sort_field: str | None,
    sort_reverse: bool,
) -> None:
    """Update document metadata."""
    from papis.importer import (
        collect_from_importers,
        fetch_importers,
        get_available_importers,
        get_matching_importers_by_doc,
        get_matching_importers_by_name,
    )
    from papis.tui.utils import confirm as ask_confirm

    if list_importers:
        from papis.commands.list import list_plugins
        for o in list_plugins(show_importers=True, verbose=True):
            click.echo(o)
        return

    # retrieve documents
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all
    )
    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    # retrieve importers
    known_importers = get_available_importers()
    extra_importers = {name for name, _ in from_importer}.difference(known_importers)
    if extra_importers:
        logger.error("Unknown importers chosen with '--from': ['%s'].",
                     "', '".join(extra_importers))
        logger.error("Supported importers are: ['%s'].", "', '".join(known_importers))
        ctx.exit(1)
        return

    if from_importer:
        from_importers = get_matching_importers_by_name(from_importer)
    else:
        from_importers = []

    # retrieve user provided operations
    operations = _process_command_line_operations(
        ctx.obj["param"],
        to_set=to_set,
        to_reset=to_reset,
        to_drop=to_drop,
        to_append=to_append,
        to_remove=to_remove,
        to_rename=to_rename,
    )

    from papis.document import get_document_field_types
    known_field_types = get_document_field_types()

    from papis.document import describe

    ret = 0
    for i, document in enumerate(documents):
        logger.info("[%d/%d] Gathering metadata changes for document: %s.",
                    i + 1, len(documents), describe(document))

        # apply changes to document
        try:
            new_data = _apply_operations(
                document, operations,
                field_types=known_field_types,
                continue_on_error=batch)
        except OperationError:
            # NOTE: this happens if the user interactively said they do not
            # want to continue updating the document, so we just skip it
            ret = 1
            continue
        except Exception:
            # NOTE: this should generally not happen, unless there's a bug or
            # the database is in an inconsistent state, so we just move on
            logger.error("Failed to apply metadata changes to document: %s.",
                         describe(document))
            ret = 1
            continue

        # get metadata from importers and merge them all together
        if from_importer:
            importers = from_importers
        elif auto:
            importers = get_matching_importers_by_doc(document)
        else:
            importers = []

        importers = fetch_importers(importers, download_files=False)
        imported = collect_from_importers(importers, batch=batch, use_files=False)

        # merge user and importer data
        # FIXME: add interactive merging to avoid overwriting user changes
        new_data.update(imported.data)

        logger.info("[%d/%d] Applying metadata changes to document: %s.",
                    i + 1, len(documents), describe(document))

        try:
            # NOTE: data contains all the fields in doc (modified by the flags),
            # so we want to just overwrite it with them => overwrite=True
            run(document, new_data, git=git, auto_doctor=auto_doctor, overwrite=True)
        except OSError as exc:
            logger.error("Failed to rename document files: %s",
                         describe(document), exc_info=exc)
            if batch:
                continue

            if ask_confirm(
                "Failed to rename document files with the above error. Continue?"
            ):
                continue
            else:
                ctx.exit(1)
                return
        except Exception as exc:
            logger.error("Failed to apply changes to document: %s",
                         describe(document), exc_info=exc)
            if batch:
                continue

            if ask_confirm(
                "Failed to apply document with the above error. Continue?"
            ):
                continue
            else:
                ctx.exit(1)
                return

    ctx.exit(ret)

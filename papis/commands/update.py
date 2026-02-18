"""
This command allows you to update the document metadata stored in the
``info.yaml`` file. With it, you can either change individual values manually
or update a document with information automatically retrieved from a variety
of sources.

When using it to add information, Papis formatting patterns and Python
expressions can be used. See below examples for more information. The command
also tries to sanitise filenames so that they don't contain any problematic
characters.

Normally, ``papis update`` will abort on encountering an error. If you want to
skip errors and apply as many changes as possible, use the ``--batch`` flag.
With this in mind, the command is mostly meant to be used to apply sweeping changes
to a larger number of documents. If you just want to update a single document,
``papis edit`` might be more appropriate.

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

- Update your library from a BibTeX file, where many entries may be listed:

    .. code:: sh

        papis update --from bibtex libraryfile.bib

  Papis will try to look for documents in your library that match these
  entries and will ask you for each entry whether you want to update it. If
  you are working with BibTeX files, the ``papis bibtex`` command may be more
  flexible.

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

        papis update --append tags physics

    This adds the tag "physics" to the existing list of tags. If the list
    doesn't yet exist, it will be created. The new tag will only be appended to
    the list if the tag does not already exist (as an exact case-sensitive match).

    The ``--append`` flag needs to know the type of the key it is appending to.
    If the key exists in the document, then the value set in the document
    determines the type. If the key doesn't exist in the document, the command
    looks at the list of types defined in the :confval:`doctor-key-type-keys`
    (and :confval:`doctor-key-type-keys-extend`) configuration option. If the
    type cannot be determined in either of these two ways, the command will
    fail.

- You can use ``--set``` to set a value into a list at a given position:

    .. code:: sh

        papis update --set files 0:some-new-file.pdf Einstein

  This special syntax for ``--set`` only works with keys that are known to be
  lists (as before, based on :confval:`doctor-key-type-keys` and
  :confval:`doctor-key-type-keys-extend`). If the key is not a list, then the
  value is treated as a string. This might be unexpected, so make sure you are
  using it for list keys only.

- To remove an item from a list, use ``--remove``:

    .. code:: sh

        papis update --remove tags physics

  If the tag "physics" is in the list of tags, this command removes it.

- To remove a key-value pair entirely, use ``--drop``:

    .. code:: sh

        papis update --drop tags

  This removes all tags.

- There is also a convenience option ``--rename`` if you want to rename
  a list item. It's equivalent to doing ``--remove`` and ``--append``, but as
  a single operation:

    .. code:: sh

        papis update --rename tags physics philosophy

  This renames the tag "physics" to "philosophy". Note that the new tag will
  not be added to the list if the original tag doesn't exist.

- As an advanced feature, ``papis update`` also supports the parsing of Python
  expressions (such as lists or dictionaries). This can be used as follows:

    .. code:: sh

        papis update --set author_list "[{'family': 'Einstein', 'given': 'Albert'}]"

  Because the above string is a valid Python expression, ``author_list`` is
  updated to a set that contains a dictionary.


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


def _try_parse_list_element(key: str, value: str) -> tuple[int, str | None]:
    """Parse a string of the form ``n:list_element`` from *value*.

    :returns: a tuple ``(index, list_element)`` if the parsing succeeded. Otherwise,
        a dummy value of ``(-1, None)`` is returned.
    """
    if ":" not in value:
        return -1, None

    index, value = value.split(":", maxsplit=1)
    if not index.isdigit():
        return -1, None

    return int(index), _try_eval_value(key, value)


def _apply_set_operation(
        data: dict[str, Any], key: str, vformat: FormatPattern, *,
        key_types: dict[str, type]
    ) -> None:
    """Update the *key* with the given *vformat* in *data* (in place).

    This function also supports some custom behavior:

    * If setting the ``ref`` key, then :func:`papis.bibtex.ref_cleanup` is
      automatically called to clean up the value.
    * If the *key* has a known type (using :confval:`doctor-key-type-keys`), then
      the *value* is automatically converted to that type.
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
        if (cls := key_types.get(key)) is not None:
            # NOTE: special syntax for lists: `n:value`, where `n` denotes
            # the list index to insert this value at
            doc_value = data.get(key)
            if issubclass(cls, list):
                index, list_value = _try_parse_list_element(key, value)
                if list_value is not None:
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
            logger.info("%s: %s (%ss)", key, value, type(value))

    data[key] = value


def _apply_reset_operation(
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
        if not files:
            raise OperationError("document has no attached files")

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
        raise OperationError(f"cannot reset key '{key}' (no known default)")

    data[key] = value


def _apply_drop_operation(
        data: dict[str, Any], key: str
    ) -> None:
    """Remove the *key* from *data* (in place)."""
    if key not in data:
        raise OperationError(f"key '{key}' not in document")

    _ = data.pop(key)


def _apply_append_operation(
        data: dict[str, Any], key: str, vformat: FormatPattern, *,
        key_types: dict[str, type],
    ) -> None:
    """Append a *value* to the *key* in *data* (in place).

    A key can only be appended to if its type is known through
    :confval:`doctor-key-type-keys`. This type must then match the actual type
    of the value in *data*. If they match, then
    * If the type is :class:`str`, then the *value* is simply concatenated at the
      end of the string (no separator is added).
    * If the type is :class:`list`, then the *value* is appended to the list if
      it does not exist in the list already.

    The value is always evaluated to a Python expression using :func:`ast.literal_eval`
    if possible.

    :raises OperationError: if any of these operations is not possible or fails
        in some way.
    """
    if key not in key_types and key not in data:
        logger.info(
            "Please use `papis update --set` instead or add the key type "
            "to the `doctor-key-type-keys` configuration setting "
            "(or `doctor-key-type-keys-extend`)."
        )
        raise OperationError(f"cannot append to key '{key}' of unknown type")

    from papis.format import format
    value: Any = format(vformat, data, default=str(vformat))

    key_type = key_types.get(key)
    doc_type = type(data[key]) if key in data else None
    if doc_type and key_type and doc_type is not key_type:
        raise OperationError(
            f"key '{key}' does not have expected type '{key_type.__name__}': "
            f"{doc_type.__name__}"
        )

    key_type = key_type or doc_type
    assert key_type is not None

    if issubclass(key_type, str):
        doc_value = data.get(key, "")
        if not doc_value.endswith(value):
            value = f"{doc_value}{value}"
    elif issubclass(key_type, list):
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
            f"cannot append to key '{key}' of type '{key_type.__name__}'")

    data[key] = value


def _apply_remove_operation(
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


def _apply_rename_operation(
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

    idx = _apply_remove_operation(data, key, from_vformat)

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
            # --drop flag, but not an `--drop key` type option
            key = next(to_drop)
            key, value = process_format_pattern_pair(key, "")

            ops.setdefault(key, []).append(Operation(
                OperationType.Drop, key, value, value))
        elif option.name == "to_append":
            key, value = next(to_append)
            key, value = process_format_pattern_pair(key, value)

            ops.setdefault(key, []).append(Operation(
                OperationType.Append, key, value, value))
        elif option.name == "to_remove":
            key, value = next(to_remove)
            key, value = process_format_pattern_pair(key, value)

            ops.setdefault(key, []).append(Operation(
                OperationType.Remove, key, value, value))
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
        key_types: dict[str, type] | None = None,
        continue_on_error: bool = False,
    ) -> dict[str, Any]:
    if key_types is None:
        key_types = {}

    # NOTE: we need to make a deepcopy here, since the document can have nested
    # lists and dictionaries and we do not want to worry about it when applying
    from copy import deepcopy
    new_data = deepcopy(dict(document))

    from papis.document import describe
    folder = document.get_main_folder()

    if not folder:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(document))

    for key, ops in key_ops:
        # orig_value = new_data.get(key)

        for op in ops:
            try:
                if op.optype == OperationType.Set:
                    _apply_set_operation(
                        new_data, op.key, op.value, key_types=key_types)
                elif op.optype == OperationType.Reset:
                    _apply_reset_operation(
                        new_data, op.key, folder=folder)
                elif op.optype == OperationType.Drop:
                    _apply_drop_operation(new_data, op.key)
                elif op.optype == OperationType.Append:
                    _apply_append_operation(
                        new_data, op.key, op.value, key_types=key_types)
                elif op.optype == OperationType.Remove:
                    _apply_remove_operation(new_data, op.key, op.value)
                elif op.optype == OperationType.Rename:
                    _apply_rename_operation(new_data, op.key, op.value, op.to_value)
                else:
                    raise TypeError(f"unknown operation type: {type(op)}")
            except OperationError as exc:
                logger.error("Failed '%s' operation on key '%s': %s (doc: %s).",
                             op.optype.name, key, exc,
                             describe(document))

                if continue_on_error:
                    continue
                    # FIXME: do we want to continue on error? This could leave
                    # the key in an unexpected state between all and no changes
                    # restore value and move on to the next key
                    # if orig_value is None:
                    #     new_data.pop(key, None)
                    # else:
                    #     new_data[key] = orig_value
                    # break
                else:
                    raise

    return new_data


def _rename_files_safely(folder: str,
                         from_files: Sequence[str],
                         to_files: Sequence[str]) -> None:
    import shutil
    import tempfile

    with tempfile.TemporaryDirectory(prefix="papis-update-tmp-") as tmpdirname:
        # NOTE: this does a two-phase rename:
        # 1. first phase moves files to a temporary directory
        # 2. second phase moves them back with the desired name
        #
        # This should avoid any collisions and other issues like that.

        to_rename_files = []
        for from_file, to_file in zip(from_files, to_files, strict=True):
            if from_file == to_file:
                continue

            from_path = os.path.join(folder, from_file)
            if not os.path.exists(from_path):
                raise FileNotFoundError(f"document file not found: {from_file}")

            to_path = os.path.join(tmpdirname, from_file)
            shutil.move(from_path, to_path)

            to_rename_files.append((to_path, os.path.join(folder, to_file)))

        for from_path, to_path in to_rename_files:
            shutil.move(from_path, to_path)


def run(
    document: Document,
    data: dict[str, Any] | None = None, *,
    git: bool = False,
    auto_doctor: bool = False,
    overwrite: bool = False,
) -> None:
    """Updates a document in the Papis library with the given *data*.

    Note that keys with no value are automatically removed from the document
    before it is saved to disk. Furthermore, if *auto_doctor* is true, the
    items in *data* and *document* could be further modified.
    """
    from papis.document import describe

    if data is None:
        data = {}

    folder = document.get_main_folder()
    info = document.get_info_file()

    if not folder or not info:
        from papis.exceptions import DocumentFolderNotFound

        raise DocumentFolderNotFound(describe(document))

    from papis.paths import normalize_path

    # rename notes files
    if "notes" in data:
        data["notes"] = normalize_path(data["notes"])

    if "notes" in data and "notes" in document:
        from_notes = os.path.join(folder, document["notes"])
        to_notes = os.path.join(folder, data["notes"])

        if from_notes != to_notes and os.path.exists(from_notes):
            os.rename(from_notes, to_notes)

    # rename document files
    if "files" in data:
        data["files"] = [normalize_path(filename) for filename in data["files"]]

    from_files = document.get("files", [])
    to_files = data.get("files", [])

    if to_files and len(set(to_files)) != len(to_files):
        raise ValueError(f"files are not unique: {to_files}")

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
        from papis.commands.doctor import fix_errors

        logger.info(
            "Running doctor auto-fixers on document: '%s'.", describe(document),
        )
        fix_errors(document)

    from papis.api import save_doc
    save_doc(document)

    if git:
        from papis.git import add_and_commit_resource
        add_and_commit_resource(
            folder,
            info,
            f"Update information for '{describe(document)}'",
        )


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

    from papis.commands.doctor import get_key_type_check_keys
    known_key_types = get_key_type_check_keys()

    from papis.document import describe
    processed_documents = []

    for i, document in enumerate(documents):
        logger.info("[%d/%d], Gathering metadata changes for document: %s.",
                    i + 1, len(documents), describe(document))

        # apply changes to document
        try:
            new_data = _apply_operations(
                document, operations,
                key_types=known_key_types,
                continue_on_error=batch)
        except OperationError:
            if batch:
                logger.error("[%s] Failed to apply changes to document. Continuing...",
                             describe(document))
                continue
            else:
                logger.error("[%s] Failed to apply changes to document. Aborting...",
                             describe(document))
                ctx.exit(1)

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

        # FIXME: handle case where nothing changed?
        processed_documents.append((document, new_data))

    for i, (doc, data) in enumerate(processed_documents):
        logger.info("[%d/%d] Applying metadata changes for document: %s.",
                    i + 1, len(processed_documents), describe(doc))

        try:
            # NOTE: data contains all the fields in doc (modified by the flags),
            # so we want to just overwrite it with them => overwrite=True
            run(doc, data, git=git, auto_doctor=auto_doctor, overwrite=True)
        except OSError as exc:
            # FIXME: can we unroll these changes to make sure we did not actually
            # ruin the user's files?
            logger.error("Failed to rename document files: %s",
                         describe(doc), exc_info=exc)
            if not batch:
                ctx.exit(1)
        except Exception as exc:
            logger.error("Failed to apply changes to document: %s",
                         describe(doc), exc_info=exc)
            if not batch:
                ctx.exit(1)

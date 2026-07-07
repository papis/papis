"""
The ``mv`` command is used to move document folders around your library (or to
another library).

It will (except when run with ``--all``) bring up the picker with a list of
documents that match the query. You can then select the document or documents
you'd like to move.

The command works similarly to the Unix
`mv <https://en.wikipedia.org/wiki/Mv_(Unix)>`__ command. Hence, when the
specified target folder exists, the document's current main folder is moved into
the target folder. If the specified target folder doesn't exist, then the
current folder is renamed to the target folder name. Unlike Unix ``mv``, if a
target folder isn't given, it defaults to the :confval:`add-folder-name` pattern,
so ``papis mv QUERY`` renames matching documents to their default folder names.

Folder names are cleaned, so that characters that can lead to invalid file paths
are avoided (see :confval:`doc-paths-extra-chars` for a list of allowed characters
and how to change it). This cleaning applies to all path components,
including any literal subfolders passed to ``--to``. This means and you cannot use
the ``mv`` command to move docs into a folder containing excluded characters.

The ``mv`` command will first check whether moving the folders as specified will
fail. If any errors are encountered, they are displayed and you will
be prompted whether you want to abort or move the unproblematic documents (if any
exist).

Examples
^^^^^^^^

- Query documents by author "Rick Astley" and move some of them. After picking
  the relevant documents, they will be renamed to their default names
  specified by the :confval:`add-folder-name` option.

   .. code:: sh

        papis mv author:"Rick Astley"

- You can use ``--to`` to pass the path of the target folder, relative to the
  library root. Here we'll move a document by the author "Rick Astley" to a
  folder named ``rick-astley``:

   .. code:: sh

        papis mv --to rick-astley author:"Rick Astley"

  If the folder "rick-astley" doesn't exist, then the document's folder will be
  renamed to that so that the new folder becomes "rick-astley". If the folder
  "rick-astley" exists, then the document's folder will be moved into it. If, say,
  the document's folder is currently "rick-s-the-best", then the new folder will
  be "rick-astley/rick-s-the-best".

  If multiple selected documents resolve to the exact same folder name, Papis will
  warn you and skip those documents. Consider the above case when the target folder
  doesn't exist. Here, each document would be renamed to ``rick-astley``, causing
  Papis to skip the documents to avoid collisions. In contrast, if the target folder
  already exists, each document will be placed into its own subfolder (e.g.
  "rick-astley/rick-s-the-best" and "rick-astley/rick-s-very-cool"), so there is
  no risk of collision.

- You can use formatting patterns to generate the folder names. For instance, to
  organise all documents by author "Rick Astley" by year, you can use this command:

   .. code:: sh

        papis mv --to "{doc[year]}" --all author:"Rick Astley"

  Note that the ``--all`` flag means that the picker isn't shown and all
  documents matching the query will be moved.

- You can use the ``--batch`` flag to skip all prompts. You will not be
  prompted if there are problematic moves and all unproblematic moves will
  happen automatically. If an unexpected error occurs while moving a
  document (e.g. a permission error), the command logs a warning and
  continues with the next document instead of aborting.

   .. code:: sh

        papis mv --batch --all author:"Rick Astley"

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.mv:cli
    :prog: papis mv
"""

from __future__ import annotations

import collections
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import click

import papis.cli
import papis.config
import papis.database
import papis.document
import papis.git
import papis.logging
import papis.paths
import papis.tui.utils
from papis.exceptions import DocumentFolderNotFound
from papis.strings import AnyString, no_documents_retrieved_message

if TYPE_CHECKING:
    from papis.document import Document


class PlannedMove(NamedTuple):
    document: Document
    source: Path
    target: Path


logger = papis.logging.get_logger(__name__)


def _check_not_nested(target: Path, lib_dir: Path) -> str | None:
    """Check that *target* would not be placed inside another document folder.

    Walks up from *target.parent* to *lib_dir*. If any ancestor is a
    document folder, this is considered an error.

    :param target: the target path for the document
    :param lib_dir: the root directory of the target library.
    :returns: ``None`` if not nested in a document folder, an error string otherwise
    """
    current = target.parent
    while current not in {lib_dir, current.parent}:
        if papis.document.is_document_folder(current):
            return f"would nest inside another document's folder: {current}"
        current = current.parent
    return None


def _check_target_already_exists(path: Path) -> str | None:
    """Check that *path* doesn't already exist.

    :returns: ``None`` if the path doesn't already exist, an error string otherwise
    """
    if path.exists():
        return f"target already exists: {path}"
    return None


def _rename_target_interactively(
    document: Document,
    default_target: Path,
    lib_dir: Path,
) -> Path:
    """Prompt the user to rename until a valid target is found.

    :param document: the document being moved.
    :param default_target: the default/computed target path (absolute).
    :param lib_dir: the root directory of the target library.
    :returns: a valid absolute target path.
    """
    while True:
        new_name = papis.tui.utils.prompt(
            f"Folder name for '{papis.document.describe(document)}'",
            default=str(default_target.relative_to(lib_dir)),
        )
        new_target = Path(
            papis.paths.get_document_folder(
                document, str(lib_dir), folder_name_format=new_name
            )
        )

        error = _check_not_nested(new_target, lib_dir)
        if error is None:
            error = _check_target_already_exists(new_target)
        if error is None:
            return new_target

        logger.warning(
            "'%s': %s.",
            papis.document.describe(document),
            error,
        )


def _register_move(
    move: PlannedMove,
    moves: dict[Path, PlannedMove],
    conflicts: dict[Path, list[PlannedMove]],
) -> None:
    """Insert *move* into *moves*, or bump it to *conflicts* on collision.

    Resolves the move's target path and checks whether it is already claimed.
    If the slot is free the move goes into *moves*; if occupied the existing
    occupant is moved to *conflicts* together with the new move.
    """
    target_path = move.target.resolve()
    if target_path in moves:
        existing = moves.pop(target_path)
        conflicts[target_path] = [existing, move]
    elif target_path in conflicts:
        conflicts[target_path].append(move)
    else:
        moves[target_path] = move


def run(
    document: Document,
    target_path_abs: str,
    target_library: str | None = None,
    git: bool = False,
) -> None:
    """Move a document's folder to *target_path_abs*.

    :param document: the document to move.
    :param target_path_abs: the target folder path (absolute)
    :param target_library: name of the target library. If ``None``, uses the current
        library.
    :param git: if ``True``, record the move in git history.
    :raises DocumentFolderNotFound: if the document has no main folder on disk.
    :raises FileNotFoundError: if the source folder does not exist.
    :raises FileExistsError: if the target folder already exists. This will also be
        raised if the target folder is the same as the source folder.
    """
    if target_library is None:
        target_library = papis.config.get_lib_name()

    source_lib_dir = Path(papis.config.get_lib().path)

    target_lib_dir = Path(papis.config.get_lib_from_name(target_library).path)

    doc_folder_old = document.get_main_folder()
    if not doc_folder_old:
        raise DocumentFolderNotFound(papis.document.describe(document))

    main_folder_old = Path(doc_folder_old)
    main_folder_new = Path(target_path_abs)

    if not main_folder_old.exists():
        raise FileNotFoundError(f"Source folder does not exist: '{main_folder_old}'")

    if main_folder_new.exists():
        raise FileExistsError(f"Target folder already exists: '{main_folder_new}'")

    source_library = papis.config.get_lib_name()
    papis.config.set_lib_from_name(target_library)

    main_folder_new.parent.mkdir(
        parents=True,
        exist_ok=True,
        # NOTE: 0o755 is default, but explicitness is needed to avoid type error
        mode=papis.config.getint("dir-umask") or 0o755,
    )

    papis.config.set_lib_from_name(source_library)

    if target_lib_dir == source_lib_dir:
        shutil.move(main_folder_old, main_folder_new)
    else:
        shutil.move(doc_folder_old, main_folder_new)

    source_db = papis.database.get()
    source_db.delete(document)

    target_db = papis.database.get(library_name=target_library)

    document.set_folder(str(main_folder_new))

    target_db.add(document)

    if git:
        if target_lib_dir == source_lib_dir:
            papis.git.rm_cached(str(source_lib_dir),
                                str(main_folder_old),
                                recursive=True)
            papis.git.add(str(source_lib_dir), str(main_folder_new))
            papis.git.commit(
                str(source_lib_dir),
                f"Move '{papis.document.describe(document)}'",
            )
        else:
            papis.git.rm_cached(str(source_lib_dir),
                                str(main_folder_old),
                                recursive=True)
            papis.git.commit(
                str(source_lib_dir),
                f"Remove '{papis.document.describe(document)}' "
                f"(moved to '{target_library}' library)",
            )

            papis.git.add_and_commit(
                str(target_lib_dir),
                str(main_folder_new),
                f"Add '{papis.document.describe(document)}'",
            )

    logger.info(
        "Moved document '%s' to '%s' (library '%s').",
        papis.document.describe(document),
        main_folder_new,
        target_library,
    )


@click.command("mv")
@click.help_option("--help", "-h")
@click.option(
    "-t",
    "--to",
    help="Path relative to the library root",
    default=None,
    type=papis.cli.FormatPatternParamType(),
)
@click.option(
    "--target-library",
    help="Target library",
    default=lambda: papis.config.get_lib_name(),  # noqa: PLW0108
    type=str,
)
@papis.cli.bool_flag(
    "-b",
    "--batch",
    help="Do not prompt. Warnings are logged but moves proceed automatically.",
)
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
def cli(
    query: str,
    git: bool,
    _all: bool,
    to: AnyString | None,
    target_library: str,
    batch: bool,
    sort_field: str | None,
    doc_folder: tuple[str, ...],
    sort_reverse: bool,
) -> None:
    """Move a document into another folder."""

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all
    )
    if not documents:
        logger.warning(no_documents_retrieved_message)
        return

    source_library = papis.config.get_lib_name()
    papis.config.set_lib_from_name(target_library)

    if to is None:
        to = papis.config.getformatpattern("add-folder-name")

    target_lib_dir = Path(papis.config.get_lib_from_name(target_library).path)

    moves: dict[Path, PlannedMove] = {}
    conflicts: dict[Path, list[PlannedMove]] = collections.defaultdict(list)

    # Gather moves, detect disk conflicts + selection collisions
    for document in documents:
        main_folder_old_str = document.get_main_folder()
        if not main_folder_old_str:
            logger.warning(
                "'%s': source folder not defined. Cannot move.",
                papis.document.describe(document),
            )
            continue

        main_folder_old = Path(main_folder_old_str)
        if not main_folder_old.exists():
            logger.warning(
                "'%s': source folder does not exist on disk. Cannot move: %s.",
                papis.document.describe(document),
                main_folder_old,
            )
            continue

        target_abs_path = Path(
            papis.paths.get_document_folder(
                document, target_lib_dir, folder_name_format=to
            )
        )

        if main_folder_old == target_abs_path:
            logger.info(
                "Skipping '%s': source and target are the same.",
                papis.document.describe(document),
            )
            continue

        # Resolve rename vs move-into semantics
        if target_abs_path.is_dir():
            main_folder_new = target_abs_path / main_folder_old.name
        else:
            main_folder_new = target_abs_path

        # Check for nesting or disk conflict
        error = _check_not_nested(main_folder_new, target_lib_dir)
        if error is None:
            error = _check_target_already_exists(main_folder_new)
        if error:
            logger.warning(
                "'%s': %s.",
                papis.document.describe(document),
                error,
            )
            if batch:
                continue
            logger.warning("You can skip this document or rename it manually.")
            if papis.tui.utils.confirm(
                "Skip this document? Answer 'no' to rename it instead.",
                yes=True,
            ):
                continue

            main_folder_new = _rename_target_interactively(
                document, main_folder_new, target_lib_dir
            )

        move = PlannedMove(document, main_folder_old, main_folder_new)
        _register_move(move, moves, conflicts)

    # Resolve selection collisions.
    #
    # At this point every target path is in one of two lists
    #   moves[path]     - a single PlannedMove, no collision
    #   conflicts[path] - list of PlannedMove that want the same folder
    # The loop below lets the user rename colliding moves. Paths that collide again
    # stay in the loop for another round.
    while conflicts:
        if batch:
            for conflict_group in conflicts.values():
                for c in conflict_group:
                    logger.warning(
                        "'%s': duplicate target folder. Skipping: %s → %s.",
                        papis.document.describe(c.document),
                        c.source,
                        c.target,
                    )
            break

        resolved: list[PlannedMove] = []

        for conflict_path, conflict_group in list(conflicts.items()):
            msg_lines = [
                f"{len(conflict_group)} documents want the same"
                f" target folder '{conflict_path}':"
            ]
            for c in conflict_group:
                msg_lines.append(f"    - '{papis.document.describe(c.document)}'")

            logger.warning("\n".join(msg_lines))

            logger.warning("You can skip these documents or rename them manually.")
            if papis.tui.utils.confirm("Skip these documents?", yes=True):
                del conflicts[conflict_path]
                continue

            for c in conflict_group:
                new_target = _rename_target_interactively(
                    c.document, c.target, target_lib_dir
                )
                resolved.append(PlannedMove(c.document, c.source, new_target))

            del conflicts[conflict_path]

        new_conflicts: dict[Path, list[PlannedMove]] = collections.defaultdict(list)
        for move in resolved:
            _register_move(move, moves, new_conflicts)

        if not new_conflicts:
            break

        conflicts = new_conflicts

    if not moves:
        logger.info("No valid moves to perform.")
        return

    # Move
    papis.config.set_lib_from_name(source_library)
    for move in moves.values():
        try:
            run(move.document, str(move.target), target_library=target_library, git=git)
        except Exception as exc:
            if batch:
                logger.warning(
                    "Failed to move '%s': %s",
                    papis.document.describe(move.document),
                    exc,
                )
                continue
            raise

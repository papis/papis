"""
The ``mv`` command is used to move document folders around your library (or to
another library).

It will (except when run with ``--all``) bring up the picker with a list of
documents that match the query. You can then select the document or documents
you'd like to move. The command works similarly to the Unix
`mv <https://en.wikipedia.org/wiki/Mv_(Unix)>`__ command. Hence, when the
specified target folder exists, the document's current main folder is moved into
the target folder. If the specified target folder doesn't exist, then the
current folder is renamed to the target folder name. Folder names are cleaned,
so that various problematic characters are avoided (see
:confval:`doc-paths-extra-chars`).

The ``mv`` command will first check whether moving the folders as specified will
result in problems. If any problems are found, they are displayed and you will
be prompted whether you want to abort or move the unproblematic documents (if any
exist).

Examples
^^^^^^^^

- Query documents by author "Rick Astley" and move some of them. After picking
  the relevant documents, they will be renamed to their default names
  specified by the :confval:`add-folder-name` option.

   .. code:: sh

        papis mv author:"Rick Astley"

- You can use ``--to`` to pass the name of the target folder. Here we'll move a
  document by the author "Rick Astley" to a folder named ``rick-astley``:

   .. code:: sh

        papis mv --to rick-astley author:"Rick Astley"

  If the folder "rick-astley" exists, then the document's folder will be moved into it.
  If, say, the document's folder is currently "rick-s-the-best", then the new folder
  will be "rick-astley/rick-s-the-best". If the folder "rick-astley" doesn't exist,
  then the document's folder will be renamed to that so that the new folder becomes
  "rick-astley".

  If you select multiple documents to be moved to the same target folder, Papis will
  warn you and refuse to move the documents.

- You can use formatting patterns to generate the folder names. For instance, to
  organise all documents by author "Rick Astley" by year, you can use this command:

   .. code:: sh

        papis mv --to "{doc[year]}" --all author:"Rick Astley"

  Note that the ``--all`` flag means that the picker isn't shown and all
  documents matching the query will be moved.

- You can use the ``--batch`` flag to skip all warnings. You will not be prompted
  if there are problematic moves and all unproblematic moves will happen
  automatically. The command will only abort if an error occurs while moving a document.

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
from typing import TYPE_CHECKING

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

logger = papis.logging.get_logger(__name__)


def _is_document_folder(path: Path) -> bool:
    """Check whether `path` is an existing document folder."""
    info_name = papis.config.getstring("info-name")
    return path.joinpath(info_name).exists()


def _get_target_library_dir(target_library: str) -> Path:
    """Get the directory path for the given library."""
    return Path(papis.config.getstring(key="dir", section=target_library)).expanduser()


def run(
    document: Document,
    doc_folder_new: str,
    target_library: str | None = None,
    git: bool = False,
) -> None:
    """Move a document's folder to *doc_folder_new*.

    :param document: The document to move.
    :param doc_folder_new: The target path for the document's folder.
    :param target_library: Name of the target library. If None, uses the current
        library.
    :param git: If True, record the move in git history.
    :returns: None
    :raises DocumentFolderNotFound: If the document has no main folder on disk.
    :raises FileNotFoundError: If the source folder does not exist.
    :raises FileExistsError: If the target folder already exists. This will also be
        raised if the target folder is the same as the source folder.
    """
    if target_library is None:
        target_library = papis.config.get_lib_name()

    source_lib_dir = Path(papis.config.getstring(key="dir")).expanduser()

    target_lib_dir = _get_target_library_dir(target_library)

    doc_folder_old = document.get_main_folder()
    if not doc_folder_old:
        raise DocumentFolderNotFound(papis.document.describe(document))

    main_folder_old = Path(doc_folder_old)
    main_folder_new = Path(doc_folder_new)

    # sanity check even if covered in `cli()`
    if not main_folder_old.exists():
        raise FileNotFoundError(f"Source folder does not exist: '{main_folder_old}'")

    # sanity check even if covered in `cli()`
    if main_folder_new.exists():
        raise FileExistsError(f"Target folder already exists: '{main_folder_new}'")

    main_folder_new.parent.mkdir(
        parents=True,
        exist_ok=True,
        # NOTE: 0o755 is default, but explicitness is needed to avoid type error
        mode=papis.config.getint("dir-umask") or 0o755,
    )
    if target_lib_dir == source_lib_dir:
        if git:
            papis.git.mv_and_commit_resource(
                str(main_folder_old),
                str(main_folder_new),
                f"Move '{papis.document.describe(document)}'",
            )
        else:
            shutil.move(main_folder_old, main_folder_new)
    else:
        shutil.move(doc_folder_old, main_folder_new)

        if git:
            papis.git.remove(str(source_lib_dir), str(main_folder_old))
            papis.git.commit(
                str(source_lib_dir), f"Remove '{papis.document.describe(document)}'"
            )

            # NOTE: this will fail when the target library isn't git tracked
            papis.git.add_and_commit_resource(
                str(target_lib_dir),
                str(main_folder_new),
                f"Add '{papis.document.describe(document)}'",
            )

    source_db = papis.database.get()
    source_db.delete(document)

    logger.debug("New document folder: '%s'.", main_folder_new)

    target_db = papis.database.get(library_name=target_library)

    document.set_folder(str(main_folder_new))

    target_db.add(document)

    logger.info(
        "Moved document '%s' to '%s'.",
        papis.document.describe(document),
        main_folder_new,
    )


@click.command("mv")
@click.help_option("--help", "-h")
@click.option(
    "-t",
    "--to",
    help="Path relative to the library root",
    default=lambda: papis.config.getformatpattern("add-folder-name"),
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
    to: AnyString,
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

    target_lib_dir = _get_target_library_dir(target_library)

    moves: list[
        tuple[Document, Path, Path]
    ] = []  # (document, main_folder_old, main_folder_new)
    warnings: list[tuple[Document, str]] = []  # (document, warning_description)

    for document in documents:
        main_folder_old_str = document.get_main_folder()
        if not main_folder_old_str:
            warnings.append((
                document,
                "source folder not defined for document. Cannot move folder.",
            ))
            continue

        main_folder_old = Path(main_folder_old_str)
        if not main_folder_old.exists():
            warnings.append((
                document,
                "source folder does not exist on disk. "
                f"Cannot move: {main_folder_old}.",
            ))
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

        # If target dir exists, we move the old folder into it,
        if target_abs_path.is_dir():
            main_folder_new = target_abs_path / main_folder_old.name

            # Avoid moving folders into other documents' main folder
            if _is_document_folder(target_abs_path):
                warnings.append((
                    document,
                    f"move would result in moving into another document's main folder. "
                    f"Skipping move: {main_folder_old} → {main_folder_new}.",
                ))
                continue
        else:
            main_folder_new = target_abs_path

        # Avoid overwriting/moving-into unexpected folders or files
        # NOTE: the exact behaviour we are avoiding here depends on the `shutil.move`
        #       semantics, and that apparently depends on OS specifics.
        if main_folder_new.exists():
            warnings.append((
                document,
                f"target already exists. "
                f"Skipping move: {main_folder_old} → {main_folder_new}.",
            ))
            continue

        moves.append((document, main_folder_old, main_folder_new))

    # Detect duplicate target folders
    conflict_groups: dict[Path, list[tuple[Document, Path, Path]]] = (
        collections.defaultdict(list)
    )
    for document, main_folder_old, main_folder_new in moves:
        conflict_groups[main_folder_new.resolve()].append((
            document,
            main_folder_old,
            main_folder_new,
        ))

    deduplicated_moves: list[tuple[Document, Path, Path]] = []
    for group in conflict_groups.values():
        if len(group) == 1:
            deduplicated_moves.append(group[0])
        else:
            for doc_i, main_folder_old_i, main_folder_new_i in group:
                warnings.append((
                    doc_i,
                    f"duplicate target folder with {len(group) - 1} other document(s). "
                    f"Skipping move: {main_folder_old_i} → {main_folder_new_i}.",
                ))

    if warnings:
        for doc, reason in warnings:
            logger.warning("'%s': %s", papis.document.describe(doc), reason)

        if not deduplicated_moves:
            logger.info("No valid moves to perform.")
            return

        if not batch:
            if not papis.tui.utils.confirm(
                f"{len(warnings)} warning(s) listed above. "
                f"Continue with the {len(deduplicated_moves)} valid move(s)?",
                yes=False,
            ):
                return

    for document, _, main_folder_new in deduplicated_moves:
        run(document, str(main_folder_new), target_library=target_library, git=git)

"""
This module serves as an lightweight interface for ``git`` related functions.

Note that these git functions do not touch the file system. The caller must always
manipulate the filesystem first and then use the git functions to record the changes
to the index. This means that failure of a git operation always just means a failure
of committing changes.

"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import papis.logging

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = papis.logging.get_logger(__name__)


def is_git_repo(
    path: str | os.PathLike[str],
    *,
    root: str | os.PathLike[str] | None = None,
) -> bool:
    """Check if *path* is inside a git repository.

    :param path: starting path.
    :param root: optional boundary directory (inclusive).
    """
    path = os.path.abspath(path)
    if root is not None:
        root = os.path.abspath(root)

    while True:
        if os.path.exists(os.path.join(path, ".git")):
            return True

        parent = os.path.dirname(path)
        if parent == path:
            return False  # hit filesystem root

        if root is not None and path == root:
            return False  # hit boundary, don't go above

        path = parent


def init(path: str | os.PathLike[str]) -> None:
    """Initialize a git repository at *path*."""
    from papis.utils import run

    logger.info("Initializing git repository: '%s'.", path)
    run(["git", "init"], cwd=str(path))


def add(
    path: str | os.PathLike[str],
    resource: str | Sequence[str],
) -> None:
    """Stage a resource (or resources) in the git repository at *path*.

    :param path: a folder with an existing git repository.
    :param resource: a resource to add to the index (e.g. ``info.yaml``),
        or a sequence of resources.
    """
    from papis.utils import run

    if isinstance(resource, str):
        resource = [resource]

    logger.info("Adding %s to '%s'.", ", ".join(resource), path)
    run(["git", "add", *resource], cwd=str(path))


def commit(path: str | os.PathLike[str], message: str) -> None:
    """Commit staged changes in the git repository at *path*.

    :param path: a folder with an existing git repository.
    :param message: a commit message.
    """
    from papis.utils import run

    logger.info("Committing '%s' with message '%s'.", path, message)
    run(["git", "commit", "-m", message], cwd=str(path))


def rm_cached(
    path: str | os.PathLike[str],
    resource: str | os.PathLike[str],
    *,
    recursive: bool = False,
) -> None:
    """Remove a *resource* from the git index without touching the
    working tree. The caller must have already deleted or moved the
    files on disk.

    :param path: a folder with an existing git repository.
    :param resource: a resource to remove from the index.
    :param recursive: if *True*, remove the resource recursively.
    """
    from papis.utils import run

    logger.info("Removing '%s' from index (cwd: '%s').", resource, path)

    flags = ["--cached"]
    if recursive:
        flags.append("-r")

    run(["git", "rm", *flags, str(resource)], cwd=str(path))


def add_and_commit(
    path: str | os.PathLike[str],
    resources: str | Sequence[str],
    message: str,
) -> None:
    """Stage *resources* and commit with *message*.

    :param path: a folder with an existing git repository.
    :param resources: a resource (e.g. ``info.yaml`` file) or sequence of
        resources to add.
    :param message: a commit message.
    """
    add(path, resources)
    commit(path, message)

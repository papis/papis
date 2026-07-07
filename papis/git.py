"""
This module serves as a lightweight interface for ``git`` related functions.

Note that these git functions do not touch the file system. The caller must always
manipulate the filesystem first and then use the git functions to record the changes
to the index. This means that failure of a git operation always just means a failure
of committing changes.

"""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

import papis.logging

if TYPE_CHECKING:
    from collections.abc import Sequence

    from papis.paths import PathLike

logger = papis.logging.get_logger(__name__)


class GitError(Exception):
    """Raised when a git operation fails."""

    def __init__(self, message: str, returncode: int) -> None:
        self.returncode = returncode
        super().__init__(message)


def _normalize_resources(
    resources: PathLike | Sequence[PathLike],
) -> list[str]:
    """Convert a resource or sequence of resources to a list of strings."""
    if isinstance(resources, (str, os.PathLike)):
        return [str(resources)]
    return [str(r) for r in resources]


def git(*args: str, cwd: PathLike) -> str:
    """Run a git command and return its stdout.

    :param args: arguments to pass to the ``git`` command.
    :param cwd: a folder with an existing git repository.

    :raises GitError: if the git command fails.
    :returns: the stdout of the git command.
    """
    from papis.utils import run

    try:
        result = run(["git", *args], cwd=str(cwd), capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else "(no output)"
        raise GitError(
            f"[GIT] 'git {' '.join(args)}' failed in '{cwd}': {stderr}",
            exc.returncode,
        ) from exc
    return result.stdout.strip()


def is_repo(
    path: PathLike,
    *,
    root: PathLike | None = None,
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


def init(path: PathLike) -> None:
    """Initialize a git repository at *path*."""
    git("init", cwd=path)


def add(
    path: PathLike,
    resources: PathLike | Sequence[PathLike],
) -> None:
    """Stage a resource (or resources) in the git repository at *path*.

    :param path: a folder with an existing git repository.
    :param resources: a resource to add to the index (e.g. ``info.yaml``),
        or a sequence of resources.
    """
    git("add", "--", *_normalize_resources(resources), cwd=path)


def commit(path: PathLike, message: str) -> None:
    """Commit staged changes in the git repository at *path*.

    :param path: a folder with an existing git repository.
    :param message: a commit message.
    """
    logger.info("[GIT] %s", message)
    git("commit", "-m", message, cwd=path)


def rm_cached(
    path: PathLike,
    resources: PathLike | Sequence[PathLike],
    *,
    recursive: bool = False,
) -> None:
    """Remove a *resources* from the git index without touching the
    working tree. The caller must have already deleted or moved the
    files on disk.

    :param path: a folder with an existing git repository.
    :param resources: a resource to remove from the index or a sequence of resources.
    :param recursive: if *True*, remove the resource recursively.
    """
    flags = ["--cached"]
    if recursive:
        flags.append("-r")

    git("rm", *flags, "--", *_normalize_resources(resources), cwd=path)


def add_and_commit(
    path: PathLike,
    resources: PathLike | Sequence[PathLike],
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

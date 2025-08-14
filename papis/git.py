"""This module serves as an lightweight interface for git related functions.
"""
from typing import Sequence

import papis.logging
import papis.utils

logger = papis.logging.get_logger(__name__)


def init(path: str) -> None:
    """Initialize a git repository at *path*."""

    logger.info("Initializing git repository: '%s'.", path)
    papis.utils.run(["git", "init"], cwd=path)


def add(path: str, resource: str) -> None:
    """Adds changes in the *path* to the git index with a *message*.

    :param path: a folder with an existing git repository.
    :param resource: a resource (e.g. ``info.yaml`` file) to add to the index.
    """
    logger.info("Adding '%s'.", path)
    papis.utils.run(["git", "add", resource], cwd=path)


def commit(path: str, message: str) -> None:
    """Commits changes in the *path* with a *message*.

    :param path: a folder with an existing git repository.
    :param message: a commit message.
    """
    logger.info("Committing '%s' with message '%s'.", path, message)
    papis.utils.run(["git", "commit", "-m", message], cwd=path)


def mv(from_path: str, to_path: str) -> None:
    """Renames (moves) the path *from_path* to *to_path*.

    :param from_path: path to be moved (the source).
    :param to_path: destination where *from_path* is moved. If this is in the
        same parent directory as *from_path*, it is a simple rename.
    """
    logger.info("Moving '%s' to '%s'.", from_path, to_path)
    papis.utils.run(["git", "mv", from_path, to_path], cwd=from_path)


def remove(path: str, resource: str,
           recursive: bool = False,
           force: bool = True) -> None:
    """Remove a *resource* from the git repository at *path*.

    :param path: a folder with an existing git repository.
    :param resource: a resource (e.g. ``info.yaml`` file) to remove from git.
    :param recursive: if *True*, the given resource is removed recursively.
    :param force: if *True*, the removal is forced so any errors (e.g. file
        does not exist) are silently ignored.
    """
    logger.info("Removing '%s'.", path)

    flag_rec = "-r" if recursive else ""
    flag_force = "-f" if force else ""
    papis.utils.run(["git", "rm", flag_force, flag_rec, resource], cwd=path)


def add_and_commit_resource(path: str, resource: str, message: str) -> None:
    """Adds and commits a single *resource*.

    :param path: a folder with an existing git repository.
    :param resource: a resource (e.g. ``info.yaml`` file) to remove from git.
    :param message: a commit message.
    """
    add(path, resource)
    commit(path, message)


def mv_and_commit_resource(from_path: str, to_path: str, message: str) -> None:
    """Moves *from_path* and commits the change.

    :param from_path: path to be moved (the source).
    :param to_path: destination where *from_path* is moved.
    :param message: a commit message.
    """
    mv(from_path, to_path)
    commit(to_path, message)


def add_and_commit_resources(path: str,
                             resources: Sequence[str],
                             message: str) -> None:
    """Add and commit multiple resources (see :func:`add_and_commit_resource`).

    Note that a single commit message is generated for all the resources.
    """
    for resource in resources:
        add(path, resource)

    commit(path, message)

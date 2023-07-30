"""This module serves as an lightweight interface for git related functions.
"""
from typing import Sequence

import papis.utils
import papis.logging


logger = papis.logging.get_logger(__name__)


def commit(path: str, message: str) -> None:
    """Commits changes in the *path* with a *message*.

    :param path: a folder with an existing git repository.
    :param message: a commit message.
    """
    logger.info("Committing '%s' with message '%s'.", path, message)
    papis.utils.run(["git", "commit", "-m", message], cwd=path)


def add(path: str, resource: str) -> None:
    """Adds changes in the *path* to the git index with a *message*.

    :param path: a folder with an existing git repository.
    :param resource: a resource (e.g. ``info.yaml`` file) to add to the index.
    """
    logger.info("Adding '%s'.", path)
    papis.utils.run(["git", "add", resource], cwd=path)


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


def add_and_commit_resources(path: str,
                             resources: Sequence[str],
                             message: str) -> None:
    """Add and commit multiple resources (see :func:`add_and_commit_resource`).

    Note that a single commit message is generated for all the resources.
    """
    for resource in resources:
        add(path, resource)

    commit(path, message)

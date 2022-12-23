"""This module serves as an lightweight interface for git related functions.
"""
import os
import logging
from typing import List

logger = logging.getLogger(__name__)


def _issue_git_command(path: str, cmd: str) -> None:
    """Issues a general git command ``cmd`` at ``path``.

    :param path: Folder where a git repo exists.
    :param message: Git command
    """
    assert isinstance(cmd, str)
    path = os.path.expanduser(path)
    assert os.path.exists(path)

    import shlex
    split_cmd = shlex.split(cmd)
    logger.debug(split_cmd)

    import subprocess
    os.chdir(path)
    subprocess.call(split_cmd)


def commit(path: str, message: str) -> None:
    """Commits changes in the path with a message.

    :param path: Folder where a git repo exists.
    :param message: Commit message
    """

    logger.info("Committing '%s' with message '%s'", path, message)
    cmd = 'git commit -m "{0}"'.format(message)
    _issue_git_command(path, cmd)


def add(path: str, resource: str) -> None:
    """Adds changes in the path with a message.

    :param path: Folder where a git repo exists.
    :param resource: Commit resource
    """
    logger.info("Adding '%s'", path)
    cmd = 'git add "{0}"'.format(resource)
    _issue_git_command(path, cmd)


def remove(path: str, resource: str, recursive: bool = False) -> None:
    """Adds changes in the path with a message.

    :param path: Folder where a git repo exists.
    :param resource: Commit resource
    """
    logger.info("Removing '%s'", path)
    # force removal always
    cmd = 'git rm -f {r} "{0}"'.format(resource, r="-r" if recursive else "")
    _issue_git_command(path, cmd)


def add_and_commit_resource(path: str, resource: str, message: str) -> None:
    """Adds and commits a resource.

    :param path: Folder where a git repo exists.
    :param resource: Commit resource
    :param message: Commit message
    """
    add(path, resource)
    commit(path, message)


def add_and_commit_resources(path: str,
                             resources: List[str],
                             message: str) -> None:
    """Adds and commits a resources.
    """
    for resource in resources:
        add(path, resource)
    commit(path, message)

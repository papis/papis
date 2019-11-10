import subprocess
import os
import shlex
import logging

logger = logging.getLogger("papis.git")


def _issue_git_command(path: str, cmd: str) -> None:
    """Issues a general git command ``cmd`` at ``path``.

    :param path: Folder where a git repo exists.
    :type  path: str
    :param message: Git command
    :type  message: str
    :returns: None

    """
    global logger
    assert(type(cmd) == str)
    path = os.path.expanduser(path)
    assert(os.path.exists(path))
    split_cmd = shlex.split(cmd)
    os.chdir(path)
    logger.debug(split_cmd)
    subprocess.call(split_cmd)


def commit(path: str, message: str) -> None:
    """Commits changes in the path with a message.

    :param path: Folder where a git repo exists.
    :type  path: str
    :param message: Commit message
    :type  message: str
    :returns: None

    """
    global logger
    logger.info('Commiting {path} with message {message}'.format(**locals()))
    cmd = 'git commit -m "{0}"'.format(message)
    _issue_git_command(path, cmd)


def add(path: str, resource: str) -> None:
    """Adds changes in the path with a message.

    :param path: Folder where a git repo exists.
    :type  path: str
    :param resource: Commit resource
    :type  resource: str
    :returns: None

    """
    global logger
    logger.info('Adding {path}'.format(**locals()))
    cmd = 'git add "{0}"'.format(resource)
    _issue_git_command(path, cmd)


def rm(path: str, resource: str, recursive: bool = False) -> None:
    """Adds changes in the path with a message.

    :param path: Folder where a git repo exists.
    :type  path: str
    :param resource: Commit resource
    :type  resource: str
    :returns: None

    """
    global logger
    logger.info('Removing {path}'.format(**locals()))
    # force removal always
    cmd = 'git rm -f {r} "{0}"'.format(resource, r="-r" if recursive else "")
    _issue_git_command(path, cmd)


def add_and_commit_resource(path: str, resource: str, message: str) -> None:
    add(path, resource)
    commit(path, message)

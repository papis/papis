import subprocess
import os
import shlex
import logging

from typing import List

logger = logging.getLogger("papis.hg")


def _issue_hg_command(path: str, cmd: str) -> None:
    """Issues a general Mercurial command ``cmd`` at ``path``.

    :param path: Folder where a Mercurial repo exists.
    :type  path: str
    :param message: Mercurial command
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

def add(path: str, resource: str) -> None:
    """Adds new files in the path.

    :param path: Folder where a Mercurial repo exists.
    :type  path: str
    :param resource: File resource
    :type  resource: str
    :returns: None

    """
    global logger
    logger.info('Adding {path}'.format(**locals()))
    cmd = 'hg add "{0}"'.format(resource)
    _issue_hg_command(path, cmd)


def commit(path: str, resources: List[str], message: str) -> None:
    """Commits changes in the path with a message.

    :param path: Folder where a Mercurial repo exists.
    :type  path: str
    :param resources: Commit resources
    :type  resources: list(str)
    :param message: Commit message
    :type  message: str
    :returns: None

    """
    global logger
    logger.info('Commiting {path} with message {message}'.format(**locals()))
    resource = " ".join(map(lambda x: '"{0}"'.format(x), resources))
    cmd = 'hg commit -m "{0}" {1}'.format(message, resource)
    _issue_hg_command(path, cmd)

def rm(path: str, resource: str, message: str, recursive: bool = False, after: bool = False) -> None:
    """Remove files in the path with a message.

    :param path: Folder where a Mercurial repo exists.
    :type  path: str
    :param resource: Commit resource
    :type  resource: str
    :param message: Commit message
    :type  message: str
    :param after: Actually remove
    :type after: bool
    :returns: None

    """
    global logger
    logger.info('Removing {path}'.format(**locals()))
    # force removal always
    pattern = '"{0}"'.format(resource) if recursive else '-I rootfilesin:"{0}"'.format(resource)
    rm_cmd = 'hg rm {a} -f {0}'.format(pattern, a = '-A' if after else '')
    _issue_hg_command(path, rm_cmd)


def add_and_commit_resource(path: str, resource: str, message: str) -> None:
    add(path, resource)
    commit(path, [resource], message)

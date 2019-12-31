import subprocess
import os
import shlex
import logging

logger = logging.getLogger("papis.git")


def _issue_git_command(path, cmd):
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
    cmd = shlex.split(cmd)
    os.chdir(path)
    logger.debug(cmd)
    subprocess.call(cmd)


def commit(path, message):
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


def add(path, resource):
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


def rm(path, resource, recursive=False):
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



def add_and_commit_resource(path, resource, message):
    add(path, resource)
    commit(path, message)

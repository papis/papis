"""Server-side git helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import papis.config
from papis import git as _git
from papis.server.exceptions import ErrorCode, PreconditionFailedError

if TYPE_CHECKING:
    from pathlib import Path


is_repo = _git.is_repo
add = _git.add
commit = _git.commit
add_and_commit = _git.add_and_commit
rm_cached = _git.rm_cached


def should_use_git(git: bool | None, path: Path | str, *, root: Path | str) -> bool:
    """Resolve ``?git`` + ``use-git`` config, raise 412 if no repo.

    :param git: explicit override (``?git=true``/``?git=false``) or ``None``.
    :param path: directory to verify is inside a git repo.
    :param root: the library root; the repo check will not walk above this directory.
    :return: ``True`` if git operations should proceed, ``False`` otherwise.
    :raises PreconditionFailedError: when git is enabled but *path* isn't in a git repo.
    """
    if git is not None:
        do_use_git = git
    else:
        do_use_git = papis.config.getboolean("use-git") or False

    if do_use_git and not _git.is_repo(path, root=str(root)):
        raise PreconditionFailedError(
            "Git is enabled but the library is not a git repository. "
            "Run 'papis init' or 'git init' on the server.",
            code=ErrorCode.NOT_A_GIT_REPOSITORY,
        )

    return do_use_git

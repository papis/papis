from __future__ import annotations

import os
import shutil
import tempfile
from typing import TYPE_CHECKING

import pytest

from papis.git import (
    GitError,
    add as git_add,
    add_and_commit as git_add_and_commit,
    commit as git_commit,
    git as git_cmd,
    init as git_init,
    is_repo as git_is_repo,
    rm_cached as git_rm_cached,
)

if TYPE_CHECKING:
    from papis.testing import TemporaryLibrary

pytestmark = pytest.mark.skipif(
    not shutil.which("git"),
    reason="Test requires 'git' executable to be in the PATH",
)


def _git_commits(cwd: str) -> int:
    stdout = git_cmd("log", "--oneline", cwd=cwd)
    return len(stdout.split("\n")) if stdout else 0


@pytest.mark.library_setup(use_git=True)
def test_is_git_repo(tmp_library: TemporaryLibrary) -> None:
    libdir = tmp_library.libdir
    assert git_is_repo(libdir)

    # works for subdirectories too
    sub = os.path.join(libdir, "sub")
    os.makedirs(sub, exist_ok=True)
    assert git_is_repo(sub)

    # a plain directory that is not inside any git repo
    with tempfile.TemporaryDirectory() as tmp:
        assert not git_is_repo(tmp)


@pytest.mark.library_setup(use_git=True)
def test_is_git_repo_root_boundary(tmp_library: TemporaryLibrary) -> None:
    libdir = tmp_library.libdir
    sub = os.path.join(libdir, "sub")
    os.makedirs(sub, exist_ok=True)

    # boundary at libdir: subdir finds .git above it
    assert git_is_repo(sub, root=libdir)
    # boundary at libdir: libdir itself has .git
    assert git_is_repo(libdir, root=libdir)
    # boundary at sub: stops there, doesn't go up to libdir
    assert not git_is_repo(sub, root=sub)


def test_init(tmp_library: TemporaryLibrary) -> None:
    """git_init creates a .git directory."""
    target = os.path.join(tmp_library.tmpdir, "new_repo")
    os.makedirs(target)
    git_init(target)
    assert os.path.isdir(os.path.join(target, ".git"))


@pytest.mark.library_setup(use_git=True)
def test_add_commit_roundtrip(tmp_library: TemporaryLibrary) -> None:
    libdir = tmp_library.libdir

    test_file = os.path.join(libdir, "test.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("hello")

    git_add(libdir, "test.txt")
    git_commit(libdir, "add test file")

    commits = _git_commits(libdir)
    assert commits == 2  # initial + ours


@pytest.mark.library_setup(use_git=True)
def test_add_and_commit(tmp_library: TemporaryLibrary) -> None:
    libdir = tmp_library.libdir

    f1 = os.path.join(libdir, "a.txt")
    f2 = os.path.join(libdir, "b.txt")
    for f in (f1, f2):
        with open(f, "w", encoding="utf-8") as fh:
            fh.write("x")

    git_add_and_commit(libdir, ["a.txt", "b.txt"], "add two files")

    commits = _git_commits(libdir)
    assert commits == 2  # initial + ours


@pytest.mark.library_setup(use_git=True)
def test_rm_cached_file(tmp_library: TemporaryLibrary) -> None:
    libdir = tmp_library.libdir

    test_file = os.path.join(libdir, "remove_me.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("goodbye")

    git_add(libdir, "remove_me.txt")
    git_commit(libdir, "add file to remove")

    # Simulate FS/DB-first: delete on disk, then rm_cached from index
    os.remove(test_file)
    git_rm_cached(libdir, "remove_me.txt")
    git_commit(libdir, "remove file")

    stdout = git_cmd("log", "-1", "--format=%B", cwd=libdir)
    assert "remove file" in stdout

    stdout = git_cmd("ls-files", "remove_me.txt", cwd=libdir)
    assert stdout == ""


@pytest.mark.library_setup(use_git=True)
def test_rm_cached_recursive(tmp_library: TemporaryLibrary) -> None:
    libdir = tmp_library.libdir

    subdir = os.path.join(libdir, "subdir")
    os.makedirs(subdir)
    for name in ("a.txt", "b.txt"):
        with open(os.path.join(subdir, name), "w", encoding="utf-8") as f:
            f.write(name)

    git_add(libdir, "subdir")
    git_commit(libdir, "add subdir")

    # FS/DB-first: delete the directory, then rm_cached --recursive
    shutil.rmtree(subdir)
    git_rm_cached(libdir, "subdir", recursive=True)
    git_commit(libdir, "remove subdir")

    # Files should be gone from the index
    stdout = git_cmd("ls-files", "subdir", cwd=libdir)
    assert stdout == ""


@pytest.mark.library_setup(use_git=True)
def test_git_operations_raise_on_failure(tmp_library: TemporaryLibrary) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(GitError):
            git_commit(tmp, "not a repo — should fail")

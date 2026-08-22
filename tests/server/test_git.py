from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.testing import TemporaryLibrary


def _git_log(libdir: str) -> list[str]:
    """Return commit subject lines (newest first)."""
    res = subprocess.run(
        ["git", "log", "--format=%s"],
        cwd=libdir,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:  # no commits yet
        return []
    return [line for line in res.stdout.splitlines() if line]


def _create_doc(
    client: TestClient, path: str = "doc", title: str = "Doc", **params: Any
) -> str:
    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"metadata": json.dumps({"title": title}), "folder": path},
        params=params,
    )
    assert response.status_code == 201, response.json()
    return str(response.json()["metadata"]["papis_id"])


@pytest.mark.library_setup(use_git=True, populate=False, settings={"use-git": "true"})
def test_create_commits_when_use_git_on(
    client: TestClient,
    tmp_library: TemporaryLibrary,
) -> None:
    """POST .../documents commits when ``use-git`` is enabled."""
    assert tmp_library.use_git
    _create_doc(client, path="git-doc", title="Git Doc")

    log = _git_log(tmp_library.libdir)
    assert log[0].startswith("Add document '")
    assert "Git Doc" in log[0]


@pytest.mark.library_setup(use_git=True, populate=False, settings={"use-git": "true"})
def test_git_false_override_skips_commit(
    client: TestClient,
    tmp_library: TemporaryLibrary,
) -> None:
    """?git=false skips committing even when ``use-git`` is on."""
    assert tmp_library.use_git
    before = _git_log(tmp_library.libdir)
    _create_doc(client, path="no-commit-doc", title="No Commit", git=False)

    after = _git_log(tmp_library.libdir)
    assert after == before  # no new commit


@pytest.mark.library_setup(use_git=False, populate=False)
def test_no_repo_patch_does_not_mutate(
    client: TestClient,
    tmp_library: TemporaryLibrary,
) -> None:
    """?git=true on a non-git library returns 412 and leaves the doc unchanged."""
    assert not tmp_library.use_git
    id = _create_doc(client, path="safe-doc", title="Safe")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{id}",
        json={"metadata": {"author": "Should Not Persist"}},
        params={"git": "true"},
    )
    assert response.status_code == 412

    doc = client.get(f"/api/v1/libraries/test/documents/{id}")
    assert doc.json()["metadata"].get("author") is None


@pytest.mark.library_setup(use_git=True, populate=False, settings={"use-git": "true"})
def test_move_preserves_history(
    client: TestClient,
    tmp_library: TemporaryLibrary,
) -> None:
    """PATCH .../documents via folder preserves mv file history."""
    id = _create_doc(client, path="move-src", title="Mover")

    client.patch(
        f"/api/v1/libraries/test/documents/{id}",
        json={"folder": "move-dst"},
    )

    log = _git_log(tmp_library.libdir)
    assert log[0].startswith("Move '")

    # info.yaml history survived the move
    out = subprocess.check_output(
        ["git", "log", "--follow", "--format=%s", "move-dst/info.yaml"],
        cwd=tmp_library.libdir,
        text=True,
    )
    subjects = [s for s in out.splitlines() if s]
    assert any("Add document" in s for s in subjects)


@pytest.mark.library_setup(use_git=True, populate=False, settings={"use-git": "true"})
def test_delete_uses_git_rm(
    client: TestClient,
    tmp_library: TemporaryLibrary,
) -> None:
    """DELETE .../documents removes the folder via git and commits."""
    import os

    id = _create_doc(client, path="del-doc", title="Deleter")

    client.delete(f"/api/v1/libraries/test/documents/{id}")

    log = _git_log(tmp_library.libdir)
    assert log[0].startswith("Remove document '")

    # Verify on disk
    assert not os.path.exists(os.path.join(tmp_library.libdir, "del-doc"))

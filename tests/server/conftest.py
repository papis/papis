from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest import MonkeyPatch


@pytest.fixture(autouse=True)
def _sequential_parmap(monkeypatch: MonkeyPatch) -> None:
    """Ensure server tests run with multiprocessing disabled.

    The lifespan sets PAPIS_NP=0 for the real server, but TestClient may
    not run the lifespan (depending on whether it's used as a context
    manager). This fixture guarantees the env var is set for every server
    test and restored afterward so non-server tests are unaffected.
    """
    monkeypatch.setenv("PAPIS_NP", "0")

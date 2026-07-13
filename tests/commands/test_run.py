from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

import papis.config

if TYPE_CHECKING:
    from papis.testing import TemporaryLibrary


def test_run_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.run import run

    libdir = papis.config.get_lib().path
    # Use a trivial no-op command that always succeeds
    run(libdir, command=[sys.executable, "-c", "pass"])

    with pytest.raises(FileNotFoundError):
        run(libdir, command=["nonexistent"])

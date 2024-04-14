import os
import sys

import pytest
import papis.config

from papis.testing import TemporaryLibrary


def test_run_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.run import run

    libdir, = papis.config.get_lib_dirs()
    # Use a mock scriptlet
    script = os.path.join(os.path.dirname(__file__), "scripts.py")
    run(libdir, command=[sys.executable, script, "ls"])

    with pytest.raises(FileNotFoundError):
        run(libdir, command=["nonexistent"])

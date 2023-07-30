import pytest
import papis.config

from tests.testlib import TemporaryLibrary


def test_run_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.run import run

    libdir, = papis.config.get_lib_dirs()
    run(libdir, command=["ls"])

    with pytest.raises(FileNotFoundError):
        run(libdir, command=["nonexistent"])

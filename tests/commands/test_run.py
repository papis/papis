import papis.config

from tests.testlib import TemporaryLibrary


def test_run_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.run import run

    libdir, = papis.config.get_lib_dirs()
    status = run(libdir, command=["ls"])
    assert status == 0

    status = run(libdir, command=["nonexistent"])
    assert status != 0

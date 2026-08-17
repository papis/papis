from __future__ import annotations

import os
import shutil

import platformdirs
import pytest

from papis.testing import PapisRunner, TemporaryConfiguration, TemporaryLibrary


@pytest.mark.parametrize("with_library", [False, True])
def test_no_config_shows_init_hint(tmp_config: TemporaryConfiguration,
                                   monkeypatch: pytest.MonkeyPatch,
                                   with_library: bool) -> None:
    import papis.config
    from papis.commands.default import run as cli

    with monkeypatch.context() as m:
        # NOTE: this is the default directory set in
        #   papis.config::Configuration.__init__
        # See https://github.com/papis/papis/issues/1227
        m.setattr(platformdirs, "user_documents_dir",
                  lambda: os.path.join(tmp_config.tmpdir, "Documents"))
        libdir = os.path.join(platformdirs.user_documents_dir(), "papers")

        if with_library:
            os.makedirs(libdir)
        else:
            assert not os.path.isdir(libdir)

        shutil.rmtree(tmp_config.configdir)
        papis.config.reset_configuration()

        cli_runner = PapisRunner()
        result = cli_runner.invoke(cli, ["list"])

        assert result.exit_code == 0
        assert "No configuration file exists at" in result.output
        assert "papis init" in result.output

        if with_library:
            os.rmdir(libdir)


def test_default_cli(tmp_library: TemporaryLibrary) -> None:
    from papis import __version__
    from papis.commands.default import run as cli

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli,
        ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output

    result = cli_runner.invoke(
        cli,
        ["--set", "something", "42"])
    # error missing command
    assert result.exit_code == 2

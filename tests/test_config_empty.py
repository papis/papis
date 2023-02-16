# NOTE: these tests need to be in a new file to ensure that no papis modules
# are loaded before the configuration file is set; some modules like
# `papis.bibtex` have import side effects involving the config and interfere

import os
import tempfile
import contextlib
from typing import Iterator

import papis.logging
papis.logging.setup("DEBUG")


@contextlib.contextmanager
def temporary_config(text: str = "") -> Iterator[None]:
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as configfile:
        configfile.write(text)

    import papis.config
    papis.config.set_config_file(configfile.name)
    papis.config.reset_configuration()

    try:
        yield
    finally:
        papis.config.set_config_file(None)
        papis.config.reset_configuration()

        os.unlink(configfile.name)


def test_empty_config() -> None:
    with temporary_config():
        import papis.config
        from papis.defaults import settings

        config = papis.config.get_configuration()
        assert papis.config.get_general_settings_name() in config
        assert papis.config.get_libs() == ["papers"]
        assert papis.config.get("picktool") == settings["picktool"]


def test_config_with_no_general_settings() -> None:
    with temporary_config("[papers]\ndir = /some/directory/probably"):
        import papis.config
        from papis.defaults import settings

        config = papis.config.get_configuration()
        assert papis.config.get_general_settings_name() in config
        assert papis.config.get_libs() == ["papers"]
        assert papis.config.get("picktool") == settings["picktool"]


def test_config_different_default_library() -> None:
    with temporary_config("[books]\ndir = /some/directory/probably"):
        import papis.config
        from papis.defaults import settings

        config = papis.config.get_configuration()
        assert papis.config.get_general_settings_name() in config
        assert papis.config.get_libs() == ["books"]
        assert papis.config.get("picktool") == settings["picktool"]

# NOTE: these tests need to be in a new file to ensure that no papis modules
# are loaded before the configuration file is set; some modules like
# `papis.bibtex` have import side effects involving the config and interfere

import pytest

from papis.testing import TemporaryConfiguration


@pytest.mark.config_setup(overwrite=True, settings={})
def test_empty_config(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.defaults import settings

    config = papis.config.get_configuration()
    assert papis.config.get_general_settings_name() in config
    assert papis.config.get_libs() == ["papers"]
    assert papis.config.get("picktool") == settings["picktool"]


@pytest.mark.config_setup(overwrite=True, settings={
    "papers": {"dir": "/some/directory/probably"}
    })
def test_config_with_no_general_settings(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.defaults import settings

    config = papis.config.get_configuration()
    assert papis.config.get_general_settings_name() in config
    assert papis.config.get_libs() == ["papers"]
    assert papis.config.get("picktool") == settings["picktool"]


@pytest.mark.config_setup(overwrite=True, settings={
    "books": {"dir": "/some/directory/probably"}
    })
def test_config_different_default_library(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.defaults import settings

    config = papis.config.get_configuration()
    assert papis.config.get_general_settings_name() in config
    assert papis.config.get_libs() == ["books"]
    assert papis.config.get("picktool") == settings["picktool"]

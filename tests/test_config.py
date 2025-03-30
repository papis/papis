import os
import re
import sys
import pytest

from papis.testing import TemporaryConfiguration


def test_default_opener(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    if sys.platform.startswith("darwin"):
        assert papis.defaults.get_default_opener() == "open"
    elif sys.platform.startswith("win"):
        assert papis.defaults.get_default_opener() == "cmd.exe /c start"
    else:
        assert papis.defaults.get_default_opener() == "xdg-open"


def test_get_config_paths(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    assert papis.config.get_config_home() == tmp_config.tmpdir
    assert papis.config.get_config_folder() == tmp_config.configdir
    assert papis.config.get_config_file() == tmp_config.configfile

    configpy = os.path.join(tmp_config.configdir, "config.py")
    assert papis.config.get_configpy_file() == configpy

    scriptsdir = os.path.join(tmp_config.configdir, "scripts")
    assert papis.config.get_scripts_folder() == scriptsdir


def test_get_config_home(tmp_config: TemporaryConfiguration,
                         monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.config
    assert re.match(r".+papis", papis.config.get_config_home()) is not None


def test_config_interpolation() -> None:
    with TemporaryConfiguration(prefix="papis%test%") as tmp_config:
        import papis.config

        assert papis.config.get("dir", section=tmp_config.libname) == tmp_config.libdir

        papis.config.set("some_value", "value1")
        papis.config.set("more_value", "more_%(some_value)s")
        assert papis.config.get("more_value") == "more_value1"


def test_set(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    papis.config.set("nonexistenkey", "rofi")
    assert papis.config.get("nonexistenkey") == "rofi"

    papis.config.set("super_key_", "adams", section="nonexistent")
    assert papis.config.get("super_key_", section="nonexistent") == "adams"


def test_get(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    section = papis.config.get_general_settings_name()
    libname = papis.config.get_lib_name()

    papis.config.set("test_get", "value1")
    assert papis.config.get("test_get") == "value1"
    assert papis.config.get("test_get", section=section) == "value1"

    papis.config.set("test_get", "value42", section=libname)
    assert papis.config.get("test_get") == "value42"
    assert papis.config.get("test_get", section=libname) == "value42"
    assert papis.config.get("test_get", section=section) == "value1"

    papis.config.set("test_getint", "42")
    assert papis.config.getint("test_getint") == 42
    assert papis.config.getint("test_getint", section=section) == 42
    assert isinstance(papis.config.getint("test_getint", section=section), int)

    papis.config.set("test_getfloat", "3.14")
    assert papis.config.getfloat("test_getfloat") == 3.14
    assert papis.config.getfloat("test_getfloat", section=section) == 3.14
    assert isinstance(papis.config.getfloat("test_getfloat", section=section), float)

    papis.config.set("test_getbool", "True")
    assert papis.config.getboolean("test_getbool") is True
    assert papis.config.getboolean("test_getbool", section=section) is True

    papis.config.set("test_getbool", "False")
    assert papis.config.getboolean("test_getbool") is False
    assert papis.config.getboolean("test_getbool", section=section) is False

    import papis.exceptions
    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("_unknown_key")


def test_get_types(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    # getint
    papis.config.set("int_config", "1")
    value = papis.config.getint("int_config")
    assert isinstance(value, int)
    assert value == 1

    papis.config.set("int_config", "x")
    with pytest.raises(ValueError,
                       match="Key 'int_config' should be an integer"):
        value = papis.config.getint("int_config")

    # getfloat
    papis.config.set("float_config", "3.1415")
    value = papis.config.getfloat("float_config")
    assert isinstance(value, float)
    assert value == 3.1415

    papis.config.set("float_config", "not1")
    with pytest.raises(ValueError,
                       match="Key 'float_config' should be a float"):
        value = papis.config.getfloat("float_config")

    # getboolean
    papis.config.set("boolean_config", "True")
    value = papis.config.getboolean("boolean_config")
    assert isinstance(value, bool)
    assert value

    papis.config.set("boolean_config", "not1")
    with pytest.raises(ValueError,
                       match="Key 'boolean_config' should be a boolean"):
        value = papis.config.getboolean("boolean_config")


def test_get_configuration(tmp_config: TemporaryConfiguration,
                           monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.config

    general_name = papis.config.get_general_settings_name()
    config_1 = papis.config.get_configuration()

    assert isinstance(config_1, papis.config.Configuration)
    assert general_name in config_1
    assert config_1 is papis.config.CURRENT_CONFIGURATION

    with monkeypatch.context() as m:
        m.setattr(papis.config, "CURRENT_CONFIGURATION", None)

        config_2 = papis.config.get_configuration()
        assert isinstance(config_2, papis.config.Configuration)
        assert general_name in config_2
        assert config_2 is not config_1


def test_merge_configuration_from_path(tmp_config: TemporaryConfiguration) -> None:
    assert tmp_config.configdir is not None
    configpath = os.path.join(tmp_config.configdir, "config_extra")

    with open(configpath, "w", encoding="utf-8") as configfile:
        configfile.write("""
[settings]
some-nice-setting = 42
some-other-setting = mandragora
        """)

    import papis.config
    import papis.exceptions

    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("some-nice-setting")

    papis.config.set("some-nice-setting", "what-is-the-question")
    assert papis.config.get("some-nice-setting") == "what-is-the-question"

    config = papis.config.get_configuration()
    papis.config.merge_configuration_from_path(configpath, config)
    assert papis.config.get("some-nice-setting") == "42"
    assert papis.config.get("some-other-setting") == "mandragora"


def test_set_lib_non_existing(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    lib = "non-existing-library"
    with pytest.raises(
            Exception,
            match=f"Library '{lib}' does not seem to exist"):
        papis.config.set_lib_from_name(lib)


def test_set_lib_from_path(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    assert tmp_config.libdir is not None

    papis.config.set_lib_from_name(tmp_config.libdir)
    assert papis.config.get_lib_name() == tmp_config.libdir


def test_set_lib_from_real_lib(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    libname = "test-set-lib"
    papis.config.set("dir",
                     papis.config.escape_interp(tmp_config.libdir),
                     section=libname)

    assert tmp_config.libdir is not None
    assert os.path.exists(tmp_config.libdir)

    papis.config.set_lib_from_name(libname)
    assert papis.config.get_lib_name() == libname


def test_reset_configuration(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    papis.config.set("test_reset_configuration", "mordor")
    assert papis.config.get("test_reset_configuration") == "mordor"

    config = papis.config.reset_configuration()
    assert isinstance(config, papis.config.Configuration)

    import papis.exceptions
    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("test_reset_configuration")


def test_get_default_settings(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    settings = papis.config.get_default_settings()
    assert isinstance(settings, dict)
    assert len(settings) != 0

    section = papis.config.get_general_settings_name()
    assert section in settings
    assert settings[section]["mvtool"] == "mv"


def test_register_default_settings(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    papis.config.register_default_settings(
        {"scihub": {"command": "open"}}
    )
    assert papis.config.get("command", section="scihub") == "open"

    papis.config.set("scihub-command", "edit")
    assert papis.config.get("command", section="scihub") == "edit"

    options = {"settings": {"hubhub": 42, "default-library": "mag"}}
    papis.config.register_default_settings(options)

    assert papis.config.get("hubhub") == 42
    assert papis.config.get("info-name") is not None
    assert not papis.config.get("default-library") == "mag"
    assert (
        papis.config.get_default_settings()["settings"]["default-library"]
        == "mag")


def test_get_list(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    papis.config.set("super-key-list", [1, 2, 3, 4])
    assert papis.config.get("super-key-list") == "[1, 2, 3, 4]"
    assert papis.config.getlist("super-key-list") == ["1", "2", "3", "4"]

    papis.config.set("super-key-list", ["asdf", 2, 3, 4])
    assert papis.config.get("super-key-list") == "['asdf', 2, 3, 4]"
    assert papis.config.getlist("super-key-list") == ["asdf", "2", "3", "4"]

    papis.config.set("super-key-list", ["asdf", 2, 3, 4])
    assert papis.config.get("super-key-list") == "['asdf', 2, 3, 4]"
    assert papis.config.getlist("super-key-list") == ["asdf", "2", "3", "4"]

    papis.config.set("super-key-list", "['asdf',2,3,4]")
    assert papis.config.get("super-key-list") == "['asdf',2,3,4]"
    assert papis.config.getlist("super-key-list") == ["asdf", "2", "3", "4"]

    papis.config.set("super-key-list", "[asdf,2,3,4]")
    assert papis.config.get("super-key-list") == "[asdf,2,3,4]"

    with pytest.raises(SyntaxError, match="must be a valid Python object"):
        papis.config.getlist("super-key-list")

    papis.config.set("super-key-list", "2")
    assert papis.config.get("super-key-list") == "2"
    assert papis.config.getint("super-key-list") == 2

    with pytest.raises(SyntaxError, match="must be a valid Python list"):
        papis.config.getlist("super-key-list")

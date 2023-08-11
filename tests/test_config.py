import os
import re
import sys
import pytest

from tests.testlib import TemporaryConfiguration


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


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_home(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    import papis.config

    with monkeypatch.context() as m:
        m.delenv("XDG_CONFIG_HOME", raising=False)
        assert re.match(r".+config", papis.config.get_config_home()) is not None


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_dirs(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    import tempfile
    import papis.config
    tmpdir = tempfile.gettempdir()

    with monkeypatch.context() as m:
        m.setenv("XDG_CONFIG_HOME", tmpdir)
        m.delenv("XDG_CONFIG_DIRS", raising=False)

        dirs = papis.config.get_config_dirs()
        assert os.environ.get("XDG_CONFIG_DIRS") is None
        assert len(dirs) == 2
        assert os.path.join("/", "tmp", "papis") == dirs[0]

    with monkeypatch.context() as m:
        m.setenv("XDG_CONFIG_DIRS", "/etc/:/usr/local/etc")
        m.setenv("XDG_CONFIG_HOME", os.path.expanduser("~"))

        dirs = papis.config.get_config_dirs()
        assert len(dirs) == 4
        assert os.path.abspath("/etc/papis") == os.path.abspath(dirs[0])
        assert os.path.abspath("/usr/local/etc/papis") == os.path.abspath(dirs[1])
        assert os.path.expanduser("~/papis") == os.path.abspath(dirs[2])
        assert os.path.expanduser("~/.papis") == os.path.abspath(dirs[3])


def test_set(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    papis.config.set("nonexistenkey", "rofi")
    assert papis.config.get("nonexistenkey") == "rofi"

    papis.config.set("super_key_", "adams", section="nonexistent")
    assert papis.config.get("super_key_", section="nonexistent") == "adams"


def test_get(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    general_name = papis.config.get_general_settings_name()
    libname = papis.config.get_lib_name()

    papis.config.set("test_get", "value1")
    assert papis.config.get("test_get") == "value1"
    assert papis.config.get("test_get", section=general_name) == "value1"

    papis.config.set("test_get", "value42", section=libname)
    assert papis.config.get("test_get") == "value42"
    assert papis.config.get("test_get", section=libname) == "value42"
    assert papis.config.get("test_get", section=general_name) == "value1"

    papis.config.set("test_getint", "42")
    assert papis.config.getint("test_getint") == 42
    assert papis.config.getint("test_getint", section=general_name) == 42
    assert type(papis.config.getint("test_getint", section=general_name)) is int

    papis.config.set("test_getfloat", "3.14")
    assert papis.config.getfloat("test_getfloat") == 3.14
    assert papis.config.getfloat("test_getfloat", section=general_name) == 3.14
    assert type(papis.config.getfloat("test_getfloat", section=general_name)) is float

    papis.config.set("test_getbool", "True")
    assert papis.config.getboolean("test_getbool") is True
    assert papis.config.getboolean("test_getbool", section=general_name) is True

    papis.config.set("test_getbool", "False")
    assert papis.config.getboolean("test_getbool") is False
    assert papis.config.getboolean("test_getbool", section=general_name) is False

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


def test_get_configuration(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
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

    with open(configpath, "w") as configfile:
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
            match="Library '{}' does not seem to exist".format(lib)):
        papis.config.set_lib_from_name(lib)


def test_set_lib_from_path(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    assert tmp_config.libdir is not None
    papis.config.set_lib_from_name(tmp_config.libdir)
    assert papis.config.get_lib_name() == tmp_config.libdir


def test_set_lib_from_real_lib(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    libname = "test-set-lib"
    papis.config.set("dir", tmp_config.libdir, section=libname)

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
    try:
        papis.config.getlist("super-key-list")
    except SyntaxError as e:
        assert (
            str(e) == (
                "The key 'super-key-list' must be a valid Python object: "
                "[asdf,2,3,4]")
        )

    papis.config.set("super-key-list", "2")
    assert papis.config.get("super-key-list") == "2"
    assert papis.config.getint("super-key-list") == 2
    try:
        papis.config.getlist("super-key-list")
    except SyntaxError as e:
        assert (
            str(e) == (
                "The key 'super-key-list' must be a valid Python list. "
                "Got: 2 (type 'int')"
            )
        )

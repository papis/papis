import os
import re
import sys
import pytest
import tempfile

import papis.exceptions
import papis.config
import papis.defaults
from papis.config import _CONFIGURATION


def test_default_opener() -> None:
    if sys.platform.startswith("darwin"):
        assert papis.defaults.get_default_opener() == "open"
    elif sys.platform.startswith("win"):
        assert papis.defaults.get_default_opener() == "start"
    else:
        assert papis.defaults.get_default_opener() == "xdg-open"


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_home(monkeypatch) -> None:
    tmpdir = tempfile.gettempdir()

    with monkeypatch.context() as m:
        m.setenv("XDG_CONFIG_HOME", tmpdir)
        assert papis.config.get_config_home() == tmpdir

    with monkeypatch.context() as m:
        m.delenv("XDG_CONFIG_HOME", raising=False)
        assert re.match(r".+config", papis.config.get_config_home()) is not None


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_dirs(monkeypatch) -> None:
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


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_folder(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as d:
        with monkeypatch.context() as m:
            m.setenv("XDG_CONFIG_HOME", d)
            configpath = os.path.join(os.environ["XDG_CONFIG_HOME"], "papis")
            if not os.path.exists(configpath):
                os.mkdir(configpath)
            assert papis.config.get_config_folder() == configpath


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_file(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as d:
        with monkeypatch.context() as m:
            m.setenv("XDG_CONFIG_HOME", d)
            configpath = os.path.join(papis.config.get_config_folder(), "config")
            assert configpath == papis.config.get_config_file()


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_configpy_file(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as d:
        with monkeypatch.context() as m:
            m.setenv("XDG_CONFIG_HOME", d)
            configpath = os.path.join(papis.config.get_config_folder(), "config.py")
            assert configpath == papis.config.get_configpy_file()
            assert os.environ["XDG_CONFIG_HOME"] in configpath


def test_set_config_file() -> None:
    with tempfile.NamedTemporaryFile() as f:
        papis.config.set_config_file(f.name)
        assert papis.config.get_config_file() == f.name


def test_get_scripts_folder() -> None:
    ccfolder = papis.config.get_config_folder()
    assert os.path.join(ccfolder, "scripts") == papis.config.get_scripts_folder()


def test_set() -> None:
    papis.config.set("nonexistenkey", "rofi")
    assert papis.config.get("nonexistenkey") == "rofi"

    papis.config.set("super_key_", "adams", section="nonexistent")
    assert papis.config.get("super_key_", section="nonexistent") == "adams"


def test_get() -> None:
    settings = papis.config.get_general_settings_name()

    papis.config.set("test_get", "value1")
    assert papis.config.get("test_get") == "value1"
    assert papis.config.get("test_get", section=settings) == "value1"

    papis.config.set("test_get", "value42", section=papis.config.get_lib_name())
    assert "value42" == papis.config.get("test_get")
    assert "value42" == papis.config.get(
        "test_get", section=papis.config.get_lib_name())
    assert "value1" == papis.config.get("test_get", section=settings)

    papis.config.set("test_getint", "42")
    assert papis.config.getint("test_getint") == 42
    assert papis.config.getint("test_getint", section=settings) == 42
    assert type(papis.config.getint("test_getint", section=settings)) is int

    papis.config.set("test_getfloat", "3.14")
    assert papis.config.getfloat("test_getfloat") == 3.14
    assert papis.config.getfloat("test_getfloat", section=settings) == 3.14
    assert type(papis.config.getfloat("test_getfloat", section=settings)) is float

    papis.config.set("test_getbool", "True")
    assert papis.config.getboolean("test_getbool") is True
    assert papis.config.getboolean("test_getbool", section=settings) is True
    papis.config.set("test_getbool", "False")
    assert papis.config.getboolean("test_getbool") is False
    assert papis.config.getboolean("test_getbool", section=settings) is False

    import pytest
    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("_unknown_key")


def test_get_types() -> None:
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


def test_get_configuration() -> None:
    settings = papis.config.get_general_settings_name()
    config = papis.config.get_configuration()
    assert type(config) is papis.config.Configuration
    assert settings in config.keys()
    assert id(_CONFIGURATION) == id(config)


def test_get_configuration_2() -> None:
    global _CONFIGURATION
    _CONFIGURATION = None

    config = papis.config.get_configuration()
    assert type(config) is papis.config.Configuration


def test_merge_configuration_from_path() -> None:
    with tempfile.NamedTemporaryFile("w+", delete=False) as configfile:
        configpath = configfile.name
        configfile.write("""
[settings]

some-nice-setting = 42
some-other-setting = mandragora
        """)

    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("some-nice-setting")

    papis.config.set("some-nice-setting", "what-is-the-question")
    assert papis.config.get("some-nice-setting") == "what-is-the-question"

    config = papis.config.get_configuration()
    papis.config.merge_configuration_from_path(configpath, config)
    assert papis.config.get("some-nice-setting") == "42"
    assert papis.config.get("some-other-setting") == "mandragora"

    os.unlink(configpath)


def test_set_lib_non_existing() -> None:
    lib = "non-existing-library"
    assert not os.path.exists(lib)

    with pytest.raises(
            Exception,
            match="Library '{}' does not seem to exist".format(lib)):
        papis.config.set_lib_from_name(lib)


def test_set_lib_from_path() -> None:
    with tempfile.TemporaryDirectory() as lib:
        assert os.path.exists(lib)
        papis.config.set_lib_from_name(lib)
        assert papis.config.get_lib_name() == lib


def test_set_lib_from_real_lib() -> None:
    with tempfile.TemporaryDirectory() as libdir:
        libname = "test-set-lib"
        papis.config.set("dir", libdir, section=libname)
        assert os.path.exists(libdir)

        papis.config.set_lib_from_name(libname)
        assert papis.config.get_lib_name() == libname


def test_reset_configuration() -> None:
    papis.config.set("test_reset_configuration", "mordor")
    assert papis.config.get("test_reset_configuration") == "mordor"
    config = papis.config.reset_configuration()
    assert type(config) is papis.config.Configuration

    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("test_reset_configuration")


def test_get_default_settings() -> None:
    settings = papis.config.get_default_settings()
    assert isinstance(settings, dict)
    assert len(settings) != 0

    section = papis.config.get_general_settings_name()
    assert section in settings
    assert settings[section]["mvtool"] == "mv"


def test_register_default_settings() -> None:
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


def test_get_list() -> None:
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
        assert papis.config.getlist("super-key-list") == "[asdf,'2','3','4']"
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
        assert papis.config.getlist("super-key-list") == "[asdf,2,3,4]"
    except SyntaxError as e:
        assert (
            str(e) == (
                "The key 'super-key-list' must be a valid Python list. "
                "Got: 2 (type 'int')"
            )
        )

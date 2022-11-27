import os
import re
import sys
import pytest
import tempfile

import papis.exceptions
import papis.config
from papis.config import _CONFIGURATION


def test_default_opener():
    if sys.platform.startswith("darwin"):
        assert papis.config.get_default_opener() == "open"
    elif sys.platform.startswith("win"):
        assert papis.config.get_default_opener() == "start"
    else:
        assert papis.config.get_default_opener() == "xdg-open"


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_home(monkeypatch):
    tmpdir = tempfile.gettempdir()

    with monkeypatch.context() as m:
        m.setenv("XDG_CONFIG_HOME", tmpdir)
        assert papis.config.get_config_home() == tmpdir

    with monkeypatch.context() as m:
        m.delenv("XDG_CONFIG_HOME", raising=False)
        assert re.match(r".+config", papis.config.get_config_home()) is not None


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_dirs(monkeypatch):
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
def test_get_config_folder(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        with monkeypatch.context() as m:
            m.setenv("XDG_CONFIG_HOME", d)
            configpath = os.path.join(os.environ["XDG_CONFIG_HOME"], "papis")
            if not os.path.exists(configpath):
                os.mkdir(configpath)
            assert papis.config.get_config_folder() == configpath


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_config_file(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        with monkeypatch.context() as m:
            m.setenv("XDG_CONFIG_HOME", d)
            configpath = os.path.join(papis.config.get_config_folder(), "config")
            assert configpath == papis.config.get_config_file()


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_configpy_file(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        with monkeypatch.context() as m:
            m.setenv("XDG_CONFIG_HOME", d)
            configpath = os.path.join(papis.config.get_config_folder(), "config.py")
            assert configpath == papis.config.get_configpy_file()
            assert os.environ["XDG_CONFIG_HOME"] in configpath


def test_set_config_file():
    with tempfile.NamedTemporaryFile() as f:
        papis.config.set_config_file(f.name)
        assert papis.config.get_config_file() == f.name


def test_get_scripts_folder():
    ccfolder = papis.config.get_config_folder()
    assert os.path.join(ccfolder, "scripts") == papis.config.get_scripts_folder()


def test_set():
    papis.config.set("nonexistenkey", "rofi")
    assert papis.config.get("nonexistenkey") == "rofi"

    papis.config.set("super_key_", "adams", section="nonexistent")
    assert papis.config.get("super_key_", section="nonexistent") == "adams"


def test_get():
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


def test_get_configuration():
    settings = papis.config.get_general_settings_name()
    config = papis.config.get_configuration()
    assert type(config) is papis.config.Configuration
    assert settings in config.keys()
    assert id(_CONFIGURATION) == id(config)


def test_get_configuration_2():
    global _CONFIGURATION
    _CONFIGURATION = None

    config = papis.config.get_configuration()
    assert type(config) is papis.config.Configuration


def test_merge_configuration_from_path():
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


def test_set_lib_from_path():
    with tempfile.TemporaryDirectory() as lib:
        assert os.path.exists(lib)
        papis.config.set_lib_from_name(lib)
        assert papis.config.get_lib_name() == lib


def test_set_lib_from_real_lib():
    with tempfile.TemporaryDirectory() as libdir:
        libname = "test-set-lib"
        papis.config.set("dir", libdir, section=libname)
        assert os.path.exists(libdir)

        papis.config.set_lib_from_name(libname)
        assert papis.config.get_lib_name() == libname


def test_reset_configuration():
    papis.config.set("test_reset_configuration", "mordor")
    assert papis.config.get("test_reset_configuration") == "mordor"
    config = papis.config.reset_configuration()
    assert type(config) is papis.config.Configuration

    with pytest.raises(papis.exceptions.DefaultSettingValueMissing):
        papis.config.get("test_reset_configuration")


def test_get_default_settings():
    assert type(papis.config.get_default_settings()) is dict
    assert papis.config.get_default_settings()["settings"]["mvtool"] == "mv"


def test_register_default_settings():
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


def test_get_list():
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
                "The key 'super-key-list' must be a valid python "
                "object\n\tname 'asdf' is not defined"
            )
        )

    papis.config.set("super-key-list", "2")
    assert papis.config.get("super-key-list") == "2"
    assert papis.config.getint("super-key-list") == 2
    try:
        assert papis.config.getlist("super-key-list") == "[asdf,2,3,4]"
    except SyntaxError as e:
        assert (
            str(e) == (
                "The key 'super-key-list' must be a valid python list"
            )
        )

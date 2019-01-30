from papis.config import *
from papis.config import _CONFIGURATION
import os
import sys
import re
import tempfile
import papis.exceptions

def test_default_opener():
    plat = sys.platform
    sys.platform = 'darwin v01'
    assert(get_default_opener() == 'open')
    sys.platform = plat
    osname = os.name
    os.name = 'nt'
    assert(get_default_opener() == 'start')
    os.name = 'posix'
    assert(get_default_opener() == 'xdg-open')
    os.name = osname


def test_get_config_home():
    os.environ['XDG_CONFIG_HOME'] = '/tmp'
    assert get_config_home() == '/tmp'
    del os.environ['XDG_CONFIG_HOME']
    assert re.match(r'.+config', get_config_home()) is not None


def test_get_config_dirs():
    os.environ['XDG_CONFIG_DIRS'] = ''
    os.environ['XDG_CONFIG_HOME'] = '/tmp'
    dirs = get_config_dirs()
    assert len(dirs) == 2
    assert '/tmp/papis' == dirs[0]

    os.environ['XDG_CONFIG_DIRS'] = '/etc/:/usr/local/etc'
    os.environ['XDG_CONFIG_HOME'] = '~'
    dirs = get_config_dirs()
    assert len(dirs) == 4
    assert '/etc/papis' == dirs[0]
    assert '/usr/local/etc/papis' == dirs[1]
    assert os.path.expanduser('~/papis') == dirs[2]
    assert os.path.expanduser('~/.papis') == dirs[3]


def test_get_config_folder():
    os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp()
    configpath = os.path.join(os.environ['XDG_CONFIG_HOME'], 'papis')
    if not os.path.exists(configpath):
        os.mkdir(configpath)
    assert get_config_folder() == configpath


def test_get_config_file():
    os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp()
    configpath = os.path.join(get_config_folder(), 'config')
    assert configpath == get_config_file()


def test_set_config_file():
    configfile = tempfile.mktemp()
    set_config_file(configfile)
    assert get_config_file() == configfile


def test_get_scripts_folder():
    ccfolder = get_config_folder()
    assert os.path.join(ccfolder, 'scripts') == get_scripts_folder()


def test_set():
    set('nonexistenkey', 'rofi')
    assert get('nonexistenkey') == 'rofi'

    set('super_key_', 'adams', section='nonexistent')
    assert get('super_key_', section='nonexistent') == 'adams'


def test_get():
    settings = get_general_settings_name()

    set('test_get', 'value1')
    assert get('test_get') == 'value1'
    assert get('test_get', section=settings) == 'value1'

    set('test_get', 'value42', section=get_lib())
    assert 'value42' == get('test_get')
    assert 'value42' == get('test_get', section=get_lib())
    assert 'value1' == get('test_get', section=settings)

    set('test_getint', '42')
    assert getint('test_getint') == 42
    assert getint('test_getint', section=settings) == 42
    assert type(getint('test_getint', section=settings)) is int

    set('test_getfloat', '3.14')
    assert getfloat('test_getfloat') == 3.14
    assert getfloat('test_getfloat', section=settings) == 3.14
    assert type(getfloat('test_getfloat', section=settings)) is float

    set('test_getbool', 'True')
    assert getboolean('test_getbool') == True
    assert getboolean('test_getbool', section=settings) == True
    set('test_getbool', 'False')
    assert getboolean('test_getbool') == False
    assert getboolean('test_getbool', section=settings) == False

    try:
        get('_unknown_key')
    except papis.exceptions.DefaultSettingValueMissing:
        assert True
    else:
        assert False


def test_get_configuration():
    settings = get_general_settings_name()
    config = get_configuration()
    assert type(config) is Configuration
    assert settings in config.keys()
    assert id(_CONFIGURATION) == id(config)


def test_get_configuration_2():
    _CONFIGURATION = None
    config = get_configuration()
    assert type(config) is Configuration


def test_merge_configuration_from_path():
    configpath = tempfile.mktemp()
    with open(configpath, "w+") as configfile:
        configfile.write("""
[settings]

some-nice-setting = 42
some-other-setting = mandragora
        """)
    config = get_configuration()
    try:
        get('some-nice-setting')
    except papis.exceptions.DefaultSettingValueMissing:
        assert True
    else:
        assert False

    set('some-nice-setting', 'what-is-the-question')
    assert get('some-nice-setting') == 'what-is-the-question'

    merge_configuration_from_path(configpath, config)
    assert get('some-nice-setting') == '42'
    assert get('some-other-setting') == 'mandragora'


def test_set_lib_from_path():
    lib = tempfile.mkdtemp()
    assert os.path.exists(lib)
    set_lib(lib)
    assert os.environ['PAPIS_LIB'] == lib
    assert os.environ['PAPIS_LIB_DIR'] == lib
    assert get_lib() == lib


def test_set_lib_from_real_lib():
    libdir = tempfile.mkdtemp()
    libname = 'test-set-lib'
    set('dir', libdir, section=libname)
    assert os.path.exists(libdir)
    set_lib(libname)
    assert os.environ['PAPIS_LIB'] == libname
    assert os.environ['PAPIS_LIB_DIR'] == libdir
    assert get_lib() == libname


def test_reset_configuration():
    set('test_reset_configuration', 'mordor')
    assert get('test_reset_configuration') == 'mordor'
    config = reset_configuration()
    assert type(config) is Configuration
    try:
        get('test_reset_configuration')
    except papis.exceptions.DefaultSettingValueMissing:
        assert True
    else:
        assert False

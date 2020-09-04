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
    tmpdir = '/tmp'
    os.environ['XDG_CONFIG_HOME'] = tmpdir
    if os.environ.get('XDG_CONFIG_DIRS') is not None:
        del os.environ['XDG_CONFIG_DIRS']
    dirs = get_config_dirs()
    assert os.environ.get('XDG_CONFIG_DIRS') is None
    assert len(dirs) == 2
    assert os.path.join('/', 'tmp', 'papis') == dirs[0]

    os.environ['XDG_CONFIG_DIRS'] = '/etc/:/usr/local/etc'
    os.environ['XDG_CONFIG_HOME'] = '~'
    dirs = get_config_dirs()
    assert len(dirs) == 4
    assert os.path.abspath('/etc/papis') == os.path.abspath(dirs[0])
    assert os.path.abspath('/usr/local/etc/papis') == os.path.abspath(dirs[1])
    assert (os.path.abspath(os.path.expanduser('~/papis'))
            == os.path.abspath(dirs[2]))
    assert (os.path.abspath(os.path.expanduser('~/.papis'))
            == os.path.abspath(dirs[3]))


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

def test_get_configpy_file():
    os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp()
    configpath = os.path.join(get_config_folder(), 'config.py')
    assert configpath == get_configpy_file()
    assert(os.environ['XDG_CONFIG_HOME'] in configpath)


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

    set('test_get', 'value42', section=get_lib_name())
    assert 'value42' == get('test_get')
    assert 'value42' == get('test_get', section=get_lib_name())
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
    set_lib_from_name(lib)
    assert get_lib_name() == lib


def test_set_lib_from_real_lib():
    libdir = tempfile.mkdtemp()
    libname = 'test-set-lib'
    set('dir', libdir, section=libname)
    assert os.path.exists(libdir)
    set_lib_from_name(libname)
    assert get_lib_name() == libname


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


def test_get_default_settings():
    import collections
    assert(type(get_default_settings()) is dict)
    assert(get_default_settings()['settings']['mvtool'] == 'mv')


def test_register_default_settings():
    papis.config.register_default_settings(
        {'scihub': { 'command': 'open'}}
    )
    assert(papis.config.get('command', section='scihub') == 'open')

    papis.config.set('scihub-command', 'edit')
    assert(papis.config.get('command', section='scihub') == 'edit')

    options = {'settings': { 'hubhub': 42, 'default-library': 'mag' }}
    papis.config.register_default_settings(options)

    assert(papis.config.get('hubhub') == 42)
    assert(papis.config.get('info-name') is not None)
    assert(not papis.config.get('default-library') == 'mag')
    assert(
        papis.config.get_default_settings()['settings']['default-library']
        == 'mag')


def test_get_list():
    papis.config.set('super-key-list', [1,2,3,4])
    assert(papis.config.get('super-key-list') == '[1, 2, 3, 4]')
    assert(papis.config.getlist('super-key-list') == ['1','2','3','4'])

    papis.config.set('super-key-list', ['asdf',2,3,4])
    assert(papis.config.get('super-key-list') == "['asdf', 2, 3, 4]")
    assert(papis.config.getlist('super-key-list') == ['asdf','2','3','4'])

    papis.config.set('super-key-list', ['asdf',2,3,4])
    assert(papis.config.get('super-key-list') == "['asdf', 2, 3, 4]")
    assert(papis.config.getlist('super-key-list') == ['asdf','2','3','4'])

    papis.config.set('super-key-list', "['asdf',2,3,4]")
    assert(papis.config.get('super-key-list') == "['asdf',2,3,4]")
    assert(papis.config.getlist('super-key-list') == ['asdf','2','3','4'])

    papis.config.set('super-key-list', "[asdf,2,3,4]")
    assert(papis.config.get('super-key-list') == "[asdf,2,3,4]")
    try:
        papis.config.getlist('super-key-list') == "[asdf,'2','3','4']"
    except SyntaxError as e:
        assert(
            str(e) == (
            "The key 'super-key-list' must be a valid python "
            "object\n\tname 'asdf' is not defined"
            )
        )
    else:
        assert(False)

    papis.config.set('super-key-list', "2")
    assert(papis.config.get('super-key-list') == "2")
    assert(papis.config.getint('super-key-list') == 2)
    try:
        papis.config.getlist('super-key-list') == "[asdf,2,3,4]"
    except SyntaxError as e:
        assert(
            str(e) == (
            "The key 'super-key-list' must be a valid python list"
            )
        )
    else:
        assert(False)

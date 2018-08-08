import papis.config
import os
import sys


def test_default_opener():
    plat = sys.platform
    sys.platform = 'darwin v01'
    assert(papis.config.get_default_opener() == 'open')
    sys.platform = plat
    osname = os.name
    os.name = 'nt'
    assert(papis.config.get_default_opener() == 'start')
    os.name = 'posix'
    assert(papis.config.get_default_opener() == 'xdg-open')
    os.name = osname

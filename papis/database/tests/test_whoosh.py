import os
import sys
import papis.config
import papis.database.whoosh

papis.config.set('database-backend', 'whoosh')
assert(papis.config.get('database-backend') == 'whoosh')

os.environ['XDG_CACHE_HOME'] = os.path.join(
    os.path.abspath(os.sep),
    'tmp',
    'cache'
)

libdir = os.path.join(
    os.path.abspath(os.sep),
    'tmp',
    'test-whoosh'
)


if not os.path.exists(libdir):
    os.mkdir(libdir, mode=0o777)
assert(os.path.exists(libdir))

papis.config.set_lib(libdir)
assert(papis.config.get_lib() == libdir)

database = papis.database.get(libdir)
assert(database is not None)
assert(database.get_lib() == libdir)
assert(database.get_dir() == libdir)



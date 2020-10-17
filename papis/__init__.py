import os

# Information
__license__ = 'GPLv3'
__version__ = '0.11.1'
__author__ = __maintainer__ = 'Alejandro Gallo'
__email__ = 'aamsgallo@gmail.com'


if os.environ.get('PAPIS_DEBUG'):
    import logging
    log_format = (
        '%(relativeCreated)d-' +
        '%(levelname)s' +
        ':' +
        '%(name)s' +
        ':' +
        '%(message)s'
    )
    logging.basicConfig(format=log_format, level=logging.DEBUG)

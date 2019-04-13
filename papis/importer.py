import papis
import logging
import os.path
from stevedore import extension
import papis.plugin

logger = logging.getLogger('importer')


class Context:
    def __init__(self):
        self.data = dict()
        self.files = []

    def __bool__(self):
        return bool(self.files) or bool(self.data)


class Importer:

    """This is the base class for every importer"""

    def __init__(self, uri="", name="", ctx=None):
        """
        :param uri: uri
        :type  uri: str
        :param name: Name of the importer
        :type  name: str
        """
        self.ctx = ctx or Context()
        assert(isinstance(uri, str))
        assert(isinstance(name, str))
        assert(isinstance(self.ctx, Context))
        self.uri = uri
        self.name = name or os.path.basename(__file__)
        self.logger = logging.getLogger("importer:{0}".format(self.name))

    @classmethod
    def match(uri):
        """This method should be called to know if a given uri matches
        the importer or not.

        For example, a valid match for archive would be:
        .. code:: python

            return re.match(r".*arxiv.org.*", uri)

        it will return something that is true if it matches and something
        falsely otherwise.

        :param uri: uri where the document should be retrieved from.
        :type  uri: str
        """
        raise NotImplementedError(
            "Matching uri not implemented for this downloader"
        )

    def fetch(self):
        """
        can return a dict to update the document with
        """
        raise NotImplementedError()

    def __str__(self):
        return 'Importer({0}, uri={1})'.format(self.name, self.uri)


import_mgr = None


def _create_import_mgr():
    global import_mgr
    if import_mgr:
        return
    import_mgr = extension.ExtensionManager(
        namespace='papis.importer',
        invoke_on_load=True,
        verify_requirements=True,
        invoke_args=(),
        # invoke_kwds
        propagate_map_exceptions=True,
        on_load_failure_callback=papis.plugin.stevedore_error_handler
    )


def get_import_mgr():
    """Get the import manager
    :returns: Import manager
    :rtype:  stevedore.extension.ExtensionManager
    """
    global import_mgr
    _create_import_mgr()
    return import_mgr


def available_importers():
    """Get the available importers defined.
    :returns: List of importer names
    :rtype:  list(str)
    """
    return get_import_mgr().entry_points_names()


def get_importer_by_name(name):
    """Get importer by name
    :param name: Name of the importer
    :type  name: str
    :returns: The importer
    :rtype:  Importer
    """
    assert(isinstance(name, str))
    return get_import_mgr()[name].plugin


def cache(f):
    """
    This is a decorator to be used if a method of an Importer
    is to be cached, i.e., if the context of the importer is already
    set, then one does not need to run the function anymore, even if
    it is explicitly run.

    :param self: Method of an Importer
    """
    def wrapper(self):
        if not self.ctx:
            f(self)
    return wrapper

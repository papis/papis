import os
import random
import tempfile
from types import TracebackType
from typing import Any, ClassVar, Dict, Iterator, Optional, Sequence, Type

import pytest
import click
import click.testing
from _pytest.fixtures import SubRequest
from _pytest.config import Config
from _pytest.config.argparsing import Parser

PAPIS_UPDATE_RESOURCES = os.environ.get("PAPIS_UPDATE_RESOURCES", "none").lower()
if PAPIS_UPDATE_RESOURCES not in {"none", "remote", "local", "both"}:
    raise ValueError("unsupported value of 'PAPIS_UPDATE_RESOURCES'")


def create_random_file(filetype: Optional[str] = None,
                       prefix: Optional[str] = None,
                       suffix: Optional[str] = None,
                       dir: Optional[str] = None) -> str:
    """Create a random file with the correct magic signature.

    This function creates random empty files that can be used for testing. It
    supports creating PDF, EPUB, DjVu or simple text files. These are
    constructed in such a way that they are recognized by
    :func:`papis.filetype.guess_content_extension`.

    :arg filetype: the desired filetype of the result, which can be one of
        ``("pdf", "epub", "djvu", "text")``.
    :arg prefix: a prefix passed to :func:`tempfile.NamedTemporaryFile`.
    :arg suffix: a suffix passed to :func:`tempfile.NamedTemporaryFile`.
    :arg dir: a base directory passed to :func:`tempfile.NamedTemporaryFile`.
    """
    if filetype is None:
        filetype = random.choice(["pdf", "epub", "djvu"])

    # NOTE: these are chosen to match using 'filetype.guess' and are not valid
    # files otherwise
    filetype = filetype.lower()
    if filetype == "pdf":
        buf = b"%PDF-1.5%\n"
        suffix = ".pdf" if suffix is None else suffix
    elif filetype == "epub":
        buf = bytes(
            [0x50, 0x4B, 0x3, 0x4]
            + [0x00 for i in range(26)]
            + [0x6D, 0x69, 0x6D, 0x65, 0x74, 0x79, 0x70, 0x65, 0x61, 0x70,
                0x70, 0x6C, 0x69, 0x63, 0x61, 0x74, 0x69, 0x6F, 0x6E, 0x2F,
                0x65, 0x70, 0x75, 0x62, 0x2B, 0x7A, 0x69, 0x70]
            + [0x00 for i in range(1)]
            )
        suffix = ".epub" if suffix is None else suffix
    elif filetype == "djvu":
        buf = bytes([
            0x41, 0x54, 0x26, 0x54, 0x46, 0x4F, 0x52, 0x4D,
            0x00, 0x00, 0x00, 0x00,
            0x44, 0x4A, 0x56, 0x4D])
        suffix = ".djvu" if suffix is None else suffix
    elif filetype == "text":
        buf = b"papis-test-file-contents"
    else:
        raise ValueError(f"Unknown file type: '{filetype}'")

    with tempfile.NamedTemporaryFile(
            dir=dir, suffix=suffix, prefix=prefix,
            delete=False) as fd:
        fd.write(buf)

    return fd.name


PAPIS_TEST_DOCUMENTS = [
    {
        "author": "doc without files",
        "title": "Title of doc without files",
        "year": 1093,
        "_test_files": 0,
    },
    {
        "author": "J. Krishnamurti",
        "title": "Freedom from the known",
        "year": 2009,
        "tags": ["tag1", 1234],
        "_test_files": 1,
    }, {
        "author": "K. Popper",
        "doi": "10.1021/ct5004252",
        "title": "The open society",
        "volume": "I",
        "_test_files": 0,
    }, {
        "type": "article",
        "author": "Turing, A. M.",
        "doi": "10.1112/plms/s2-42.1.230",
        "issue": "1",
        "journal": "Proceedings of the London Mathematical Society",
        "note": "First turing machine paper foundation of cs",
        "pages": "230--265",
        "title": "On Computable Numbers with an Application to the Entscheidungsproblem",           # noqa: E501
        "url": "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1112%2Fplms%2Fs2-42.1.230",
        "volume": "s2-42",
        "year": 1937,
        "_test_files": 2,
    },
    {
        "author": "test_author",
        "title": "Test Document 1 (wRkdff)",
        "year": 2019,
        "_test_files": 1
    },
    {
        "author": "test_author",
        "title": "Test Document 2 (ZD9QRz)",
        "year": 2019,
        "_test_files": 1
    },
    {
        "address": "Scranton, PA, USA",
        "author": "Scott, Michael",
        "booktitle": "Humor in the Workplace",
        "editor_list": [{"family": "Halpert", "given": "Jim"},
                        {"family": "Beesly", "given": "Pam"}],
        "pages": "56-71",
        "publisher": "Scranton Publishing",
        "ref": "scott2008that",
        "title": "That is What She Said. The Art of Office Banter",
        "type": "incollection",
        "year": "2008",
        "_test_files": 1
    },
    {
        "address": "Scranton, PA, USA",
        "author": "Schrute, Dwight K.",
        "booktitle": "Beets: The Ultimate Guide to Beet Farming",
        "editor": "Martin, Angela",
        "pages": "15-30",
        "publisher": "Schrute Farms Publishing",
        "ref": "schrute2020beet",
        "title": "Beet Identity. Unraveling the Mysteries of Schrute Farms Secret Crop",
        "type": "incollection",
        "year": "2020",
        "_test_files": 1
    },
]


def populate_library(libdir: str) -> None:
    """Add temporary documents with random files into the folder *libdir*.

    :arg libdir: an existing empty library directory.
    """
    import papis.id
    from papis.document import Document

    for i, data in enumerate(PAPIS_TEST_DOCUMENTS):
        doc_data = data.copy()

        folder_path = os.path.join(libdir, f"test_doc_{i}")
        os.makedirs(folder_path)

        # add files
        num_test_files = int(str(doc_data.pop("_test_files")))
        if num_test_files:
            doc_data["files"] = [
                os.path.basename(create_random_file(dir=folder_path))
                for _ in range(num_test_files)
                ]

        # create document
        doc = Document(folder_path, doc_data)
        doc[papis.id.key_name()] = papis.id.compute_an_id(doc)
        doc.save()


class TemporaryConfiguration:
    """A context manager used to create a temporary papis configuration.

    This configuration is created in a temporary directory and all the required
    paths are set to point to that directory (e.g. ``XDG_CONFIG_HOME`` and
    ``XDG_CACHE_HOME``). This is meant to be used by tests to create a default
    environment in which to run.

    It can be used in the standard way as

    .. code:: python

        # Set the configuration option `picktool`
        papis.config.set("picktool", "fzf")

        with TemporaryConfiguration() as config:
            # In this block, it is back to its default value
            value = papis.config.get("picktool")
            assert value == "papis"
    """

    #: Name of the default library
    libname: ClassVar[str] = "test"

    def __init__(self,
                 prefix: str = "papis-test-",
                 settings: Optional[Dict[str, Any]] = None,
                 overwrite: bool = False) -> None:
        #: A set of settings to be added to the configuration on creation
        self.settings: Optional[Dict[str, Any]] = settings
        #: If *True*, any configuration settings are overwritten by *settings*.
        self.overwrite: bool = overwrite

        #: When entering the context manager, this will contain the directory of
        #: a temporary library to run tests on. The library is unpopulated by default
        self.libdir: str = ""
        #: When entering the context manager, this will contain the config
        #: directory used by papis.
        self.configdir: str = ""
        #: When entering the context manager, this will contain the config
        #: file used by papis.
        self.configfile: str = ""

        #: Prefix for the temporary directory created for the test.
        self.prefix = prefix

        self._tmpdir: Optional[tempfile.TemporaryDirectory[str]] = None
        self._monkeypatch: Optional[pytest.MonkeyPatch] = None

    @property
    def tmpdir(self) -> str:
        """Base temporary directory name."""
        assert self._tmpdir
        return self._tmpdir.name

    def create_random_file(self,
                           filetype: Optional[str] = None,
                           prefix: Optional[str] = None,
                           suffix: Optional[str] = None) -> str:
        """Create a random file in the :attr:`tmpdir` using `create_random_file`."""
        return create_random_file(
            filetype, suffix=suffix, prefix=prefix,
            dir=self.tmpdir)

    def __enter__(self) -> "TemporaryConfiguration":
        if self._tmpdir is not None:
            raise ValueError(f"'{type(self).__name__}' cannot be nested")

        # create directories and files
        self._monkeypatch = pytest.MonkeyPatch()
        self._tmpdir = tempfile.TemporaryDirectory(prefix=self.prefix)

        self.libdir = os.path.join(self.tmpdir, "lib")
        self.configdir = os.path.join(self.tmpdir, "papis")
        self.configfile = os.path.join(self.configdir, "config")
        self.configscripts = os.path.join(self.configdir, "scripts")

        os.makedirs(self.libdir)
        os.makedirs(self.configdir)
        os.makedirs(self.configscripts)

        # load settings
        import papis.config

        settings = {
            self.libname: {"dir": papis.config.escape_interp(self.libdir)},
            "settings": {"default-library": self.libname}
        }

        if self.settings is not None:
            if self.overwrite:
                settings = self.settings
            else:
                settings["settings"].update(self.settings)

        # NOTE: set variables to overwrite platformdirs
        self._monkeypatch.setenv("PAPIS_CONFIG_DIR", self.configdir)
        self._monkeypatch.setenv("PAPIS_CACHE_DIR", self.configdir)

        # NOTE: set XDG variables so that old path still works
        self._monkeypatch.setenv("XDG_CONFIG_HOME", self.tmpdir)
        self._monkeypatch.setenv("XDG_CACHE_HOME", self.tmpdir)

        # write settings
        import configparser
        with open(self.configfile, "w", encoding="utf-8") as fd:
            config = configparser.ConfigParser()
            config.read_dict(settings)
            config.write(fd)

        # monkeypatch globals
        import papis.format
        self._monkeypatch.setattr(papis.format, "FORMATTER", {})

        import papis.database
        self._monkeypatch.setattr(papis.database, "DATABASES", {})
        # FIXME: may need to also add the following:
        #   * reset papis.bibtex globals
        #   * reset papis.plugin managers

        # reload configuration
        papis.config.set_config_file(self.configfile)
        papis.config.reset_configuration()

        assert papis.config.get("default-library")
        assert papis.config.get_config_folder() == self.configdir
        assert papis.config.get_config_file() == self.configfile

        from papis.config import _get_deprecated_config_folder
        assert _get_deprecated_config_folder() == self.configdir

        return self

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        # cleanup
        if self._monkeypatch:
            self._monkeypatch.undo()
        if self._tmpdir:
            self._tmpdir.cleanup()

        # reset variables
        self._tmpdir = None
        self.libdir = ""
        self.configdir = ""
        self.configfile = ""


class TemporaryLibrary(TemporaryConfiguration):
    """A context manager used to create a temporary papis configuration with a
    library.

    This extends :class:`TemporaryConfiguration` with more support for creating
    and maintaining a temporary library. This can be used by tests that
    specifically require handling documents in a library.
    """

    def __init__(self,
                 settings: Optional[Dict[str, Any]] = None,
                 use_git: bool = False,
                 populate: bool = True) -> None:
        super().__init__(settings=settings)

        #: If *True*, a git repository is created in the library directory.
        self.use_git = use_git
        #: If *True*, the library is prepopulated with a set of documents that
        #: contain random files and keys, which can be used for testing.
        self.populate = populate

    def __enter__(self) -> "TemporaryLibrary":
        super().__enter__()

        # initialize library
        import papis.library
        lib = papis.library.Library(self.libname, [self.libdir])

        import papis.config
        papis.config.set("default-library", self.libname)
        papis.config.set_lib(lib)

        # populate library
        if self.populate:
            populate_library(self.libdir)

        if self.use_git:
            from papis.utils import run

            # make sure to initialize a git repository for the library
            run(["git", "init", "-b", "main"], cwd=self.libdir)
            run(["git", "config", "user.name", "papis"],
                cwd=self.libdir)
            run(["git", "config", "user.email", "papis@example.com"],
                cwd=self.libdir)

            if self.populate:
                run(["git", "add", "."], cwd=self.libdir)
                run(["git", "commit", "-m", "Initial commit"], cwd=self.libdir)

        return self


class PapisRunner(click.testing.CliRunner):
    """A wrapper around :class:`click.testing.CliRunner`."""

    def __init__(self, **kwargs: Any) -> None:
        if "mix_stderr" not in kwargs:
            kwargs["mix_stderr"] = False

        super().__init__(**kwargs)

    def invoke(self,        # type: ignore[override]
               cli: click.Command,
               args: Sequence[str], **kwargs: Any) -> click.testing.Result:
        """A simple wrapper around the :meth:`click.testing.CliRunner.invoke`
        method that does not catch exceptions by default.
        """

        if "catch_exceptions" not in kwargs:
            kwargs["catch_exceptions"] = False

        return super().invoke(cli, args, **kwargs)


class ResourceCache:
    """A class that handles retrieving local and remote resources for tests from
    default folders.

    This class mainly exists to test importers and downloaders that require
    getting a remote resource and testing it against results of the papis
    converters.

    It can be controlled by the ``PAPIS_UPDATE_RESOURCES`` environment variable,
    which takes the values:

    * ``"none"``: no resources are downloaded or updated (default).
    * ``"remote"``: remote resources are downloaded and the on-disk files are
      updated (used in :meth:`get_remote_resource`).
    * ``"local"``: local resources are updated with the results of the papis
      conversion (used in :meth:`get_local_resource`).
    * ``"both"``: both local and remote resources are updated.

    Resources can then be retrieved as

    .. code:: python

        # Call some function that retrieves and converts remote data
        local = papis.arxiv.get_data(...)

        # Check that the expected cached resource matches the result
        expected_local = cache.get_local_resource("resources/test.json", local)
        assert local == expected_local
    """

    def __init__(self, cachedir: str) -> None:
        import papis.utils

        #: The location of the resource directory.
        self.cachedir = os.path.abspath(cachedir)
        if not os.path.exists(self.cachedir):
            raise ValueError(f"Cache directory does not exist: {self.cachedir}")

        #: A :class:`requests.Session` used to download remote resources.
        self.session = papis.utils.get_session()

    def get_remote_resource(
            self, filename: str, url: str,
            force: bool = False,
            params: Optional[Dict[str, str]] = None,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Dict[str, str]] = None,
            ) -> bytes:
        """Retrieve a remote resource from the resource cache.

        If *force* is *True*, the *filename* does not exist or
        ``PAPIS_UPDATE_RESOURCES`` is set to ``("remote", "both")``, then the
        resource is downloaded from the remote location at *url*. Otherwise, it
        is retrieved from the locally cached version at *filename*.

        :arg filename: a file where to store the remote resource.
        :arg url: a remote URL from which to retrieve the resource.
        :arg force: if *True*, force updating the resource cached at *filename*.
        :arg params: additional params passed to :func:`requests.get`.
        :arg headers: additional headers passed to :func:`requests.get`.
        :arg cookies: additional cookies passed to :func:`requests.get`.
        """
        filename = os.path.join(self.cachedir, filename)

        force = force or not os.path.exists(filename)
        if force or PAPIS_UPDATE_RESOURCES in {"remote", "both"}:
            if headers is None:
                headers = {}

            response = self.session.get(
                url, params=params, headers=headers, cookies=cookies)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.content.decode())

        with open(filename, encoding="utf-8") as f:
            return f.read().encode()

    def get_local_resource(
            self, filename: str, data: Any,
            force: bool = False) -> Any:
        """Retrieve a local resource from the resource cache.

        If *force* is *True*, the *filename* does not exist or
        ``PAPIS_UPDATE_RESOURCES`` is set to ``("local", "both")``, then the
        local resource is updated using *data*. Otherwise, it is retrieved from
        the locally cached version at *filename*.

        :arg filename: a file where to store the local resource.
        :arg data: data that should be retrieve from the resource.
        :arg force: if *True*, force updating the resource cached at *filename*.
        """
        filename = os.path.join(self.cachedir, filename)
        _, ext = os.path.splitext(filename)

        import json
        import yaml
        import papis.yaml

        force = force or not os.path.exists(filename)
        if force or PAPIS_UPDATE_RESOURCES in {"local", "both"}:
            assert data is not None
            with open(filename, "w", encoding="utf-8") as f:
                if ext == ".json":
                    json.dump(
                        data, f,
                        indent=2,
                        sort_keys=True,
                        ensure_ascii=False,
                        )
                elif ext in {".yml", ".yaml"}:
                    yaml.dump(
                        data, f,
                        indent=2,
                        sort_keys=True,
                        )
                else:
                    raise ValueError(f"Unknown file extension: '{ext}'")

        with open(filename, encoding="utf-8") as f:
            if ext == ".json":
                return json.load(f)
            elif ext in {".yml", ".yaml"}:
                return papis.yaml.yaml_to_data(filename)
            else:
                raise ValueError(f"Unknown file extension: '{ext}'")


@pytest.fixture(autouse=True)
def _doctest_tmp_config(request: SubRequest) -> Iterator[None]:
    """A fixture for doctests to ensure that they run in a clean environment.

    This fixture is enabled automatically for all doctests using the
    ``--papis-tmp-doctests`` command-line flag.
    """
    # NOTE: taken from https://stackoverflow.com/a/46991331
    doctest_plugin = request.config.pluginmanager.getplugin("doctest")

    # NOTE: this should only run for papis doctests
    if (
            isinstance(request.node, doctest_plugin.DoctestItem)
            and request.config.getoption("--papis-tmp-doctests")):
        with TemporaryConfiguration():
            yield
    else:
        yield


@pytest.fixture(scope="function")
def tmp_config(request: SubRequest) -> Iterator[TemporaryConfiguration]:
    """A fixture that creates a :class:`TemporaryConfiguration`.

    Additional keyword arguments can be passed using the ``config_setup`` marker

    .. code:: python

        @pytest.mark.config_setup(overwrite=True)
        def test_me(tmp_config: TemporaryConfiguration) -> None:
            ...
    """
    # NOTE: using markers to pass arguments to fixtures as defined in
    #   https://docs.pytest.org/en/latest/how-to/fixtures.html#using-markers-to-pass-data-to-fixtures
    marker = request.node.get_closest_marker("config_setup")
    kwargs = marker.kwargs if marker else {}

    # NOTE: support indirect fixture parametrizations that overwrite markers
    #   https://docs.pytest.org/en/latest/example/parametrize.html#apply-indirect-on-particular-arguments
    kwargs.update(getattr(request, "param", {}))

    with TemporaryConfiguration(**kwargs) as config:
        yield config


@pytest.fixture(scope="function")
def tmp_library(request: SubRequest) -> Iterator[TemporaryLibrary]:
    """A fixture that creates a :class:`TemporaryLibrary`.

    Additional keyword arguments can be passed using the ``library_setup`` marker

    .. code:: python

        @pytest.mark.library_setup(use_git=False)
        def test_me(tmp_library: TemporaryLibrary) -> None:
            ...
    """
    marker = request.node.get_closest_marker("library_setup")
    kwargs = marker.kwargs if marker else {}

    # NOTE: support indirect fixture parametrizations that overwrite markers
    kwargs.update(getattr(request, "param", {}))

    with TemporaryLibrary(**kwargs) as lib:
        yield lib


@pytest.fixture(scope="function")
def resource_cache(request: SubRequest) -> ResourceCache:
    """A fixture that creates a :class:`ResourceCache`.

    Additional keyword arguments can be passed using the ``resource_setup`` marker

    .. code:: python

        @pytest.mark.resource_setup(cachedir="resources")
        def test_me(resource_cache: ResourceCache) -> None:
            ...
    """
    marker = request.node.get_closest_marker("resource_setup")
    kwargs = marker.kwargs if marker else {"cachedir": "resources"}

    cachedir = kwargs.get("cachedir")
    if cachedir is not None:
        # NOTE: ensure that the resource folder is relative to the file
        dirname = os.path.dirname(request.path)
        kwargs["cachedir"] = os.path.join(dirname, cachedir)

    return ResourceCache(**kwargs)


def pytest_addoption(parser: Parser) -> None:
    parser.addoption("--papis-enable-logging", action="store_true",
                     help="Enable logging while running tests")
    parser.addoption("--papis-tmp-doctests", action="store_true",
                     help="Use a temporary configuration file for doctests")
    parser.addoption("--papis-tmp-xdg-home", action="store_true",
                     help="Set XDG_CONFIG_HOME to a temporary directory")


def pytest_configure(config: Config) -> None:
    if config.getoption("--papis-tmp-xdg-home"):
        # NOTE: some Papis modules call papis.config even before the tests have
        # a chance to construct a TemporaryConfiguration. We set XDG_CONFIG_HOME
        # here first to avoid them picking up any sort of user configuration.
        os.environ["XDG_CONFIG_HOME"] = tempfile.gettempdir()

    if config.getoption("--papis-enable-logging"):
        import papis.logging
        papis.logging.setup()

    config.addinivalue_line(
        "markers",
        "config_setup(**kwargs): pass kwargs to TemporaryConfiguration initialization")
    config.addinivalue_line(
        "markers",
        "library_setup(**kwargs): pass kwargs to TemporaryLibrary initialization")
    config.addinivalue_line(
        "markers",
        "resource_setup(**kwargs): pass kwargs to ResourceCache initialization")

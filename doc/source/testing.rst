Testing
=======

Papis uses :mod:`pytest` for its testing infrastructure and makes use of some of
its more advanced features (such as
`fixtures <https://docs.pytest.org/en/latest/explanation/fixtures.html>`__) to
set everything up. The command-line interface is based on :mod:`click` and is
tested using their testing helpers.

We give here an overview of the pieces needed to test the various parts of the
papis codebase, but in general mimicking existing tests is your best choice.

Using the default configuration
-------------------------------

The papis configuration is automatically loaded (and cached) on the first call
to a function such as :func:`papis.config.get` or :func:`papis.config.set`. By
default, it loads the configuration of the current user, somewhere at
``~/.config/papis/config``. This is obviously not desired for testing purposes,
as the configuration settings may differ and give incorrect results (that fail
on the CI).

To handle this, the :class:`~papis.testing.TemporaryConfiguration` context
manager is introduced to temporary redirect all the configuration paths to a
temporary location and load the default settings. It can be used as

.. code:: python

    import papis.testing

    def test_me() -> None:
        # ... some test setup ...

        with papis.testing.TemporaryConfiguration() as config:
            # ... tests that use papis.config functionality ...
            # ... and require default values ...

        # ... any calls outside of the context manager will take values ...
        # ... from the user configuration file if it exists ...

When using :mod:`pytest`, we can use a fixture to overwrite the configuration
for the whole function scope. For example, this can look like

.. code:: python

    import pytest
    import papis.testing

    @pytest.mark.config_setup(**kwargs)
    def test_me(tmp_config: papis.testing.TemporaryConfiguration) -> None:
        # ... all calls to papis.config in this function will point ...
        # ... to the temporary configuration ...
        assert tmp_config.configfile == papis.config.get_config_file()

The :func:`~papis.testing.tmp_config` fixture is automatically installed with
papis and can be used directly as above. It uses the ``config_setup`` marker
to pass keyword arguments directly to the underlying context manager. Check out
the documentation for :class:`papis.testing.TemporaryConfiguration` to see
additional attributes and functionality provided by this class.

If the test requires access to a papis library, e.g. to add, remove, or load
documents from the disk, the :class:`papis.testing.TemporaryLibrary` context
manager should be used instead. It also has a corresponding fixture called
``tmp_library`` that can be configured with ``library_setup`` as follows

.. code:: python

    import pytest
    import papis.testing

    @pytest.mark.library_setup(populate=True)
    def test_me(tmp_library: papis.testing.TemporaryLibrary) -> None:
        # ... this inherits all functionality of TemporaryConfiguration ...
        # ... but also has a small library populated with a dozen-ish documents ...
        # ... that have random files and metadata attached ...

        assert tmp_library.libname == papis.config.get_lib_name()

Testing commands
----------------

To test papis commands (such as ``papis add``), we make use of the infrastructure
from :class:`click.testing.CliRunner` and, in particular, the customized
:class:`papis.testing.PapisRunner`. To run a papis command like it would be invoked
from the command-line use

.. code:: python

    import papis.testing

    def test_me(tmp_library: papis.testing.TemporaryLibrary) -> None:
        from papis.commands.add import cli

        cli_runner = papis.testing.PapisRunner()
        result = cli_runner.invoke(
            # This needs to be a function that was wrapped by @click.group
            # ot @click.command to have all the argument handling
            cli,
            # This is a list of command-line arguments that will be passed to
            # the cli similar to how subprocess works
            ["--from", "doi", "10.1007/s11075-008-9193-8"]
        )
        assert result.exist_code == 0

The second argument to :meth:`~papis.testing.PapisRunner.invoke` is a list of
arguments that should match exactly what would be passed on the command-line.
The invocation returns a :class:`click.testing.Result` that has captured the
STDOUT and STDERR streams and can be easily inspected for testing purposes.

Testing downloaders
-------------------

Testing importers and downloaders generally requires handling some remote
resources, which are then converted to the papis format and saved as documents
in the library. To help with downloading and caching these resources, we can use
the :class:`papis.testing.ResourceCache` class.

This class handles caching resources on disk so that they can be used and compared
against in the test. In particular, testing a downloader involves the following
steps

1. Remote: download resource from a URL or retrieve from a local path
   (if it exists).
2. Convert: feed the remote resource to papis for conversion.
3. Local: retrieve an expected result from a local path (if it exists),
   otherwise save the existing conversion.
4. Check: check current conversion against the cached local resource.

When first adding a test case for a downloader, the resources are downloaded and
cached automatically, since they do not exist. To update the resources for a test,
use the ``PAPIS_UPDATE_RESOURCES`` environment variable when running the tests
locally. This is done simply as

.. code:: sh

    PAPIS_UPDATE_RESOURCES=remote python -m pytest -v -s test/downloaders/test_acl.py
    # ... or ...
    PAPIS_UPDATE_RESOURCES=local python -m pytest -v -s test/downloaders/test_acl.py
    # ... or ...
    PAPIS_UPDATE_RESOURCES=both python -m pytest -v -s test/downloaders/test_acl.py

The resources can also be updated in the test itself by using the ``force``
argument to :meth:`~papis.testing.ResourceCache.get_remote_resource` or
:meth:`~papis.testing.ResourceCache.get_local_resource`. The resource cache can
also be accessed through a fixture called :func:`~papis.testing.resource_cache`
that can be configured through the ``resource_setup`` marker. For example, we
can write something like

.. code:: python

    @pytest.mark.resource_setup(cachedir="downloaders/resources")
    def test_me(tmp_config: papis.testing.TemporaryConfiguration,
                resource_cache: papis.testing.ResourceCache,
                monkeypatch: pytest.MonkeyPatch) -> None:
        # ... pick a URL and some files names ...

        # ... monkeypatch the downloader to use the resource_cache ...
        downloader = papis.downloaders.get_downloader_by_name("acl")
        monkeypatch.setattr(downloader, "_get_body",
                            lambda: resource_cache.get_remote_resource(infile, url))

        # ... fetch remote resource data and check it against the stored version ...
        downloader.fetch()
        expected_data = resource_cache.get_local_resource(outfile, downloader.ctx.data)
        assert expected_data == downloader.ctx.data

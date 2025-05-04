.. _plugin-architecture:

Plugin architecture
===================

General architecture
--------------------

Papis uses the `stevedore <https://github.com/openstack/stevedore/>`__ library
for general plugin management. However, other modules are not expected to
interact with it and instead use the helper wrappers given by ``papis.plugin``.

The different plugins in Papis (e.g. ``papis.command``, ``papis.exporter`` etc.)
define a so-called :class:`~stevedore.extension.ExtensionManager`, which loads various
objects that have been declared as
`entrypoints <https://packaging.python.org/en/latest/specifications/entry-points/>`__
(plugins) in the package
`metadata <https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/>`__.

For example, the ``yaml`` exporter in ``papis.yaml`` is defined as:

.. code:: python

    def exporter(documents: List[papis.document.Document]) -> str:
        string = yaml.dump_all(
            [papis.document.to_dict(document) for document in documents],
            allow_unicode=True)
        return str(string)

... and declared in ``pyproject.toml`` as:

.. code:: toml

    [project.entry-points."papis.exporter"]
    yaml = "papis.yaml:exporter"

... where ``yaml`` is the name of the entrypoint, ``papis.yaml`` is the module
in which it is located and ``exporter`` is the callable used to invoke the
plugin, i.e. the format is ``<name> = "<module>:<callable>"``. The exporter can
be retrieved by name using:

.. code:: python

    import papis.plugin

    extension_manager = papis.plugin.get_extension_manager("papis.exporter")
    yaml_exporter = extension_manager["yaml"].plugin

    yaml_string = yaml_exporter(mydocs)

Due to the entrypoint mechanism used by ``stevedore``, any third-party package
can add plugins to Papis in this fashion. More information about each type of
plugin available in Papis is given below.

Exporter
--------
TO DOCUMENT

Command
-------
TO DOCUMENT

Importer
--------

Papis allows implementing additional plugins for importing external metadata
into its database through so-called "importers" and "downloaders". The
difference between a downloader and an importer is largely semantic. Downloaders
are mostly meant to scrape websites or download files from a remote location.

As an example we show here how to implement a custom downloader for the
`ACL Anthology <https://aclanthology.org/>`__. An :class:`~papis.importer.Importer`
is generally simpler, as it does not require scraping remote websites. We
recommend taking a look at one of the existing importers (e.g. in ``papis/crossref.py``)
or downloaders (e.g. in ``papis/downloaders/sciencedirect.py``) to get an idea
about existing features and implementations.

For a downloader, we create a new file in ``papis/downloaders`` and start writing
a class that inherits from :class:`papis.downloaders.Downloader`. This can look
something like:

.. code:: python

    from typing import Any, Dict, Optional

    import papis.document
    import papis.downloaders.base


    class Downloader(papis.downloaders.Downloader):
        def __init__(self, url: str) -> None:
            super().__init__(
                url,
                # A name for the downloader that is shown to the user at times
                name="acl",
                # The extensions that are expected from the downloaded files
                expected_document_extension="pdf",
                # Priority is sorted ascendingly (0 is the largest) and is used to
                # present the downloaders to the user and in automatic merging
                priority=10,
            )

The main way to recognize if a downloader can be used with a given URI is
through the :meth:`~papis.downloaders.Downloader.match` method. This generally
checks if a given URI matches a website URL, e.g.:

.. code:: python

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return Downloader(url) if re.match(r".*aclanthology\.org.*", url) else None

By default, a downloader implements a :meth:`~papis.downloaders.Downloader.get_data`
method to retrieve metadata. This already does a good job in fetching basic
metadata (title, authors, etc.) through standard elements such as the
`Dublin Core Metadata <https://www.dublincore.org/specifications/dublin-core/dces/>`__.
We can however extend it for any specific downloader. For instance, some
documents in the ACL Anthology provide a "code" field, with a link to e.g. a
GitHub repository. We will try to extract code repository URL using
:mod:`bs4`. An instance of :mod:`bs4` with the parsed HTML can be obtained and
manipulated as follows:

.. code:: python

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        paper_details = soup.find("div", "row acl-paper-details").find("dl")
        for dt in elem.find_all("dt"):
            if "Code" in dt.text:
                data["code"] = dt.find_next_sibling().find("a").attrs["href"]
                break

        return data

Metadata can also be obtained from BibTeX by overriding the
:meth:`~papis.downloaders.Downloader.get_bibtex_url` method. This can be useful
if, for instance, the ``get_data`` method fails to correctly identify the abstract
section. In our example we can fix this by scraping the metadata found in the
BibTeX file. Luckily, for ACL, the BibTeX URL is simply the document URL with a
``.bib`` extension. We can implement it as:

.. code:: python

    def get_bibtex_url(self) -> Optional[str]:
        url = self.ctx.data.get("url")
        return f"{url}.bib" if url is not None else url

To download files from a remote resource, the downloader relies on
``data["pdf_url"]`` by default. However, if this does not exist or does not
return the actual document PDF, we can override the
:meth:`~papis.downloaders.Downloader.get_document_url` method:

.. code:: python

    def get_document_url(self) -> Optional[str]:
        if "pdf_url" in self.ctx.data:
            return str(self.ctx.data["pdf_url"])

        return None

Finally, to install the plugin and have it recognized by the extension system
that Papis uses, it needs to be added to ``pyproject.toml``. This can be done with
extending the ``papis.downloader`` entrypoint as follows:

.. code:: toml

    [project.entry-points."papis.downloader"]
    acl = "papis.downloaders.acl:Downloader"

Explore
-------
TO DOCUMENT

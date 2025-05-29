from importlib import metadata

m = metadata.metadata("papis")

__license__ = m["License"]
__version__ = m["Version"]

# NOTE: this is formatted like `John Smith <johnsmith@example.com>`
__author__ = m["Author-email"].split("<")[0].strip()
__maintainer__ = m["Maintainer-email"].split("<")[0].strip()
__email__ = m["Author-email"].split("<")[-1][:-1].strip()

#: A User-Agent string for the Papis application itself. This is mainly used to
#: identify Papis when making requests to third-party services (e.g. Crossref).
#: If simply downloading web pages, PDF files, etc. for a document, the
#: value provided by the :confval:`user-agent` setting should be used instead.
PAPIS_USER_AGENT = f"papis/{__version__}"

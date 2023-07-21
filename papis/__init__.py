from importlib import metadata

m = metadata.metadata("papis")

__license__ = m["License"]
__version__ = m["Version"]

# NOTE: this is formatted like `John Smith <johnsmith@example.com>`
__author__ = m["Author-email"].split("<")[0].strip()
__maintainer__ = m["Maintainer-email"].split("<")[0].strip()
__email__ = m["Author-email"].split("<")[-1][:-1].strip()

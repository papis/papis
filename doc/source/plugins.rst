Plugin architecture
===================

.. automodule:: papis.plugin

Exporter
--------
TO DOCUMENT

Command
-------
TO DOCUMENT

Importer
--------

The difference between a downloader and an importer in `papis` is largely
semantic. Downloaders are mostly meant to scrape websites or download files
from a remote location. They can be implemented in a similar way.

As a example we implement a custom downloader for the [ACL Anthology](https://aclanthology.org/).
First create a downloader module in `papis.downloaders` and write a class that inherits from `papis.downloaders.Downloader`:

```python
from typing import Any, Dict, Optional

import papis.document
import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    def __init__(self, url: str) -> None:
        super().__init__(
            url,
            name="acl",
            expected_document_extension="pdf",
            priority=10,
        )

```

We then implement the `Downloader.match` method, which generally checks if a given URI matches a website URL:

```python
@classmethod
def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
    return Downloader(url) if re.match(r".*aclanthology\.org.*", url) else None
```

The `Downloader` comes with a `get_data` method, which does already a good job
in fetching basic metadata such as title, authors, etc. We can however extend this to our liking.
For instance, some documents in the ACL Anthology
provide a "code" field, with a link to e.g. a github repository.
We will try to extract from the `soup` (the parsed html) the element containing the link to the code.

```python
def get_data(self) -> Dict[str, Any]:
    soup = self._get_soup()
    data = papis.downloaders.base.parse_meta_headers(soup)

    paper_details = soup.find("div", "row acl-paper-details").find("dl")  # type: ignore

    for dt in elem.find_all("dt"):
        if "Code" in dt.text:
            data["code"] = dt.find_next_sibling().find("a").attrs["href"]

    return data
```

Optionally you can extend it further by overriding the `Downloader.get_bibtex_url`.
For instance, the `get_data` method fails to correctly identify the abstract section.
In our example we can fix this by scraping the metadata found in the bibtex file.
Luckily the bibtex url is simply the document url with a .bib extension.

```python
def get_bibtex_url(self) -> Optional[str]:
    url = self.ctx.data.get("url")
    if url is not None:
        url = url + ".bib"
    return url
```

If you are not happy with the result the `data['pdf_url]`,
which contain the file that papis will try to download,
you can override the `Downloader.get_document_url`.

```python
def get_document_url(self) -> Optional[str]:
    if "pdf_url" in self.ctx.data:
        url = str(self.ctx.data["pdf_url"])
        self.logger.debug("Using document URL: '%s'.", url)
        return url

    return None
```

Finally, you need to edit the `setup.py` file to let papis know
there's a new downloader available:

```python
 'papis.downloader': [ 
     "acl=papis.downloaders.acl:Downloader", 
```

Explore
-------
TO DOCUMENT

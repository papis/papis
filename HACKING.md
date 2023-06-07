# Guidelines for Code Modification

## Coding Style

- Use syntax compatible with Python `3.8+`.
- Use docstrings with [Sphinx](https://www.sphinx-doc.org/en/master/) in mind.
- Follow the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/)
- Try and run tests locally before submitting a new PR.

## Development

For development, consider creating a new virtual environment (with any
prefered method, e.g. [venv](https://docs.python.org/3/library/venv.html)).
All development packages can be installed with

```bash
python -m pip install -e '.[develop]'
```

To run the tests, just use `pytest`. Some helpful wrappers are given in the
`Makefile` (see `make help`), e.g. to run the tests

```bash
make test
```

which runs the full test suite and doctests for `papis`. To run the tests exactly
as they are set up on the Github Actions CI use

```
make ci-install
make ci-test
```

The docs can be generated with

```
make doc
```

## Issues

You can open issues in the [GitHub issue tracker](https://github.com/papis/papis/issues).

## Version Numbering

The versioning scheme generally follows semantic versioning. That is, we
have three numbers, `A.B.C`, where:

- `A` changes on a rewrite
- `B` changes when major configuration incompatibilities occur
- `C` changes with each release (bug fixes..)

# Extending Papis

## Adding Configuration Options

To add a new main option:

- Add a default value in `defaults.py` in the `settings` dictionary.
- Document the option in `doc/source/default-settings.rst`. Try to answer the
  following questions:
  - What is it?
  - Where is it used?
  - What type should it be?
  - What values are allowed? (default values are added automatically)

The setting is now accessible with `papis.config.get("myoption")`
or through the command-line interface `papis config myoption`.

To add a new option in a custom section (or generally with a common prefix)

- Call `papis.config.register_default_settings` with a dictionary
  `{"section": {"option1": "value", ...}}`.
- Document the option in a similar fashion to above

The setting can now be accessed with `papis.config.get("section-option1")`
or `papis.config.get("option1", section="section")`.

## Adding Scripts

Can add scripts for everyone to share to the folder `examples/scripts` in the
repository. These scripts will not be shipped with papis, but they are there
for other users to use and modify.

## Adding Importers

An importer is used to get data from a file or service into `papis`. For example,
see the arXiv importers in `arxiv.py`. To add a new importer

- Create a class that inherits from `papis.importer.Importer`.
- Implement the `Importer.match` method, which is used to check if a given URI
  can be handled by the importer.
- Implement the `Importer.fetch` method, that gets the data. This method should
  set the `Importer.ctx` attribute to contain the extracted information.
- (Optional) Instead of the `fetch` method, you can also implement the `fetch_data`
  and / or `fetch_files` methods separately.

The importer is then registered with `papis` by adding it to `setup.py`. In the
`entry_points` argument under `"papis.importer"` add

```
myimporter=papis.myservice:Importer
```

or see the existing examples.

## Adding Downloaders

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

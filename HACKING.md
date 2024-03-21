Guidelines for Code Modification
================================

Coding Style
------------

* Use syntax compatible with Python `3.8+`.
* Use docstrings with [Sphinx](https://www.sphinx-doc.org/en/master/) in mind.
* Follow the [PEP8 style guide](https://www.python.org/dev/peps/pep-0008/)
* Try and run tests locally before submitting a new PR.

Issues
------

You can open issues in the [GitHub issue tracker](https://github.com/papis/papis/issues).

Development
-----------

For development, consider creating a new virtual environment (with any
preferred method, e.g. [venv](https://docs.python.org/3/library/venv.html)).
All development packages can be installed with
```bash
python -m pip install -e '.[develop,docs]'
```

To run the tests, just use `pytest`. Some helpful wrappers are given in the
`Makefile` (see `make help`), e.g. to run the tests
```bash
make pytest
```
which runs the full test suite and doctests for `papis`. To run the tests exactly
as they are set up on the Github Actions CI use
```bash
make ci-install
make ci-test
```

The docs can be generated with
```bash
make doc
```

### Containers

To quickly get things up and running, you can also use Docker:
```bash
# build the image
docker build -t papisdev .
# to run the CI tests
docker run -v $(pwd):/papis --rm -it papisdev
# enter the container interactively
docker run -v $(pwd):/papis --rm -it papisdev bash
```

(or replace `docker` with `podman` if you prefer)

### Nix

If you're using Nix, you can also use the included `flake.nix` and get a
development shell up with `nix develop`.

This also gives you access to the following convenience commands to interact
with the containers (they require either Docker or Podman to run):

* `papis-build-container`: build the container.
* `papis-run-container-tests`: run the CI tests in the container.
* `papis-run-container-interactive`: enter the container interactively and
  populate the library with some test documents.

Guidelines for Testing
======================

To add tests to the various parts of Papis, use the functionality in
`papis.testing`. This is documented in the
[Testing](https://papis.readthedocs.io/en/latest/testing.html) section of the
docs and more complex examples can be found in the existing `tests` folder.

When adding functionality or fixing a bug with an accompanying test, make
sure everything still works correctly by running
```
make ci-test
make ci-lint
```

Guidelines for Extending Papis
==============================

Adding Configuration Options
----------------------------

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

Adding Scripts
--------------

Can add scripts for everyone to share to the folder `examples/scripts` in the
repository. These scripts will not be shipped with Papis, but they are there
for other users to use and modify.

Adding Importers
----------------

An importer is used to get data from a file or service into `papis`. For example,
see the arXiv importers in `arxiv.py`. To add a new importer

- Create a class that inherits from `papis.importer.Importer`.
- Implement the `Importer.match` method, which is used to check if a given URI
  can be handled by the importer.
- Implement the `Importer.fetch` method, that gets the data. This method should
  set the `Importer.ctx` attribute to contain the extracted information.
- (Optional) Instead of the `fetch` method, you can also implement the `fetch_data`
  and / or `fetch_files` methods separately.

The importer is then registered with `papis` by adding it to `pyproject.toml`.
In the `project.entry_points."papis.importer"` section add
```
myimporter = "papis.myservice:Importer"
```
or see the existing examples.

Adding Downloaders
------------------

The difference between a downloader and an importer in `papis` is largely
semantic. Downloaders are mostly meant to scrape websites or download files
from a remote location. They can be implemented in a very similar way:

- Create a class that inherits from `papis.downloaders.Downloader`.
- Implement the `Downloader.match` method, which generally checks if a given
  URI matches a website URL.
- (Optional) Implement the `Downloader.get_data` method, which returns a dictionary.
- (Optional) Implement the `Downloader.get_bibtex_url` method to return an URL
  from which a BibTeX file can be downloaded. This is then parsed and merged
  automatically.
- (Optional) Implement the `Downloader.get_document_url` method to return an
  URL from which a document (e.g. PDF file) can be downloaded.

The downloader can then be added to the `project.entry-points."papis.downloader"`
section, similarly to an importer.


Guidelines for Documentation
============================

You'll find the source code of the Papis documentation under the `doc/src`
directory. The documentation uses the Sphinx documentation stack to build the
manual and HTML pages and, to format the text, the [Sphinx reStrucTured
markup](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).
You'll notice that, under the `doc/source/commands` folder, most files are
pretty sparse. The reason is that Sphinx populates the documentation
automatically gathering information from the docstrings and the
[Click](https://click.palletsprojects.com/) configuration of each command.


To document existing or new features
------------------------------------

- Concise API documentation for a command or module as well as their usage
examples should be generally placed in each module's source file. Visit the
`papis/commands/add.py` or `papis/yaml.py` for examples of such use.

- Longer-form texts, such as guides, tutorials or workflows can go to an
appropriate file under `doc/source/`, and you can also use the
`examples/scripts` directory to distribute scripts that you think will be
helpful for other users.


Deciding whether to write `papis` or Papis
------------------------------------------

These tips can help you figure out which form, `papis` or Papis should be used.

- When referring to the command-line interface, use `papis`, in lowercase and
with code markup: 
  - Incorrect:
      > The **papis** commands are `add`, `edit`, `update`...
  - Correct:
      > The **`papis`** commands are `add`, `edit`, `update`.

- When referring to the workflow or project, use uppercase P:
  - Incorrect:
      > The YAML files contain the metadata that **papis** uses for search
      > The documentation for **papis** is built with Sphinx
  - Correct:
      > The YAML files contain the metadata that **Papis** uses for search
      > The documentation for **Papis** is built using Python

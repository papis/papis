.. raw:: html

   <div align="center">

   <img src="resources/logo.svg" width=300>

   <h1>Papis</h1>

   <a href="https://github.com/papis/papis/actions?query=branch%3Amain+workflow%3ACI">
       <img src="https://github.com/papis/papis/workflows/CI/badge.svg" alt="GitHub Badge"></a>
   <a href="https://papis.readthedocs.io/en/latest/?badge=latest">
       <img src="https://readthedocs.org/projects/papis/badge/?version=latest" alt="Readthedocs"></a>
   <a href="https://github.com/papis/papis/actions?query=branch%3Amain+workflow%3ACodeQL">
       <img src="https://github.com/papis/papis/workflows/CodeQL/badge.svg" alt="CodeQL"></a>
   <a href="https://pypi.org/project/papis/">
       <img src="https://badge.fury.io/py/papis.svg" alt="PyPI"></a>
   <a href="https://zenodo.org/badge/latestdoi/82691622">
       <img src="https://zenodo.org/badge/82691622.svg" alt="Zenodo"></a>

   <br><br>

   Papis is a powerful and highly extensible CLI document and bibliography manager.

   <br><br>

   </div>

|first_glance|

With Papis, you can search your library for books and papers, add documents and
notes, import and export to and from other formats, and much much more. Papis
uses a human-readable and easily hackable ``.yaml`` file to store each entry's
bibliographical data. It strives to be easy to use while providing a wide range
of features. And for those who still want more, Papis makes it easy to write
scripts that extend its features even further.

Features
--------

- **Add documents** and automatically fetch their metadata.
- **Search** by author, title, tags, and so on.
- **Synchronize** your library with whatever software you're already using.
- **Share** your documents with colleagues without having to force some proprietary
  service onto them.
- **Import** your data from other bibliography managers.
- **Export** to BibTeX and other formats.
- **Integrate with your editor** with plugins for (Neo)vim and Emacs.
- **TUIs** make it easy to get a quick overview of your library.
- **Use the web app** when the CLI doesn't quite cut it (for example on your tablet).
- **Hacking** Papis is easy! Use the API to easily create your own custom python scripts.

Quick tour
----------

Install Papis with pip (or `one of the alternatives <https://papis.readthedocs.io/en/latest/install.html>`__):

.. code:: bash

    pip install papis

Let's download a couple of documents:

.. code:: bash

    wget https://www.gnu.org/s/libc/manual/pdf/libc.pdf
    wget https://www.ams.org/notices/201304/rnoti-p434.pdf

We can now add these to the (default) library. This will automatically query for
the metadata associated with the ``doi``.

.. code:: bash

    papis add --from doi 10.1090/noti963 rnoti-p434.pdf

|add|

You can also use ``--set`` to add information:

.. code:: bash

    papis add libc.pdf --set author "Sandra Loosemore" \
                       --set title "GNU C reference manual" \
                       --set year 2018 \
                       --set tags programming \
                       --confirm

Now open an attached file or edit an entry:

.. code:: bash

    papis open
    papis edit


|edit|

The Papis picker (set using the ``picktool`` configuration option) has
helpful shortcuts to call other functionality as well (press ``F1`` for 
a complete list). It can be used to open (``Ctrl-o``), browse (``Ctrl-b``)
or edit (``Ctrl-e``) selected documents (marked with ``Ctrl-t``).

Import your bibliography into Papis from BibTeX:

.. code:: bash

    papis bibtex read mylib.bib import --all

Or export it to BibTeX:

.. code:: bash

    papis export --all --format bibtex > mylib.bib

|bibtex_export|

Papis also includes a web app that you can start with:

.. code:: bash

    papis serve

You can then open the indicated address (``http://localhost:8888``) in your
browser.

|web_app|

All ``papis`` commands come with help messages:

.. code:: bash

    papis -h      # General help
    papis add -h  # Help with a specific command

Installation & setup
--------------------

Information about installation and setup can be found in the
`docs <https://papis.readthedocs.io/en/latest/>`__, for example in the these sections:

- `Installation <https://papis.readthedocs.io/en/latest/install.html>`__
- `Configuration <https://papis.readthedocs.io/en/latest/configuration.html>`__
- `Import <https://papis.readthedocs.io/en/latest/importing.html>`__
- `Editor integration <https://papis.readthedocs.io/en/latest/editors.html>`__

Questions?
----------

The `docs <https://papis.readthedocs.io/en/latest/>`__ cover Papis' features and
discuss possible work flows. If you still have questions, head to our
`GitHub discussions <https://github.com/papis/papis/discussions>`__ — we're
more than happy to help. If you've found a bug, please
`open an issue <https://github.com/papis/papis/issues>`__ and help make Papis
even better!

If you're not finding a command or configuration value that shows up in the
documentation in your local installation, you may just be looking at the wrong
docs. You can find the documentation for the latest *released* version
`here <https://papis.readthedocs.io/en/stable/>`__ and the documentation for
the *in-development* version `here <https://papis.readthedocs.io/en/latest/>`__.

Reviews and blog posts
----------------------

- `Blog post <https://alejandrogallo.github.io/blog/posts/getting-paper-references-with-papis/>`__
  about getting a paper's references with ``papis explore``.
- `Blog post <https://nicolasshu.com/zotero_and_papis.html>`__ about using Papis
  with Zotero and Syncthing.
- GNU/Linux Switzerland `wrote about Papis <https://gnulinux.ch/papis-dokumentenverwaltung-fuer-die-kommandozeile>`__
  *(in German)*.
- The folks at OSTechNix wrote a review of `Papis
  <https://www.ostechnix.com/papis-command-line-based-document-bibliography-manager/>`__.
- A `review of Papis <https://ubunlog.com/papis-administrador-documentos/>`__
  by Ubunlog *(in Spanish)*.

Contributing
------------

Contributions are very welcome! Take a look at
`CONTRIBUTING.md <https://github.com/papis/papis/blob/main/CONTRIBUTING.md>`__ for
general rules and `HACKING.md <https://github.com/papis/papis/blob/main/HACKING.md>`__
for additional code-related information. We encourage you to also check out,
contribute to, or even help maintain the other projects in the Papis ecosystem
mentioned below :wink:.

The Papis ecosystem
-------------------

Papis has grown over the years and there are now a number of projects that
extend Papis' features or integrate it with other software.

.. list-table::
   :widths: 33 67
   :header-rows: 1

   * - Project
     - Maintained by

   * - `papis (core) <https://github.com/papis/papis-rofi/>`__
     - `Alejandro Gallo <https://alejandrogallo.github.io/>`__, `Julian Hauser <https://github.com/jghauser>`__, `Alex Fikl <https://github.com/alexfikl>`__

   * - `papis-rofi <https://github.com/papis/papis-rofi/>`__
     - `Etn40ff <https://github.com/Etn40ff>`__

   * - `papis-dmenu <https://github.com/papis/papis-dmenu>`__
     - you?

   * - `papis-vim <https://github.com/papis/papis-vim>`__
     - you?

   * - `papis.nvim <https://github.com/jghauser/papis.nvim>`__
     - `Julian Hauser <https://github.com/jghauser>`__

   * - `papis-emacs <https://github.com/papis/papis.el>`__
     - `Alejandro Gallo <https://alejandrogallo.github.io/>`__

   * - `papis-zotero <https://github.com/papis/papis-zotero>`__
     - `Alex Fikl <https://github.com/alexfikl>`__

   * - `papis-libgen <https://github.com/papis/papis-zotero>`__
     - you?

   * - `papis-firefox <https://github.com/papis/papis-firefox>`__
     - `wavefrontshaping <https://github.com/wavefrontshaping>`__
   * - `papis-qa <https://github.com/isaksamsten/papisqa>`__ (AI for Papis)
     - `Isak Samsten <https://github.com/isaksamsten>`__

Related software
----------------

Papis isn't the only fish in the pond. You might also be interested in:

- `bibman <https://codeberg.org/KMIJPH/bibman>`__ (open source)
- `cobib <https://github.com/mrossinek/cobib>`__ (open source)
- `jabref <https://www.jabref.org/>`__ (open source)
- `Mendeley <https://www.mendeley.com/>`__ (proprietary)
- `pubs <https://github.com/pubs/pubs/>`__ (open source)
- `Xapers <https://finestructure.net/xapers/>`__ (open source)
- `Zotero <https://www.zotero.org/>`__ (open source)


Thanks
------

We thank `Irteza Rehman <https://www.irtezarehman.com/>`__ for generously creating
our beautiful logo.

.. |first_glance| image:: https://papis.github.io/images/first_glance.gif
.. |edit| image:: https://papis.github.io/images/edit.gif
.. |bibtex_export| image:: https://papis.github.io/images/bibtex_export.gif
.. |add| image:: https://papis.github.io/images/add.gif
.. |web_app| image:: https://papis.github.io/images/web_app.jpg

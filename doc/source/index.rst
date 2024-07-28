Papis: Command-line Bibliography Manager
========================================

.. note::

   `This <https://papis.readthedocs.io/en/latest>`__ is the documentation for
   the current **in development** version of Papis. For the documentation of
   the lastest **released** version see
   `here <https://papis.readthedocs.io/en/stable>`__.

.. grid:: 3

    .. grid-item-card:: :material-regular:`install_desktop;2em` Installation
      :columns: 12 6 6 4
      :link: installation
      :link-type: ref
      :class-card: getting-started

    .. grid-item-card:: :material-regular:`rocket_launch;2em` Quick Guide
      :columns: 12 6 6 4
      :link: quick-guide
      :link-type: ref
      :class-card: getting-started

    .. grid-item-card:: :material-regular:`library_books;2em` Configuration
      :columns: 12 6 6 4
      :link: configuration-file
      :link-type: ref
      :class-card: getting-started

.. grid:: 3

    .. grid-item-card:: :material-regular:`terminal;2em` Commands
      :columns: 12 6 6 4
      :link: commands-add
      :link-type: ref
      :class-card: getting-started

    .. grid-item-card:: :material-regular:`api;2em` API
      :columns: 12 6 6 4
      :link: api
      :link-type: ref
      :class-card: getting-started

    .. grid-item-card:: :material-regular:`laptop_chromebook;2em` Developer Docs
      :columns: 12 6 6 4
      :link: developer-api-reference
      :link-type: ref
      :class-card: getting-started

Papis is a command-line based document and bibliography manager. Its
command-line interface (*CLI*) is heavily tailored after
`Git <https://git-scm.com>`__.

With Papis, you can search your library for books and papers, add documents and
notes, import and export to and from other formats, and much much more. Papis
uses a human-readable and easily hackable ``.yaml`` file to store each entry's
bibliographical data. It strives to be easy to use while providing a wide range
of features. And for those who still want more, Papis makes it easy to write
scripts that extend its features even further.

Papis has grown over the years and there are now a number of projects that
extend Papis' features or integrate it with other software.

.. list-table::
   :widths: 33 67
   :header-rows: 1
   :align: center

   * - **Project**
     - **Maintained by**

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

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Getting started

   install
   quick_guide
   configuration
   info_file
   library_structure

.. toctree::
   :hidden:
   :glob:
   :maxdepth: 2
   :caption: Commands

   commands/*

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: User guides

   database_structure
   papis_id
   bibtex
   citations
   web-application
   gui
   editors
   scripting
   git
   scihub
   importing
   shell_completion
   faq

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Developer documentation

   api
   plugins
   hooks
   testing
   developer_reference

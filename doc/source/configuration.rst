.. _configuration-file:

Configuration file
==================

Papis uses a configuration file in `INI <https://en.wikipedia.org/wiki/INI_file>`__
format. This configuration file will usually be located in
``~/.config/papis/config`` (on Linux) or similar locations on other platforms.

In the Papis configuration file, the main entries will be sections describing
what libraries you have. For example, assume you have two libraries: a library
called ``papers`` and another called ``books``. In general, these libraries
work and can be configured independently from each other.

In the simplest case, you would simply need to declare their location in your
system, like so:

.. code:: ini

    [settings]
    default-library = papers

    # my library for papers and stuff
    [papers]
    dir = ~/Documents/papers

    # my library for books and related documents
    [books]
    dir = ~/Documents/books

The ``[settings]`` section is used to set global configuration options.
However, an important aspect of the configuration system is that you can override
settings on a per library basis. This means that you can set options with different
values for each of your libraries.

For example, let's suppose you want to open your documents from ``papers`` using
the PDF reader ``okular``. In ``books``, however, you want to open the documents
in ``firefox``. In this case, you would add the following lines to your
configuration:

.. code:: ini

    [settings]
    opentool = evince
    default-library = papers

    # my library for papers and stuff
    [papers]
    dir = ~/Documents/papers
    opentool = okular

    # my library for books and related documents
    [books]
    dir = ~/Documents/books
    opentool = firefox

Here we also added the ``opentool`` setting in the global section ``[settings]``.
With this configuration file, the two shown libraries will open documents with
their respective tool, while any other library will default to ``evince``. There
are many configuration options and you can check their values using the
:ref:`papis config <command-config>` command, e.g.:

.. code:: sh

    # show all the current options in the [settings] section
    papis config --section settings
    # show the default options
    papis config --default --section settings
    # show the value of the 'opentool' option for the books library
    papis -l books config opentool

A more complete example of a configuration file is the following
(see :ref:`General Settings <general-settings>` for a comprehensive list of
all the options and more extensive descriptions):

.. warning::

   Many configuration options use special format patterns that can depend on
   the document that is being worked on. When using these, make sure to also
   set the :confval:`formatter` to your desired choice. Below, we
   are using the default ``python`` formatter that is based on :meth:`str.format`.

.. code:: ini

    #
    # This is a general section, the settings set here will be global for
    # all libraries
    #
    [settings]
    # General file opener program ("rifle" is a nice general opener). This
    # setting should be platform dependent, so on macOS you can use "open",
    # on Linux you can use "xdg-open", on Windows you can set it to "cygstart"
    # (under Cygwin at least), etc.
    opentool = rifle
    # Use "ranger" as a file browser
    file-browser = ranger

    # Ask for confirmation when doing "papis add" before adding to the library.
    # Equivalent to "papis add --confirm".
    add-confirm = True
    # Edit the "info.yaml" file before adding a document to the library.
    # Equivalent to "papis add --edit".
    add-edit = True
    # Open any document files before adding the document to the library.
    # Equivalent to "papis add --open".
    add-open = True

    # Define custom default match formats. This format is used when searching
    # documents in the default picker.
    match-format = {doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}
    # Define header format with colors and multiline support. This formatting
    # will be used when displaying a document in the default picker.
    header-format = <red>{doc.html_escape[title]}</red>
      <span color='#ff00ff'>  {doc.html_escape[author]}</span>
      <yellow>   ({doc.html_escape[year]})</yellow>

    # Set options for the default picker and other CLI widgets.
    [tui]
    editmode = vi
    options_list.selected_margin_style = bg:ansigreen fg:ansired
    options_list.unselected_margin_style =

    # Define a library for papers
    [papers]
    dir = ~/Documents/papers

    # Override settings from the "tui" section only for the "papers" library.
    # When using settings from another settings, the section name needs to be
    # prepended -- here we prepend "tui-" to the settings.
    tui-editmode = emacs
    tui-options_list.unselected_margin_style = bg:blue

    # Use whoosh as a database for "papers".
    database-backend = whoosh
    # Rename files added by author and title in "papis add"
    add-file-name = {doc[author]}{doc[title]}

    # Define a library for books.
    [books]
    dir = ~/Documents/books
    database-backend = whoosh

    # Define a library for videos.
    [videos]
    dir = ~/Videos/courses

    # Define a lib for contacts (why not?). To make it work you just have to
    # define some sane settings.
    [contacts]
    dir = ~/contacts/general
    database-backend = papis

    match-format = {doc[org]} {doc[first_name]} {doc[last_name]}
    header-format = {doc[first_name]} {doc[last_name]}

    browse-query-format = {doc[first_name]} {doc[last_name]}
    add-open = False

.. note::

   Papis uses the standard :class:`~configparser.ConfigParser` to read and write
   configuration options. It also allows interpolation of values
   (using :class:`~configparser.BasicInterpolation`) so that previous values
   can be referred back to. For example, one can do:

   .. code:: ini

        [DEFAULT]
        basedir = /path/to/libraries

        [papers]
        dir = %(basedir)s/papers

        [books]
        dir = %(basedir)s/books

   Interpolation variables are looked for in the current section and in the
   standard ``DEFAULT`` section.

Local configuration files
-------------------------

Papis also offers the possibility of creating local configuration files.
The name of the local configuration file can be configured with the
:confval:`local-config-file` setting. The local configuration files
are looked for in the current directory (where the ``papis`` command is issued) or
in the directory of the current library.

For instance, suppose that you are in some project folder ``~/Documents/myproject``
and you have a local config file there with a definition of a new library ``project``.
Then, whenever you are in the ``~/Documents/myproject`` directory, Papis will also
read the local configuration file and you will have access to the additional
library ``project``.

On the other hand, if you have a configuration file in the folder
for your papers, for instance in::

    ~/Documents/papers/.papis.config

Then, every time that you use this library Papis will also source this
configuration file. This can be used as an alternative to adding more configuration
options in the main configuration file or if you expect this library to be
used on more machines with different configurations.

An example of a project using a local configuration file can be seen
`here <https://github.com/alejandrogallo/datasheets/blob/master/.papis.config>`__.
The repository includes documents for component datasheets and every time
``papis`` is using that library the ``.papis.config`` file is also read and
some settings will get overridden.

.. _config_py:

Python configuration file
-------------------------

For some more dynamic use cases, it would be useful to have a Python file that
gets loaded together with the usual configuration file. This file lives in your
Papis configuration directory and has the name ``config.py``. For instance,
for most users it will be in::

    ~/.config/papis/config.py


.. include:: default_settings.rst

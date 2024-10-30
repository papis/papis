.. _general-settings:

General settings
----------------

.. papis-config:: local-config-file

    Relative path of the local configuration file that Papis will additionally
    read. The file must be present in the current directory or in the base
    directory of a given library.

    This can be used to set special configuration settings for a library that
    do not clutter your global configuration file. This is particularly useful
    if the library is shared with someone else (or just on a different machine)
    and you want them to have the same settings. For example, say you're sharing
    a library with your friend Fulano. You have your library at::

        ~/Documents/lib-with-fulano

    and you've created a local configuration file at::

        ~/Documents/lib-with-fulano/.papis.config

    Then, you can share your library (through e.g. Dropbox or a network drive)
    and have the same settings for the library across machines, e.g. to generate
    consistent references with :confval:`ref-format`. In this setup,
    whenever Fulano uses that library, their Papis calls will also read the
    configuration settings and use the same settings.

.. papis-config:: dir-umask

    This is the default :func:`os.umask` that will be used to create the new
    directories for documents and libraries.

.. papis-config:: use-git

    Some commands will issue `git <https://git-scm.com/>`__ commands if this
    option is set to *True*. For example ``papis mv`` or ``papis rename`` can
    automatically commit any changes to a document by default. See
    :ref:`Git support <git-support>` for additional details.

.. papis-config:: user-agent

    `User agent <https://en.wikipedia.org/wiki/User_agent>`__ used by Papis
    whenever querying information from external sources.

.. papis-config:: scripts-short-help-regex

    This is the format of the short help indicator in external Papis
    commands. In general, for an external command, the first lines are expected
    to resemble

    .. code:: python

        #!/usr/bin/env python3
        # papis-short-help: My awesome script fixes everything

.. papis-config:: info-name

    The default name for files containing the document metadata. In Papis, these
    are referred to as *info files* (see :ref:`info-file`) and contain metadata
    in the YAML format.

.. papis-config:: doc-url-key-name

    Some documents might have multiple URLs associated with them, e.g. remote
    URLs from different sources or a file URL. This setting can be used to
    choose which one is more appropriate to use in different settings, e.g.
    the Crossref importer uses it to download files.

.. papis-config:: default-library

    The name of the library that is to be used when Papis is run without the
    ``-l``/``--lib`` argument. Papis will not immediately check if this library
    exists in the configuration file or that it is correctly configured.

.. papis-config:: format-doc-name

    This setting controls the name of the document in the Papis format strings
    like in format strings such as :confval:`match-format` or
    :confval:`header-format`. For instance, if you are managing
    videos, you might want to set this option to ``vid`` in order to set  the
    :confval:`header-format` to

    .. code:: ini

        header-format = {vid[title]} - {vid[director]} - {vid[duration]}.

.. papis-config:: match-format

    Default format that is used to match a document in the default Papis picker
    and in the ``papis`` database backend. For example, if the ``match-format``
    is set to ``{doc[year]} {doc[author]}``, then words from the title will not
    match the document, only using the year or the author will work. It is
    recommended to set this to all the keys used by :confval:`header-format`,
    so that any visible information can be matched.

.. papis-config:: header-format

    Default format that is used to show a document in the default Papis picker.
    This can be a complex multiline string containing any key from a document.

.. papis-config:: header-format-file
    :type: str

    If the :confval:`header-format` grows too complex, it can be
    stored in a separate file. This option should give the path to that file (in
    which case the ``header-format`` option will be ignored). For example, this
    can be set to

    .. code:: ini

        header-format-file = ~/.config/papis/styles/header-format.txt

.. papis-config:: info-allow-unicode

    If *True*, this flag will allow unicode characters in your *info files*.
    Otherwise, the strings will be decoded and written as bytes. Unless you have
    very strong reasons not to, this should always be set to *True* (we live
    a unicode world after all!).

.. papis-config:: unique-document-keys

    Whenever you add a new document, Papis tries to figure out if
    you have already added this document before. This is partially done
    checking for matches in some special keys. This setting controls which keys
    are checked.

    For instance, if you add a paper with a given ``doi``, and then you
    add another document with the same ``doi``, then Papis will notify
    you that there is already another document with this ``doi`` because
    the ``doi`` key is part of the ``unique-document-keys`` option.

.. papis-config:: document-description-format

    Papis sometimes will have to tell you which document it is processing. This
    format string can be used to display the document to the user in a
    non-intrusive way. Preferable, this should be a short string that allows
    easily identifying which document is being referenced.

.. papis-config:: sort-field
    :type: str

    This setting controls which field queries are sorted by before being presented
    to the user in, e.g., the picker. Most commands support a ``--sort`` option
    that uses this setting as its default value.

.. papis-config:: sort-reverse

    A setting that augments :confval:`sort-field` by allowing the
    documents to be sorted in reverse order. Most commands support a ``--reverse``
    flag that uses this setting as a default value.

.. papis-config:: formatter

    Picks the formatter for templated strings in the configuration file and
    in various strings presented to the user. Supported formatters are

    * ``"python"``: based on :class:`papis.format.PythonFormatter`.
    * ``"jinja2"``: based on :class:`papis.format.Jinja2Formatter`.

    Note that the default values of many of the Papis configuration settings are
    based on the Python formatter. These will need to all be specified explicitly
    if another formatter is chosen.

    **Note** The older (misspelled) version ``"formater"`` is deprecated.

.. papis-config:: doc-paths-lowercase
    :type: bool

    This setting controls whether capital letters in a (generated or specified)
    document path should be lowercased before the path is created.

.. papis-config:: doc-paths-extra-chars
    :type: str

    By default document paths in Papis libraries can contain only a limited set
    of characters. This is mainly to exclude characters that are invalid for
    file paths on any operating system or possibly unprintable. Allowed
    characters are:

    * latin letters (a to z)
    * arabic digits (0 to 9)
    * dots (for file extensions)
    * directory separators (usually ``/`` on UNIX-like systems and ``\\``
      on Windows)

    This setting allows to append additional characters to this set. It expects
    a string containing all additional valid characters. A possible value would
    be ``"_"`` to allow underscores in document paths.

.. papis-config:: doc-paths-word-separator
    :type: str

    This setting defines the separator between words in document paths (usually
    replacing spaces or other non-letter characters). By default this is the
    hyphen ``"-"`` but it could, e.g., also be the underscore ``"_"``.

.. papis-config:: ref-word-separator
    :type: str

    This setting defines the separator between words in ref keys (usually
    replacing spaces or other non-letter characters). By default this is the
    underscore ``"_"`` but it could, e.g., also be the hyphen ``"-"``.

    The ref is used as the bibtex key when creating bibtex format bibliographies.
    Therefore, characters ``" # ' ( ) , = { } %`` are not recommended for use as
    separators because neither ``bibtex`` nor ``biber`` can process them.

.. papis-config:: library-header-format

    The format of a library when shown in a picker, e.g. when using
   ``papis --pick-lib export --all``. The format takes a dictionary named
   ``library`` with the keys *name*, *dir*, and *paths*.

Tools options
-------------

.. papis-config:: opentool

    This is a general program that will be used to open document files. Papis
    is not intended to detect the type of file that is being opened or decide on
    how to open the document. Therefore, the ``opentool`` should handle this
    functionality. If you are on Linux, you might want to take a look at
    `ranger <https://ranger.github.io>`__ or just use ``xdg-open``. For macOS
    users, this should likely be set to ``open``.

.. papis-config:: browser
    :default: $BROWSER

    Program to be used for opening websites, the default is the environment
    variable ``$BROWSER``.

.. papis-config:: picktool

    This is the program used whenever Papis asks to pick a document for a
    query, pick a file to open, or any other such use case with multiple options.
    The following pickers are available:

    * ``"papis"``: uses ``papis.picker.Picker`` to display and search
      through documents.
    * ``"fzf"``: uses `fzf <https://github.com/junegunn/fzf>` to display and search
      through documents.

    Papis pickers use a plugin architecture similar to other components
    (see :ref:`plugin-architecture`) with the ``papis.picker`` entrypoint. Note
    that not all plugins will support all the same features.

.. papis-config:: editor
    :default: $EDITOR

    Editor used to edit files in Papis, e.g., for the ``papis edit``
    command. This will search for the ``$EDITOR`` environment variable or the
    ``$VISUAL`` environment variables to obtain a default if it is not set.
    Otherwise, the default :confval:`opentool` will be used.

.. papis-config:: file-browser

    File browser used when opening a directory. It defaults to the default file
    browser in your system. However, you can set it to different file browsers,
    such as ``dolphin``, ``thunar`` or ``ranger``, to name a few.

.. _bibtex-options:

BibTeX options
--------------

.. papis-config:: bibtex-journal-key

    This option allows the user to set the key for the journal entry when using
    ``papis export --bibtex``. The intended use of such a setting is to allow
    selecting e.g. abbreviated journal titles for publishers that require it.
    For example, if the document has a ``abbrev_journal_title`` key that should
    be used instead of the default ``journal`` key.

.. papis-config:: extra-bibtex-keys

    A list of additional keys, besides the known standard BibTeX keys from
    :data:`~papis.bibtex.bibtex_keys`, to add to the BibTeX export. This can be
    used to include keys such as ``doc_url`` or ``tags`` to the export by
    setting

    .. code:: ini

        [mylib]
        extra-bibtex-keys = ["doc_url", "tags"]

    These keys will likely not be recognized by the BibTeX engine, so they should
    be used with care. However, they can be useful when exporting documents as
    a form of backup to be imported in another library later.

.. papis-config:: bibtex-ignore-keys

    A list of keys that should be ignored when exporting to BibTeX. This might
    be useful if you have some keys that have a lot of content, such as
    ``abstract``, or maybe you have used a valid BibTeX key for some other
    purpose, like the ``note`` key.

.. papis-config:: extra-bibtex-types

    A list of additional types, besides the known standard BibTeX types from
    :data:`~papis.bibtex.bibtex_types`, that should be allowed for a BibTeX export.
    These types can be added as

    .. code:: ini

        [mylib]
        extra-bibtex-types = ["wikipedia", "video", "song"]

.. papis-config:: bibtex-unicode

    A flag used to choose whether or not to allow direct Unicode characters in
    the document fields to be exported into the BibTeX text. Some engines, such
    as `Biber <https://github.com/plk/biber>`__ support Unicode by default and
    should be used whenever possible.

.. papis-config:: bibtex-export-file

    A flag that can be used to add a ``"file"`` field to exported BibTeX entries.
    The files are added as a semicolon separated string.

    This entry used to be named ``bibtex-export-zotero-file`` and should be
    used instead.

.. papis-config:: multiple-authors-format

    A format string for concatenating author fields into a string that can be
    used for display purposes or for building the ``author`` key for the
    document. For example, when retrieving automatic author information from
    services like `Crossref <https://www.crossref.org>`__, Papis builds the
    ``author`` using this setting. For instance, this can be set to

    .. code:: ini

        multiple-authors-format = {au[family]} -- {au[given]}

    which for the author ``{"family": "Einstein", "given": "Albert"}`` would
    construct the string ``Einstein -- Albert``. In most circumstances, multiple
    authors are then concatenated together using
    :confval:`multiple-authors-separator`.

.. papis-config:: multiple-authors-separator

    A string used with :confval:`multiple-authors-format` to
    concatenate multiple authors, e.g. into the ``authors`` document key.
    By default, this is set to ``and``, which is the separator used by
    BibTeX in its so-called *name-lists*.

.. _bibtex-command-options:

BibTeX command options
^^^^^^^^^^^^^^^^^^^^^^

.. papis-config:: default-read-bibfile
    :section: bibtex

    A path to a BibTex file that should be automatically read when using the
    ``papis bibtex`` command. This should be equivalent to using
    ``papis bibtex read file.bib`` when used with :confval:`auto-read`.

.. papis-config:: default-save-bibfile
    :section: bibtex

    A path to a BibTex file that should be automatically saved when using the
    ``papis bibtex`` command. This should be equivalent to using
    ``papis bibtex save file.bib``.

.. papis-config:: auto-read
    :section: bibtex

    A flag used in conjunction with :confval:`default-read-bibfile` to
    automatically read a BibTeX file.

.. _add-command-options:

Add options
-----------

.. papis-config:: ref-format

    This option is used to set the ``ref`` key in the *info file* when a document
    is created. In BibLaTeX, the reference (or ref for short) is also sometimes
    called a citation key. The reference format is usually heavily customized
    by users, depending on their personal preferences. For example to use a
    ``FirstAuthorYear`` format, set

    .. code:: ini

        ref-format = {doc[author_list][0][family]}{doc[year]}

    However, any custom string can be used, e.g.

    .. code:: ini

        ref-format = {doc[title]:.15} {doc[author]:.6} {doc[year]}

    The resulting reference is also cleaned up by Papis to ensure that no invalid
    characters make it into final version. If a reference does not exist in the
    document, it is created using :func:`papis.bibtex.create_reference`. Any
    reference is then cleaned up using :func:`papis.bibtex.ref_cleanup`.

    .. warning::

        Note that the reference clean up can result in a heavily modified version
        compared to the string that was set by the ``ref-format`` option. For example,
        all spaces are transformed into underscores and all unicode characters are
        converted to their closest ASCII representation.

        If you want to add some punctuation, dots (``.``) and underscores (``_``)
        can be escaped by a backslash. For example,

        .. code:: ini

            ref-format = {doc[author_list][0][surname]}\.{doc[year]}

.. papis-config:: add-folder-name

    Set the default name for the folder of newly added documents. For example,
    if you want the folder of your documents to be named after the format
    ``author-title`` then you should set it to

    .. code:: ini

        add-folder-name = ``{doc[author]}-{doc[title]}``

    You can create formatted subfolders by using path separators
    (i.e., ``/``) in this format string, e.g.

    .. code:: ini

        add-folder-name = ``{doc[year]} / {doc[author]}-{doc[title]}``

    This setting should aim to result in unique (sub)folder names.
    If a (sub)folder name is not unique and the document does not appear to
    be a duplicate, a suffix ``-a``, ``-b``, etc. is added to the name.
    If this setting is ``None`` the template ``{doc[papis_id]}`` is used.

.. papis-config:: add-file-name
    :type: str

    Set the default file name for newly added documents, similarly to
    :confval:`add-folder-name`. If it is not set, the names of the
    files will be cleaned and taken *as-is*.

.. papis-config:: add-subfolder

    Configure a default for the ``--subfolder`` command-line option of ``papis add``.
    Note that, this setting is not allowed to contain formatting options. However,
    one can also specify nested sub-folders.

.. papis-config:: add-confirm

    A setting that controls the default for the ``--confirm`` flag of ``papis add``.
    If set to *True*, then the flag will be added by default and additional
    confirmation will be asked for when adding the document. In this case, the
    confirmation can be turned off using ``--no-confirm`` on an individual basis.

.. papis-config:: add-edit

    A setting that controls the default for the ``--edit`` flag of ``papis add``.
    If set to *True*, then the flag will be added by default and an editor will
    be opened before the document is saved for additional modifications. In this
    case, the edit can be disabled using ``--no-edit`` on an individual basis.

.. papis-config:: add-open

    A setting that controls the default for the ``--open`` flag of ``papis add``.
    If set to *True*, then the flag will be added by default and a viewer will
    be opened to allow checking every file added to the document. In this
    case, the open can be disabled using ``--no-open`` on an individual basis.

.. papis-config:: add-download-files

    A setting that controls the default for the ``--download-files`` flag of
    ``papis add``. If set to *True*, then the flag will be added by default and
    the selected importers and downloaders will attempt to also download files
    (metadata is always downloaded). In this case, the download can be disabled
    by using ``--no-download-files`` on an individual basis.

.. papis-config:: add-fetch-citations

    A setting that controls the default for the ``--fetch-citations flag of
    ``papis add``. If set to *True*, then the flag will be added by default
    and Papis will attempt to retrieve citations for the newly added document.
    In this case, the fetching can be disabled by using ``--no-fetch-citations``
    on an individual basis.

.. papis-config:: auto-doctor

   A setting that controls the default for the ``--auto-doctor`` flag of
   ``papis add`` and ``papis update``. If set to *True*, then the flag will be
   enabled by default and the doctor fixes will be applied to new documents.
   In this case, the automatic fixers can be disabled by using
   ``--no-auto-doctor`` on an individual basis.

.. papis-config:: time-stamp

    A setting that controls if a timestamp is added to a document on
    ``papis add``. The timestamp uses the standard ISO format and can be used
    for sorting and querying like any other fields.

Browse options
--------------

.. papis-config:: browse-key

    This setting provides the key that is used to generate a URL for the
    ``papis browse`` command. In the simplest case, ``browse-key`` is just a
    key in the document (e.g. ``url``) that contains a URL to open. It also
    supports the following special values:

    * ``"doi"``: construct a URL from the DOI as ``https://dx.doi.org/<DOI>``.
    * ``"isbn"``: construct a URL from the ISBN as ``https://isbnsearch/isbn/<ISBN>``.
    * ``"ads"``: construct a URL for the Astrophysics Data System as
      ``https://ui.adsabs.harvard.edu/abs/<DOI>``.
    * ``"auto"``: automatically pick between ``url``, ``doi`` and ``isbn``
      (first existing key is chosen).
    * ``"search-engine"``: the :confval:`search-engine` is used
      to search for the contents of :confval:`browse-query-format`.

    If the required keys are not found in the document (e.g. the DOI or the
    ISBN), the key will fallback to the ``"search-engine"`` case.

.. papis-config:: browse-query-format

    The query string that is to be searched for in the ``papis browse`` command
    whenever a search engine is used (see :confval:`browse-key`).

.. papis-config:: search-engine

    Search engine to be used by some commands like ``papis browse``. This should be
    a base URL that is then used to construct a search as ``<BASE>/?<PARAMS>``.

.. _edit-command-options:

Edit options
------------

.. papis-config:: notes-name

    In ``papis edit`` you can edit notes about the document. ``notes-name``
    is the default name of the notes file. The ``notes-name`` is formatted by the
    :confval:`formatter`, so that the filename of notes can be
    dynamically defined, e.g.:

    .. code:: ini

        notes-name = notes_{doc[ref]}.rst

.. papis-config:: notes-template

    When editing notes for the first time, a preliminary notes file will be
    generated based on a template. The path to this template is specified by
    ``notes-template``. The template will then be formatted by
    :confval:`formatter`. This can be useful to enforce the same
    style in the notes for all documents.

    Default value is set to the empty ``""``, which will return an empty notes
    file. If no file is found at the path to the template, then also an empty
    notes file will be generated.

.. _marks-options:

Doctor options
--------------

.. papis-config:: doctor-default-checks

    A list of checks that are performed by default.

.. papis-config:: doctor-default-checks-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of checks that extend the default ones from :confval:`doctor-default-checks`.
    This list extends instead of overwriting the given checks.

.. papis-config:: doctor-keys-missing-keys

    A list of keys used by the ``keys-missing`` check. The check will show an
    error if these keys are not present in a document.

.. papis-config:: doctor-keys-missing-keys-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of keys that extend the default ones from
    :confval:`doctor-keys-missing-keys`. This list extends instead of overwriting
    the given keys.

.. papis-config:: doctor-duplicated-keys-keys

    A list of keys used by the ``duplicated-keys`` check. The check will show
    an error if the value of these keys is duplicated across multiple documents.

.. papis-config:: doctor-duplicated-keys-keys-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of keys that extend the default ones from
    :confval:`doctor-duplicated-keys-keys`. This list extends instead of overwriting
    the given keys.

.. papis-config:: doctor-duplicated-values-keys

   A list of keys used by the ``duplicated-values`` check. The check will show
   an error if any of the keys listed here have repeated values. This can check,
   e.g., if a file was mistakenly added multiple times or if a tag already
   exists in the document.

.. papis-config:: doctor-duplicated-values-keys-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of keys that extend the default ones from
    :confval:`doctor-duplicated-values-keys`. This list extends instead of overwriting
    the given keys.

.. papis-config:: doctor-html-codes-keys

    A list of keys used by the ``html-codes`` check. The check will show an error
    if any of the keys contain unwanted HTML codes, e.g. ``&amp;``.

.. papis-config:: doctor-html-codes-keys-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of keys that extend the default ones from
    :confval:`doctor-html-codes-keys`. This list extends instead of overwriting
    the given keys.

.. papis-config:: doctor-html-tags-keys

    A list of keys used by the ``html-tags`` check. The check will show an error
    if any of the keys contain unwanted HTML tags, e.g. ``<div>``.

.. papis-config:: doctor-html-tags-keys-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of keys that extend the default ones from
    :confval:`doctor-html-tags-keys`. This list extends instead of overwriting
    the given keys.

.. papis-config:: doctor-key-type-keys

   A list of strings ``key:type`` used by the ``key-type`` check. This
   check will show an error if the key does not have the corresponding type. The
   type should be a builtin Python type. For example, this can be
   ``["year:int", "tags:list"]`` to check that the year is an integer and the
   tags are given as a list in a document.

.. papis-config:: doctor-key-type-keys-extend
    :type: :class:`~typing.List` [:class:`str`]

    A list of keys that extend the default ones from
    :confval:`doctor-key-type-keys`. This list extends instead of overwriting
    the given keys.

.. papis-config:: doctor-key-type-separator
    :type: str

    A separator used by the ``key-type`` check fixer. When converting from
    :class:`str` to :class:`list`, it is used to split the string into a list,
    and when converting from :class:`list` to :class:`str`, it is used to join
    list items. The split will ignore additional whitespace around the separator
    (for instance, when set to ``,``, the string ``"extra,    whitespace"`` will
    be converted to the list ``["extra", "whitespace"]``). To preserve leading
    or trailing whitespace in the separator, make sure to quote it (for instance,
    ``", "``).

Open options
------------

.. papis-config:: open-mark

    A setting that controls the default for the ``--mark`` flag of ``papis open``.
    If set to *True*, then the flag will be added by default and the mark will
    be opened for editing. In this case, the open can be disabled using
    ``--no-mark`` on an individual basis.

.. papis-config:: mark-key-name

    This is the default key name for the marks in the *info file*. For
    example, if you set ``mark-key-name = bookmarks`` then you would have
    in your ``info.yaml`` file

    .. code:: yaml

        author: J. Krishnamurti
        bookmarks:
        - name: Chapter 1
          value: 120

.. papis-config:: mark-format-name

    This is the name of the mark to be passed to
    :confval:`mark-header-format` and other such settings, similarly
    to :confval:`format-doc-name`. For example, if we want to set
    it to ``m``, then other settings must be consistent, e.g.

    .. code:: ini

        mark-format-name = m
        mark-header-format = {m[value]} - {m[name]}

.. papis-config:: mark-header-format

    This is the format of the mark when shown in a picker, similarly to
    :confval:`header-format`. This can be changed to allow for
    more complex marks. However, by default, we just assume that each mark is
    of the form ``{"name": <NAME>, "value": <VALUE>}``.

.. papis-config:: mark-match-format

    Format in which the mark name has to match the user input, similarly to
    :confval:`match-format`.

.. papis-config:: mark-opener-format

    Due to the difficulty to generalize opening a general document at a given
    bookmark, the user should set this to whatever suits their needs. For example

    - If you are using the PDF viewer ``evince`` and you want to open a
      mark, you would use::

        mark-opener-format = evince -p {mark[value]}

    - If you are using ``okular`` you would use::

        mark-opener-format = okular -p {mark[value]}

    - If you are using ``zathura``, then use::

        mark-opener-format = zathura -P {mark[value]}

Serve (Web App) options
-----------------------

.. papis-config:: serve-default-tag-sorting

   The default sorting strategy used on the "Tags" tab of the Web UI. Can be
   either ``'alpha'`` for sorting by tags' names or ``'numeric'`` for sorting by
   their frequency of use.

.. papis-config:: serve-empty-query-get-all-documents

    If *True*, when no documents are found by a query then all documents are
    shown instead. By default this is false, since showing all the documents
    can be slow.

.. papis-config:: serve-enable-timeline

    If *True*, the :confval:`time-stamp` of documents is used to
    create a timeline for when the documents were added.

.. papis-config:: serve-timeline-max

    Maximum number of documents to display in the timeline.

Frameworks
^^^^^^^^^^

All the frameworks used by the web UI are taken from the configuration file. This
allows users to easily provide newer versions that may fix some bugs or other
inconsistencies.

.. warning::

    Updating the URLs for one of the frameworks may result in a broken UI, as
    Papis is not compatible with all versions. For safety only update minor
    bugfix releases, not major new updates.

.. papis-config:: serve-user-css

    A list of ``href`` URLs that will be added to the header of each webpage
    of the web UI. These style sheets are added to the end and can be used to
    overwrite previous entries.

.. papis-config:: serve-user-js

    A list of ``href`` URLs that will be added to the header of each webpage
    of the web UI. These scripts are added to the end and can be used to
    overwrite previous entries.

.. papis-config:: serve-bootstrap-css

    Link to the desired version of the Bootstrap framework.

.. papis-config:: serve-bootstrap-js

    Link to the desired version of the Bootstrap framework.

.. papis-config:: serve-jquery-js

    Link to the desired version of the jQuery framework.

.. papis-config:: serve-jquery.dataTables-css

    Link to the desired version of the `jQuery DataTables <https://datatables.net/>`__
    framework.

.. papis-config:: serve-jquery.dataTables-js

    Link to the desired version of the `jQuery DataTables <https://datatables.net/>`__
    framework.

.. papis-config:: serve-katex-css

    Link to the desired version of the `KaTeX <https://katex.org/>`__ framework.

.. papis-config:: serve-katex-js

    Link to the desired version of the `KaTeX <https://katex.org/>`__ framework.

.. papis-config:: serve-katex-auto-render-js

    Link to the desired version of the
   `KaTeX Auto-render <https://katex.org/docs/autorender.html>`__ extension.

.. papis-config:: serve-ace-urls

    A list of links to the desired version of the `Ace editor <https://ace.c9.io/>`__.
    This should contain all necessary links to all the desired modes and
    keybindings, as exemplified by the default values.

.. papis-config:: serve-timeline-css

    Link to the desired version of the `Timeline <https://timeline.knightlab.com/>`__
    widget.

.. papis-config:: serve-timeline-js

    Link to the desired version of the `Timeline <https://timeline.knightlab.com/>`__
    widget.

Citations options
-----------------

You can change the name of the citation files, however we discourage this.

.. papis-config:: citations-file-name

    The name of the file to store the citations of the documents.

.. papis-config:: cited-by-file-name

    The name of the file to store the citations to the document.

Downloaders
-----------

.. papis-config:: downloader-proxy
    :type: str

    There is the possibility of download papers using a proxy. We use :mod:`requests`
    to handle web queries, which has extensive documentation on how to use
    proxies
    `here <https://docs.python-requests.org/en/latest/user/advanced/#proxies>`__.
    This value should give a URL that can be used as a proxy for both HTTP
    and HTTPS.

.. papis-config:: isbn-service

    Sets the ISBN service used by the ISBN importer. Available plugins are
    documented
    `here <https://isbnlib.readthedocs.io/en/latest/devs.html#plugins>`__.

Databases
---------

.. papis-config:: default-query-string

    This is the default query that a command will take if no query string is given
    at the command line. For example, if you want to open all papers authored
    by ``John Smith`` whenever you do not specify an input query string, then setting::

        default-query-string = author:"John Smith"

    would do the trick. Note that each :confval:`database-backend`
    will have a different search query, so this setting is specific to the
    default ``papis`` backend.

.. papis-config:: database-backend

    The backend to use in the database. The database is used to store the
    document in a library for improved querying performance and can be better
    thought of as a cache. The supported backends are

    - ``"papis"``: a backend that uses the :mod:`pickle` format as a storage
      format and has a query syntax based on :mod:`papis.docmatcher`.
    - ``"whoosh"``: a backend that uses `whoosh <https://whoosh.readthedocs.io/en/latest/>`__.
      for its storage and querying needs.

.. papis-config:: use-cache

    If set to *False*, then no database caching layer is used. This is only
    effective when using the ``papis`` backend and disables the storage aspects,
    while keeping the query syntax.

    If the cache is disabled, then every call to ``papis`` commands will have to
    walk the library directory tree to gather all the documents. This can be
    very slow for large libraries.

.. papis-config:: cache-dir
    :default: $XDG_CACHE_HOME

    The default directory where the cache for the ``papis`` backend is stored.

.. papis-config:: whoosh-schema-fields

    Python list with the ``TEXT`` fields that should be included in the
    whoosh database schema. For instance, say that you want to be able
    to search for the ``doi`` and ``ref`` of the documents, then you could
    include::

        whoosh-schema-fields = ['doi', 'ref']

.. papis-config:: whoosh-schema-prototype

    This is the model for the whoosh schema, check
    `the documentation <https://whoosh.readthedocs.io/en/latest/schema.html>`__
    for more information. The resulting string is passed to :func:`eval`, so
    care should be taken when modifying it.

Terminal user interface (picker)
--------------------------------

These options are for the terminal user interface (TUI). The TUI is mainly used
by the default Papis picker, but other small widgets also make use of some elements.
The TUI can be heavily customized as well in the separate ``tui`` section. For
example,

.. code:: ini

    [tui]
    status_line_format = "F1: Help"

These settings are based on styling and options used by
:ref:`prompt_toolkit <prompt_toolkit:getting_started>`, so their documentation
should be consulted.

Styling
^^^^^^^

For styling the individual components, see the extensive documentation available
`here <https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/styling.html>`__.

.. papis-config:: status_line_format
    :section: tui

    This is the format of the string that appears at the bottom in the picker
    status line. Right now there are only two variables defined:
    ``selected_index`` and ``number_of_documents``.

.. papis-config:: status_line_style
    :section: tui

    The style the status line should based on the ``prompt_toolkit`` styling,
    e.g.``fg:#ff00aa bg:black``.

.. papis-config:: message_toolbar_style
    :section: tui

    The style of the message toolbar. This toolbar is the one where messages of
    the ``echo`` command are rendered.

.. papis-config:: options_list.selected_margin_style
    :section: tui

    Style of the margin of the selected document in the picker.

.. papis-config:: options_list.unselected_margin_style
    :section: tui

    Style of the margin of the unselected documents in the picker. If no
    styling is desired on these elements, this setting can be empty.

.. papis-config:: options_list.marked_margin_style
    :section: tui

    Style of the margin of the marked documents in the picker. If no
    styling is desired on these elements, this setting can be empty.

.. papis-config:: error_toolbar_style
    :section: tui

    The style for the error message toolbar.

.. papis-config:: editmode
    :section: tui

    Controls keybindings when typing text in various TUI widgets. This can be
    set to either ``emacs`` or ``vi`` type keybindings. If this does not tell you
    anything, you can just leave it as is.

Key bindings
^^^^^^^^^^^^

For information about keybindings, see the corresponding
`documentation <https://python-prompt-toolkit.readthedocs.io/en/master/pages/advanced_topics/key_bindings.html>`__.

.. papis-config:: move_down_key
    :section: tui

.. papis-config:: move_up_key
    :section: tui

.. papis-config:: move_down_while_info_window_active_key
    :section: tui

.. papis-config:: move_up_while_info_window_active_key
    :section: tui

.. papis-config:: focus_command_line_key
    :section: tui

.. papis-config:: browse_document_key
    :section: tui

.. papis-config:: edit_notes_key
    :section: tui

.. papis-config:: edit_document_key
    :section: tui

.. papis-config:: open_document_key
    :section: tui

.. papis-config:: show_help_key
    :section: tui

.. papis-config:: show_info_key
    :section: tui

.. papis-config:: go_top_key
    :section: tui

.. papis-config:: go_bottom_key
    :section: tui

.. papis-config:: mark_key
    :section: tui

FZF integration
---------------

Papis ships with *out-of-the-box* `fzf <https://github.com/junegunn/fzf>`__
integration for the picker.  A minimal terminal user interface is provided,
together with options for its customization. You can set the picktool to
``fzf`` to select this picker.

In comparison to the *built-in* Papis picker TUI, the advantage of the fzf
picker is that it is much faster. However, a disadvantage is that it is
restricted to one-line entries. It is also important to note that ``fzf`` will
**only** match against what is shown on the terminal screen, as opposed to the
Papis matcher, that can match against the **whole** title and **whole** author
text, since this is controlled by the ``match-format`` setting.
However, for many uses it might not bother the user to have this limitation
of fzf.

.. papis-config:: fzf-binary

    Path to or name of the fzf binary.

.. papis-config:: fzf-extra-flags

    Extra flags to be passed to fzf every time it gets called.

.. papis-config:: fzf-extra-bindings

    Extra bindings to fzf as a Python list. Refer to the fzf documentation for
    more details.

.. papis-config:: fzf-header-format

    Format for the entries for fzf.
    Notice that if you want colors you should add the ``--ansi`` flag to
    ``fzf-extra-flags`` and include the colors in the
    :confval:`header-format` as ``ansi`` escape sequences.

    The Papis format string is given the additional variable ``c`` which
    contains the package ``colorama`` in it. Refer to the ``colorama``
    `documentation <https://github.com/tartley/colorama/blob/master/colorama/ansi.py#L49>`__.
    to see which colors are available. For instance, if you want the title in
    red, you would put in your ``fzf-header-format``

    .. code:: python

        "{c.Fore.RED}{doc[title]}{c.Style.RESET_ALL}"

Preview window
^^^^^^^^^^^^^^

``fzf`` has the disadvantage that it does not support multiline output and
it matches only against what it shows on the screen. To get around this issue,
we can try composing a ``fzf`` customization. The following will add a preview
window to the picker

.. code:: ini

    fzf-extra-flags = ["--ansi", "--multi", "-i",
                       "--preview", "echo {} | sed -r 's/~~/\\n/g; /^ *$/d' ",
                       "--preview-window", "bottom:wrap:20%%",
                       "--color", "preview-fg:#F6E6E4,preview-bg:#5B6D5B"]

    fzf-extra-bindings = ["ctrl-s:jump",
                          "ctrl-t:toggle-preview"]

    fzf-header-format = {c.Fore.MAGENTA}{doc[title]}{c.Style.RESET_ALL}~~ {c.Fore.CYAN}{doc[author]}{c.Style.RESET_ALL}~~ {c.Fore.YELLOW}«{doc[year]}»{c.Style.RESET_ALL}~~ {c.Fore.YELLOW}{doc[journal]}{c.Style.RESET_ALL}~~ :{doc[tags]}

This will add unrestricted titles, author, journal etc fields against which the
query will match and it will show in the ``fzf`` preview window a tidy description
of the currently selected field by replacing the token ``~~`` by a newline. You
can try this out and play with ``fzf`` customizations.

.. note::

    Please note that ``bottom:wrap:20%%`` has two ``%`` since the config file
    interpolator uses ``%`` as a reserved symbol, so it must be escaped
    by writing two of them.

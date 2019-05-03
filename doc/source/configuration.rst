.. _configuration-file:

Configuration file
==================

Papis uses a configuration file in *INI* format. You can then have
several libraries which work independently from each other.

For example, maybe you want to have one library for papers and the other
for some miscellaneous documents. An example for that is given below

.. code:: ini

    [papers]
    dir = ~/Documents/papers

    [settings]
    editor = vim
    default-library = papers

    [books]
    dir = ~/Documents/books

A more complete example of a configuration file is the following

.. code:: ini

  #
  # This is a general section, the settings set here will be set for
  # all libraries
  #
  [settings]
  #
  # General file opener program, rifle is a nice python program
  # If you're on macOS, you can write "open", if you're on linux
  # you can also write "xdg-open", on windows-cygwin, you can set it to
  # "cygstart"
  #
  opentool = rifle
  # Use ranger as a file browser, a nice python program
  file-browser = ranger
  # Ask for confirmation when doing papis add
  add-confirm = True
  # Edit the info.yaml file before adding a doc into the library
  # papis add --edit
  add-edit = True
  # Open the files before adding a document into the library
  # papis add --open
  add-open = True
  #
  # Define custom default match and header formats
  #
  match-format = {doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}
  #
  # Define header format with colors and multiline support
  #
  header-format = <red>{doc.html_escape[title]}</red>
    <span color='#ff00ff'>  {doc.html_escape[author]}</span>
    <yellow>   ({doc.html_escape[year]})</yellow>

  [tui]
  editmode = vi
  options_list.selected_margin_style = bg:ansigreen fg:ansired
  options_list.unselected_margin_style =



  # Define a lib
  [papers]
  dir = ~/Documents/papers

  # override settings from the section tui only for the papers library
  # you have to prepend "tui-" to the settings
  tui-editmode = emacs
  tui-options_list.unselected_margin_style = bg:blue
  # use whoosh as a database for papers
  database-backend = whoosh
  # rename files added by author and title
  add-file-name = {doc[author]}[doc[title]}

  # Define a lib for books
  [books]
  dir = ~/Documents/books
  database-backend = whoosh

  # Define a lib for Videos
  [videos]
  dir = ~/Videos/courses

  # Define a lib for contacts, why not?
  # To make it work you just have to define some default settings
  [contacts]
  dir = ~/contacts/general
  database-backend = papis
  mode = contact
  header-format = {doc[first_name]} {doc[last_name]}
  match-format = {doc[org]} {doc[first_name]} {doc[last_name]}
  browse-query-format = {doc[first_name]} {doc[last_name]}
  add-open = False


Local configuration files
-------------------------
Papis also offers the possibility of creating local configuration files.
The name of the local configuration file can be configured with the
``local-config-file`` setting.

The local configuration file can be found in the current directory of
where you are issuing the papis command or in the directory of the
library that you are considering in the papis command.

For instance let us suppose that you are in some project folder
``~/Documents/myproject`` and you have a local config file there
with a definition of a new library. Then whenever you are
in the ``~/Documents/myproject`` directory papis will also source the
local configuration file found there.

On the other hand, also if you have a configuration file in the library folder
for your papers, for instance in

::

  ~/Documents/papers/.papis.config

then every time that you use this library papis will also source this
configuration file.

.. include:: default-settings.rst

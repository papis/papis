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

  [settings]
  # Open file with rifle, a nice python program
  opentool = rifle
  # Use gvim as a graphical editor
  xeditor = gvim
  # Use ranger as a file browser, too a  nice python package
  file-browser = ranger
  # Ask for confirmation when doing papis add ...
  add-confirm = True
  # Edit the info.yaml file before adding a doc into the library
  # papis add --edit
  add-edit = True
  # Open the files before adding a document into the library
  # papis add --open
  add-open = True

  # Define custom default match and header formats
  match-format = {doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}
  header-format = > {doc[title]:<70.70}|{doc[author]:<20.20} ({doc[year]:-<4})

  # Commands that will be run when one does papis run ...
  # e.g., papis run gagp will run the command below in the library folder
  gagp = git commit -a && git push origin master
  gs = git status
  gm = git commit
  gp = git push
  gu = git pull
  gma = git commit -a

  # Define a lib
  [papers]
  dir = ~/Documents/papers

  # Define a lib for books
  [books]
  dir = ~/Documents/books

  # Define a lib for Videos
  [videos]
  dir = ~/Videos/courses

  # Define a lib for contacts, why not?
  # To make it work you just have to define some default settings
  [contacts]
  dir = ~/contacts/general
  mode = contact
  header-format = {doc[first_name]} {doc[last_name]}
  match-format = {doc[org]} {doc[first_name]} {doc[last_name]}
  browse-query-format = {doc[first_name]} {doc[last_name]}
  add-open = False
  rofi-gui-gui-eh = 2
  rofi-gui-header-format = %(header-format)s
                       {doc[tel][cell]}
  tk-gui-header-format = %(rofi-gui-header-format)s
  vim-gui-header-format = Title: %(header-format)s
                          Tel  : {doc[tel]}
                          Mail : {doc[email]}
                       {doc[empty]}


Default settings
----------------

.. exec::

    import papis.config
    import os
    settings = papis.config.get_default_settings()
    sep = " " * 4
    folder = "configuration"
    source = os.path.dirname(__file__)
    for section, vals in settings.items():
        print(section)
        print("^"*len(section))
        print("\n")
        for key, val in sorted(vals.items()):
            doc_file = os.path.join(
                folder, section, key + ".rst"
            )
            print("%s" % key)

            if "\n" in str(val):
                print(sep + "Default:")
                print((sep * 2) + "::")
                print("")
                for line in val.split("\n"):
                    print((sep * 3) + "%s " % line)
            else:
                print((sep * 3) + "Default: ``%s``" % val)

            print("\n")

            if os.path.exists(os.path.join(source, doc_file)):
                print((sep * 3) + ".. include:: %s" % doc_file)

            print("\n")



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
    opentool = rifle
    editor = vim
    default = papers

    [books]
    dir = ~/Documents/books
    gagp = git add . && git commit && git push origin master


Default variables
-----------------

.. exec::

    import papis.config
    settings = papis.config.get_default_settings()
    sep = " " * 4
    for section, vals in settings.items():
        print(section)
        print("^"*len(section))
        print("\n")
        for key, val in sorted(vals.items()):
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



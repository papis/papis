Guidelines for Code Modification
================================

Coding Style
------------

* Use syntax compatible with Python `3.1+`.
* Use docstrings with `sphinx` in mind
* 4 spaces are the preferred indentation method.
* No trailing white spaces are allowed.
* Restrict each line of code to 80 characters.
* Follow the PEP8 style guide: https://www.python.org/dev/peps/pep-0008/
* Always run `make test` before submitting a new PR. You need to run
  `pip3 install -e .[develop]` in the papis directory before running the
  tests.


Patches
-------

Send patches, created with `git format-patch`, to the email address

    gallo@fkf.mpg.de

or open a pull request on GitHub.


Version Numbering
-----------------

Three numbers, `A.B.C`, where
* `A` changes on a rewrite
* `B` changes when major configuration incompatibilities occur
* `C` changes with each release (bug fixes..)



Common Changes
==============

Adding options
--------------

* Add a default value in `config.py`, along with a comment that describes the
  option.

The setting is now accessible with `papis.config.get('myoption')`
or through the cli interface `papis config myoption`.


Adding scripts
--------------

* You can add scripts for everyone to share to the folder
  `examples/scripts/` in the repository. These scripts will not be shipped
  with papis, but they are there for other users to use and modify.


Adding downloaders
------------------

TODO: explain how to add new downloaders

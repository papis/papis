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
* Always run tests before submitting a new PR.
  You need to install the develop packages of papis for this:
  ```
  pip3 install -e .[develop]
  ```
  You can then run the tests with the command
  ```
  ./tools/ci-run-tests.sh
  ```


Issues
------

You can open issues in the github issue tracker
https://github.com/papis/papis/issues.


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

- Add a default value in `defaults.py`.
- Document the option in `./doc/source/default-settings.rst`
  - What is it?
  - What type should it be?
  - Note: the default is displayed automatically, so no need to write it
    explicitly.

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

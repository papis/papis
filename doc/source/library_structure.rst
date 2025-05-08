The library structure
=====================

The Papis library structure is very flexible. It is specified by directories
(and, possibly, subdirectories) in the filesystem.

A Papis library is a directory containing subfolders with documents. Papis
simply searches the library directory for (possibly nested) subfolders that
contain an information file, which by default is an ``info.yaml`` file.

Every subfolder that has an ``info.yaml`` file in it is a valid Papis document.
As an example let us consider the following library:

::

  /home/fulano/Documents/papers/
  ├── folder1
  │   └── paper.pdf
  ├── folder2
  │   ├── folder3
  │   │   ├── info.yaml
  │   │   └── blahblahblah.pdf
  │   └── folder4
  │       ├── info.yaml
  │       └── output.pdf
  ├── classics
  │   └── folder5
  │       ├── info.yaml
  │       └── output.pdf
  ├── physics
  │   └── newton
  │       └── principia
  │           ├── document.pdf
  │           ├── supplements.pdf
  │           └── info.yaml
  └─── rpa
      └── bohm
          ├── info.yaml
          ├── notes.tex
          └── output.pdf

First, you can see there are a lot of folders. Note that not all of them contain
valid documents. The PDF in ``folder1/paper.pdf`` is not valid since the
``folder1`` does not contain a ``info.yaml`` file. It does not matter how deep
your library's folder structure is: you can have a ``physics`` folder in which
you have a ``newton`` folder in which you have a folder containing the actual
book ``document.pdf`` plus some supplementary information ``supplements.pdf``.
In this case, inside the ``info.yaml`` you would have the following ``file``
section:

.. code:: yaml

  files:
  - document.pdf
  - supplements.pdf

which tells Papis that this folder contains two relevant files.

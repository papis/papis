The library structure
=====================

One of the things that makes Papis interesting is the fact that its library
structure is nearly nonexistent.

A Papis library is linked to a directory, where all the documents are (and
possibly sublibraries). What Papis does is simply go to the library folder
and look for all subfolders that contain an information file, which by default
is the ``info.yaml`` file.

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

The first thing that you might notice is that there are many folders. Just to
check that you understand exactly what is a document, please think about which
of these PDFs is not a valid Papis document... That's right!
``folder1/paper.pdf`` is not a valid document since the ``folder1`` does not
contain the ``info.yaml`` file. You see also that it does not matter how deep
the folder structure is in your library: you can have a ``physics`` folder in
which you have a ``newton`` folder in which you have a folder containing the
actual book ``document.pdf`` plus some supplementary information
``supplements.pdf``.  In this case, inside the ``info.yaml`` you would have the
following ``file`` section:

.. code:: yaml

  files:
  - document.pdf
  - supplements.pdf

which tells Papis that this folder contains two relevant files.

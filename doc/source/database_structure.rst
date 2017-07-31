The database
============

One of the things that makes papis interesting is the fact
that its database is *no database*.

A papis library is linked to a directory, where all the documents are (and
possibly sublibraries).  What papis does is simply to go to the library folder
and look for all subfolders that contain a information file, which by default
is a ``info.yaml`` file.

Every subfolder that has an ``info.yaml`` file in it is a valid papis document.
As an example let us consider the following library

::

  /home/fulano/Documents/papers/
  ├── 046e75f514ec734a1334fbaef69202ef--Hedin-Lars-
  │   └── paper.pdf
  ├── cc
  │   ├── 874f8ddf69391babdeb2712e1a14dc2b-HERMANN
  │   │   ├── info.yaml
  │   │   └── s0217979203020442.pdf
  │   └── a79190dbd574c21792d545b71755aeab-Scuseria-Gustavo-E
  │       ├── info.yaml
  │       └── output.pdf
  ├── classics
  │   └── ac61103f8b7bb4c69fb6ecd0bfc63f37-Feynman-Richard-P
  │       ├── info.yaml
  │       └── output.pdf
  ├── physics
  │   └── penrose
  │       └── 1829d718969c7271c5905fe3a997497b-Roger-Penrose
  │           ├── document.pdf
  │           └── info.yaml
  └─── rpa
      └── 697d14061ee3554777c7c276d47b0d7c-Furche-Filipp
          ├── info.yaml
          ├── notes.tex
          └── output.pdf

Cache system
------------

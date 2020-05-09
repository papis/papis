The ``info.yaml`` file
======================

At the heart of papis there is the information file. The info file contains
all information about the documents.

It uses the `yaml <http://www.yaml.org/start.html>`_ syntax to store
information, which is a very human-readable language.
It is quite format-free:
`papis` does not assume that any special information should be there.
However it will interpret the field ``files`` as the files linked to the
document for the ``papis open`` command. The ``files`` field
should be formatted as a ``yaml`` list.

For instance, if are storing papers with papis, then you most probably would
like to store author and title in there like this:

.. code:: yaml

  author: Isaac Newton
  title: Opticks, or a treatise of the reflections refractions, inflections and
    colours of light
  files:
    - document.pdf

Here we have used the ``files`` field to tell papis that the paper
has a pdf document attached to it. You can of course attach many other documents
so that you can open them when you are opening it with the ``papis open``
command. For instance if you have a paper with supporting information, you
could store it like such

.. code:: yaml

  author: Isaac Newton
  title: Opticks, or a treatise of the reflections refractions, inflections and
    colours of light
  files:
    - document.pdf
    - supporting-information.pdf

Therefore, in the folder where this document lives we have the following
structure

::

  .
  └── paper-folder
      ├── info.yaml
      ├── document.pdf
      └── supporting-information.pdf

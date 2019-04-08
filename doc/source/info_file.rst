The ``info.yaml`` file
======================

At the heart of papis there is the information file. The info file contains
all information about the documents.

It uses the `yaml <http://www.yaml.org/start.html>`_ syntax to store
information, which is a very human-readable language. It is quite format-free:
`papis` does not assume that any special information should be there.

If you are storing papers with papis, then you most probably would like to
store author and title in there like this:

.. code:: yaml

  author: Isaac Newton
  title: Opticks, or a treatise of the reflections refractions, inflections and
    colours of light
  files:
    - document.pdf

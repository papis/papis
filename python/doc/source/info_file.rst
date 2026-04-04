.. _info-file:

The ``info.yaml`` file
======================

At the heart of Papis is the information file (or info file, for short).
All information about documents is contained in info files.

It uses the `YAML <https://yaml.org>`__ syntax, which is very human-readable.
The information file is flexible: Papis does not assume that any specific
information is contained in it, except for the ``papis_id``, which is
automatically generated when missing. However, certain functionality requires
additional keys (e.g. the ``files`` key is required by ``papis open``).

For instance, when storing papers with Papis, you likely want to store author
and title in like this:

.. code:: yaml

  author: Isaac Newton
  title: Opticks, or a treatise of the reflections refractions, inflections and
    colours of light
  files:
    - document.pdf

Here, we have used the ``files`` field to tell Papis that the paper has a PDF
document attached to it. You can of course attach many other documents so that
you can open them with ``papis open``. For instance, if you have a paper with
supporting information, you could store it like this:

.. code:: yaml

  author: Isaac Newton
  title: Opticks, or a treatise of the reflections refractions, inflections and
    colours of light
  files:
    - document.pdf
    - supporting-information.pdf

Therefore, in the folder where this document lives we have the following
structure:

::

  .
  └── paper-folder
      ├── info.yaml
      ├── document.pdf
      └── supporting-information.pdf

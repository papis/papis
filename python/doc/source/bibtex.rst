BibTeX
======

Exporting documents to BibTeX is done in the same way throughout Papis.
However, given the nature of TeX, there are some special corner cases
to bear in mind when deciding on a workflow.

Note that you can check out the settings related to BibTeX handling
in :ref:`bibtex-options`.

Unicode output
--------------

The :confval:`bibtex-unicode` setting can be used to allow Unicode characters in
exported BibTeX files.

Even though this setting is set to ``False`` by default, many TeX setups support
the use of Unicode characters in BibTeX files. Enabling Unicode avoids having to
write ``\`{a}`` instead of just ``à`` to display words such as ``apareixerà``.
If your setup supports Unicode in BibTeX files, you can safely set
:confval:`bibtex-unicode` to ``True``.

Override keys
-------------

There might be some issues with the above approach though. If you are exporting
the information from your ``info.yaml`` to a BibTeX file, characters like ``&``
or ``$`` have a special meaning in TeX and need to be escaped. With the default
``bibtex-unicode = False``, these characters are exported as ``\&`` and ``\$``,
respectively. If it is just a couple of documents that are causing this problem,
you can instead override the problematic field like so:

.. code:: yaml

    title: Масса & энергия
    title_latex: Масса \& энергия
    author: Fok, V. A.
    type: article
    volume: '48'
    year: '1952'

In this example, the title that will be added to the BibTeX entry
is ``title_latex``, since we have overridden it by appending the ``_latex``
suffix to the ``title`` key.

This approach is also useful if you need to use some tricks to get BibTeX to
parse and render your entries correctly. Some examples (taken from `Tame the
BeaST`_ 13.1-13.5):

.. code:: yaml

   # Names with multicharacter initials
   author: Matiyasevich, Yuri
   author_latex: Matiyasevich, {\relax Yu}ri

   # Names with capitalized "von" parts
   author: De La Cruz, Maria
   author_latex: {D}e {L}a Cruz, Maria

   # Names with uncapitalized last name parts
   author: de la Cierva y Codorníu, Juan
   author_latex: de la {Cierva y} Codorn{\’\i}u, Juan

   # Names with no space between von and last name
   author: d'Ormesson, Jean
   author_latex: d'\relax Ormesson, Jean

.. _`Tame the BeaST`:
   http://texdoc.net/texmf-dist/doc/bibtex/tamethebeast/ttb_en.pdf

Ignore keys
-----------

If you do not want to export certain keys to the BibTeX file,
like the ``abstract``, you can use the :confval:`bibtex-ignore-keys`
setting to omit them in the exporting process.

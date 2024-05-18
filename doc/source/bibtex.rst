BibTeX
======

Exporting documents to BibTeX is done in the same way throughout Papis.
However, given the nature of TeX, there are some special corner cases
to bear in mind when deciding on a workflow.

Note that you can check out the settings related to BibTeX handling
in :ref:`bibtex-options`.

Unicode output
--------------

If you are using TeX engines like XeTeX or LuaTeX, then you can use unicode
characters for your BibTeX files as well. This means there is no need to write
``\`{a}`` instead of ``à`` in words such as ``apareixerà``. To control the
output of unicode characters in Papis, use the
:confval:`bibtex-unicode` setting.

Override keys
-------------

There might be some issues with this approach though. If you are
exporting the information from your ``info.yaml`` to a BibTeX file, characters
like ``&`` or ``$`` have a special meaning in TeX and would need to be escaped.
When ``bibtex-unicode = False``, these characters would be exported as ``\&``
and ``\$``, respectively. If it is just a couple of documents that are causing
this problem, you can just override the problematic field like so

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

Ignore keys
-----------

If you do not want to export certain keys to the BibTeX file,
like the ``abstract``, you might use the :confval:`bibtex-ignore-keys`
setting to omit them in the exporting process.

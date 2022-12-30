Bibtex
======

Exporting documents to bibtex is done in the same way throughout papis.
However, given the nature of TeX there are some special corner cases
that one should bear in mind and decide for yourself what should be
your best workflow.

Note that you can check out the settings related to bibtex handling
in :ref:`bibtex-options`.

Unicode output
--------------

If you are using TeX engines like XeTeX, then you can use unicode characters
for your bibtex files. This means, there is no need to write
``\`{a}`` instead of ``à`` in words such as ``apareixerà``.
Checkout the bibtex settings for this, in this particular case the relevant
settings is :ref:`config-settings-bibtex-unicode`.

Override keys
-------------

There might be some issues with this approach though.
If you're exporting one-to-one the information in your ``info.yaml``
to the bibtex files, characters like ``&`` or ``$`` have a special meaning
in TeX and therefore will get interpreted accordingly.
When ``bibtex-unicode = False``, these characters would be exported
as ``\&`` and ``\$`` respectively. If it is just a couple of documents
that are causing this problem, you can just override the problematic field
like so

.. code:: yaml

    title: Масса & энергия
    title_latex: Масса \& энергия
    author: Fok, V.A.
    type: article
    volume: '48'
    year: '1952'

In this example, the title that will be output to the bibtex entry
is ``title_latex``, since we have overridden it by appending the ``_latex``
prefix to the ``title`` key.


Ignore keys
-----------

If you do not want to export certain keys to the bib file,
like abstract, you might use the :ref:`config-settings-bibtex-ignore-keys` setting
to omit them in the exporting process.

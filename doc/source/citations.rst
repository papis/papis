Citations of documents: ``citations.yaml`` and ``cited-by.yaml`` files
----------------------------------------------------------------------

Papis has support for downloading and exploring citations that documents reference,
and also cited-by type references.

If your document has a ``doi`` associated and you use the updater from
this ``doi``, or you added information from the ``doi`` when you added the
document, then chances are that the ``info.yaml`` file has a ``citations``
key within it.

In this case, papis can actually get metadata from these dois and
store it in a ``citations.yaml`` file, for references that the document
has within it.

You can generate this file either from the web application or
from the ``papis citations`` command. Refer to their respective
documentations in order to know more about it.

As of version ``v0.13``, it is also possible to generate a
``cited-by.yaml`` file with the information of other papers that cite
your document. This is done by scanning your papis library for
documents that cite said document. You can also generate this
file from the web application or from the ``papis citations`` command.

The citation files try to include always first information already
existing in the library. This is, before doing any online query,
papis tries to find the relevant information in your library.

Notice that papis copies most of the metadata to the ``citations.yaml``
and ``cited-by.yaml`` files. Even though this might seem quite heavy on
disk space, as a rule of thumb all the ``citation.yaml`` files of a
library with 2k papers containing physics papers will amount to only
around 30MB.

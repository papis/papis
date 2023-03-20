Scihub support
==============

.. image:: https://badge.fury.io/py/papis-scihub.svg
    :target: https://badge.fury.io/py/papis-scihub

Papis has a script that uses the scihub platform to download scientific
papers. Due to legal caution the script is not included directly
as a papis command, and it has its own PyPi repository.


To install it, just type

::

  pip3 install papis-scihub


Now you can type

.. code:: bash

  papis scihub -h

and see the help message of the script.

Some usage examples are:


  - Download via the doi number:

    .. code:: bash

      papis scihub 10.1002/andp.19053220607 \\
        add -d einstein_papers --folder-name photon_definition

  - Download via a url that contains the doi number in the format ``.*/doi/<doinumber>``

    .. code:: bash

      papis scihub https://physicstoday.scitation.org/doi/10.1063/1.881498 \\
        add --folder-name important_paper

  - Download via the ``doi.org`` url:

    .. code:: bash

      papis scihub https://doi.org/10.1016/j.physrep.2016.12.002 add



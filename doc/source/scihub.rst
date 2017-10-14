Scihub support
==============

Papis has a script that uses the scihub platform to download scientific
papers. Due to legal caution the script is not included directly
as a papis command, and it is written ``bash``.

If you want to use it, you can download it from
`here <https://raw.githubusercontent.com/alejandrogallo/papis/master/examples/scripts/papis-scihub/>`_
and copy it into your papis script folder.

Usuar locations for your script folder are

  - ``~/.config/papis/scripts``
  - ``~/.papis/scripts``

Therefore, if you decide to have the script folder in the first option,
you can install the script by doing:

.. code:: bash

  wget -O ~/.config/papis/scripts/papis-scihub https://raw.githubusercontent.com/alejandrogallo/papis/master/examples/scripts/papis-scihub
  chmod +x ~/.config/papis/scripts/papis-scihub

The ``chmod +x`` command is necessary to make the ``papis-scihub`` file
executable.

Now you can type

.. code:: bash

  papis scihub -h

and see the help message of the script.

Some usage examples are:


  - Download via the doi number:

    .. code:: bash

      papis scihub 10.1002/andp.19053220607 -d einstein_papers --name photon_definition

  - Download via a url that contains the doi number in the format ``.*/doi/<doinumber>``

    .. code:: bash

      papis scihub http://physicstoday.scitation.org/doi/10.1063/1.881498 --name important_paper

  - Download via the ``doi.org`` url:

    .. code:: bash

      papis scihub https://doi.org/10.1016/j.physrep.2016.12.002



Custom scripts
==============

As in `git <http://git-scm.com>`__, you can write custom scripts to
include them in the command spectrum of papis.

Imagine you want to write a script to send papers to someone via
``mutt``, you could write the following script caled ``papis-mail``:

.. code:: sh

    #! /usr/bin/env bash

    if [[ $1 = "-h" ]]; then
      echo "Email a paper to my friend"
      exit 0
    fi

    folder_name=$1
    zip_name="${folder_name}.zip"

    papis -l ${PAPIS_LIB} export --folder --out ${folder_name}
    zip -r ${zip_name} ${folder_name}

    mutt -a ${zip_name}

Papis defines environment variables such as ``PAPIS_LIB`` so that
external scripts can make use of the user input.

If you have the script above in your path you can run

::

    papis -h

and you will see that there is another command besides the default
called ``mail``. Then if you type

::

    papis -l mylib mail this_paper

this will create a folder called ``this_paper`` with a selection of a
document, zip it, and send it to whoever you choose to.


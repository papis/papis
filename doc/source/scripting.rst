Custom scripts
==============

As in `git <https://git-scm.com>`__, you can write custom scripts to
include them in the command spectrum of Papis.

Example: Mail script
--------------------

Imagine you want to write a script to send papers to someone via the email
client ``mutt`` (you can try to do it with another mail client). You could
write the following script called ``papis-mail``:

.. code:: sh

    #! /usr/bin/env bash
    # papis-short-help: Email a paper to my friend.

    folder_name=$1
    zip_name="${folder_name}.zip"

    papis -l ${PAPIS_LIB} export --folder --out ${folder_name}
    zip -r ${zip_name} ${folder_name}

    mutt -a ${zip_name}

Papis defines environment variables such as ``PAPIS_LIB`` so that external
scripts can make use of the user input.

To use the script you can put it somewhere in your ``PATH`` or alternatively
inside the ``~/.papis/scripts`` folder. In the latter case when you run:

::

    papis -h

... you will see that there is another command besides the default commands called
``mail``:

::

    Commands:
      add        Add a document into a given library.
      ...        ...
      mail       Email a paper to my friend.
      ...        ...

... where the description ``Email a paper to my friend.`` is there because
we have defined the comment ``# papis-short-help: Email a paper to my friend.``
in the header of the script.

Then, if you type:

::

    papis -l mylib mail this_paper

... this will create a folder called ``this_paper`` with a selection of a
document, zip it and send it to whoever you choose to.

Example: Accessing Papis from within mutt
-----------------------------------------

You may want to pick documents to attach to your email in ``mutt``
from the Papis interface.

Add this code to your ``muttrc``:

::

   # # macro to attach paper from Papis
   macro attach,compose \cp \
   "\
   <enter-command>unset wait_key<enter>\                                 # Don't require 'press any key'
   <shell-escape>rm -rf /tmp/paper /tmp/paper.zip<enter>\                # remove the folder /tmp/paper if it already exists
   <shell-escape>papis export --folder -o /tmp/paper<enter>\             # start papis with the --folder flag
   <shell-escape>zip -r /tmp/paper.zip /tmp/paper<enter>\                # zip the directory
   <attach-file>/tmp/paper.zip<enter>\                                   # attach zip file to the email
   "

Try it out with ``Ctrl-p`` on your ``Compose`` screen. This makes use
of the ``papis export --folder`` flag that moves the paper folder you choose to
a temporary location (``/tmp/paper``). Mutt will then attach the
paper to the email, which you can rename to be more descriptive with
``R``.


Example: Define Papis mode in i3wm
----------------------------------

This is an example of using Papis with the window manager `i3`:

::

  # Enter Papis mode
  bindsym $mod+Ctrl+p mode "papis"

  # Define Papis mode
  mode "papis" {

    # open documents
    bindsym $mod+o exec python3 -m papis.main \
      --pick-lib --set picktool dmenu open

    # edit documents
    bindsym $mod+e exec python3 -m papis.main \
      --pick-lib --set picktool dmenu --set editor gvim edit

    # open document's url
    bindsym $mod+b exec python3 -m papis.main \
      --pick-lib --set picktool dmenu browse

    # return to default mode
    bindsym Ctrl+c mode "default"
    bindsym Return mode "default"
    bindsym Escape mode "default"
  }

Useful links
------------

- `Get paper references with papis <https://alejandrogallo.github.io/blog/posts/getting-paper-references-with-papis/>`__:

    .. code:: sh

        citget() {
            query=$1
            shift
            papis explore \
                citations -s "$query" \
                pick \
                cmd "papis add --from doi {doc[doi]} $@"
        }




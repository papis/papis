"""
Vim gui
*******

.. papis-config:: help-key
    :section: vim-gui

.. papis-config:: open-key
    :section: vim-gui

.. papis-config:: edit-key
    :section: vim-gui

.. papis-config:: search-key
    :section: vim-gui

.. papis-config:: delete-key
    :section: vim-gui

.. papis-config:: open-dir-key
    :section: vim-gui

.. papis-config:: next-search-key
    :section: vim-gui

.. papis-config:: prev-search-key
    :section: vim-gui

.. papis-config:: header-format
    :section: vim-gui

dmenu gui
*********

See `dmenu <https://tools.suckless.org/dmenu/>`_ and the python wrapper
`here <http://dmenu.readthedocs.io/en/latest/>`_ for more information.
You will need to install the latter to make use of this function,

::

    pip3 install dmenu


.. papis-config:: lines
    :section: dmenu-gui

.. papis-config:: case_insensitive
    :section: dmenu-gui

.. papis-config:: bottom
    :section: dmenu-gui

.. papis-config:: font
    :section: dmenu-gui

.. papis-config:: background
    :section: dmenu-gui

.. papis-config:: foreground
    :section: dmenu-gui

.. papis-config:: background_selected
    :section: dmenu-gui

.. papis-config:: foreground_selected
    :section: dmenu-gui

.. papis-config:: header-format
    :section: dmenu-gui

    This is not set per default, and it will default to
    the general header-format if not set.

"""


def get_default_settings():
    return {
        "vim-gui": {
            "help-key": "h",
            "open-key": "o",
            "edit-key": "e",
            "search-key": "/",
            "delete-key": "dd",
            "open-dir-key": "<S-o>",
            "next-search-key": "n",
            "prev-search-key": "N",
            "header-format":
                "Title : {doc[title]}\n"
                "Author: {doc[author]}\n"
                "Year  : {doc[year]}\n"
                "-------\n",
        },
        "dmenu-gui": {
            "lines": 20,
            "case_insensitive": True,
            "bottom": True,
            "font": 'monospace-14',
            "background": '#000000',
            "foreground": '#55ff55',
            "background_selected": '#005500',
            "foreground_selected": '#f0f0f0',
            "header-format": None,
        },
    }

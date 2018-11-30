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
    }

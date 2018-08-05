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

Rofi gui
********
.. papis-config:: key-quit
    :section: rofi-gui

.. papis-config:: key-query
    :section: rofi-gui

.. papis-config:: key-refresh
    :section: rofi-gui

.. papis-config:: key-edit
    :section: rofi-gui

.. papis-config:: key-delete
    :section: rofi-gui

.. papis-config:: key-help
    :section: rofi-gui

.. papis-config:: key-open-stay
    :section: rofi-gui

.. papis-config:: key-normal-window
    :section: rofi-gui

.. papis-config:: key-browse
    :section: rofi-gui

.. papis-config:: key-open
    :section: rofi-gui

.. papis-config:: eh
    :section: rofi-gui

.. papis-config:: sep
    :section: rofi-gui

.. papis-config:: width
    :section: rofi-gui

.. papis-config:: lines
    :section: rofi-gui

.. papis-config:: fullscreen
    :section: rofi-gui

.. papis-config:: normal_window
    :section: rofi-gui

.. papis-config:: fixed_lines
    :section: rofi-gui

.. papis-config:: markup_rows
    :section: rofi-gui

.. papis-config:: multi_select
    :section: rofi-gui

.. papis-config:: case_sensitive
    :section: rofi-gui

.. papis-config:: header-format
    :section: rofi-gui

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
        "urwid-gui": {
            "prompt-key": ":",
            "search-key": "/",
            "help-key": "?",
            "quit-key": "Q",
            "redraw-key": "ctrl l",
            "kill-buffer-key": "q",
            "show-fields": "title,author,year,abstract",
        },
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
        "rofi-gui": {
            "key-quit": "Alt+q",
            "key-query": "Alt+y",
            "key-refresh": "Alt+r",
            "key-edit": "Alt+e",
            "key-delete": "Alt+d",
            "key-help": "Alt+h",
            "key-open-stay": "Alt+o",
            "key-normal-window": "Alt+w",
            "key-browse": "Alt+u",
            "key-open": "Enter",
            "eh": 3,
            "sep": "|",
            "width": 80,
            "lines": 10,
            "fullscreen": False,
            "normal_window": False,
            "fixed_lines": 20,
            "markup_rows": True,
            "multi_select": True,
            "case_sensitive": False,
            "header-format": \
                "<b>{doc[title]}</b>\n"\
                "{doc[empty]}  <i>{doc[author]}</i>\n"
                "{doc[empty]}  <span foreground=\"red\">"
                "({doc[year]:->4})</span>"\
                "<span foreground=\"green\">{doc[tags]}</span>",
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

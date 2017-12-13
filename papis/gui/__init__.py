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

Tk gui
*******
.. papis-config:: open
    :section: tk-gui

.. papis-config:: edit
    :section: tk-gui

.. papis-config:: exit
    :section: tk-gui

.. papis-config:: clear
    :section: tk-gui

.. papis-config:: help
    :section: tk-gui

.. papis-config:: focus_prompt
    :section: tk-gui

.. papis-config:: move_down
    :section: tk-gui

.. papis-config:: move_up
    :section: tk-gui

.. papis-config:: move_top
    :section: tk-gui

.. papis-config:: move_bottom
    :section: tk-gui

.. papis-config:: print_info
    :section: tk-gui

.. papis-config:: half_down
    :section: tk-gui

.. papis-config:: half_up
    :section: tk-gui

.. papis-config:: scroll_down
    :section: tk-gui

.. papis-config:: scroll_up
    :section: tk-gui

.. papis-config:: prompt-fg
    :section: tk-gui

.. papis-config:: prompt-bg
    :section: tk-gui

    Color of the foreground of an entry

.. papis-config:: entry-fg
    :section: tk-gui

    Color of the foreground of an active entry

.. papis-config:: activeforeground
    :section: tk-gui

    Color of the background of an active entry

.. papis-config:: activebackground
    :section: tk-gui

.. papis-config:: insertbackground
    :section: tk-gui

.. papis-config:: prompt-font-size
    :section: tk-gui

.. papis-config:: entry-bg-size
    :section: tk-gui

.. papis-config:: entry-font-size
    :section: tk-gui

.. papis-config:: entry-font-name
    :section: tk-gui

.. papis-config:: entry-font-style
    :section: tk-gui

.. papis-config:: entry-lines
    :section: tk-gui

.. papis-config:: entry-bg-odd
    :section: tk-gui

.. papis-config:: entry-bg-pair
    :section: tk-gui

.. papis-config:: cursor
    :section: tk-gui

.. papis-config:: height
    :section: tk-gui

.. papis-config:: labels-per-page
    :section: tk-gui

.. papis-config:: borderwidth
    :section: tk-gui

.. papis-config:: window-width
    :section: tk-gui

.. papis-config:: window-bg
    :section: tk-gui

.. papis-config:: window-height
    :section: tk-gui

.. papis-config:: match-format
    :section: tk-gui

.. papis-config:: header-format
    :section: tk-gui

Rofi gui
********
.. papis-config:: key-quit
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

"""

def get_default_settings():
    return {
        "vim-gui": {
            "help-key"          : "h",
            "open-key"          : "o",
            "edit-key"          : "e",
            "search-key"        : "/",
            "delete-key"        : "dd",
            "open-dir-key"      : "<S-o>",
            "next-search-key"   : "n",
            "prev-search-key"   : "N",
            "header-format" : \
                "Title : {doc[title]}\n"\
                "Author: {doc[author]}\n"\
                "Year  : {doc[year]}\n"\
                "-------\n",
        },
        "tk-gui": {
            "open"         : "o",
            "edit"         : "e",
            "exit"         : "<Control-q>",
            "clear"        : "q",
            "help"         : "h",
            "focus_prompt" : ":",
            "move_down"    : "j",
            "move_up"      : "k",
            "move_top"     : "g",
            "move_bottom"  : "<Shift-G>",
            "print_info"   : "i",
            "half_down"    : "<Control-d>",
            "half_up"      : "<Control-u>",
            "scroll_down"  : "<Control-e>",
            "scroll_up"    : "<Control-y>",
            "prompt-fg"    : "lightgreen",
            "prompt-bg"        : "black",
            # Color of the foreground of an entry
            "entry-fg"         : "grey77",
            # Color of the foreground of an active entry
            "activeforeground" : "gray99",
            # Color of the background of an active entry
            "activebackground" : "#394249",
            "insertbackground" : "red",
            "prompt-font-size" : "14",
            "entry-bg-size"    : "14",
            "entry-font-size"  : "14",
            "entry-font-name"  : "Times",
            "entry-font-style" : "normal",
            "entry-lines"      : "3",
            "entry-bg-odd"     : "#273238",
            "entry-bg-pair"    : "#273238",
            "cursor"           : "xterm",
            "height"           : 1,
            "labels-per-page"  : 6,
            "borderwidth"      : -1,
            "window-width"     : "1200",
            "window-bg"        : "#273238",
            "window-height"    : "700",
            "match-format" : \
                "{doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}",
            "header-format"    : \
                "{doc[title]}\n"\
                "{doc[empty]}   {doc[author]}\n"\
                "({doc[year]:->4})",
        },
        "rofi-gui": {
            "key-quit"          : "Alt+q",
            "key-edit"          : "Alt+e",
            "key-delete"        : "Alt+d",
            "key-help"          : "Alt+h",
            "key-open-stay"     : "Alt+o",
            "key-normal-window" : "Alt+w",
            "key-browse"        : "Alt+u",
            "key-open"          : "Enter",
            "eh"                : 3,
            "sep"               : "|",
            "width"             : 80,
            "lines"             : 10,
            "fullscreen"        : False,
            "normal_window"     : False,
            "fixed_lines"       : 20,
            "markup_rows"       : True,
            "multi_select"      : True,
            "case_sensitive"    : False,
            "header-format"     : \
               "<b>{doc[title]}</b>\n"\
               "{doc[empty]}  <i>{doc[author]}</i>\n"
               "{doc[empty]}  <span foreground=\"red\">({doc[year]:->4})</span>"\
               "<span foreground=\"green\">{doc[tags]}</span>",
        },
    }

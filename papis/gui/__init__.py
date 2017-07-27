
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

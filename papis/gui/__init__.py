
def get_default_settings():
    return {
        "vim-gui": {
            "help_key"        : "h",
            "open_key"        : "o",
            "edit_key"        : "e",
            "search_key"      : "/",
            "delete_key"      : "dd",
            "open_dir_key"    : "<S-o>",
            "next_search_key" : "n",
            "prev_search_key" : "N",
        },
        "tk-gui": {
            "open"          : "o",
            "prompt-fg"     : "lightgreen",
            "window-width"  : "1200",
            "window-bg"     : "#273238",
            "window-height" : "700",
            "header_format" : \
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
            "fixed-lines"       : 20,
            "markup_rows"       : True,
            "multi_select"      : True,
            "case_sensitive"    : False,
            "header_format"     : \
               "<b>{doc[title]}</b>\n"\
               "{doc[empty]}  <i>{doc[author]}</i>\n"
               "{doc[empty]}  <span foreground=\"red\">({doc[year]:->4})</span>"\
               "<span foreground=\"green\">{doc[tags]}</span>",
        },
    }

from papis.tui.app import Picker


def get_default_settings():
    return dict(tui={
        "status_line_format": (
            "{selected_index}/{number_of_documents}  " +
            "F1:help  " +
            "Ctrl-l:redraw  " +
            "c-x:execute command  "
        ),

        "status_line_style": 'bg:ansiwhite fg:ansiblack',
        'message_toolbar_style': 'bg:ansiyellow fg:ansiblack',
        'options_list.selected_margin_style': 'bg:ansiblack fg:ansigreen',
        'options_list.unselected_margin_style': 'bg:ansiwhite',
        'error_toolbar_style': 'bg:ansired fg:ansiblack',

        "editmode": "emacs",
    })

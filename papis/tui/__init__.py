def get_default_settings():
    return dict(tui={
        "status_line_format": (
            "{selected_index}/{number_of_documents}  " +
            "F1:help  " +
            "c-l:redraw  "
        ),

        "status_line_style": 'bg:ansiwhite fg:ansiblack',
        'message_toolbar_style': 'bg:ansiyellow fg:ansiblack',
        'options_list.selected_margin_style': 'bg:ansiblack fg:ansigreen',
        'options_list.unselected_margin_style': 'bg:ansiwhite',
        'error_toolbar_style': 'bg:ansired fg:ansiblack',

        'move_down_key': 'down',
        'move_up_key': 'up',
        'move_down_while_info_window_active_key': 'c-n',
        'move_up_while_info_window_active_key': 'c-p',
        'focus_command_line_key': 'tab',
        'edit_document_key': 'c-e',
        'open_document_key': 'c-o',
        'show_help_key': 'f1',
        'show_info_key': 's-tab',
        'go_top_key': 'home',
        'go_bottom_key': 'end',

        "editmode": "emacs",
    })

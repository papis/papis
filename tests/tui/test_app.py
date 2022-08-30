from papis.tui.app import config, get_keys_info


def test_settings():
    config.get("status_line_format", section="tui")
    config.get("status_line_style", section="tui")
    config.get("message_toolbar_style", section="tui")
    config.get("options_list.selected_margin_style", section="tui")
    config.get("options_list.unselected_margin_style", section="tui")
    config.get("error_toolbar_style", section="tui")
    config.get("move_down_key", section="tui")
    config.get("move_up_key", section="tui")
    config.get("move_down_while_info_window_active_key", section="tui")
    config.get("move_up_while_info_window_active_key", section="tui")
    config.get("focus_command_line_key", section="tui")
    config.get("edit_document_key", section="tui")
    config.get("open_document_key", section="tui")
    config.get("show_help_key", section="tui")
    config.get("show_info_key", section="tui")
    config.get("go_top_key", section="tui")
    config.get("go_bottom_key", section="tui")
    config.get("editmode", section="tui")

    kb = get_keys_info()
    assert kb is not None

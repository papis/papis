from papis.testing import TemporaryConfiguration


def test_settings(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    papis.config.getstring("status_line_format", section="tui")
    papis.config.getstring("status_line_style", section="tui")
    papis.config.getstring("message_toolbar_style", section="tui")
    papis.config.getstring("options_list.selected_margin_style", section="tui")
    papis.config.getstring("options_list.unselected_margin_style", section="tui")
    papis.config.getstring("options_list.marked_margin_style", section="tui")
    papis.config.getstring("error_toolbar_style", section="tui")
    papis.config.getstring("move_down_key", section="tui")
    papis.config.getstring("move_up_key", section="tui")
    papis.config.getstring("move_down_while_info_window_active_key", section="tui")
    papis.config.getstring("move_up_while_info_window_active_key", section="tui")
    papis.config.getstring("focus_command_line_key", section="tui")
    papis.config.getstring("browse_document_key", section="tui")
    papis.config.getstring("edit_document_key", section="tui")
    papis.config.getstring("edit_notes_key", section="tui")
    papis.config.getstring("open_document_key", section="tui")
    papis.config.getstring("show_help_key", section="tui")
    papis.config.getstring("show_info_key", section="tui")
    papis.config.getstring("go_top_key", section="tui")
    papis.config.getstring("go_bottom_key", section="tui")
    papis.config.getstring("editmode", section="tui")

    from papis.tui.app import get_keys_info
    kb = get_keys_info()
    assert kb is not None

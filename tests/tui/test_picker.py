from papis.testing import TemporaryConfiguration


def test_settings(tmp_config: TemporaryConfiguration) -> None:
    from papis.config import getstring

    getstring("status_line_format", section="tui")
    getstring("status_line_style", section="tui")
    getstring("message_toolbar_style", section="tui")
    getstring("options_list.selected_margin_style", section="tui")
    getstring("options_list.unselected_margin_style", section="tui")
    getstring("options_list.marked_margin_style", section="tui")
    getstring("error_toolbar_style", section="tui")
    getstring("move_down_key", section="tui")
    getstring("move_up_key", section="tui")
    getstring("move_down_while_info_window_active_key", section="tui")
    getstring("move_up_while_info_window_active_key", section="tui")
    getstring("focus_command_line_key", section="tui")
    getstring("browse_document_key", section="tui")
    getstring("edit_document_key", section="tui")
    getstring("edit_notes_key", section="tui")
    getstring("open_document_key", section="tui")
    getstring("show_help_key", section="tui")
    getstring("show_info_key", section="tui")
    getstring("go_top_key", section="tui")
    getstring("go_bottom_key", section="tui")
    getstring("editmode", section="tui")

    from papis.tui.picker import get_keys_info

    kb = get_keys_info()
    assert kb is not None

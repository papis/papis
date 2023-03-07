from tests.testlib import TemporaryConfiguration


def test_settings(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    papis.config.get("status_line_format", section="tui")
    papis.config.get("status_line_style", section="tui")
    papis.config.get("message_toolbar_style", section="tui")
    papis.config.get("options_list.selected_margin_style", section="tui")
    papis.config.get("options_list.unselected_margin_style", section="tui")
    papis.config.get("error_toolbar_style", section="tui")
    papis.config.get("move_down_key", section="tui")
    papis.config.get("move_up_key", section="tui")
    papis.config.get("move_down_while_info_window_active_key", section="tui")
    papis.config.get("move_up_while_info_window_active_key", section="tui")
    papis.config.get("focus_command_line_key", section="tui")
    papis.config.get("edit_document_key", section="tui")
    papis.config.get("open_document_key", section="tui")
    papis.config.get("show_help_key", section="tui")
    papis.config.get("show_info_key", section="tui")
    papis.config.get("go_top_key", section="tui")
    papis.config.get("go_bottom_key", section="tui")
    papis.config.get("editmode", section="tui")

    from papis.tui.app import get_keys_info
    kb = get_keys_info()
    assert kb is not None

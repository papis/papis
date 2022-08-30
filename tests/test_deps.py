def test_pygments():
    # This function exists after version 2.2.0 only
    from pygments.lexers import find_lexer_class_by_name
    yaml = find_lexer_class_by_name("yaml")
    assert yaml is not None


def test_colorama():
    import colorama
    assert colorama.Back
    assert colorama.Style
    assert colorama.Style.RESET_ALL
    assert colorama.Fore.RED
    assert colorama.Fore.YELLOW
    assert colorama.init


def test_prompt_toolkit():
    from prompt_toolkit.formatted_text.html import HTML, html_escape    # noqa: F401
    from prompt_toolkit.application import Application                  # noqa: F401

    from prompt_toolkit.history import FileHistory                      # noqa: F401
    from prompt_toolkit.buffer import Buffer                            # noqa: F401
    from prompt_toolkit.enums import EditingMode                        # noqa: F401
    from prompt_toolkit.key_binding import KeyBindings                  # noqa: F401
    from prompt_toolkit.layout.screen import Point                      # noqa: F401
    from prompt_toolkit.layout.containers import HSplit, Window         # noqa: F401
    from prompt_toolkit.layout.controls import (                        # noqa: F401
        BufferControl,
        FormattedTextControl
    )
    from prompt_toolkit.layout.layout import Layout                     # noqa: F401
    from prompt_toolkit.widgets import HorizontalLine                   # noqa: F401

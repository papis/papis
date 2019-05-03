def test_pygments():
    # This function exists after version 2.2.0 only
    from pygments.lexers import find_lexer_class_by_name
    yaml = find_lexer_class_by_name('yaml')
    assert(yaml is not None)


def test_colorama():
    import colorama
    assert(colorama.Back)
    assert(colorama.Style)
    assert(colorama.Style.RESET_ALL)
    assert(colorama.Fore.RED)
    assert(colorama.Fore.YELLOW)
    assert(colorama.init)


def test_prompt_toolkit():
    from prompt_toolkit.formatted_text.html import HTML, html_escape
    from prompt_toolkit.application import Application

    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.enums import EditingMode
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout.screen import Point
    from prompt_toolkit.layout.containers import HSplit, Window
    from prompt_toolkit.layout.controls import (
        BufferControl,
        FormattedTextControl
    )
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.widgets import (
        HorizontalLine
    )
    assert(True)

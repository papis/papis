from papis.tui.widgets import MessageToolbar, InfoWindow, HelpWindow
from prompt_toolkit.application.current import get_app


def test_message_toolbar() -> None:
    app = get_app()
    mt = MessageToolbar()
    assert not app.layout.has_focus(mt)

    mt.text = "Hello world"
    assert mt.filter()

    mt.text = ""
    assert not mt.filter()

    mt.text = None
    assert not mt.filter()


def test_info_window() -> None:
    app = get_app()
    iw = InfoWindow()
    assert iw.text == ""

    iw.text = " info"
    assert iw.text == " info"
    assert not iw.filter()

    app.layout.focus(iw.window)
    assert app.layout.has_focus(iw)


def test_help_window() -> None:
    hw = HelpWindow()
    assert hw.text.value == ""

    hw.text = "Help?"
    assert hw.text == "Help?"

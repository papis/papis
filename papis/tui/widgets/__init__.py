from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.containers import (
    HSplit, Window, WindowAlign, ConditionalContainer
)
from prompt_toolkit.layout.controls import (
    BufferControl,
    FormattedTextControl
)
from prompt_toolkit.widgets import (
    HorizontalLine
)
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers import find_lexer_class_by_name
import logging

from .list import OptionsListControl

logger = logging.getLogger('pick')


class CommandWindow(ConditionalContainer):
    focus = False
    instance = None
    def __init__(self):
        CommandWindow.instance = self
        self.buf = Buffer()
        self.buf.text = ''
        self.window = Window(
            content=BufferControl(
                buffer=self.buf,
                input_processors=[BeforeInput(':')]
            ),
            height=1
        )
        super(CommandWindow, self).__init__(
            content=self.window,
            filter=has_focus(CommandWindow.instance)
        )


class InfoWindow:
    shown = False

    @Condition
    def is_shown():
        return InfoWindow.shown

    def __init__(self):
        self.buf = Buffer()
        self.buf.text = ''
        self.lexer = PygmentsLexer(find_lexer_class_by_name('yaml'))
        self.window = ConditionalContainer(
            content=HSplit([
                HorizontalLine(),
                Window(
                    content=BufferControl(
                        buffer=self.buf, lexer=self.lexer)
                )
            ], height=None),
            filter=InfoWindow.is_shown
        )

    def set_text(self, text):
        self.buf.text = text

    def get_text(self):
        return self.buf.text


class HelpWindow:
    shown = False
    text = """
    <span fg='ansired'> Bindings: </span>

----------------------------------------------------
/   Ctrl-e, Ctrl-down, Shift-down : Scroll Down     /
/   Ctrl-y, Ctrl-up,   Shift-up   : Scroll up       /
/   Ctrl-n, down                  : Next item       /
/   Ctrl-p, up                    : Previous item   /
/   Ctrl-q, Ctrl-c                : Quit            /
/   Home                          : First item      /
/   End                           : Last item       /
----------------------------------------------------
    """

    @Condition
    def is_shown():
        return HelpWindow.shown

    def __init__(self):
        self.format_text_control = FormattedTextControl(
            key_bindings=None,
            show_cursor=False,
            focusable=False,
            text=HTML(self.text)
        )
        self.window = ConditionalContainer(
            content=Window(
                content=self.format_text_control,
                align=WindowAlign.CENTER
            ),
            filter=HelpWindow.is_shown
        )

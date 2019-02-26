from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.filters import has_focus, Condition
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import (
    HSplit, Window, WindowAlign, ConditionalContainer
)
from prompt_toolkit.layout import Dimension
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

from .list import OptionsList
from .command_line_prompt import CommandLinePrompt

logger = logging.getLogger('pick')


class MessageToolbar(ConditionalContainer):

    def __init__(self, style=""):
        self.message = None
        self.text_control = FormattedTextControl(text="")
        super(MessageToolbar, self).__init__(
            content=Window(
                style=style, content=self.text_control,
                height=1
            ),
            filter=Condition(lambda: self.text)
        )

    @property
    def text(self):
        return self.text_control.text

    @text.setter
    def text(self, value):
        self.text_control.text = value


class InfoWindow(ConditionalContainer):

    def __init__(self, lexer_name='yaml'):
        self.buf = Buffer()
        self.buf.text = ''
        self.lexer = PygmentsLexer(find_lexer_class_by_name(lexer_name))
        self.window = HSplit([
            HorizontalLine(),
            Window(
                content=BufferControl(
                    buffer=self.buf, lexer=self.lexer)
            )
        ], height=Dimension(min=5, max=20, weight=1))
        super(InfoWindow, self).__init__(
            content=self.window,
            filter=has_focus(self)
        )

    def set_text(self, text):
        self.buf.text = text

    def get_text(self):
        return self.buf.text


class HelpWindow(ConditionalContainer):
    help_text = ''
    # help_text = """
    # <span fg='ansired'> Bindings: </span>

# ----------------------------------------------------
# /   Ctrl-e, Ctrl-down, Shift-down : Scroll Down     /
# /   Ctrl-y, Ctrl-up,   Shift-up   : Scroll up       /
# /   Ctrl-n, down                  : Next item       /
# /   Ctrl-p, up                    : Previous item   /
# /   Ctrl-q, Ctrl-c                : Quit            /
# /   Home                          : First item      /
# /   End                           : Last item       /
# ----------------------------------------------------
    # """

    def __init__(self):
        self.text_control = FormattedTextControl(
            text=HTML(self.help_text)
        )
        self.window = Window(
            content=self.text_control,
            always_hide_cursor=True,
            align=WindowAlign.LEFT
        )
        super(HelpWindow, self).__init__(
            content=self.window,
            filter=has_focus(self.window)
        )

    @property
    def text(self):
        return self.text_control.text

    @text.setter
    def text(self, value):
        self.text_control.text = value

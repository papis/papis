from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.formatted_text.html import HTML
from prompt_toolkit.layout import Dimension
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.widgets import HorizontalLine
from pygments.lexers import find_lexer_class_by_name

from .command_line_prompt import Command, CommandLinePrompt
from .options_list import Option, OptionsList

__all__ = [
    "Command",
    "CommandLinePrompt",
    "HelpWindow",
    "InfoWindow",
    "MessageToolbar",
    "Option",
    "OptionsList",
]


class MessageToolbar(ConditionalContainer):
    def __init__(self, style: str = "") -> None:
        self.message = None
        self.text_control = FormattedTextControl(text="")
        super().__init__(
            content=Window(
                style=style,
                content=self.text_control,
                height=1
            ),
            filter=Condition(lambda: bool(self.text_control.text))
        )

    @property
    def text(self) -> AnyFormattedText:
        return self.text_control.text

    @text.setter
    def text(self, value: AnyFormattedText) -> None:
        self.text_control.text = value


class InfoWindow(ConditionalContainer):
    def __init__(self, lexer_name: str = "yaml") -> None:
        self.buf = Buffer()
        self.buf.text = ""

        lexer = find_lexer_class_by_name(lexer_name)
        self.lexer = PygmentsLexer(lexer)   # type: ignore[arg-type]

        self.window = HSplit([
            HorizontalLine(),
            Window(
                content=BufferControl(buffer=self.buf, lexer=self.lexer)
            )
        ], height=Dimension(min=5, max=20, weight=1))
        super().__init__(
            content=self.window,
            filter=has_focus(self)
        )

    @property
    def text(self) -> str:
        return self.buf.text

    @text.setter
    def text(self, text: str) -> None:
        self.buf.text = text


class HelpWindow(ConditionalContainer):
    def __init__(self) -> None:
        self.text_control = FormattedTextControl(text=HTML(""))
        self.window = Window(
            content=self.text_control,
            always_hide_cursor=True,
            align=WindowAlign.LEFT
        )
        super().__init__(
            content=self.window,
            filter=has_focus(self.window)
        )

    @property
    def text(self) -> AnyFormattedText:
        return self.text_control.text

    @text.setter
    def text(self, value: AnyFormattedText) -> None:
        self.text_control.text = value

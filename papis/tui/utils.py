import re
from typing import Optional, List, Callable, Any


def confirm(prompt_string: str,
            yes: bool = True,
            bottom_toolbar: Optional[str] = None) -> bool:
    """Confirm with user input

    :param prompt_string: Question or text that the user gets.
    :param yes: If yes should be the default.
    :returns: True if go ahead, False if stop
    """
    result = prompt(prompt_string,
                    bottom_toolbar=bottom_toolbar,
                    default="Y/n" if yes else "y/N",
                    validator_function=lambda x: x in "YyNn",
                    dirty_message='Please, write either "y" or "n" to confirm')
    if yes:
        return result not in "Nn"
    return result in "Yy"


def text_area(title: str,
              text: str,
              lexer_name: str = "",
              height: int = 10,
              full_screen: bool = False) -> str:
    """
    Small implementation of an editor/pager for small pieces of text.

    :param title: Title of the text_area
    :param text: Editable text
    :param lexer_name: If the editable text should be highlighted with
        some kind of grammar, examples are ``yaml``, ``python`` ...
    :param height: Max height of the text area
    :param full_screen: Whether or not the text area should be full screen.
    """
    from prompt_toolkit import Application
    from prompt_toolkit.enums import EditingMode
    from prompt_toolkit.buffer import Buffer
    from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
    from prompt_toolkit.layout.controls import (
        BufferControl, FormattedTextControl
    )
    from prompt_toolkit.layout.layout import Layout
    from prompt_toolkit.utils import Event
    from prompt_toolkit.layout import Dimension
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.lexers import PygmentsLexer
    from pygments.lexers import find_lexer_class_by_name

    kb = KeyBindings()
    buffer1 = Buffer()
    buffer1.text = text

    @kb.add("c-q")  # type: ignore
    def exit_(event: Event) -> None:
        event.app.exit(0)

    @kb.add("c-s")  # type: ignore
    def save_(event: Event) -> None:
        event.app.return_text = buffer1.text

    class App(Application):  # type: ignore
        # TODO: add stubs to be able to remove type ignore above
        return_text = ""  # type: str

    text_height = Dimension(min=0, max=height) if height is not None else None

    import pygments
    from prompt_toolkit import print_formatted_text
    pygment_lexer = find_lexer_class_by_name(lexer_name)
    lexer = PygmentsLexer(pygment_lexer)
    tokens = list(pygments.lex(text, lexer=pygment_lexer()))
    from prompt_toolkit.formatted_text import PygmentsTokens
    # print_formatted_text(PygmentsTokens(tokens))
    # print(tokens)

    PAPIS_PYGMENTS_DEFAULT_STYLE = {
        "pygments.whitespace": "ansigray",
        "pygments.comment": "italic ansigreen",
        "pygments.comment.preproc": "noitalic ansiyellow",
        "pygments.keyword": "bold ansigreen",
        "pygments.keyword.pseudo": "nobold",
        "pygments.keyword.type": "nobold ansired",
        "pygments.operator": "ansigray",
        "pygments.operator.word": "bold ansimagenta",
        "pygments.name.builtin": "ansigreen",
        "pygments.name.function": "ansicyan",
        "pygments.name.class": "bold ansicyan",
        "pygments.name.namespace": "bold ansicyan",
        "pygments.name.exception": "bold ansired",
        "pygments.name.variable": "ansiblue",
        "pygments.name.constant": "ansired",
        "pygments.name.label": "ansigreen",
        "pygments.name.entity": "bold ansigray",
        "pygments.name.attribute": "ansigreen",
        "pygments.name.tag": "bold ansigreen",
        "pygments.name.decorator": "ansimagenta",
        # Note: In Pygments, Token.String is an alias for Token.Literal.String,
        #       and Token.Number as an alias for Token.Literal.Number.
        "pygments.literal.string": "ansired",
        "pygments.literal.string.doc": "italic",
        "pygments.literal.string.interpol": "bold ansired",
        "pygments.literal.string.escape": "bold ansired",
        "pygments.literal.string.regex": "ansired",
        "pygments.literal.string.symbol": "ansiblue",
        "pygments.literal.string.other": "ansigreen",
        "pygments.literal.number": "ansigray",
        "pygments.generic.heading": "bold ansiblue",
        "pygments.generic.subheading": "bold ansimagenta",
        "pygments.generic.deleted": "ansired",
        "pygments.generic.inserted": "ansigreen",
        "pygments.generic.error": "ansired",
        "pygments.generic.emph": "italic",
        "pygments.generic.strong": "bold",
        "pygments.generic.prompt": "bold ansiblue",
        "pygments.generic.output": "ansigray",
        "pygments.generic.traceback": "ansiblue",
        "pygments.error": "border:ansired",
    }

    from prompt_toolkit.styles import Style
    papis_style = Style.from_dict(PAPIS_PYGMENTS_DEFAULT_STYLE)
    # print_formatted_text(PygmentsTokens(tokens), style=style)
    print(tokens)
    # text_window = Window(height=text_height,
    #                      # style=style,
    #                      # content=BufferControl(buffer=buffer1, lexer=lexer))
    #                      content=FormattedTextControl(
    #                          text=PygmentsTokens(tokens), style=papis_style))

    root_container = HSplit([
        Window(
            align=WindowAlign.LEFT,
            style="bg:ansiwhite",
            height=1,
            content=FormattedTextControl(
                text=[("fg:ansiblack bg:ansiwhite", title)]
            ),
            always_hide_cursor=True
        ),

        Window(
            align=WindowAlign.LEFT,
            # style="bg:ansiwhite",
            height=text_height,
            style=papis_style,
            content=FormattedTextControl(
                text=PygmentsTokens(tokens),
            ),
            always_hide_cursor=True
        ),

        # print_formatted_text(PygmentsTokens(tokens), style=style),

        # Window(
        #     height=1,
        #     width=None,
        #     align=WindowAlign.LEFT,
        #     style="bg:ansiwhite",
        #     content=FormattedTextControl(
        #         text=[(
        #             "fg:ansiblack bg:ansiwhite",
        #             "Quit [Ctrl-q]  Save [Ctrl-s]"
        #         )]
        #     )
        # ),
    ])

    layout = Layout(root_container)

    # layout.focus(text_window)

    app = App(editing_mode=EditingMode.EMACS,
              layout=layout,
              key_bindings=kb,
              full_screen=full_screen)
    app.run()
    return app.return_text


def yes_no_dialog(title: str, text: str) -> Any:
    from prompt_toolkit.shortcuts import yes_no_dialog
    from prompt_toolkit.styles import Style

    example_style = Style.from_dict({
        "dialog": "bg:#88ff88",
        "dialog frame-label": "bg:#ffffff #000000",
        "dialog.body": "bg:#000000 #00ff00",
        "dialog shadow": "bg:#00aa00",
    })

    return yes_no_dialog(title=title, text=text, style=example_style)


def prompt(
        prompt_string: str,
        default: str = "",
        bottom_toolbar: Optional[str] = None,
        multiline: bool = False,
        validator_function: Optional[Callable[[str], bool]] = None,
        dirty_message: str = "") -> str:
    """Prompt user for input

    :param prompt_string: Question or text that the user gets.
    :param default: Default value to give if the user does not input anything
    :returns: User input or default
    """
    import prompt_toolkit
    import prompt_toolkit.validation
    if validator_function is not None:
        validator = prompt_toolkit.validation.Validator.from_callable(
            validator_function,
            error_message=dirty_message,
            move_cursor_to_end=True
        )
    else:
        validator = None

    fragments = [
        ("", prompt_string),
        ("fg:ansired", " ({0})".format(default)),
        ("", ": "),
    ]

    result = prompt_toolkit.prompt(fragments,
                                   validator=validator,
                                   multiline=multiline,
                                   bottom_toolbar=bottom_toolbar,
                                   validate_while_typing=True)

    return result or default


def get_range(range_str: str) -> List[int]:
    range_regex = re.compile(r"(\d+)-?(\d+)?")
    try:
        return sum([
            list(range(int(p[0]), int(p[1] if p[1] else p[0]) + 1))
            for p in range_regex.findall(range_str)], [])
    except ValueError:
        return []


def select_range(options: List[Any],
                 message: str,
                 accept_none: bool = False,
                 bottom_toolbar: Optional[str] = None) -> List[int]:
    for i, o in enumerate(options):
        print("{i}. {o}".format(i=i, o=o))

    possible_indices = range(len(options))
    all_keywords = ["all", "a"]
    none_keywords = ["n", "none"]
    valid_keywords = all_keywords + (none_keywords if accept_none else [])

    if not options:
        return []

    selection = prompt(
        prompt_string=message,
        default="",
        bottom_toolbar=bottom_toolbar,
        dirty_message="Range not valid, example: "
                      "0, 2, 3-10, {}, ...".format(", ".join(valid_keywords)),
        validator_function=lambda string:
                string in valid_keywords
                or len(set(get_range(string)) & set(possible_indices)) > 0)

    if selection in all_keywords:
        selection = ",".join(map(str, range(len(options))))

    if selection in none_keywords:
        return []

    return [i for i in get_range(selection) if i in possible_indices]

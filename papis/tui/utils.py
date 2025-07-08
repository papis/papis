import re
from typing import Optional, List, Callable, Any, Iterable

import click

from papis.api import T


# Highlighting style used by pygments. This is a copy of the prompt_toolkit
# default style, but changed to use ansi colors.
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
    # NOTE: In Pygments, Token.String is an alias for Token.Literal.String,
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


def text_area(text: str,
              title: str = "",
              lexer_name: str = "") -> None:
    """
    Small implementation of a pager for small pieces of text.

    :param text: main text to be displayed.
    :param title: a title for the text.
    :param lexer_name: a pygments lexer name (e.g. ``yaml``, ``python``) if the
        text should be highlighted.
    """
    from pygments.lexers import find_lexer_class_by_name

    pygment_lexer = find_lexer_class_by_name(lexer_name)

    from prompt_toolkit.lexers import PygmentsLexer
    from prompt_toolkit.shortcuts import print_container
    from prompt_toolkit.styles import Style
    from prompt_toolkit.widgets import Frame, TextArea

    papis_style = Style.from_dict(PAPIS_PYGMENTS_DEFAULT_STYLE)
    print_container(
        Frame(
            TextArea(
                text=text,
                lexer=PygmentsLexer(pygment_lexer),  # type: ignore[arg-type]
            ),
            title=title,
        ),
        style=papis_style,
    )


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
        ("fg:ansired", f" ({default})"),
        ("", ": "),
    ]

    result = prompt_toolkit.prompt(fragments,       # type: ignore[arg-type]
                                   validator=validator,
                                   multiline=multiline,
                                   bottom_toolbar=bottom_toolbar,
                                   validate_while_typing=True)

    return result or default


def progress_bar(iterable: Iterable[T]) -> Iterable[T]:
    from prompt_toolkit.styles import Style
    from prompt_toolkit.shortcuts import ProgressBar
    from prompt_toolkit.shortcuts.progress_bar import formatters

    # NOTE: this style is chosen to make it look like the default tqdm bar
    style = Style.from_dict({"bar-a": "reverse"})
    fmt = [
        formatters.Percentage(),
        formatters.Bar(start="|", end="|", sym_a=" ", sym_b=" ", sym_c=" "),
        formatters.Text(" "),
        formatters.Progress(),
        formatters.Text(" ["),
        formatters.TimeElapsed(),
        formatters.Text("<"),
        formatters.TimeLeft(),
        formatters.Text(", "),
        formatters.IterationsPerSecond(),
        formatters.Text(" it/s]"),
        formatters.Text("  "),
    ]

    with ProgressBar(style=style, formatters=fmt) as pb:
        yield from pb(iterable)


def get_range(range_str: str) -> List[int]:
    from itertools import chain

    range_regex = re.compile(r"(\d+)-?(\d+)?")
    try:
        return list(chain.from_iterable(
            range(int(p[0]), int(p[1] if p[1] else p[0]) + 1)
            for p in range_regex.findall(range_str)))
    except ValueError:
        return []


def select_range(options: List[Any],
                 message: str,
                 accept_none: bool = False,
                 bottom_toolbar: Optional[str] = None) -> List[int]:
    for i, o in enumerate(options):
        click.echo(f"{i}. {o}")

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

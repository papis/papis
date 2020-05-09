import difflib
from prompt_toolkit import Application, print_formatted_text
from prompt_toolkit.utils import Event
from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings

from typing import (  # noqa: ignore
    Dict, Any, List, Union, NamedTuple, Callable, Sequence)

Action = NamedTuple('Action',
                    [
                        ('name', str),
                        ('key', str),
                        ('action', Callable[[Event], None])
                    ])


def prompt(text: Union[str, FormattedText],
           title: str = '',
           actions: List[Action] = [],
           **kwargs: Any
           ) -> None:
    """A simple and extensible prompt helper routine

    :param text: Text to be printed before the prompt, it can be formatted text
    :type  text: str or FormattedText
    :param title: Title to be shown in a bottom bar
    :type  title: str
    :param actions: A list of Actions as defined in `Action`.
    :type  actions: [Action]
    :param kwargs: kwargs to prompt_toolkit application class
    """
    assert(isinstance(actions, list))
    assert(type(title) == str)

    kb = KeyBindings()

    for action in actions:
        kb.add(action.key)(action.action)

    print_formatted_text(FormattedText(text))

    root_container = HSplit([

        Window(
            wrap_lines=True,
            height=1,
            align=WindowAlign.LEFT,
            always_hide_cursor=True,
            style='bg:ansiblack fg:ansiwhite',
            content=FormattedTextControl(
                focusable=False,
                text=HTML(' '.join(
                    "{a.name}<yellow>[{a.key}]</yellow>".format(a=a)
                    for a in actions
                ))
            )
        )] +
        ([
            Window(
                height=1, align=WindowAlign.LEFT,
                always_hide_cursor=True,
                style='bold fg:ansipurple bg:ansiwhite',
                content=FormattedTextControl(focusable=False, text=title))
        ] if title else [])
    )

    app = Application(
        layout=Layout(root_container),
        key_bindings=kb,
        **kwargs)
    app.run()


def diffshow(texta: str,
             textb: str,
             title: str = '',
             namea: str = 'a',
             nameb: str = 'b',
             actions: List[Action] = []
             ) -> None:
    """Show the difference of texta and textb with a prompt.

    :param texta: From text
    :type  texta: str
    :param textb: To text
    :type  textb: str
    """
    assert(isinstance(actions, list))
    assert(isinstance(texta, str))
    assert(isinstance(textb, str))

    # diffs = difflib.unified_diff(
    #         str(texta).splitlines(keepends=True),
    #         str(textb).splitlines(keepends=True),
    #         fromfile=namea, tofile=nameb)

    diffs = difflib.ndiff(
            str(texta).splitlines(keepends=True),
            str(textb).splitlines(keepends=True),)

    _diffs = list(diffs)
    if len(_diffs) == 1:
        # this means that _diffs is just a new line character, so there is
        # no real difference, in that case then do not instantiate a prompt
        return

    raw_text = _diffs + [
        "^^^^^^^^^\ndiff from\n",
        "----- {namea}\n".format(namea=namea),
        "+++++ {nameb}\n".format(nameb=nameb),
    ]  # type: Sequence[str]

    formatted_text = list(map(
        lambda line:
            # match line values
            line.startswith('@') and ('fg:violet bg:ansiblack', line) or
            line.startswith('+') and ('fg:ansigreen bg:ansiblack', line) or
            line.startswith('-') and ('fg:ansired bg:ansiblack', line) or
            line.startswith('?') and ('fg:ansiyellow bg:ansiblack', line) or
            line.startswith('^^^') and ('bg:ansiblack fg:ansipurple', line) or
            ('fg:ansiwhite', line), raw_text))

    prompt(title=title,
           text=formatted_text,
           actions=actions)


def diffdict(dicta: Dict[str, Any],
             dictb: Dict[str, Any],
             namea: str = 'a',
             nameb: str = 'b'
             ) -> Dict[str, Any]:
    """
    Compute the difference of two dictionaries.

    :param dicta: Base dictionary
    :type  dicta: dict
    :param dictb: Dictionary with the differences that the result might add
    :type  dictb: dict
    :param namea: Label to be shown for dictionary a
    :type  namea: str
    :param namea: Label to be shown for dictionary b
    :type  namea: str
    :returns: A dictionary containig the base data of dicta plus data
        from dictb if this was chosen.
    :rtype:  return_type
    """

    rdict = dict()

    options = {
        "add": False,
        "reject": False,
        "split": False,
        "quit": False,
        "add_all": False,
        "cancel": False,
    }  # type: Dict[str, bool]

    def reset() -> None:
        for k in options:
            options[k] = False

    def oset(event: Event, option: str, value: bool) -> None:
        options[option] = value
        event.app.exit(0)

    actions = [
        Action(
            name='Add all',
            key='a', action=lambda e: oset(e, "add_all", True)),
        Action(
            name='Split', key='s', action=lambda e: oset(e, "split", True)),
        Action(
            name='Reject', key='n', action=lambda e: oset(e, "reject", True)),
        Action(
            name='Quit', key='q', action=lambda e: oset(e, "quit", True)),
        Action(
            name='Cancel', key='c', action=lambda e: oset(e, "cancel", True)),
    ]

    keys = [k for k in sorted(set(dicta) | set(dictb))
            if not dicta.get(k) == dictb.get(k) and dictb.get(k)]

    texta = "\n".join(
            "{k}: {v}".format(k=k, v=dicta.get(k, '')) for k in sorted(keys)
            ) + "\n"
    textb = "\n".join(
            "{k}: {v}".format(k=k, v=dictb.get(k, '')) for k in sorted(keys)
            ) + "\n"

    diffshow(
        texta=texta, textb=textb,
        title='GENERAL DIFFERENCE',
        namea=namea,
        nameb=nameb,
        actions=actions)

    if options["cancel"] or options['quit']:
        return dict()
    elif options["add_all"]:
        rdict.update(dicta)
        rdict.update(dictb)
        return rdict
    elif options["split"]:
        reset()

    actions = [
        Action(name='Add', key='y', action=lambda e: oset(e, "add", True)),
    ] + actions

    for key in keys:

        if options["add_all"]:
            rdict[key] = dictb.get(key, dicta.get(key))
            continue

        diffshow(
            texta=str(dicta.get(key, '')) + "\n",
            textb=str(dictb.get(key, '')) + "\n",
            title='Key: {0}'.format(key),
            namea=namea,
            nameb=nameb,
            actions=actions)

        if options["cancel"]:
            return dict()
        elif options["add"]:
            rdict[key] = dictb.get(key, dicta.get(key))
        elif options["quit"]:
            break

        if not options["add_all"]:
            reset()

    return rdict

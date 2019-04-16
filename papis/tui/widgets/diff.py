import difflib
import collections
import prompt_toolkit
from prompt_toolkit import Application
from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings


Action = collections.namedtuple('Action', ['name', 'key', 'action'])


def prompt(text, title='', actions=[], **kwargs):
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

    prompt_toolkit.print_formatted_text(FormattedText(text))

    root_container = HSplit([

        Window(
            wrap_lines=True,
            height=1,
            align=WindowAlign.LEFT,
            always_hide_cursor=True,
            style='bg:ansiblack',
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
                always_hide_cursor=True, style='fg:ansiblack bg:ansiwhite',
                content=FormattedTextControl(focusable=False, text=title))
        ] if title else [])
    )

    Application(
        layout=Layout(root_container),
        key_bindings=kb,
        **kwargs).run()


def diffshow(texta, textb, title='', namea='a', nameb='b', actions=[]):
    """Show the difference of texta and textb with a prompt.

    :param texta: From text
    :type  texta: str
    :param textb: To text
    :type  textb: str
    """
    assert(isinstance(actions, list))
    assert(isinstance(texta, str))
    assert(isinstance(textb, str))

    diffs = difflib.unified_diff(
            str(texta).splitlines(keepends=True),
            str(textb).splitlines(keepends=True),
            fromfile=namea, tofile=nameb)

    formatted_text = list(map(lambda line:
        line.startswith('@') and ('fg:violet', line) or
        line.startswith('+') and ('fg:ansigreen', line) or
        line.startswith('-') and ('fg:ansired', line) or
        line.startswith('?') and ('fg:ansiyellow', line) or
        ('fg:ansiwhite', line), diffs))

    prompt(
        title=title,
        text=formatted_text,
        actions=actions)


def diffdict(dicta, dictb, namea='a', nameb='b'):

    rdict = dict()

    options = {
        "add": False,
        "reject": False,
        "split": False,
        "quit": False,
        "add_all": False,
        "cancel": False,
    }

    def reset():
        for k in options:
            options[k] = False

    def oset(event, option, value):
        options[option] = value
        event.app.exit(0)

    actions = [
        Action(
            name='Add all', key='a', action=lambda e: oset(e, "add_all", True)),
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
            "{k}: {v}".format(k=k, v=dicta.get(k, '')) for k in sorted(keys))
    textb = "\n".join(
            "{k}: {v}".format(k=k, v=dictb.get(k, '')) for k in sorted(keys))

    diffshow(
        texta=texta, textb=textb,
        title='GENERAL DIFFERENCE',
        namea=namea, nameb=nameb, actions=actions)

    if options["cancel"] or options['quit']:
        return dict()
    elif options["add_all"]:
        rdict.update(dicta)
        rdict.update(dictb)
        return rdict
    elif options["split"]:
        reset()

    actions = [
        Action(
            name='Add', key='y', action=lambda e: oset(e, "add", True)),
    ] + actions

    for key in keys:

        if options["add_all"]:
            rdict[key] = dictb.get(key, dicta.get(key))
            continue

        diffshow(
            texta=str(dicta.get(key, '')), textb=str(dictb.get(key, '')),
            title='Key: {0}'.format(key),
            namea=namea, nameb=nameb, actions=actions)

        if options["cancel"]:
            return dict()
        elif options["add"]:
            rdict[key] = dictb.get(key, dicta.get(key))
        elif options["quit"]:
            break

        if not options["add_all"]:
            reset()

    return rdict

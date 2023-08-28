from typing import (
    Dict, Any, List, Tuple, NamedTuple, Callable, Optional)

from prompt_toolkit import Application, print_formatted_text
from prompt_toolkit.layout.containers import HSplit, Window, WindowAlign
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent

# Needed for diffmerge
import ast


class Action(NamedTuple):
    name: str
    key: str
    action: Callable[[KeyPressEvent], None]


def prompt(text,
           title: str = "",
           actions: Optional[List[Action]] = None,
           **kwargs: Any
           ) -> None:
    """A simple and extensible prompt helper routine

    :param text: Text to be printed before the prompt, it can be formatted text
    :param title: Title to be shown in a bottom bar
    :param actions: A list of Actions as defined in `Action`.
    :param kwargs: kwargs to prompt_toolkit application class
    """
    if not isinstance(text, FormattedText):
        text = FormattedText([("", text)])

    if actions is None:
        actions = []

    assert isinstance(actions, list)
    assert isinstance(title, str)

    kb = KeyBindings()

    for action in actions:
        kb.add(action.key)(action.action)

    print_formatted_text(text)

    action_texts = []
    for a in actions:
        action_texts.append(("", a.name))
        action_texts.append(("fg:ansiyellow", "[" + a.key + "] "))

    root_container = HSplit([
        Window(
            wrap_lines=True,
            height=1,
            align=WindowAlign.LEFT,
            always_hide_cursor=True,
            style="bg:ansiblack",
            content=FormattedTextControl(
                focusable=False,
                text=FormattedText(action_texts)
            )
        )]
        + ([
            Window(
                height=1, align=WindowAlign.LEFT,
                always_hide_cursor=True,
                style="bold",
                content=FormattedTextControl(focusable=False, text=title))
        ] if title else [])
    )

    app: Application[Any] = Application(
        layout=Layout(root_container),
        key_bindings=kb,
        **kwargs)
    app.run()


def diffshow(texta: str,
             textb: str,
             title: str = "",
             namea: str = "a",
             nameb: str = "b",
             actions: Optional[List[Action]] = None
             ) -> None:
    """Show the difference of texta and textb with a prompt.

    :param texta: From text
    :param textb: To text
    """
    if actions is None:
        actions = []

    assert isinstance(actions, list)
    assert isinstance(texta, str)
    assert isinstance(textb, str)

    import difflib
    # diffs = difflib.unified_diff(
    #         str(texta).splitlines(keepends=True),
    #         str(textb).splitlines(keepends=True),
    #         fromfile=namea, tofile=nameb)

    diffs = difflib.ndiff(
        texta.splitlines(keepends=True),
        textb.splitlines(keepends=True),)

    _diffs = list(diffs)
    if len(_diffs) == 1:
        # this means that _diffs is just a new line character, so there is
        # no real difference, in that case then do not instantiate a prompt
        return

    raw_text = _diffs + [
        "^^^^^^^^^\ndiff from\n",
        f"----- {namea}\n",
        f"+++++ {nameb}\n",
    ]

    formatted_text = FormattedText([
        line.startswith("@") and ("fg:ansimagenta bg:ansiblack", line)
        or line.startswith("+") and ("fg:ansigreen bg:ansiblack", line)
        or line.startswith("-") and ("fg:ansired bg:ansiblack", line)
        or line.startswith("?") and ("fg:ansiyellow bg:ansiblack", line)
        or line.startswith("^^^") and ("bg:ansiblack fg:ansimagenta", line)
        or ("", line)
        for line in raw_text
    ])

    prompt(title="--- Diff view: " + title + " ---",
           text=formatted_text,
           actions=actions)


def diffdict(dicta: Dict[str, Any],
             dictb: Dict[str, Any],
             namea: str = "a",
             nameb: str = "b"
             ) -> Dict[str, Any]:
    """
    Compute the difference of two dictionaries.

    :param dicta: Base dictionary
    :param dictb: Dictionary with the differences that the result might add
    :param namea: Label to be shown for dictionary a
    :param namea: Label to be shown for dictionary b
    :returns: A dictionary containing the base data of dicta plus data
        from dictb if this was chosen.
    """

    rdict = {}

    options = {
        "add": False,
        "reject": False,
        "split": False,
        "quit": False,
        "add_all": False,
        "cancel": False,
    }

    def reset() -> None:
        for k in options:
            options[k] = False

    def oset(event: KeyPressEvent, option: str, value: bool) -> None:
        options[option] = value
        event.app.exit(result=0)

    actions = [
        Action(
            name="Add all",
            key="a", action=lambda e: oset(e, "add_all", True)),
        Action(
            name="Split",
            key="s", action=lambda e: oset(e, "split", True)),
        Action(
            name="Reject",
            key="n", action=lambda e: oset(e, "reject", True)),
        Action(
            name="Quit",
            key="q", action=lambda e: oset(e, "quit", True)),
        Action(
            name="Cancel",
            key="c", action=lambda e: oset(e, "cancel", True)),
    ]

    keys = [k for k in sorted(set(dicta) | set(dictb))
            if not dicta.get(k) == dictb.get(k) and dictb.get(k)]

    texta = "\n".join(
        "{k}: {v}".format(k=k, v=dicta.get(k, "")) for k in sorted(keys)
        ) + "\n"
    textb = "\n".join(
        "{k}: {v}".format(k=k, v=dictb.get(k, "")) for k in sorted(keys)
        ) + "\n"

    diffshow(
        texta=texta, textb=textb,
        title="all changes",
        namea=namea,
        nameb=nameb,
        actions=actions)

    if options["cancel"] or options["quit"]:
        return {}
    elif options["add_all"]:
        rdict.update(dicta)
        rdict.update(dictb)
        return rdict
    elif options["split"]:
        reset()

    actions = [
        Action(name="Add", key="y", action=lambda e: oset(e, "add", True)),
    ] + actions

    for key in keys:

        if options["add_all"]:
            rdict[key] = dictb.get(key, dicta.get(key))
            continue

        diffshow(
            texta=str(dicta.get(key, "")) + "\n",
            textb=str(dictb.get(key, "")) + "\n",
            title=f'changes for key "{key}"',
            namea=namea,
            nameb=nameb,
            actions=actions)

        if options["cancel"]:
            return {}
        elif options["add"]:
            rdict[key] = dictb.get(key, dicta.get(key))
        elif options["quit"]:
            break

        if not options["add_all"]:
            reset()

    return rdict


# Maybe we could set user settings to choose the colors...
def diffmerge_format_text(key: str,
                          value: str,
                          idx: int,
                          defval: int,
                          alt_color: Optional[str] = None,
                          ) -> Tuple[str, str]:
    """
    Set the text color for diffmerge.
    """
    if idx == defval:
        text = "+ " + key + ": " + value + "\n"
        if alt_color:
            color = "fg:ansi{} bg:ansiblack".format(alt_color)
        else:
            color = "fg:ansigreen bg:ansiblack"
    else:
        text = "- " + key + ": " + value + "\n"
        color = "fg:ansired bg:ansiblack"

    return (color, text)


def diffmerge_add_all(merged: Dict[str, Any], merge_opt: str) -> Dict[str, Any]:
    rdict = {}

    # Select the default value if multiple key values
    for key, value in list(merged.items()):
        if merge_opt == "last":
            defval = len(value) - 1
        try:
            rdict[key] = merged[key][defval]
        except Exception:
            rdict[key] = merged[key][0]

        # Rebuild list/int from string
        try:
            rdict[key] = ast.literal_eval(rdict[key])
        except Exception:
            pass

    return rdict


def diffmerge(merged: Dict[str, Any], merge_opt: str, batch: bool) -> Dict[str, Any]:
    """
    Like diffdict, but handles a unique dictionary instead of the diff
    between two files.

    Used when --merge-data is set.

    :param merged: dictionary merging all importers data
    :param merged_opt: the default value to select when multiples
                       values are available for a dict.key ('first' or 'last')
    :param batch: when --batch option is set, set rdict to its default value
                  without asking the user to confirm/pick values
    :returns: The dictionary used to create the entry
    """

    rdict = {}

    if batch:
        return diffmerge_add_all(merged, merge_opt)

    options = {
        "add": False,
        "reject": False,
        "pick": False,
        "quit": False,
        "add_all": False,
        "cancel": False,
    }  # type: Dict[str, bool]

    def reset() -> None:
        for k in options:
            options[k] = False

    def oset(event: KeyPressEvent, option: str, value: bool) -> None:
        options[option] = value
        event.app.exit(result=0)

    actions = [
        Action(
            name="Add all",
            key="a", action=lambda e: oset(e, "add_all", True)),
        Action(
            name="Pick", key="p", action=lambda e: oset(e, "pick", True)),
        Action(
            name="Reject", key="n", action=lambda e: oset(e, "reject", True)),
        Action(
            name="Quit", key="q", action=lambda e: oset(e, "quit", True)),
        Action(
            name="Cancel", key="c", action=lambda e: oset(e, "cancel", True)),
    ]

    show_all = []
    for key, value in list(merged.items()):
        if merge_opt == "last":
            defval = len(value)
        else:
            defval = 1

        for i, v in enumerate(value, start=1):
            show_all.append(diffmerge_format_text(key, v, i, defval))

    prompt(title="--- Merge view: " + " ---",
           text=show_all,
           actions=actions)

    if options["cancel"] or options["quit"]:
        return {}
    elif options["add_all"]:
        return diffmerge_add_all(merged, merge_opt)
    elif options["pick"]:
        reset()

    actions = [
        Action(name="Add", key="y", action=lambda e: oset(e, "add", True)),
    ] + actions

    for key, value in list(merged.items()):
        if merge_opt == "last":
            defval = len(value)
        else:
            defval = 1

        if options["add_all"]:
            for i, v in enumerate(value, start=1):
                if i == defval:
                    rdict[key] = v
            continue

        for i, v in enumerate(value, start=1):
            options["add"] = False
            options["reject"] = False

            # Show: 1) the values saved is rdict
            show_selected = []
            for rk, rv in list(rdict.items()):
                show_selected.append(diffmerge_format_text(rk, rv, i, i))
            # 2) the new value to add or reject
            show_selected.append(diffmerge_format_text(key, v, i, defval, "yellow"))

            prompt(title="--- Pick fields values : " + " ---",
                   text=show_selected,
                   actions=actions)

            if options["cancel"]:
                return {}
            elif options["add"]:
                rdict[key] = v
                show_selected.pop()
            elif options["reject"]:
                show_selected.pop()

        if options["quit"]:
            break

        if not options["add_all"]:
            reset()

    # Rebuild list/int from string
    for key in rdict:
        try:
            rdict[key] = ast.literal_eval(rdict[key])
        except Exception:
            pass

    return rdict

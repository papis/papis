import sys

try:
    import dmenu
except:
    print('You don\'t have dmenu for python, try pip3 install dmenu')
    sys.exit(1)

import papis.api
import papis.utils
import functools


_dmenu_pick = functools.partial(
    dmenu.show,
    case_insensitive=papis.config.getboolean(
        'case_insensitive', section="dmenu-gui"
    ),
    lines=papis.config.getint('lines', section='dmenu-gui'),
    bottom=papis.config.getboolean('bottom', section='dmenu-gui'),
    font=papis.config.get('font', section='dmenu-gui'),
    background=papis.config.get('background', section='dmenu-gui'),
    foreground=papis.config.get('foreground', section='dmenu-gui'),
    background_selected=papis.config.get(
        'background_selected', section='dmenu-gui'
    ),
    foreground_selected=papis.config.get(
        'foreground_selected', section='dmenu-gui'
    )
)


def pick(options, header_filter=None, body_filter=None, match_filter=None):
    if header_filter is None:
        fmt = papis.config.get('header-format', section='dmenu-gui')
        if fmt is None:
            fmt = papis.config.get('header-format')

        def header_filter(x):
            return papis.utils.format_doc(fmt, x)
    if len(options) == 1:
        index = 0
    else:
        headers = [header_filter(o) for o in options]
        header = _dmenu_pick(headers)
        if not header:
            return None
        index = headers.index(header)
    return options[index]

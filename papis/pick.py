import logging
import papis.config
from papis.tui.app import Picker as PapisPicker
logger = logging.getLogger("pick")


class Picker:
    """
    Main class for pickers, all possible pickers should follow this example
    and subclass it.

    """
    def __init__(
            self, options, default_index=0,
            header_filter=lambda x: x, match_filter=lambda x: x
            ):
        self.options = options
        self.default_index = default_index
        self.header_filter = header_filter
        self.match_filter = match_filter

    def __call__(self):
        if len(self.options) == 0:
            return ""
        if len(self.options) == 1:
            return self.options[0]

        picker = PapisPicker(
            self.options,
            self.default_index,
            self.header_filter,
            self.match_filter
        )
        picker.run()
        return picker.options_list.get_selection()


_PICKERS = {
    "papis.pick": Picker
}


def pick(
        options,
        default_index=0,
        header_filter=lambda x: x,
        match_filter=lambda x: x
        ):
    """Construct and start a :class:`Picker <Picker>`.
    """
    name = papis.config.get("picktool")
    try:
        picker = get_picker(name)
    except KeyError:
        logger.exception("I don't know how to use the picker '%s'" % name)
    else:
        return picker(
            options,
            default_index=default_index,
            header_filter=header_filter,
            match_filter=match_filter
        )()


def register_picker(name, picker):
    global _PICKERS
    _PICKERS[name] = picker


def get_picker(name):
    """Get a registered picker

    :param name: Name of the picker
    :type  name: Picker
    :returns: Picker
    :rtype:  Picker
    :raises KeyError: Whenever the picker is not found
    """
    global _PICKERS
    return _PICKERS[name]

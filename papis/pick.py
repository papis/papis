from papis.tui import Picker

def pick(
        options,
        title="Pick: ",
        indicator='>',
        default_index=0,
        header_filter=lambda x: x,
        match_filter=lambda x: x
        ):
    """Construct and start a :class:`Picker <Picker>`.
    """

    if len(options) == 0:
        return ""
    if len(options) == 1:
        return options[0]

    picker = Picker(
        options,
        title,
        indicator,
        default_index,
        header_filter,
        match_filter
    )
    picker.run()
    return picker.options_list.get_selection()

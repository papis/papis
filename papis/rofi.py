import rofi
import papis.utils
import papis.config


def pick(
        options,
        header_filter=lambda x: x,
        body_filter=None,
        match_filter=lambda x: x
        ):
    if len(options) == 1:
        index = 0
    else:
        r = rofi.Rofi()
        index, no_idea = r.select(
            "Select: ",
            [
                header_filter(d) for d in
                options
            ]
        )
        r.close()
    return options[index]



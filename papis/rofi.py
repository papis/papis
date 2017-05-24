import rofi
import papis.utils
import papis.config

def get_options():
    options = dict()
    try:
        options["fullscreen"] = papis.config.get("rofi-fullscreen")
    except:
        options["fullscreen"] = False
    try:
        options["width"] = papis.config.get("rofi-width")
    except:
        options["width"] = 80
    return options

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
        index, key = r.select(
            "Select: ",
            [
                header_filter(d) for d in
                options
            ],
            xcase_sensitive=False,
            **get_options()
        )
        r.close()
    return options[index]



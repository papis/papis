import rofi
import papis.utils
import papis.config


def get_header_format():
    return papis.config.get_header_format(
        "rofi-header_format"
    ).replace("\\\\", "\r").replace("\\t", "\t")


def get_options():
    options = dict()
    try:
        options["fullscreen"] = papis.config.getboolean("rofi-fullscreen")
    except:
        options["fullscreen"] = False
    try:
        options["case_sensitive"] =\
            papis.config.getboolean("rofi-case_sensitive")
    except:
        options["case_sensitive"] = False
    try:
        options["width"] = papis.config.getint("rofi-width")
    except:
        options["width"] = 80
    try:
        options["eh"] = papis.config.getint("rofi-eh")
    except:
        options["eh"] = 1
    try:
        options["sep"] = papis.config.get("rofi-sep")
    except:
        options["sep"] = "|"
    try:
        options["lines"] = papis.config.getint("rofi-lines")
    except:
        options["lines"] = 20
    try:
        options["fixed_lines"] = papis.config.getint("rofi-fixed-lines")
    except:
        options["fixed_lines"] = 20
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
            **get_options()
        )
        r.close()
    return options[index]



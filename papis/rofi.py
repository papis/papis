import rofi
import papis.utils
import papis.config


def get_header_format(section=None):
    args = []
    if section:
        args = [section, "rofi-header_format"]
    else:
        args = ["rofi-header_format"]

    return papis.config.get(
        *args
    )


def get_options(section=None):
    options = dict()
    def args(section, arg):
        return [section, arg] if section is not None else [arg]
    for key in ["fullscreen",
            "normal_window", "multi_select", "case_sensitive", "markup_rows"]:
        try:
            options[key] =\
                papis.config.getboolean(*args( section, "rofi-"+key ))
        except:
            options[key] = False
    try:
        options["width"] = papis.config.getint(*args( section, "rofi-width" ))
    except:
        options["width"] = 80
    try:
        options["eh"] = papis.config.getint(*args( section, "rofi-eh" ))
    except:
        options["eh"] = 1
    try:
        options["sep"] = papis.config.get(*args( section, "rofi-sep" ))
    except:
        options["sep"] = "|"
    try:
        options["lines"] = papis.config.getint(*args( section, "rofi-lines" ))
    except:
        options["lines"] = 20
    try:
        options["fixed_lines"] = papis.config.getint(*args( section, "rofi-fixed-lines" ))
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
        indices = 0
    else:
        r = rofi.Rofi()
        indices, key = r.select(
            "Select: ",
            [
                header_filter(d) for d in
                options
            ],
            **get_options()
        )
        r.close()
    # TODO: Support multiple choice
    if not isinstance(indices, list):
        indices = [indices]
    return options[indices[0]]

class Gui(object):

    esc_key = -1
    open_key = 0
    quit_key = 1
    edit_key = 2
    delete_key = 3
    help_key = 4
    open_stay_key = 5
    normal_widnow_key = 6

    def __init__(self):
        self.documents = []
        self.help_message = ""
        self.keys = self.get_keys()
        self.window = None

    def get_help(self):
        space = " "*10
        message = \
"Rofi based gui for papis\n"\
"========================\n".format(space)
        for k in self.keys:
            message += "%s%s%s\n" % (self.keys[k][0], space, self.keys[k][1])
        return message

    def get_key(self, key, default=""):
        try:
            return papis.config.get("rofi-gui", "key-" + key.lower())
        except:
            return default

    def get_keys(self):
        return {
            "key%s" % self.quit_key: (
                self.get_key('quit', 'Alt+q'),
                'Quit'
            ),
            "key%s" % self.edit_key: (
                self.get_key('edit', 'Alt+e'),
                'Edit'
            ),
            "key%s" % self.delete_key: (
                self.get_key('delete', 'Alt+d'),
                'Delete'
            ),
            "key%s" % self.help_key: (
                self.get_key('help', 'Alt+h'),
                'Help'
            ),
            "key%s" % self.open_stay_key: (
                self.get_key('open-stay', 'Alt+o'),
                'Help'
            ),
            "key%s" % self.normal_widnow_key: (
                self.get_key('normal-window', 'Alt+w'),
                'Normal Win'
            ),
            "key%s" % self.open_key: (
                self.get_key('open', 'Enter'),
                'Open'
            )
        }


    def main(self, documents):
        # Set default picker
        self.documents = documents
        key = None
        indices = None
        options = get_options("rofi-gui")
        header_format = get_header_format("rofi-gui")
        header_filter = lambda x: header_format.format(doc=x)
        self.help_message = self.get_help()
        options.update(self.keys)
        # Initialize window
        self.window = rofi.Rofi()
        while not (key == self.quit_key or key == self.esc_key):
            indices, key = self.window.select( "Select: ",
                [
                    header_filter(d) for d in
                    self.documents
                ],
                select=indices,
                **options
            )
            if not isinstance(indices, list):
                indices = [indices]
            if key == self.edit_key:
                for i in indices:
                    self.edit(self.documents[i])
            elif key in [self.open_key, self.open_stay_key]:
                for i in indices:
                    self.open(self.documents[i])
                options["normal_window"] ^= True
                if key == self.open_key:
                    return 0
            elif key == self.delete_key:
                for i in indices:
                    self.delete(self.documents[i])
            elif key == self.help_key:
                self.window.error(self.help_message)
            elif key == self.normal_widnow_key:
                options["normal_window"] ^= True

    def delete(self, doc):
        answer = self.window.text_entry(
            "Are you sure? (y/N)",
            message="<b>Be careful!</b>"
        )
        if answer and answer in "Yy":
            doc.rm()
            self.documents = self.fetch_documents()

    def open(self, doc):
        papis.utils.open_file(
            doc.get_files()
        )

    def edit(self, doc):
        papis.utils.general_open(
            doc.get_info_file(),
            "xeditor",
            default_opener="xterm -e vim",
            wait=True
        )
        doc.load()



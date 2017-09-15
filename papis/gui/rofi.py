import rofi
import webbrowser
import papis.api
import papis.utils
import papis.config


def get_options():
    options = dict()

    for key in ["fullscreen",
            "normal_window", "multi_select", "case_sensitive", "markup_rows"]:
        options[key] =\
            papis.config.getboolean(key, section="rofi-gui")

    for key in ["width", "eh", "lines", "fixed_lines"]:
        options[key] =\
            papis.config.getint(key, section="rofi-gui")

    for key in ["sep"]:
        options[key] =\
            papis.config.get(key, section="rofi-gui")

    return options


def pick(options, header_filter=None, body_filter=None, match_filter=None):
    if header_filter is None:
        header_filter = lambda x: papis.utils.format_doc(
            papis.config.get('header-format', section='rofi-gui'), x
        )
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
    browse_key = 7

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

    def get_key(self, key):
        return papis.config.get("key-" + key.lower(), section="rofi-gui")

    def get_keys(self):
        return {
            "key%s" % self.quit_key: (
                self.get_key('quit'),
                'Quit'
            ),
            "key%s" % self.edit_key: (
                self.get_key('edit'),
                'Edit'
            ),
            "key%s" % self.delete_key: (
                self.get_key('delete'),
                'Delete'
            ),
            "key%s" % self.help_key: (
                self.get_key('help'),
                'Help'
            ),
            "key%s" % self.open_stay_key: (
                self.get_key('open-stay'),
                'Open'
            ),
            "key%s" % self.normal_widnow_key: (
                self.get_key('normal-window'),
                'Normal Win'
            ),
            "key%s" % self.open_key: (
                self.get_key('open'),
                'Open'
            ),
            "key%s" % self.browse_key: (
                self.get_key('browse'),
                'Browse'
            )
        }

    def main(self, documents):
        # Set default picker
        self.documents = documents
        key = None
        indices = None
        options = get_options()
        header_format = papis.config.get("header-format", section="rofi-gui")
        header_filter = lambda x: papis.utils.format_doc(header_format, x)
        self.help_message = self.get_help()
        options.update(self.keys)
        # Initialize window
        self.window = rofi.Rofi()
        while not (key == self.quit_key or key == self.esc_key):
            indices, key = self.window.select("Select: ",
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
            elif key == self.browse_key:
                for i in indices:
                    self.browse(self.documents[i])
            elif key == self.normal_widnow_key:
                options["normal_window"] ^= True

    def delete(self, doc):
        answer = self.window.text_entry(
            "Are you sure? (y/N)",
            message="<b>Be careful!</b>"
        )
        if answer and answer in "Yy":
            doc.rm()
            self.documents = papis.api.get_documents_in_lib()

    def open(self, doc):
        papis.api.open_file(
            doc.get_files()
        )

    def browse(self, doc):
        url = doc["url"]
        if not url:
            self.window.error("No url for document found")
        else:
            papis.utils.general_open(
                doc["url"], "browser"
            )

    def edit(self, doc):
        papis.utils.general_open(
            doc.get_info_file(),
            "xeditor",
            wait=True
        )
        doc.load()

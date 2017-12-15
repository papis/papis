import papis.config
import os
import subprocess
import urwid


def xclip(text, isfile=False):
    """Copy text or file contents into X clipboard."""
    f = None
    if isfile:
        f = open(text, 'r')
        sin = f
    else:
        sin = subprocess.PIPE
    p = subprocess.Popen(["xclip", "-i"],
                         stdin=sin)
    p.communicate(text)
    if f:
        f.close()


class DocListItem(urwid.WidgetWrap):

    def __init__(self, doc):
        self.doc = doc
        self.docid = self.doc["ref"]

        data = self.doc.to_dict()
        # fill the default attributes for the fields
        show_fields = papis.config.get(
            "show-fields", section="urwid-gui"
        ).replace(" ", "").split(",")
        self.fields = {}
        for field in show_fields:
            self.fields[field] = urwid.Text('')
            if field in data:
                self.fields[field].set_text(str(self.doc[field]))


        self.c1width = 10

        self.rowHeader = urwid.AttrMap(
            urwid.Text('ref:%s ' % (self.docid)),
            'head',
            'head_focus'
        )
        docfields = [self.docfield(field) for field in show_fields]

        # FIXME: how do we hightlight everything in pile during focus?
        w = urwid.Pile(
            [
                urwid.Divider('-'),
                self.rowHeader,
            ] + docfields,
            focus_item=1
        )
        self.__super.__init__(w)

    def docfield(self, field):
        attr_map = field
        return urwid.Columns(
            [
                (
                    'fixed',
                    self.c1width,
                    urwid.AttrMap(
                        urwid.Text(field + ':'),
                        'field',
                        'field_focus'
                    )
                ),
                urwid.AttrMap(
                    self.fields[field],
                    attr_map
                )
            ]
        )

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class Search(urwid.WidgetWrap):

    palette = [
        ('head', 'dark blue, bold', ''),
        ('head_focus', 'white, bold', 'dark blue'),
        ('field', 'light gray', ''),
        ('field_focus', '', 'light gray'),
        ('sources', 'light magenta, bold', ''),
        ('tags', 'dark green, bold', ''),
        ('title', 'yellow', ''),
        ('author', 'dark cyan, bold', ''),
        ('year', 'dark red', '',),
    ]

    keys = {
        'j': "next_entry",
        'k': "prev_entry",
        'G': "go_to_last",
        'g': "go_to_first",
        'down': "next_entry",
        'f': "filter",
        'up': "prev_entry",
        'o': "open_file",
        'e': "edit",
        'u': "open_in_browser",
        'p': "print_info",
        'b': "print_bibtex",
        'ctrl f': "page_down",
        'z': "scroll_middle",
        'page down': "page_down",
        ' ': "page_down",
        'ctrl b': "page_up",
    }

    def __init__(self, ui, query=None):
        self.ui = ui

        self.ui.set_header("Search: " + query)

        docs = self.ui.db.search(query)
        if len(docs) == 0:
            self.ui.set_status('No documents found.')

        items = []
        for doc in docs:
            items.append(DocListItem(doc))

        self.lenitems = len(items)
        self.listwalker = urwid.SimpleListWalker(items)
        self.listbox = urwid.ListBox(self.listwalker)
        w = self.listbox

        self.__super.__init__(w)
        self.update_prompt()


    def scroll_middle(self, size, key):
        """Scroll to middle"""
        entry, pos = self.listbox.get_focus()
        self.go_to_last(size, key)
        self.listbox.set_focus(pos)
        self.update_prompt()

    def next_entry(self, size, key):
        """next entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos + 1 >= self.lenitems: return
        self.listbox.set_focus(pos + 1)
        self.update_prompt()

    def print_info(self, size, key):
        """Print information"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos + 1 >= self.lenitems: return
        self.ui.echo(entry.doc.dump())

    def print_bibtex(self, size, key):
        """Print bibtex"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos + 1 >= self.lenitems: return
        self.ui.echo(entry.doc.to_bibtex())

    def update_prompt(self):
        """
        Write a statusline in the prompt to get some extra information
        of the document one is at.
        """
        entry, pos = self.listbox.get_focus()
        # percentage = 100*float(pos+1)/self.lenitems if pos else 0
        self.ui.echo(
            "%s/%s" % (pos+1 if pos is not None else 0, self.lenitems) +\
            # "  %.0f%%" % (percentage) +\
            "  (" + papis.api.get_lib() + ")"
        )

    def filter(self, size, key):
        #TODO: get a live filtering of the documents
        filterQuery = self.ui.prompt("Filter: ").get_text()
        # self.ui.set_status(filterQuery)

    def page_down(self, size, key):
        """page down"""
        self.listbox.keypress(size, 'page down')
        self.update_prompt()

    def page_up(self, size, key):
        """page up"""
        self.listbox.keypress(size, 'page up')
        self.update_prompt()

    def go_to_first(self, size, key):
        """first entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        self.listbox.set_focus(0)
        self.update_prompt()

    def go_to_last(self, size, key):
        """last entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        self.listbox.set_focus(self.lenitems-1)
        self.update_prompt()

    def prev_entry(self, size, key):
        """previous entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos == 0: return
        self.listbox.set_focus(pos - 1)
        self.update_prompt()

    def edit(self, size, key):
        """edit document"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        papis.api.edit_file(entry.doc.get_info_file())
        # TODO: Update information drawn on screen

    def open_file(self, size, key):
        """open document file"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_files()
        if not path:
            self.ui.set_status('No file for document id:%s.' % entry.docid)
            return
        path = path[0]
        if not os.path.exists(path):
            self.ui.echoerr('id:%s: file not found.' % entry.docid)
            return
        self.ui.set_status('opening file: %s...' % path)
        papis.api.open_file(path)

    def open_in_browser(self, size, key):
        """open document URL in browser"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        self.ui.set_status('Opening in browser...')
        papis.document.open_in_browser(entry.doc)

    def view_bibtex(self, size, key):
        """view document bibtex"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        self.ui.newbuffer(['bibview', 'ref = ' + entry.docid])

    def keypress(self, size, key):
        if key in self.keys:
            cmd = eval("self.%s" % (self.keys[key]))
            cmd(size, key)
        else:
            self.ui.keypress(key)

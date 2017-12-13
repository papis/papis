import papis.config
import os
import subprocess
import urwid

############################################################

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

############################################################

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
            urwid.Text('id:%s ' % (self.docid)),
            'head', 'head_focus')
        docfields = [self.docfield(field) for field in show_fields]

        # FIXME: how do we hightlight everything in pile during focus?
        w = urwid.Pile(
            [
                urwid.Divider('-'),
                self.rowHeader,
            ] + docfields
            ,
            focus_item=1)
        self.__super.__init__(w)

    def docfield(self, field):
        attr_map = field
        return urwid.Columns(
            [
                ('fixed', self.c1width,
                 urwid.AttrMap(
                     urwid.Text(field + ':'),
                     'field', 'field_focus')),
                urwid.AttrMap(
                    self.fields[field],
                    attr_map)
                ]
            )

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

############################################################

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
        'j': "nextEntry",
        'k': "prevEntry",
        'G': "goToLast",
        'g': "goToFirst",
        'down': "nextEntry",
        'f': "filter",
        'up': "prevEntry",
        'enter': "open_file",
        'u': "open_url",
        'b': "viewBibtex",
        '+': "addTags",
        '-': "removeTags",
        'a': "archive",
        'meta i': "copyID",
        'meta f': "copyPath",
        'meta u': "copyURL",
        'meta b': "copyBibtex",
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

    ##########

    def nextEntry(self):
        """next entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos + 1 >= self.lenitems: return
        self.listbox.set_focus(pos + 1)

    def goToFirst(self):
        """first entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        self.listbox.set_focus(0)

    def goToLast(self):
        """last entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        self.listbox.set_focus(self.lenitems-1)

    def prevEntry(self):
        """previous entry"""
        entry, pos = self.listbox.get_focus()
        if not entry: return
        if pos == 0: return
        self.listbox.set_focus(pos - 1)

    def open_file(self):
        """open document file"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_files()
        if not path:
            self.ui.set_status('No file for document id:%s.' % entry.docid)
            return
        path = path[0]
        if not os.path.exists(path):
            self.ui.set_status('ERROR: id:%s: file not found.' % entry.docid)
            return
        self.ui.set_status('opening file: %s...' % path)
        papis.api.open_file(path)

    def open_url(self):
        """open document URL in browser"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        urls = [entry.doc["url"]]
        if not urls:
            self.ui.set_status('ERROR: id:%s: no URLs found.' % entry.docid)
            return
        # FIXME: open all instead of just first?
        url = urls[0]
        self.ui.set_status('opening url: %s...' % url)

    def viewBibtex(self):
        """view document bibtex"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        self.ui.newbuffer(['bibview', 'id:' + entry.docid])

    def copyID(self):
        """copy document ID to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        docid = "id:%s" % entry["id"]
        xclip(docid)
        self.ui.set_status('docid yanked: %s' % docid)

    def copyPath(self):
        """copy document file path to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        path = entry.doc.get_fullpaths()[0]
        if not path:
            self.ui.set_status('ERROR: id:%s: file path not found.' % entry.docid)
            return
        xclip(path)
        self.ui.set_status('path yanked: %s' % path)

    def copyURL(self):
        """copy document URL to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        urls = entry.doc.get_urls()
        if not urls:
            self.ui.set_status('ERROR: id:%s: URL not found.' % entry.docid)
            return
        url = urls[0]
        xclip(url)
        self.ui.set_status('url yanked: %s' % url)

    def copyBibtex(self):
        """copy document bibtex to clipboard"""
        entry = self.listbox.get_focus()[0]
        if not entry: return
        bibtex = entry.doc.get_bibpath()
        if not bibtex:
            self.ui.set_status('ERROR: id:%s: bibtex not found.' % entry.docid)
            return
        xclip(bibtex, isfile=True)
        self.ui.set_status('bibtex yanked: %s' % bibtex)

    def addTags(self):
        """add tags from document (space separated)"""
        self.promptTag('+')

    def removeTags(self):
        """remove tags from document (space separated)"""
        self.promptTag('-')

    def promptTag(self, sign):
        entry = self.listbox.get_focus()[0]
        if not entry: return
        if sign is '+':
            # FIXME: autocomplete to existing tags
            prompt = 'add tags: '
        elif sign is '-':
            # FIXME: autocomplete to doc tags only
            prompt = 'remove tags: '
        urwid.connect_signal(self.ui.prompt(prompt), 'done', self._promptTag_done, sign)

    def _promptTag_done(self, tag_string, sign):
        self.ui.view.set_focus('body')
        urwid.disconnect_signal(self, self.ui.prompt, 'done', self._promptTag_done)
        if not tag_string:
            self.ui.set_status('No tags set.')
            return
        entry = self.listbox.get_focus()[0]
        with Database(self.ui.xroot, writable=True) as db:
            doc = db[entry.docid]
            tags = tag_string.split()
            if sign is '+':
                doc.add_tags(tags)
                msg = "Added tags: %s" % (tag_string)
            elif sign is '-':
                doc.remove_tags(tags)
                msg = "Removed tags: %s" % (tag_string)
            doc.sync()
        tags = doc.get_tags()
        entry.fields['tags'].set_text(' '.join(tags))
        self.ui.set_status(msg)

    def archive(self):
        """archive document (remove 'new' tag)"""
        self._promptTag_done('new', '-')

    def keypress(self, size, key):
        if key in self.keys:
            cmd = "self.%s()" % (self.keys[key])
            eval(cmd)
        else:
            self.ui.keypress(key)

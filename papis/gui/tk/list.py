from papis.gui.tk import PapisWidget
from papis.gui.tk import tk
import papis.api
import papis.config
import papis.utils


class ListEntry(tk.Frame, PapisWidget):

    def __init__(self, master, text):
        tk.Frame.__init__(self, master)
        PapisWidget.__init__(self)
        self["justify"] = tk.LEFT
        self["padx"] = 10
        self["font"] = "12"
        self["borderwidth"] = 1
        self["fg"] = self.get_config("entry-fg")
        self["anchor"] = tk.W
        self["activeforeground"] = self.get_config("activeforeground")
        self["activebackground"] = self.get_config("activebackground")
        self.text = text
        self.lines = text.split("\n")
        self["height"] = self.lines
        self.lines_label = []
        for line in self.lines:
            self.lines_label.append(
                tk.Label(
                    self
                )
            )


class PapisList(tk.Frame, PapisWidget):

    index_draw_first = 0
    index_draw_last = 0
    key = None
    selected = None
    index = 0
    entries_drawning = False
    doc_primitive_height = 10
    matched_indices = []
    documents_lbls = []

    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)
        PapisWidget.__init__(self)
        self["bg"] = self.master["bg"]

    def set_bindings(self):
        self.logger.debug("Setting bindings")
        self.noremap("<Control-l>", self.redraw_screen)
        self.master.prompt.cmap("<KeyPress>", self.filter_and_draw)
        self.master.prompt.cmap("<Control-n>", self.move_down)
        self.master.prompt.cmap("<Control-p>", self.move_up)
        self.master.prompt.cmap("<Control-o>", self.open)
        self.master.prompt.cmap("<Control-i>", self.print_info)
        self.bindings = [
            (self.get_config("move_down"), "move_down"),
            (self.get_config("move_up"), "move_up"),
            (self.get_config("open"), "open"),
            (self.get_config("edit"), "edit"),
            (self.get_config("move_top"), "move_top"),
            (self.get_config("move_bottom"), "move_bottom"),
            (self.get_config("print_info"), "print_info"),
            (self.get_config("half_down"), "half_down"),
            (self.get_config("half_up"), "half_up"),
            (self.get_config("scroll_down"), "scroll_down"),
            (self.get_config("scroll_up"), "scroll_up"),
            ("<Down>", "move_down"),
            ("<Up>", "move_up"),
        ]
        for bind in self.bindings:
            key = bind[0]
            name = bind[1]
            self.master.nmap(key, getattr(self, name))

    def get_matched_indices(self, force=False):
        if not self.master.prompt.changed() and not force:
            return self.matched_indices
        self.logger.debug("Indexing")
        command = self.master.prompt.get_command()
        match_format = self.get_config("match-format")
        indices = list()
        for i, doc in enumerate(self.documents):
            if papis.utils.match_document(doc, command, match_format):
                indices.append(i)
        self.matched_indices = indices
        return indices

    def filter_and_draw(self, event=None):
        indices = self.get_matched_indices()
        self.undraw_documents_labels()
        self.draw_documents_labels(indices)

    def set_documents(self, docs):
        self.documents = docs

    def scroll(self, direction):
        self.undraw_documents_labels()
        if direction == "down":
            self.index_draw_first += 1
        else:
            if self.index_draw_first > 0:
                self.index_draw_first -= 1
        self.update_selection_index()
        self.draw_documents_labels()

    def scroll_down(self, event=None):
        self.scroll("down")

    def scroll_up(self, event=None):
        self.scroll("up")

    def half_up(self, event=None):
        self.logger.debug("Half up")
        print("TODO")

    def half_down(self, event=None):
        self.logger.debug("Half down")
        print("TODO")

    def move_top(self, event=None):
        self.logger.debug("Moving to top")
        self.index_draw_first = 0
        self.index = self.index_draw_first
        self.redraw_documents_labels()

    def move_bottom(self, event=None):
        self.logger.debug("Moving to bottom")
        self.index_draw_first = len(self.get_matched_indices())-1
        self.index = self.index_draw_first
        self.redraw_documents_labels()

    def move_down(self, event=None):
        self.move("down")

    def move_up(self, event=None):
        self.move("up")

    def draw_selection(self, event=None):
        indices = self.get_matched_indices()
        if not len(indices):
            return False
        if self.get_selected() is not None:
            self.get_selected().configure(state="normal")
        self.update_selection_index()
        self.set_selected(self.documents_lbls[indices[self.index]])
        self.get_selected().configure(state="active")

    def get_selected(self):
        return self.selected

    def get_selected_doc(self):
        return self.selected.doc

    def set_selected(self, doc_lbl):
        self.selected = doc_lbl

    def set_documents_labels(self):
        self.update_drawing_indices()
        font_size = self.get_config("entry-font-size")
        font_name = self.get_config("entry-font-name")
        font_style = self.get_config("entry-font-style")
        font_lines = self.get_config("entry-lines")
        font = (font_name, font_size, font_style)
        doc_primitive_height = int(font_size)*int(font_lines)
        # number_of_entries = self.winfo_height()/doc_primitive_height
        pady = int(abs(self.winfo_height() - int(font_size)*int(font_lines))/2)
        for doc in self.documents:
            self.documents_lbls.append(
                tk.Label(
                    text=papis.utils.format_doc(
                        self.get_config("header-format"),
                        doc
                    ),
                    justify=tk.LEFT,
                    padx=10,
                    pady=pady,
                    height=font_lines,
                    font=font,
                    borderwidth=1,
                    fg=self.get_config("entry-fg"),
                    anchor=tk.W,
                    activeforeground=self.get_config("activeforeground"),
                    activebackground=self.get_config("activebackground")
                )
            )
            setattr(self.documents_lbls[-1], "doc", doc)

    def redraw_documents_labels(self):
        self.undraw_documents_labels()
        self.draw_documents_labels()

    def undraw_documents_labels(self):
        if self.entries_drawning:
            return False
        if not len(self.documents_lbls):
            return False
        for doc in self.documents_lbls:
            doc.pack_forget()

    def draw_documents_labels(self, indices=[]):
        if self.entries_drawning:
            return False
        else:
            self.logger.debug("Drawing")
            self.entries_drawning = True
        if not len(indices):
            indices = self.get_matched_indices()
        colors = (
            self.get_config("entry-bg-odd"),
            self.get_config("entry-bg-pair"),
        )
        self.update_height()
        self.update_drawing_indices()
        for i in range(self.index_draw_first, self.index_draw_last):
            if i >= len(indices):
                break
            doc = self.documents_lbls[indices[i]]
            doc["bg"] = colors[i % 2]
            doc.pack(
                fill=tk.X
            )
        self.logger.debug("Drawing done")
        self.entries_drawning = False
        self.draw_selection()

    def redraw_screen(self, event=None):
        self.redraw_documents_labels()

    def update_drawing_indices(self):
        label_number = self.get_config("labels-per-page")
        self.doc_primitive_height = int(self["height"]/label_number)
        self.index_draw_last = self.index_draw_first +\
            int(self["height"]/self.doc_primitive_height)
        self.logger.debug("label_h %s" % self.doc_primitive_height)
        self.logger.debug("i_draw_last %s" % self.index_draw_last)

    def update_selection_index(self):
        indices = self.get_matched_indices()
        if self.index < self.index_draw_first:
            self.index = self.index_draw_first
        if self.index > self.index_draw_last:
            self.index = self.index_draw_last-1
        if self.index > len(indices)-1:
            self.index = len(indices)-1

    def move(self, direction):
        indices = self.get_matched_indices()
        if direction == "down":
            if self.index < len(indices)-1:
                self.index += 1
        if direction == "up":
            if self.index > 0:
                self.index -= 1
        if self.index > self.index_draw_last-1:
            self.scroll_down()
        if self.index < self.index_draw_first:
            self.scroll_up()
        self.logger.debug(
            "index = %s in (%s , %s)"
            % (self.index, self.index_draw_first, self.index_draw_last)
        )
        self.draw_selection()

    def open(self, event=None):
        doc = self.get_selected_doc()
        papis.api.open_file(
            doc.get_files()
        )

    def print_info(self, event=None):
        doc = self.get_selected_doc()
        self.master.prompt.echomsg(
            doc.dump()
        )

    def edit(self, event=None):
        doc = self.get_selected_doc()
        papis.utils.general_open(
            doc.get_info_file(),
            "xeditor",
            default_opener="xterm -e vim",
            wait=True
        )
        doc.load()

    def update_height(self):
        self["height"] = self.master.winfo_height() - \
            self.master.prompt.winfo_height()
        self.logger.debug("Updating height (%s)" % self["height"])
        assert(not self["height"] == 0)

    def init(self):
        self.set_bindings()
        self.logger.debug("Creating labels")
        # force indexing
        self.logger.debug("Forcing indexing...")
        self.get_matched_indices(True)
        self.update_height()
        self.set_documents_labels()
        self.draw_documents_labels()

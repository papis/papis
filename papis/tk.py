
import tkinter as tk
import papis.config
import papis.utils
import re


class Gui(tk.Tk):

    def __init__(self):
        super().__init__()
        self.index = 0
        self.command = ""
        self.lines = 3
        self.index_draw_first = 0
        self.index_draw_last = 0 # int(self.winfo_height()/3.0)
        self.key = None
        self.selected = None
        self.documents = []
        self.documents_lbls = []
        self.title("Papis document manager")
        self.prompt = tk.Text(
            self,
            bg="black",
            borderwidth=0,
            cursor="xterm",
            fg="white",
            insertbackground=self.get_config("insertbackground", "red"),
            height=1
        )
        self.bind("<Return>", self.handle_return)
        self.bind("<Escape>", self.cancel)
        self.bind("<Configure>", self.on_resize)
        self.bind(self.get_config("cancel", "<Control-c>"), self.cancel)
        self.bind(self.get_config("focus_prompt", ":"), self.focus_prompt)
        self.bind(self.get_config("move_down", "j"), self.move_down)
        self.bind(self.get_config("move_up", "k"), self.move_up)
        self.bind(self.get_config("scroll_down", "<Control-e>"), self.scroll_down)
        self.bind(self.get_config("scroll_up", "<Control-y>"), self.scroll_up)
        self.bind(self.get_config("open", "o"), self.open)
        self.bind(self.get_config("edit", "e"), self.edit)
        self.bind(self.get_config("exit", "q"), self.exit)
        self.bind_all(self.get_config("autocomplete", "<Tab>"), self.autocomplete)
        self.prompt.bind("<KeyPress>", self.filter_and_draw)

    def get_matched_indices(self):
        match_format = self.get_config(
            "match_format", papis.config.get("match_format")
        )
        indices = list()
        self.get_command()
        for i, doc in enumerate(self.documents):
            if papis.utils.match_document(doc, self.command, match_format):
                indices.append(i)
        return indices

    def filter_and_draw(self, event=None):
        indices = self.get_matched_indices()
        print(indices)
        self.undraw_documents_labels()
        self.draw_documents_labels(indices)

    def get_command(self):
        self.command = self.prompt.get(1.0, tk.END)
        return self.command

    def get_config(self, key, default):
        """Get user configuration

        :key: Key value
        :default: Default value

        """
        try:
            return papis.config.get(
                "tk-"+key, extras=[("tk-gui", "", key)]
            )
        except:
            return default

    def on_resize(self, event=None):
        self.undraw_documents_labels()
        self.draw_documents_labels()

    def get_selected(self):
        return self.selected

    def set_selected(self, doc_lbl):
        self.selected = doc_lbl

    def move(self, direction):
        print("----")
        print(self.winfo_height())
        print(self.winfo_width())
        print(self.winfo_reqheight())
        print(self.winfo_reqwidth())
        if self.in_command_mode():
            return
        if direction == "down":
            if self.index < len(self.documents):
                self.index += 1
        if direction == "up":
            if self.index > 0:
                self.index -= 1
        self.draw_selection()

    def scroll(self, direction):
        self.undraw_documents_labels()
        if direction == "down":
            self.index_draw_first+=1
        else:
            if self.index_draw_first > 0:
                self.index_draw_first-=1
        self.draw_documents_labels()

    def scroll_down(self, event=None):
        print("Scrolling down")
        self.scroll("down")

    def scroll_up(self, event=None):
        print("Scrolling up")
        self.scroll("up")

    def move_down(self, event=None):
        self.lower()
        self.move("down")

    def move_up(self, event=None):
        self.move("up")

    def draw_selection(self, event=None):
        if not len(self.documents):
            return False
        self.get_selected().configure(state="normal")
        self.set_selected(self.documents_lbls[self.index])
        self.get_selected().configure(state="active")

    def set_documents(self, docs):
        self.documents = docs

    def in_command_mode(self):
        return True if not str(self.prompt.focus_get()) == "." else False

    def cancel(self, event=None):
        if self.in_command_mode():
            self.prompt.delete(1.0, tk.END)
            self.focus()

    def autocomplete(self, event=None):
        print("autocomplete")
        if self.in_command_mode():
            command = self.prompt.get(1.0, tk.END)
            print(command)
            self.prompt["bg"] = "blue"

    def handle_return(self, event=None):
        if self.in_command_mode():
            self.command = self.prompt.get(1.0, tk.END)
            print(self.command)
            self.prompt.delete(1.0, tk.END)
            self.focus()

    def focus_prompt(self, event=None):
        self.prompt.focus_set()

    def set_documents_labels(self):
        colors = ["grey", "lightgrey"]
        i = 0
        for doc in self.documents:
            i += 1
            self.documents_lbls.append(
                tk.Label(
                    text=self.get_config("header_format", "").format(doc=doc),
                    justify=tk.LEFT,
                    padx=10,
                    width=self.winfo_width(),
                    borderwidth=10,
                    activeforeground="black",
                    activebackground="gold4",
                    bg=colors[i%2]
                )
            )

    def undraw_documents_labels(self):
        if not len(self.documents_lbls):
            return False
        for doc in self.documents_lbls:
            doc.pack_forget()

    def draw_documents_labels(self, indices=[]):
        if not len(self.documents_lbls):
            return False
        primitive_height = self.documents_lbls[0].winfo_height()
        self.index_draw_last = self.index_draw_last +\
                int(self.winfo_height()/primitive_height)
        print(self.index_draw_last)
        indices = self.get_matched_indices()
        for i in range(self.index_draw_first, self.index_draw_last):
            if i >= len(indices):
                return True
            doc = self.documents_lbls[indices[i]]
            doc.pack(
                anchor=tk.W,
                fill=tk.X
            )

    def main(self, documents):
        self.prompt.pack(fill=tk.X, side=tk.BOTTOM)
        self.set_documents(documents)
        self.set_documents_labels()
        self.draw_documents_labels()
        self.set_selected(self.documents_lbls[self.index])
        self.draw_selection()
        return self.mainloop()

    def open(self, event=None):
        if self.in_command_mode():
            return False
        papis.utils.open_file(
            self.documents[self.index].get_files()
        )

    def exit(self, event=None):
        if self.in_command_mode():
            return False
        self.quit()

    def edit(self, event=None):
        if self.in_command_mode():
            return False
        papis.utils.general_open(
            self.documents[self.index].get_info_file(),
            "xeditor",
            default_opener="xterm -e vim",
            wait=True
        )
        doc.load()



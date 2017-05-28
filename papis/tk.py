
import tkinter as tk
import papis.config

def get_header_format(section=None, prefix="rofi-"):
    args = []
    if section:
        args = [section, prefix+"header_format"]
    else:
        args = [prefix+"header_format"]

    return papis.config.get(
        *args
    )


class Gui(tk.Tk):

    def __init__(self):
        super().__init__()
        self.index = 0
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
            insertbackground="red",
            height=1
        )
        self.bind(":", self.focus_prompt)
        self.bind("<Return>", self.handle_return)
        self.bind("<Escape>", self.cancel)
        self.bind("<Control-c>", self.cancel)
        self.bind("j", self.move_down)
        self.bind("k", self.move_up)
        self.bind("<Control-n>", self.move_down)
        self.bind("<Control-p>", self.move_up)
        self.bind("o", self.open)
        self.bind("e", self.edit)
        self.bind("q", self.exit)
        self.bind_all("<Tab>", self.autocomplete)

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
            command = self.prompt.get(1.0, tk.END)
            print(command)
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
                    text=get_header_format(prefix="tk-").format(doc=doc),
                    justify=tk.LEFT,
                    padx=10,
                    width=self.winfo_width(),
                    borderwidth=10,
                    activeforeground="black",
                    activebackground="gold4",
                    bg=colors[i%2]
                )
            )

    def draw_documents_labels(self):
        self.index_draw_first = 0
        self.index_draw_last = 5
        print(self.index_draw_last)
        print(self.winfo_height())
        for i in range(self.index_draw_first, self.index_draw_last):
            if i >= len(self.documents_lbls):
                return True
            doc = self.documents_lbls[i]
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
        papis.utils.open_file(
            self.documents[self.index].get_files()
        )

    def exit(self, event=None):
        self.quit()

    def edit(self, event=None):
        papis.utils.general_open(
            self.documents[self.index].get_info_file(),
            "xeditor",
            default_opener="xterm -e vim",
            wait=True
        )
        doc.load()



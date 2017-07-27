
import papis.config
import papis.utils
import sys
import logging
from papis.gui.tk import tk
import papis.gui.tk


class PapisWidget(tk.Misc):

    normal_mode = "normal"
    insert_mode = "insert"
    command_mode = "command"

    CURRENT_MODE = normal_mode

    def __init__(self):
        tk.Misc.__init__(self)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_mode(self):
        return PapisWidget.CURRENT_MODE

    def set_mode(self, mode):
        self.logger.debug("Mode -> %s" % mode)
        PapisWidget.CURRENT_MODE = mode

    def general_map(self, key, function, mode=None, recursive=False):
        def help_function(*args, **kwargs):
            if self.get_mode() == mode or mode is None:
                return function(*args, **kwargs)
        if recursive:
            self.bind_all(key, help_function)
        else:
            self.bind(key, help_function)

    def noremap(self, key, function, mode=None):
        self.general_map(key, function, mode, recursive=True)

    def norenmap(self, key, function):
        self.noremap(key, function, self.normal_mode)

    def noreimap(self, key, function):
        self.noremap(key, function, self.insert_mode)

    def norecmap(self, key, function):
        self.noremap(key, function, self.command_mode)

    def map(self, key, function, mode=None):
        self.general_map(key, function, mode, recursive=False)

    def nmap(self, key, function):
        self.map(key, function, self.normal_mode)

    def imap(self, key, function):
        self.map(key, function, self.insert_mode)

    def cmap(self, key, function):
        self.map(key, function, self.command_mode)

    def to_normal(self, event=None):
        self.focus()
        self.set_mode(self.normal_mode)

    def get_config(self, key):
        """Get configuration to key
        """
        return papis.config.get(
            key, section="tk-gui"
        )


class Gui(tk.Tk, PapisWidget):

    def __init__(self):
        tk.Tk.__init__(self)
        PapisWidget.__init__(self)
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.geometry(
            "{}x{}".format(
                self.get_config("window-width"),
                self.get_config("window-height"),
            )
        )
        self["bg"] = self.get_config("window-bg")
        self.title("Papis document manager")
        self.prompt = papis.gui.tk.Prompt(
            self,
        )
        self.main_frame = papis.gui.tk.PapisList(
            self
        )
        self.prompt.add_new_command("help", self.print_help)
        self.prompt.add_new_command("q", self.exit)
        self.prompt.add_new_command("quit", self.exit)

    def set_bindings(self):
        self.logger.debug("Setting bindings")
        self.norecmap("<Return>", self.prompt.run)
        self.noremap("<Escape>", self.clear)
        self.cmap("<Control-c>", self.to_normal)
        self.map("<Configure>", self.on_resize)
        self.bindings = [
            (self.get_config("exit"), "exit"),
            (self.get_config("focus_prompt"), "focus_prompt"),
            (self.get_config("clear"), "clear"),
            (self.get_config("help"), "print_help"),
        ]
        for bind in self.bindings:
            key = bind[0]
            name = bind[1]
            self.nmap(key, getattr(self, name))

    def on_resize(self, event=None):
        pass

    def exit(self, event=None):
        self.logger.debug("Exiting")
        self.destroy()
        sys.exit(0)

    def clear(self, event=None):
        self.prompt.clear()
        self.to_normal()

    def handle_return(self, event=None):
        self.prompt.get_command()
        self.prompt.clear()
        self.focus()

    def focus_prompt(self, event=None):
        self.prompt.clear()
        self.prompt.focus()

    def main(self, documents):
        self.set_bindings()
        self.logger.debug("Packing prompt")
        self.prompt.pack(fill=tk.X, side=tk.BOTTOM)
        self.logger.debug("Setting docs")
        # self.main_frame.pack(fill=tk.X, side=tk.TOP)
        self.main_frame.set_documents(documents)
        self.after(
            200,
            self.main_frame.init
        )
        return self.mainloop()

    def print_help(self, event=None):
        text = ""
        for bind in self.bindings + self.main_frame.bindings:
            text += "{key}  -  {name}\n".format(key=bind[0], name=bind[1])
        self.prompt.echomsg(text)

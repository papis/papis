from papis.tk import PapisWidget
from papis.tk import tk

class Command(object):

    def __init__(self, name, function, prompt, nargs=0):
        self.name = name
        self.function = function
        self.nargs = nargs
        self.prompt = prompt

    def run(self, *args):
        return self.function(*args)

class Prompt(tk.Text,PapisWidget):

    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        PapisWidget.__init__(self)
        self.bind("<Control-u>", self.clear)
        self.command = ""
        self.last_command = ""
        self.registered_commands = []

    def changed(self):
        self.get_command()
        if self.last_command == self.command:
            return False
        else:
            return True

    def register_command(self, cmd):
        self.register_command.append(cmd)

    def add_new_command(self, name, function, nargs=0):
        cmd = Command(name, function, self, nargs)
        self.register_command(cmd)

    def get_command(self):
        self.last_command = self.command
        if self.get_mode() == self.command_mode:
            self.command = self.get(1.0, tk.END)
        return self.command

    def echomsg(self, text):
        self.clear()
        self["height"] = len(text.split("\n"))-1
        self.insert(1.0, text)

    def clear(self, event=None):
        self["height"] = 1
        self.delete(1.0, tk.END)

    def focus(self, event=None):
        self.set_mode(self.command_mode)
        self.focus_set()

    def autocomplete(self, event=None):
        pass

    def register_command(self, arg1):
        pass


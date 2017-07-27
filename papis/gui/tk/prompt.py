from papis.gui.tk import PapisWidget
from papis.gui.tk import tk
import re


class Command(object):

    def __init__(self, name, function, prompt, nargs=0):
        self.name = name
        self.function = function
        self.nargs = nargs
        self.args = []
        self.prompt = prompt

    def set_args(self, args):
        self.args = args

    def run(self):
        return self.function(*self.args)


class Prompt(tk.Text, PapisWidget):

    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        PapisWidget.__init__(self)
        self.bind("<Control-u>", self.clear)
        self.command = ""
        self.last_command = ""
        self.registered_commands = []
        self.reset_style()

    def reset_style(self):
        self["font"] = self.get_config("prompt-font-size")
        self["fg"] = self.get_config("prompt-fg")
        self["insertbackground"] = self.get_config("insertbackground")
        self["bg"] = self.get_config("prompt-bg")
        self["borderwidth"] = -1
        self["cursor"] = self.get_config("cursor")
        self["height"] = 1

    def changed(self):
        self.get_command()
        if self.last_command == self.command:
            return False
        else:
            return True

    def register_command(self, cmd):
        self.registered_commands.append(cmd)

    def get_registered_commands(self):
        return self.registered_commands

    def parse_command(self, command_string):
        for cmd in self.get_registered_commands():
            m = re.match(r"^\s*%s\s*" % cmd.name, command_string)
            if m:
                return cmd
        return None

    def run(self, event=None):
        command_string = self.get_command()
        command = self.parse_command(command_string)
        if command is None:
            self.logger.error("Command %s not recognised" % command_string)
            return False
        self.logger.debug("Running %s" % command_string)
        return command.run()

    def add_new_command(self, name, function, nargs=0):
        self.logger.debug("Adding command %s" % name)
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

    def echoerr(self, text):
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

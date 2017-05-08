import os
import re
import sys
from . import Command
import subprocess

class External(Command):

    def init(self, path):
        self.script_path = path
        self.subparser = self.parser.add_parser(
            self.get_command_name(),
            help=self.get_command_help()
        )

        self.subparser.add_argument(
            "args",
            help="Arguments",
            nargs="*",
            action="store"
        )

    def get_command_name(self):
        m = re.match(r"^.*papis-(.*)$", self.script_path)
        if not m:
            return None
        else:
            return m.group(1)

    def get_command_help(self):
        p = subprocess.Popen(
            [self.script_path, "-h"],
            stdout=subprocess.PIPE
        )
        h, err = p.communicate()
        if not h or (not p.returncode == 0):
            return "No help message available"
        else:
            return h.decode("ascii")

    def main(self, config, args):
        subprocess.call([self.script_path] + args.args)

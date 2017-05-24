import os
import re
import papis.config
import subprocess


class External(papis.commands.Command):

    def init(self, path):
        self.script_path = path

        self.parser = self.get_subparsers().add_parser(
            self.get_command_name(),
            help=self.get_command_help()
        )

        self.parser.add_argument(
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

    def export_variables(self):
        """Export environment variables so that external script can access to
        the information
        """
        os.environ["PAPIS_LIB"] = self.args.lib
        os.environ["PAPIS_LIB_PATH"] = self.config[self.args.lib]["dir"]
        os.environ["PAPIS_CONFIG_PATH"] = papis.config.get_config_folder()
        os.environ["PAPIS_CONFIG_FILE"] = papis.config.get_config_file()
        os.environ["PAPIS_SCRIPTS_PATH"] = papis.config.get_scripts_folder()

    def main(self):
        self.export_variables()
        subprocess.call([self.script_path] + self.args.args)

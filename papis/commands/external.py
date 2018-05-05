import os
import re
import argparse
import subprocess
import papis.config
import papis.commands


class Command(papis.commands.Command):

    def init(self, path):

        self._external = True

        self.script_path = path

        self.parser = self.get_subparsers().add_parser(
            self.get_command_name(),
            add_help=False,
            help=self.get_command_help()
        )

        self.parser.add_argument(
            'args',
            help="Arguments",
            default='',
            nargs=argparse.REMAINDER,
            action="store"
        )

    def get_command_name(self):
        m = re.match(r"^.*papis-(.*)$", self.script_path)
        return m.group(1) if m else None

    def get_command_help(self):
        magic_word = papis.config.get("scripts-short-help-regex")
        with open(self.script_path) as fd:
            for line in fd:
                m = re.match(magic_word, line)
                if m:
                    return m.group(1)
        return "No help message available"

    def export_variables(self):
        """Export environment variables so that external script can access to
        the information
        """
        os.environ["PAPIS_LIB"] = self.args.lib
        os.environ["PAPIS_LIB_PATH"] = papis.config.get('dir')
        os.environ["PAPIS_CONFIG_PATH"] = papis.config.get_config_folder()
        os.environ["PAPIS_CONFIG_FILE"] = papis.config.get_config_file()
        os.environ["PAPIS_SCRIPTS_PATH"] = papis.config.get_scripts_folder()
        os.environ["PAPIS_VERBOSE"] = "-v" if self.args.verbose else ""

    def main(self):
        self.logger.debug("Exporting variables")
        self.export_variables()
        # We have to get from the first argument due to the limitation of
        # argparse that REMAINDER needs a non-flag argument first to work.
        # see papis.command.patch_external_input_args and
        # https://stackoverflow.com/questions/43219022/using-argparse-remainder-at-beginning-of-parser-sub-parser
        cmd = [self.script_path] + self.args.args[1:]
        self.logger.debug("Calling {}".format(cmd))
        subprocess.call(cmd)

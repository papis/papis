import papis.commands


class Command(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "git",
            help="Run a git command in the library folder"
        )

        self.parser.add_argument(
            "commands",
            help="Commands",
            default="",
            nargs="+",
            action="store"
        )

    def main(self):
        run = papis.commands.get_commands("run")
        run.set_args(self.get_args())
        run.set_commands(["git"] + self.args.commands)
        run.main()

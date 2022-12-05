from papis.commands.git import cli

import tests


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_simple(self):
        result = self.invoke([
            "init"
        ])
        self.assertEqual(result.exit_code, 0)

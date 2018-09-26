import tests.cli
from papis.commands.default import run


class TestCli(tests.cli.TestCli):

    cli = run

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_version(self):
        result = self.invoke([
            '--version'
        ])
        self.assertTrue(result.exit_code == 0)

    # def test_set(self):
        # result = self.invoke([
            # '--set', 'something', '42'
        # ])
        # self.assertTrue(result.exit_code == 0)

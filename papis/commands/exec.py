r"""
This command is useful to execute Python scripts with the environment of your
``papis`` executable.

Often Papis is installed in a virtual environment or locally in the user's home
directory, and therefore the global Python executable does not have access to
the Papis environment.

This command tries to mend this issue by allowing the user to write a
Python script and run it using the correct environment where Papis is
installed.

Examples
^^^^^^^^

- Run the code in the file ``my-script.py`` and pass it the
    arguments arg1 and arg2

    .. code:: sh

        papis exec my-script.py arg1 arg2

- Pass the help argument ``-h`` to the script ``my-script.py``

    .. code:: sh

        papis exec my-script.py -- -h

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.exec:cli
    :prog: papis exec
"""

import sys
from typing import List

import click


def run(_file: str) -> None:
    with open(_file) as f:
        exec(f.read())


@click.command("exec", context_settings={"ignore_unknown_options": True})
@click.help_option("--help", "-h")
@click.argument("python_file", type=click.Path(exists=True))
@click.argument("args", nargs=-1)
def cli(python_file: str, args: List[str]) -> None:
    """Execute a python file in the environment of papis' executable"""
    sys.argv = [python_file, *args]
    run(python_file)

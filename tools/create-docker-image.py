#! /usr/bin/env python
# vim-run: python % -p 3.3 ../Dockerfile --norun

import argparse
import itertools as it
import os
import subprocess
import shlex

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", help="Python version",
        choices=map(
            lambda x: "{}.{}".format(*x),
            zip(it.repeat(3), range(3, 8))))
    parser.add_argument("dockerfile")
    parser.add_argument(
        "--norun",
        help="Do not run the command, just print", action="store_true")
    args = parser.parse_args()

    assert os.path.exists(args.dockerfile), "Dockerfile does not exist"
    folder = os.path.abspath(os.path.dirname(args.dockerfile))

    command = (
        "sudo docker build {folder} -t papis:python{version} "
        "--build-arg PYTHON_VERSION={version}".format(
            folder=folder,
            version=args.p
        )
    )
    print(command)
    args.norun or subprocess.check_call(shlex.split(command))

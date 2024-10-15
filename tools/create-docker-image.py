#! /usr/bin/env python
# vim-run: python % -p 3.3 ../Dockerfile --norun

import pathlib


def main(dockerfile: pathlib.Path, py_version: str, *, norun: bool = False) -> int:
    if not dockerfile.exists():
        print(f"ERROR: Dockerfile does not exist: '{dockerfile}'")
        return 1

    import shutil

    if not shutil.which("docker"):
        print("ERROR: 'docker' command not found")
        return 1

    folder = dockerfile.parent.resolve()
    command = [
        "docker",
        "build",
        str(folder),
        "-t",
        f"papis:python{py_version}",
        "--build-arg",
        f"PYTHON_VERSION={py_version}",
    ]

    print(">> Command:")
    print(" ".join(command))

    if not norun:
        import subprocess

        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError as exc:
            print(f"ERROR: {exc}")
            return exc.returncode

    return 0


if __name__ == "__main__":
    import argparse
    from itertools import repeat

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--python-version", help="Python version",
        choices=[f"{major}.{minor}" for major, minor in zip(repeat(3), range(8, 14))],
        default="3.12")
    parser.add_argument("dockerfile", type=pathlib.Path, default="Dockerfile")
    parser.add_argument(
        "--norun",
        help="Do not run the command, just print",
        action="store_true")
    args = parser.parse_args()

    raise SystemExit(main(args.dockerfile, args.python_version, norun=args.norun))

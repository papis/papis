import sys


def sed_replace(filename: str) -> None:
    # NOTE: this function is used by 'test_edit_run' to provide a cross-platform
    # way to edit a file that the test can later recognize and see it was called
    with open(filename) as fd:
        contents = "\n".join([
            line.replace("title: ", "title: test_edit") for line in fd
            ])

    with open(filename, "w") as fd:
        fd.write(contents)


def echo(filename: str) -> None:
    # NOTE: this function is used by 'test_open_run' to provide a cross-platform
    # custom command that shows it tried to open a file
    print("Attempted to open '{}'".format(filename))


if __name__ == "__main__":
    cmd, filename = sys.argv[-2:]

    try:
        ret = 0
        if cmd == "sed":
            sed_replace(filename)
        elif cmd == "echo":
            echo(filename)
        else:
            ret = 1
    except Exception:
        ret = 1

    raise SystemExit(ret)

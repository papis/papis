import sys


def sed_replace(filename: str) -> None:
    # NOTE: this function is used by 'test_edit_run' to provide a cross-platform
    # way to edit a file that the test can later recognize and see it was called
    import papis.yaml

    data = papis.yaml.yaml_to_data(filename)
    data["title"] = "test_edit " + data["title"]
    papis.yaml.data_to_yaml(filename, data)


def echo(filename: str) -> None:
    # NOTE: this function is used by 'test_open_run' to provide a cross-platform
    # custom command that shows it tried to open a file
    print(f"Attempted to open '{filename}'")


def ls(filename: str) -> None:
    # NOTE: This function is used by 'test_edit_cli' and 'test_run_run'
    print(filename)


if __name__ == "__main__":
    cmd, filename = sys.argv[-2:]

    try:
        ret = 0
        if cmd == "sed":
            sed_replace(filename)
        elif cmd == "echo":
            echo(filename)
        elif cmd == "ls":
            ls(filename)
        else:
            ret = 1
    except Exception:
        ret = 1

    raise SystemExit(ret)

import pathlib


def main(filename: pathlib.Path, *, outfile: pathlib.Path | None = None) -> int:
    if not filename.exists():
        print(f"ERROR: Filename does not exist: '{filename}'")
        return 1

    with open(filename, encoding="utf-8") as inf:
        contents = inf.read()

    result = contents.split("\n# ")
    if not result:
        print(f"ERROR: Could not find any sections in file: '{filename}'")
        return 1

    # remove the h1 title and unindent all other sections
    latest = "\n".join(
        line.replace("##", "#") for line in result[0].strip().split("\n")[2:]
    )

    if outfile is not None:
        with open(outfile, "w", encoding="utf-8") as outf:
            print(latest, file=outf)
    else:
        print(latest)

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("changelog", default="CHANGELOG.md", type=pathlib.Path)
    parser.add_argument("-o", "--outfile", default=None, type=pathlib.Path)
    args = parser.parse_args()

    raise SystemExit(main(args.changelog, outfile=args.outfile))

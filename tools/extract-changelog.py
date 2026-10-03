# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "markdown-it-py>=3.0",
# ]
# ///
from __future__ import annotations

import pathlib


def unwrap_markdown(text: str) -> str:
    from markdown_it import MarkdownIt  # ty: ignore[unresolved-import]

    md = MarkdownIt("commonmark")

    # NOTE: `inline` tokens cover the source lines of a single paragraph or
    # list item, so consecutive lines within a token are soft-wrapped
    joins: set[int] = set()
    for token in md.parse(text):
        if token.type == "inline" and token.map is not None:
            start, end = token.map
            joins.update(range(start, end - 1))

    lines = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        current = lines[i].rstrip()
        while i in joins:
            i += 1
            current = f"{current} {lines[i].strip()}"
        result.append(current)
        i += 1

    return "\n".join(result)


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
    latest = unwrap_markdown(latest)

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

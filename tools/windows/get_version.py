#!/usr/bin/env python

from packaging.version import Version
import subprocess
from typing import Literal

import pytest
import click


Mode = Literal["python", "msi"]


def get_version(description: str, mode: Mode) -> str:
    if "-" in description:
        # Expected version like v0.14-1-f00b4r
        raw_version, count, commit_hash = description.split("-")
    else:
        # Otherwise version like v0.14
        raw_version = description
        count = "0"
        commit_hash = ""

    version = Version(raw_version)

    if mode == "python":
        # `git describe --tags` returns v.0.14
        if count == "0":
            return raw_version
        # `git describe --tags` returns v0.14-1-f00b4r
        else:
            return f"{raw_version}.dev{count}+g{commit_hash}"

    # MSI versions can be either X.Y.Z.W or X.Y.Z-LABEL.W
    elif mode == "msi":
        if version.is_prerelease and version.pre is not None:
            prerelease_id = f"{version.pre[0]}.{version.pre[1]}"
            # This yields, for example, 0.14.0-rc.1
            return f"{version.major}.{version.minor}.{version.micro}-{prerelease_id}"
        else:
            # 0.14.0.X where X is the commit count after last the tagged commit
            return f"{version.major}.{version.minor}.{version.micro}.{count}"


@pytest.mark.parametrize(
    "git_description, mode, expected",
    [
        # Release commits
        ("v0.14", "python", "v0.14"),
        ("v0.14", "msi", "0.14.0.0"),
        # Release candidates
        ("v0.14rc3", "python", "v0.14rc3"),
        ("v0.14rc3", "msi", "0.14.0-rc.3"),
        # A commit after release
        ("v0.14-1-g6d2f2957", "python", "v0.14+dev1+gg6d2f2957"),
        ("v0.14-1-g6d2f2957", "msi", "0.14.0.1"),
    ],
)
def test_get_version(git_description: str, mode: Mode, expected: str) -> None:
    assert get_version(git_description, mode) == expected


@click.command()
@click.argument("mode", type=click.Choice(["python", "msi"]))
def main(mode: Mode) -> None:
    """
    Return a version compatible with either Python modules or MSI packages.
    """
    cmd = "git describe --tags --no-dirty".split()
    description = subprocess.run(cmd, capture_output=True, text=True)
    result = get_version(description.stdout, mode)
    click.echo(result)


if __name__ == "__main__":
    main()

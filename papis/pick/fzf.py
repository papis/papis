import re
import subprocess as sp
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Generic, TypeVar

from papis.pick import Picker

T = TypeVar("T")

# NOTE: This version is required for the 'become' action used in the commands
#   https://github.com/junegunn/fzf/releases/tag/0.38.0
MIN_FZF_VERSION = (0, 38, 0)


def fzf_version(exe: str = "fzf") -> tuple[int, int, int]:
    result = sp.run([exe, "--version"], capture_output=True, check=True)
    version, _ = result.stdout.decode("utf-8").split()

    parts = version.split(".")
    if len(parts) == 3:
        major, minor, patch = parts
    elif len(parts) == 2:
        major, minor = parts
        patch = "0"
    else:
        major = minor = patch = "0"

    return int(major), int(minor), int(patch)


class Command(ABC, Generic[T]):
    regex: re.Pattern[str] | None = None
    command: str = ""
    key: str = ""

    def binding(self) -> str:
        return f"{self.key}:{self.command}"

    def indices(self, line: str) -> list[int] | None:
        m = self.regex.match(line) if self.regex else None
        return [int(i) for i in m.group(1).split()] if m else None

    @abstractmethod
    def run(self, docs: list[T]) -> list[T]:
        pass


class Browse(Command[T]):
    regex = re.compile(r"browse ([\d ]+)")
    command = "become(echo browse {+n})"
    key = "ctrl-b"

    def run(self, docs: list[T]) -> list[T]:  # noqa: PLR6301
        from papis.commands.browse import run
        from papis.document import Document

        for doc in docs:
            if isinstance(doc, Document):
                run(doc)
        return []


class Choose(Command[T]):
    regex = re.compile(r"choose ([\d ]+)")
    command = "become(echo choose {+n})"
    key = "enter"

    def run(self, docs: list[T]) -> list[T]:  # noqa: PLR6301
        return docs


class Edit(Command[T]):
    regex = re.compile(r"edit ([\d ]+)")
    command = "become(echo edit {+n})"
    key = "ctrl-e"

    def run(self, docs: list[T]) -> list[T]:  # noqa: PLR6301
        from papis.commands.edit import run
        from papis.document import Document

        for doc in docs:
            if isinstance(doc, Document):
                run(doc)
        return []


class EditNote(Command[T]):
    regex = re.compile(r"edit_notes ([\d ]+)")
    command = "become(echo edit_notes {+n})"
    key = "ctrl-q"

    def run(self, docs: list[T]) -> list[T]:  # noqa: PLR6301
        from papis.commands.edit import edit_notes
        from papis.document import Document

        for doc in docs:
            if isinstance(doc, Document):
                edit_notes(doc)
        return []


class Open(Command[T]):
    regex = re.compile(r"open ([\d ]+)")
    command = "become(echo open {+n})"
    key = "ctrl-o"

    def run(self, docs: list[T]) -> list[T]:  # noqa: PLR6301
        from papis.commands.open import run
        from papis.document import Document

        for doc in docs:
            if isinstance(doc, Document):
                run(doc)
        return []


class FzfPicker(Picker[T]):
    """A picker that uses ``fzf`` as a backend."""

    def __call__(self,
                 items: Sequence[T],
                 header_filter: Callable[[T], str] = str,
                 match_filter: Callable[[T], str] = str,
                 default_index: int = 0) -> list[T]:
        if len(items) == 0:
            return []

        if len(items) == 1:
            return [items[0]]

        import papis.config
        from papis.format import format

        fzf = papis.config.getstring("fzf-binary")
        version = fzf_version(fzf)
        if version < MIN_FZF_VERSION:
            raise ValueError(
                f"Found 'fzf' version {version} but "
                f"version >={MIN_FZF_VERSION} is required")

        commands: list[Command[T]] = [Browse(), Choose(), Open(), Edit(), EditNote()]

        bindings = (
            [c.binding() for c in commands]
            + papis.config.getlist("fzf-extra-bindings"))

        command = [
            fzf, "--bind", ",".join(bindings),
            *papis.config.getlist("fzf-extra-flags")]

        fmt = papis.config.getformatpattern("fzf-header-format")

        def _header_filter(d: T) -> str:
            if isinstance(d, papis.document.Document):
                import colorama
                return format(fmt, d, additional={"c": colorama})
            else:
                return header_filter(d)

        headers = [_header_filter(o) for o in items]
        docs: list[T] = []

        with sp.Popen(command, stdin=sp.PIPE, stdout=sp.PIPE) as p:
            if p.stdin is not None:
                with p.stdin as stdin:
                    for h in headers:
                        stdin.write((h + "\n").encode())
            if p.stdout is not None:
                for line in p.stdout.readlines():
                    for c in commands:
                        indices = c.indices(line.decode())
                        if not indices:
                            continue
                        docs = c.run([items[i] for i in indices])

        return docs

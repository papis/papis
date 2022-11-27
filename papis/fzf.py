import re
from abc import ABC, abstractmethod
from typing.re import Pattern
from typing import Callable, Sequence, TypeVar, List, Optional, Generic

import papis.pick
import papis.config
import papis.format

T = TypeVar("T")


class Command(ABC, Generic[T]):
    regex = None  # type: Optional[Pattern]
    command = ""  # type: str
    key = ""  # type: str

    def binding(self) -> str:
        return "{0}:{1}".format(self.key, self.command)

    def indices(self, line: str) -> Optional[List[int]]:
        m = self.regex.match(line) if self.regex else None
        return [int(i) for i in m.group(1).split()] if m else None

    @abstractmethod
    def run(self, docs: Sequence[T]) -> Sequence[T]:
        pass


class Choose(Command[T]):
    regex = re.compile(r"choose ([\d ]+)")
    command = "execute(echo choose {+n})+accept"
    key = "enter"

    def run(self, docs: Sequence[T]) -> Sequence[T]:
        return docs


class Edit(Command[T]):
    regex = re.compile(r"edit ([\d ]+)")
    command = "execute(echo edit {+n})"
    key = "ctrl-e"

    def run(self, docs: Sequence[T]) -> Sequence[T]:
        from papis.commands.edit import run
        for doc in docs:
            if isinstance(doc, papis.document.Document):
                run(doc)
        return []


class Open(Command[T]):
    regex = re.compile(r"open ([\d ]+)")
    command = "execute(echo open {+n})"
    key = "ctrl-o"

    def run(self, docs: Sequence[T]) -> Sequence[T]:
        from papis.commands.open import run
        for doc in docs:
            if isinstance(doc, papis.document.Document):
                run(doc)
        return []


class Picker(papis.pick.Picker[T]):
    def __call__(self,
                 options: Sequence[T],
                 header_filter: Callable[[T], str] = str,
                 match_filter: Callable[[T], str] = str,
                 default_index: int = 0) -> Sequence[T]:

        if len(options) == 0:
            return []
        if len(options) == 1:
            return [options[0]]

        commands = [Choose(), Open(), Edit()]  # type: Sequence[Command[T]]

        bindings = [c.binding() for c in commands
                    ] + papis.config.getlist("fzf-extra-bindings")

        command = [papis.config.getstring("fzf-binary"),
                   "--bind", ",".join(bindings)
                   ] + papis.config.getlist("fzf-extra-flags")

        _fmt = papis.config.getstring("fzf-header-format")

        def _header_filter(d: T) -> str:
            if isinstance(d, papis.document.Document):
                import colorama
                return papis.format.format(_fmt,
                                           d,
                                           additional={"c": colorama})
            else:
                return header_filter(d)

        headers = [_header_filter(o) for o in options]
        docs = []  # type: Sequence[T]

        import subprocess as sp
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
                        docs = c.run([options[i] for i in indices])

        return docs

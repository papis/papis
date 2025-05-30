import pytest


def test_confirm(monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.tui.utils

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "prompt", lambda *args, **kwargs: "y")
        assert papis.tui.utils.confirm("This is true")

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "prompt", lambda *args, **kwargs: "Y")
        assert papis.tui.utils.confirm("This is true")

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "prompt", lambda *args, **kwargs: "n")
        assert not papis.tui.utils.confirm("This is false")

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "prompt", lambda *args, **kwargs: "N")
        assert not papis.tui.utils.confirm("This is false")

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "prompt", lambda *args, **kwargs: "\n")
        assert papis.tui.utils.confirm("This is true")

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "prompt", lambda *args, **kwargs: "\n")
        assert not papis.tui.utils.confirm("This is false", yes=False)


def test_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    import prompt_toolkit
    import papis.tui.utils

    with monkeypatch.context() as m:
        m.setattr(prompt_toolkit, "prompt", lambda *args, **kwargs: "Hello World")
        assert papis.tui.utils.prompt("What: ") == "Hello World"

    with monkeypatch.context() as m:
        m.setattr(prompt_toolkit, "prompt", lambda *args, **kwargs: "")
        assert papis.tui.utils.prompt("What: ", default="Bye") == "Bye"


def test_get_range() -> None:
    from papis.tui.utils import get_range

    assert get_range("2") == [2]
    assert get_range("2, 3") == [2, 3] == get_range("2  3") == get_range("2-3")
    assert get_range("0, 1 2-20 21-200") == list(range(0, 201))
    assert get_range("0, 2-20 1 21-200") == [0, *range(2, 21), 1, *range(21, 201)]
    assert get_range("hello") == []


def test_select_range() -> None:
    from papis.tui.utils import select_range
    assert select_range([], "select") == []

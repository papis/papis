from unittest.mock import patch
from papis.tui.utils import confirm, prompt, get_range, select_range


def test_confirm():
    with patch("papis.tui.utils.prompt", lambda prompt, **x: "y"):
        assert confirm("This is true")
    with patch("papis.tui.utils.prompt", lambda prompt, **x: "Y"):
        assert confirm("This is true")
    with patch("papis.tui.utils.prompt", lambda prompt, **x: "n"):
        assert not confirm("This is false")
    with patch("papis.tui.utils.prompt", lambda prompt, **x: "N"):
        assert not confirm("This is false")

    with patch("papis.tui.utils.prompt", lambda prompt, **x: "\n"):
        assert confirm("This is true")
    with patch("papis.tui.utils.prompt", lambda prompt, **x: "\n"):
        assert not confirm("This is false", yes=False)


def test_prompt():
    with patch("prompt_toolkit.prompt", lambda p, **x: "Hello World"):
        assert prompt("What: ") == "Hello World"
    with patch("prompt_toolkit.prompt", lambda p, **x: ""):
        assert prompt("What: ", default="Bye") == "Bye"


def test_get_range():
    assert get_range("2") == [2]
    assert get_range("2, 3") == [2, 3] == get_range("2  3") == get_range("2-3")
    assert get_range("0, 1 2-20 21-200") == list(range(0, 201))
    assert get_range("0, 2-20 1 21-200") == (
        [0] + list(range(2, 21)) + [1] + list(range(21, 201)))
    assert get_range("hello") == []


def test_select_range():
    assert select_range([], "select") == []

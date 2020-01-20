from unittest.mock import patch
from papis.tui.utils import confirm, prompt


def test_confirm():
    with patch('papis.tui.utils.prompt', lambda prompt, **x: 'y'):
        assert(confirm('This is true'))
    with patch('papis.tui.utils.prompt', lambda prompt, **x: 'Y'):
        assert(confirm('This is true'))
    with patch('papis.tui.utils.prompt', lambda prompt, **x: 'n'):
        assert(not confirm('This is false'))
    with patch('papis.tui.utils.prompt', lambda prompt, **x: 'N'):
        assert(not confirm('This is false'))

    with patch('papis.tui.utils.prompt', lambda prompt, **x: '\n'):
        assert(confirm('This is true'))
    with patch('papis.tui.utils.prompt', lambda prompt, **x: '\n'):
        assert(not confirm('This is false', yes=False))


def test_prompt():
    with patch('prompt_toolkit.prompt', lambda p, **x: 'Hello World'):
        assert(prompt('What: ') == 'Hello World')
    with patch('prompt_toolkit.prompt', lambda p, **x: ''):
        assert(prompt('What: ', default='Bye') == 'Bye')

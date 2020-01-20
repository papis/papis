import re
from papis.tui.widgets.list import match_against_regex, OptionsList
from prompt_toolkit.layout.screen import Point


def test_basic():
    ol = OptionsList(['hello', 'world', '<bye'])
    assert(ol.get_selection() == ['hello'])
    assert(len(ol.marks) == 0)
    assert(len(ol.indices) == 3)
    ol.move_down()
    assert(ol.get_selection() == ['world'])
    ol.move_up()
    assert(ol.get_selection() == ['hello'])
    ol.mark_current_selection()
    assert(ol.marks == [0])
    ol.move_down()
    ol.move_down()
    ol.mark_current_selection()
    assert(ol.marks == [0, 2])
    ol.toggle_mark_current_selection()
    assert(ol.marks == [0])
    # fg:red because it failed
    assert(
        ol.get_tokens() ==
        [('', 'hello\n'), ('', 'world\n'), ('fg:red', '<bye\n')]
    )
    assert(
        ol.get_line_prefix(2, None) ==
        [('class:options_list.selected_margin', '|')]
    )
    assert(
        ol.get_line_prefix(1, None) ==
        [('class:options_list.unselected_margin', ' ')]
    )
    assert(
        ol.get_line_prefix(0, None) ==
        [('class:options_list.marked_margin', '#')]
    )

    assert(ol.search_regex == re.compile('.*', re.I))
    ol.search_buffer.text = 'l'
    assert(ol.search_regex == re.compile('.*l', re.I))
    assert(ol.indices == [0, 1])
    ol.search_buffer.text = 'l  '
    assert(ol.search_regex == re.compile('.*l.*', re.I))
    assert(ol.indices == [0, 1])
    assert(len(ol.get_options()) == 3)
    ol.deselect()
    assert(ol.current_index is None)

    ol.set_options([str(i) for i in range(1000)])
    assert(len(ol.marks) == 0)
    assert(len(ol.indices) == 1000)
    ol.go_top()
    assert(ol.get_selection() == ['0'])
    ol.move_up()
    assert(ol.get_selection() == ['999'])
    ol.move_down()
    assert(ol.get_selection() == ['0'])
    ol.go_bottom()
    assert(ol.get_selection() == ['999'])
    ol.search_buffer.text = 'asdfadsf'
    assert(ol.indices == [])
    ol.update_cursor()
    assert(ol.cursor == Point(0, 0))
    # when there is nothing selected and appearing it's ok to
    # move up and down
    ol.move_down()
    ol.move_up()

    ol.go_top()
    ol.search_buffer.text = '99'
    assert(len(ol.indices) == 19)
    ol.update()


def test_match_against_regex():
    assert match_against_regex(re.compile(r'.*he.*'), 'he', 2) == 2
    assert match_against_regex(re.compile(r'hes'), 'he', 2) is None

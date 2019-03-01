from papis.tui.widgets.list import *


def test_basic():
    ol = OptionsList(['hello', 'world'])
    assert(ol.get_selection() == 'hello')
    assert(len(ol.marks) == 0)
    assert(len(ol.indices) == 2)
    ol.move_down()
    assert(ol.get_selection() == 'world')
    ol.move_up()
    assert(ol.get_selection() == 'hello')
    ol.mark_current_selection()
    assert(ol.marks == [0])

    ol.options = [str(i) for i in range(1000)]
    assert(len(ol.marks) == 0)
    assert(len(ol.indices) == 1000)
    ol.go_bottom()
    assert(ol.get_selection() == '999')
    ol.go_top()
    assert(ol.get_selection() == '0')

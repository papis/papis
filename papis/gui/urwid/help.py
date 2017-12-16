import urwid

############################################################

class Help(urwid.WidgetWrap):

    def __init__(self, ui, target=None):
        self.ui = ui
        self.target = target

        if self.target:
            tname = self.target.__class__.__name__
            self.ui.set_header("Help: " + tname)
        else:
            self.ui.set_header("Help")

        pile = []


        if self.target and hasattr(self.target, 'keys'):
            pile.append(urwid.Text('%s commands:' % (tname)))
            pile.append(urwid.Text(''))
            for key, cmd in sorted(self.target.keys.items()):
                pile.append(self.row('target', cmd, key))
            pile.append(urwid.Text(''))
            pile.append(urwid.Text(''))

        pile.append(urwid.Text('Global commands:'))
        pile.append(urwid.Text(''))
        for key, cmd in sorted(self.ui.keys.items()):
            pile.append(self.row('ui', cmd, key))

        w = urwid.Filler(urwid.Pile(pile))
        self.__super.__init__(w)

    def row(self, c, cmd, key):
        hstring = eval('str(self.%s.%s.__doc__)' % (c, cmd))
        return urwid.Columns(
            [
                ('fixed', 8,
                 urwid.Text(key)),
                urwid.Text(hstring),
                 ]
                )

    def keypress(self, size, key):
        self.ui.keypress(key)

import urwid


class Bibview(urwid.WidgetWrap):

    def __init__(self, ui, query):
        self.ui = ui

        self.ui.set_header("Bibtex: " + query)

        docs = self.ui.db.search(query)
        if len(docs) == 0:
            self.ui.set_status('No documents found.')

        string = ''
        for doc in docs:
            string = string + doc.to_bibtex() + '\n'

        self.box = urwid.Filler(urwid.Text(string))
        w = self.box

        self.__super.__init__(w)

    def keypress(self, size, key):
        self.ui.keypress(key)

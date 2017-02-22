#-*-coding:utf-8-*-
# adapted from
# https://github.com/wong2/pick

import curses
import re


__all__ = ['Picker', 'pick']

Ctrl_P = 16
Ctrl_N = 14
Ctrl_H = 8
Ctrl_C = 3
KEYS_ENTER = (curses.KEY_ENTER, ord('\n'), ord('\r'))
KEYS_UP = (curses.KEY_UP, Ctrl_P)
KEYS_DOWN = (curses.KEY_DOWN, Ctrl_N)
KEYS_ERASE = (curses.KEY_BACKSPACE, Ctrl_H)
KEYS_QUIT = (Ctrl_C, curses.KEY_EXIT, 27)

class Picker(object):
    """The :class:`Picker <Picker>` object

    :param options: a list of options to choose from
    :param title: (optional) a title above options list
    :param indicator: (optional) custom the selection indicator
    :param default_index: (optional) set this if the default selected option is not the first one
    """

    def __init__(self, options, title=None, indicator='*', default_index=0):

        if len(options) == 0:
            raise ValueError('options should not be an empty list')

        self.options = options
        self.title = title
        self.indicator = indicator
        self.search = ""

        if default_index >= len(options):
            raise ValueError('default_index should be less than the length of options')

        self.index = default_index
        self.custom_handlers = {}

    def register_custom_handler(self, key, func):
        self.custom_handlers[key] = func

    def move_up(self):
        self.index -= 1
        if self.index < 0:
            self.index = len(self.options) - 1

    def move_down(self):
        self.index += 1
        if self.index >= len(self.options):
            self.index = 0

    def get_selected(self):
        """return the current selected option as a tuple: (option, index)
        """
        return self.get_filtered_options()[self.index]

    def get_title_lines(self):
        return [self.title+self.search+"  --"+self.get_search_regex()]

    def get_option_lines(self):
        lines = []
        index_found = False
        last_index = -1
        for index, option in enumerate(self.get_filtered_options()):
            last_index += 1
            if index == self.index:
                index_found = True
                prefix = self.indicator
            else:
                prefix = len(self.indicator) * ' '
            line = '{0} {1}'.format(prefix, option)
            lines.append(line)
        if not index_found:
            self.index = last_index
            if len(lines):
                lines[-1] = "{0} {1}".format(self.indicator, lines[-1].strip(" "))

        return lines

    def get_search_regex(self):
        """TODO: Docstring for get_search_regex.
        :returns: TODO

        """
        return r".*"+re.sub(r"(.)", r"\1.*", self.search)

    def get_filtered_options(self):
        """TODO: Docstring for get_filtered_options.
        :returns: TODO

        """
        new_lines = []
        regex = self.get_search_regex()
        for line in self.options:
            if re.match(regex, line):
                new_lines += [line]
        return new_lines

    def get_lines(self):
        """TODO: Docstring for get_filtered_lines.
        :returns: TODO

        """
        title_lines = self.get_title_lines()
        option_lines = self.get_option_lines()
        lines = title_lines + option_lines
        current_line = self.index + len(title_lines) + 1
        return lines, current_line

    def draw(self):
        """draw the curses ui on the screen, handle scroll if needed"""
        self.screen.clear()

        x, y = 1, 1  # start point
        max_y, max_x = self.screen.getmaxyx()
        max_rows = max_y - y  # the max rows we can draw

        lines, current_line = self.get_lines()

        # calculate how many lines we should scroll, relative to the top
        scroll_top = getattr(self, 'scroll_top', 0)
        if current_line <= scroll_top:
            scroll_top = 0
        elif current_line - scroll_top > max_rows:
            scroll_top = current_line - max_rows
        self.scroll_top = scroll_top

        lines_to_draw = lines[scroll_top:scroll_top+max_rows]

        for line in lines_to_draw:
            self.screen.addnstr(y, x, line, max_x-2)
            y += 1

        self.screen.refresh()

    def editSearch(self, c):
        """TODO: Docstring for editSearch.

        :c: TODO
        :returns: TODO

        """
        if c in KEYS_ERASE:
            self.search = self.search[0:-1]
        else:
            self.search += chr(c)

    def run_loop(self):
        while True:
            self.draw()
            c = self.screen.getch()
            if c in KEYS_UP:
                self.move_up()
            elif c in KEYS_DOWN:
                self.move_down()
            elif c in KEYS_ENTER:
                return self.get_selected()
            elif c in KEYS_QUIT:
                return ""
            else:
                self.editSearch(c)

    def config_curses(self):
        # use the default colors of the terminal
        curses.use_default_colors()
        # hide the cursor
        curses.curs_set(0)

    def _start(self, screen):
        self.screen = screen
        self.config_curses()
        return self.run_loop()

    def start(self):
        return curses.wrapper(self._start)


def pick(options, title="Pick: ", indicator='>', default_index=0):
    """Construct and start a :class:`Picker <Picker>`.
    """
    picker = Picker(options, title, indicator, default_index)
    return picker.start()

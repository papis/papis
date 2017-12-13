"""
This file is part of xapers.

Xapers is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

Xapers is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with notmuch.  If not, see <http://www.gnu.org/licenses/>.

Copyright 2012, 2013
Jameson Rollins <jrollins@finestructure.net>
"""

import sys
import urwid
from .search import Search
from .bibview import Bibview
from .help import Help

import papis.database
import papis.config


class UI():

    palette = [
        ('header', 'white', 'dark blue'),
        ('footer', 'white', 'dark blue'),
        ('prompt', 'black', 'light green'),
        ('error', 'black', 'light red'),
    ]

    keys = {
        papis.config.get("help-key", section="urwid-gui"): "help",
        papis.config.get("prompt-key", section="urwid-gui"): "prompt_enter",
        papis.config.get("search-key", section="urwid-gui"): "prompt_search",
        papis.config.get("kill-buffer-key", section="urwid-gui"): "kill_buffer",
        papis.config.get("quit-key", section="urwid-gui"): "quit",
        papis.config.get("redraw-key", section="urwid-gui"): "redraw",
    }

    def __init__(self, db=None, cmd=None):
        self.db = papis.database.Database()

        self.header_string = "Papis"
        self.status_string = "q: quit buffer, Q: quit Papis, ?: help"

        self.view = urwid.Frame(urwid.SolidFill())
        self.set_header()
        self.set_status()

        if not cmd:
            cmd = ['search', '']

        if cmd[0] == 'search':
            query = ' '.join(cmd[1:])
            self.buffer = Search(self, query)
        elif cmd[0] == 'bibview':
            query = ' '.join(cmd[1:])
            self.buffer = Bibview(self, query)
        elif cmd[0] == 'help':
            target = None
            if len(cmd) > 1:
                target = cmd[1]
            if isinstance(target, str):
                target = None
            self.buffer = Help(self, target)
        else:
            self.buffer = Help(self)
            self.set_status("Unknown command '%s'." % (cmd[0]))

        self.merge_palette(self.buffer)

        self.view.body = urwid.AttrMap(self.buffer, 'body')

        self.mainloop = urwid.MainLoop(
            self.view,
            self.palette,
            unhandled_input=self.keypress,
            handle_mouse=False,
        )

    def main(self):
        self.mainloop.run()

    ##########

    def merge_palette(self, buffer):
        if hasattr(buffer, 'palette'):
            self.palette = list(set(self.palette) | set(buffer.palette))

    def set_header(self, text=None):
        if text:
            self.header_string = '%s' % (text)
        self.view.set_header(urwid.AttrMap(urwid.Text(self.header_string), 'header'))

    def set_status(self, text=None):
        if text:
            self.status_string = '%s' % (text)
        self.view.set_footer(
            urwid.AttrMap(urwid.Text(self.status_string), 'footer')
        )

    def newbuffer(self, cmd):
        UI(db=self.db, cmd=cmd).main()
        self.set_status()

    def prompt(self, string):
        prompt = PromptEdit(string)
        self.view.set_footer(urwid.AttrMap(prompt, 'prompt'))
        self.view.set_focus('footer')
        return prompt

    ##########

    def prompt_enter(self):
        """Prompt enter"""
        prompt = ':'
        urwid.connect_signal(
            self.prompt(prompt),
            'done',
            self._prompt_enter_done
        )

    def _prompt_enter_done(self, query):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self,
            self.prompt,
            'done',
            self._prompt_search_done
        )
        if not query:
            self.set_status()
            return
        self.set_status(query)
        match = re.match(r" *([a-z]+)  *(.*)", query)
        if match:
            cmd = match.group(1)
            args = match.group(2)
            # self.set_status(cmd + args)
            self.newbuffer([cmd, args])
        else:
            self.echoerr(
                "No such command (%s)" % query
            )

    def prompt_search(self):
        """search database"""
        prompt = 'search: '
        urwid.connect_signal(
            self.prompt(prompt),
            'done',
            self._prompt_search_done
        )

    def _prompt_search_done(self, query):
        self.view.set_focus('body')
        urwid.disconnect_signal(
            self,
            self.prompt,
            'done',
            self._prompt_search_done
        )
        if not query:
            self.set_status()
            return
        self.newbuffer(['search', query])

    def kill_buffer(self):
        """Kill current buffer"""
        raise urwid.ExitMainLoop()

    def redraw(self):
        """Redraw screen"""
        self.set_status("Redrawing...")
        self.mainloop.draw_screen()

    def quit(self):
        """Quit Papis"""
        sys.exit()

    def help(self):
        """Show help"""
        self.newbuffer(['help', self.buffer])

    def keypress(self, key):
        if key in self.keys:
            cmd = "self.%s()" % (self.keys[key])
            eval(cmd)


class PromptEdit(urwid.Edit):
    __metaclass__ = urwid.signals.MetaSignals
    signals = ['done']

    def keypress(self, size, key):
        if key == 'enter':
            urwid.emit_signal(self, 'done', self.get_edit_text())
            return
        elif key == 'esc':
            urwid.emit_signal(self, 'done', None)
            return

        urwid.Edit.keypress(self, size, key)

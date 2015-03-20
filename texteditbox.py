"""Simple textbox editing widget with Emacs-like keybindings."""

import curses
import curses.ascii


def rectangle(win, uly, ulx, lry, lrx):
    """Draw a rectangle with corners at the provided upper-left
    and lower-right coordinates.
    """
    win.vline(uly + 1, ulx, curses.ACS_VLINE, lry - uly - 1)
    win.hline(uly, ulx + 1, curses.ACS_HLINE, lrx - ulx - 1)
    win.hline(lry, ulx + 1, curses.ACS_HLINE, lrx - ulx - 1)
    win.vline(uly + 1, lrx, curses.ACS_VLINE, lry - uly - 1)
    win.addch(uly, ulx, curses.ACS_ULCORNER)
    win.addch(uly, lrx, curses.ACS_URCORNER)
    win.addch(lry, lrx, curses.ACS_LRCORNER)
    win.addch(lry, ulx, curses.ACS_LLCORNER)


class TextEditBox:

    """Editing widget using the interior of a window object.
     Supports the following Emacs-like key bindings:

    Ctrl-A      Go to left edge of window.
    Ctrl-B      Cursor left, wrapping to previous line if appropriate.
    Ctrl-D      Delete character under cursor.
    Ctrl-E      Go to right edge (stripspaces off) or end of line (stripspaces on).
    Ctrl-F      Cursor right, wrapping to next line when appropriate.
    Ctrl-G      Terminate, returning the window contents.
    Ctrl-H      Delete character backward.
    Ctrl-J      Terminate if the window is 1 line, otherwise insert newline.
    Ctrl-K      If line is blank, delete it, otherwise clear to end of line.
    Ctrl-L      Refresh screen.
    Ctrl-N      Cursor down; move down one line.
    Ctrl-O      Insert a blank line at cursor location.
    Ctrl-P      Cursor up; move up one line.

    Move operations do nothing if the cursor is at an edge where the movement
    is not possible.  The following synonyms are supported where possible:

    KEY_LEFT = Ctrl-B, KEY_RIGHT = Ctrl-F, KEY_UP = Ctrl-P, KEY_DOWN = Ctrl-N
    KEY_BACKSPACE = Ctrl-h
    """

    def __init__(self, win, insert_mode=True):
        self.win = win
        self.insert_mode = insert_mode
        self.lastcmd = None
        self.text = ['']
        self.txln = [0]
        self.ppos = [0, 0] # physical position
        self.vpos = [0, 0] # virtual position
        self.nlines = 1
        win.keypad(1)

    def _getmaxyx(self):
        (maxy, maxx) = self.win.getmaxyx()
        return maxy - 1, maxx - 1

    def _end_of_line(self, y):
        """Go to the location of the first blank on the given line,
        returning the index of the last non-blank character."""
        (maxy, maxx) = self._getmaxyx()
        last = maxx
        while True:
            if curses.ascii.ascii(self.win.inch(y, last)) != curses.ascii.SP:
                last = min(maxx, last + 1)
                break
            elif last == 0:
                break
            last = last - 1
        return last

    def _insert_printable_char(self, ch):

        if self.ppos[1] == 0:
            self.text[self.ppos[0]] = chr(ch) + self.text[self.ppos[0]]
        else:
            self.text[self.ppos[0]]\
                = self.text[self.ppos[0]][:self.ppos[1]] + chr(ch) \
                + self.text[self.ppos[0]][self.ppos[1]:]
        
        (y, x) = self.win.getyx()
        (maxy, maxx) = self._getmaxyx()
        (backy, backx) = self.win.getyx()
        
        trailingstr = self.text[self.ppos[0]][self.ppos[1]+1:]
        try:
            self.win.addch(ch)
        except curses.error:
            pass
        
        if (self.insert_mode):
            self.ppos[1] += 1
            nspaces = maxx - self.ppos[1]
            if nspaces > len(trailingstr):
                self.win.addstr(self.ppos[0], self.ppos[1], trailingstr[:])
            else:
                self.win.addstr(self.ppos[0], self.ppos[1], trailingstr[:nspaces])
                self.win.addstr(self.ppos[0]+1, 0, trailingstr[nspaces:])
                self.ppos[0] += 1

            self.win.move(backy, backx)

    def do_command(self, ch):
        "Process a single editing command."
        (maxy, maxx) = self._getmaxyx()
        self.lastcmd = ch

        if curses.ascii.isprint(ch):
            if self.ppos[0] < maxy or self.ppos[1] < maxx:
                self._insert_printable_char(ch)
            else:
                curses.beep()
            self.win.move(self.ppos[0], self.ppos[1])
                
        elif ch == curses.ascii.SOH:  # ^a
            self.ppos[1] = 0
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch == curses.ascii.ENQ:  # ^e
            self.ppos[1] = len(self.text[self.ppos[0]])
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.STX, curses.KEY_LEFT):
            if self.ppos[1] > 0:
                self.ppos[1] -= 1
                self.win.move(self.ppos[0], self.ppos[1])
            elif self.ppos[0] == 0:
                curses.beep()
                pass
            else:
                self.ppos[0] -= 1
                self.ppos[1] = len(self.text[self.ppos[0]])
                self.win.move(self.ppos[0], self.ppos[1])

        elif ch == curses.ascii.EOT:  # ^d
            if self.ppos[1] == len(self.text[self.ppos[0]]):
                curses.beep()
            else:
                self.text[self.ppos[0]]\
                    = self.text[self.ppos[0]][:self.ppos[1]]\
                    + self.text[self.ppos[0]][self.ppos[1] + 1:]
                self.win.delch()

        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL):
            if self.ppos[1] == 0:
                if self.ppos[0] == 0:
                    curses.beep()
                else:
                    self.ppos[1] = len(self.text[self.ppos[0] - 1])
                    self.text[self.ppos[0] - 1] += self.text[self.ppos[0]]
                    self.text.pop(self.ppos[0])
                    self.nlines -= 1
                    self.ppos[0] -= 1
                    self.redraw_lines(self.ppos[0], self.nlines)
                    self.win.move(self.ppos[0], self.ppos[1])
            else:
                self.text[self.ppos[0]]\
                    = self.text[self.ppos[0]][:self.ppos[1] - 1]\
                    + self.text[self.ppos[0]][self.ppos[1]:]
                self.win.move(self.ppos[0], self.ppos[1] - 1)
                self.win.delch()
                self.ppos[1] -= 1

        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):  # ^f
            if self.ppos[1] < len(self.text[self.ppos[0]]):
                self.ppos[1] += 1
                self.win.move(self.ppos[0], self.ppos[1])
            elif (self.ppos[0] == maxy) | (self.ppos[0] == self.nlines - 1):
                curses.beep()
                pass
            else:
                self.ppos[1] = 0
                self.ppos[0] += 1
                self.win.move(self.ppos[0], 0)

        elif ch in [curses.ascii.NL, curses.ascii.SI]:  # ^j, ^o
            if maxy == 0:
                curses.beep()
                return 0
            elif self.ppos[0] < maxy:
                self.text.insert(self.ppos[0] + 1, self.text[self.ppos[0]][self.ppos[1]:])
                self.text[self.ppos[0]] = self.text[self.ppos[0]][:self.ppos[1]]
                self.ppos[0] += 1
                self.ppos[1] = 0
                self.nlines += 1
                self.redraw_lines(self.ppos[0] - 1, self.nlines)
                self.win.move(self.ppos[0], 0)

        elif ch == curses.ascii.VT:  # ^k
            for c in range(self.ppos[1], len(self.text[self.ppos[0]])):
                self.win.addch(' ')
            self.text[self.ppos[0]]\
                = self.text[self.ppos[0]][:self.ppos[1]]
            self.ppos[1] = len(self.text[self.ppos[0]])
            self.win.move(self.ppos[0], self.ppos[1])
            
        elif ch == curses.ascii.FF:  # ^l
            self.win.refresh()

        elif ch in (curses.ascii.SO, curses.KEY_DOWN):  # ^n
            if self.ppos[0] < (self.nlines - 1):
                self.ppos[0] += 1
                self.ppos[1] = min(self.ppos[1], len(self.text[self.ppos[0]]))
                self.win.move(self.ppos[0], self.ppos[1])
            else:
                curses.beep()

        elif ch in (curses.ascii.DLE, curses.KEY_UP):  # ^p
            if self.ppos[0] > 0:
                self.ppos[0] -= 1
                self.ppos[1] = min(self.ppos[1], len(self.text[self.ppos[0]]))
                self.win.move(self.ppos[0], self.ppos[1])
            else:
                curses.beep()

        elif ch == curses.ascii.BEL:  # ^g
            return 0

        return 1

    def redraw_lines(self, stl, edl):
        "Redraw lines from stl to edl"

        for l in range(stl, edl):
            self.win.deleteln()

        for l in range(stl, edl):
            self.win.addstr(l, 0, self.text[l])

        return

    def edit(self, validate=None):
        "Edit in the widget window and collect the results."
        while 1:
            ch = self.win.getch()
            if validate:
                ch = validate(ch)
            if not ch:
                continue
            if not self.do_command(ch):
                break

            # (backy, backx) = self.win.getyx()
            # maxy, maxx = self._getmaxyx()
            # self.win.addstr(maxy - 2, maxx - 20, '%d %d %d'
                            # % (ch, self.ppos[0], self.ppos[1]))
            # self.win.refresh()

            # self.win.move(backy, backx)

        return self.text


class EscapePressed(Exception):
    pass


def validate(ch):
    "Filters characters for special key sequences"

    if ch == curses.ascii.ESC:
        raise EscapePressed

    if ch == curses.KEY_RESIZE:
        raise EscapePressed

    # Fix backspace for iterm
    if ch == curses.ascii.DEL:
        ch = curses.KEY_BACKSPACE

    return ch


if __name__ == '__main__':
    def test_editbox(stdscr):
        ymax, xmax = stdscr.getmaxyx()

        ncols, nlines = xmax - 5, ymax - 3
        ncols, nlines = 20, 20
        uly, ulx = 2, 2
        stdscr.addstr(uly - 2, ulx, "Use Ctrl-G to end editing.")
        win = curses.newwin(nlines, ncols, uly, ulx)
        rectangle(stdscr, uly - 1, ulx - 1, uly + nlines, ulx + ncols)
        stdscr.refresh()

        try:
            out = TextEditBox(win, stdscr).edit(validate=validate)
        except EscapePressed:
            out = None

        return out

    text = curses.wrapper(test_editbox)
    print 'Contents of text box:', repr(text)

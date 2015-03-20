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


class Textbox:

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
        self.stripspaces = 1
        self.lastcmd = None
        self.text = ['']
        self.ln = 0  # line number
        self.cn = 0  # column number
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
        (y, x) = self.win.getyx()
        (maxy, maxx) = self._getmaxyx()
        (backy, backx) = None, None
        (backy, backx) = 0, 0

        nl = 0
        while (y < maxy and x <= maxx):
            oldch = self.win.inch()
            # The try-catch ignores the error we trigger from some curses
            # versions by trying to write into the lowest-rightmost spot
            # in the window.
            try:
                self.win.addch(ch)
            except curses.error:
                pass

            if not self.insert_mode:
                break

            # Remember where to put the cursor back since we are in insert_mode
            if nl == 0:
                nl = 1
                (backy, backx) = self.win.getyx()

            ch = oldch
            (y, x) = self.win.getyx()
            if (x == 0 and y > 0):
                break

        if self.insert_mode:
            self.win.move(backy, backx)

    def do_command(self, ch):
        "Process a single editing command."
        (maxy, maxx) = self._getmaxyx()
        (y, x) = self.win.getyx()
        self.lastcmd = ch

        if curses.ascii.isprint(ch):
            if y < maxy or x < maxx:
                self._insert_printable_char(ch)
                if self.cn == 0:
                    self.text[self.ln] = chr(ch) + self.text[self.ln]
                else:
                    self.text[self.ln]\
                        = self.text[self.ln][:self.cn] + chr(ch) \
                        + self.text[self.ln][self.cn:]
                self.cn += 1
                
        elif ch == curses.ascii.SOH:  # ^a
            self.cn = 0
            self.win.move(self.ln, self.cn)
            
        elif ch == curses.ascii.ENQ:  # ^e
            self.cn = len(self.text[self.ln])
            self.win.move(self.ln, self.cn)
            
        elif ch in (curses.ascii.STX, curses.KEY_LEFT):
            if x > 0:
                self.cn -= 1
                self.win.move(y, x - 1)
            elif y == 0:
                curses.beep()
                pass
            elif self.stripspaces:
                self.win.move(y - 1, self._end_of_line(y - 1))
                self.ln -= 1
            else:
                self.win.move(y - 1, maxx)
                self.ln -= 1
                self.cn = len(self.text[self.ln])

        elif ch == curses.ascii.EOT:  # ^d
            if self.cn == len(self.text[self.ln]):
                curses.beep()
            else:
                self.text[self.ln]\
                    = self.text[self.ln][:self.cn]\
                    + self.text[self.ln][self.cn+1:]
                self.win.delch()
                
        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL):
            if x == 0:
                curses.beep()
            else:
                self.text[self.ln]\
                    = self.text[self.ln][:self.cn - 1]\
                    + self.text[self.ln][self.cn:]
                self.win.move(y, self.cn - 1)
                self.win.delch()
                self.cn -= 1

        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):  # ^f
            if x < len(self.text[self.ln]):
                self.cn += 1
                self.win.move(y, x + 1)
            elif (y == maxy) | (y == self.nlines - 1):
                curses.beep()
                pass
            else:
                self.cn = 0
                self.ln += 1
                self.win.move(y + 1, 0)
        
        elif ch in [curses.ascii.NL, curses.ascii.SI]:  # ^j, ^o
            if maxy == 0:
                curses.beep()
                return 0
            elif y < maxy:
                self.text.insert(self.ln + 1, self.text[self.ln][self.cn:])
                self.text[self.ln] = self.text[self.ln][:self.cn]
                self.ln += 1
                self.cn = 0
                self.nlines += 1
                self.redraw_lines(self.ln - 1, self.nlines)
                self.win.move(self.ln, 0)
                
        elif ch == curses.ascii.VT:  # ^k
            self.text[self.ln]\
                = self.text[self.ln][:self.cn]
            self.redraw_lines(self.ln, self.ln+1)
            
        elif ch == curses.ascii.FF:  # ^l
            self.win.refresh()

        elif ch in (curses.ascii.SO, curses.KEY_DOWN):  # ^n
            if y < (self.nlines - 1):
                self.cn = min(x, len(self.text[y + 1]))
                self.ln += 1
                self.win.move(self.ln, self.cn)
            else:
                curses.beep()

        elif ch in (curses.ascii.DLE, curses.KEY_UP):  # ^p
            if self.ln > 0:
                self.cn = min(x, len(self.text[y - 1]))
                self.win.move(y - 1, self.cn)
                self.ln -= 1
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

    def gather(self):
        "Collect and return the contents of the window."
        result = ""
        (maxy, maxx) = self._getmaxyx()
        for y in range(maxy + 1):
            self.win.move(y, 0)
            stop = self._end_of_line(y)
            if stop == 0 and self.stripspaces:
                continue
            for x in range(maxx + 1):
                if self.stripspaces and x > stop:
                    break
                result = result + chr(curses.ascii.ascii(self.win.inch(y, x)))
            if maxy > 0:
                result = result + "\n"
        return result, self.text

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

            (backy, backx) = self.win.getyx()
            maxy, maxx = self._getmaxyx()
            self.win.addstr(maxy - 2, maxx - 20, '%d %d %d'
                            % (ch, self.ln, self.cn))
            self.win.refresh()

            self.win.move(backy, backx)

        return self.gather()


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
        uly, ulx = 2, 2
        stdscr.addstr(uly - 2, ulx, "Use Ctrl-G to end editing.")
        win = curses.newwin(nlines, ncols, uly, ulx)
        rectangle(stdscr, uly - 1, ulx - 1, uly + nlines, ulx + ncols)
        stdscr.refresh()

        try:
            out = Textbox(win, stdscr).edit(validate=validate)
        except EscapePressed:
            out = None, None

        return out

    str, text = curses.wrapper(test_editbox)
    print 'Contents of text box:', repr(text)

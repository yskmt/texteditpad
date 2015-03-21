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
        self.lnbg = [[0]]
        self.ppos = (0, 0)  # physical position
        self.vpos = (0, 0)  # virtual position
        (self.maxy, self.maxx) = self._getmaxyx()
        (self.height, self.width) = (self.maxy + 1, self.maxx + 1)
        win.keypad(1)

    def _getmaxyx(self):
        (maxy, maxx) = self.win.getmaxyx()
        return maxy - 1, maxx - 1

    def _insert_printable_char(self, ch):
        trailingstr = self.text[self.vpos[0]][self.vpos[1]:]

        # update text
        self.text[self.vpos[0]]\
            = self.text[self.vpos[0]][:self.vpos[1]] + chr(ch) \
            + trailingstr
        self.vpos = (self.vpos[0], self.vpos[1] + 1)

        # update line count
        self.lnbg[self.vpos[0]] = range(0, len(self.text[self.vpos[0]]),
                                        self.width)
        self.ppos = self.win.getyx()

        # draw the trailing part
        try:
            self.win.addch(ch)
        except curses.error:
            pass
        (backy, backx) = self.win.getyx()

        nspaces = self.maxx - (self.ppos[1])
        # right space big enough to fit the rest of line
        if nspaces > len(trailingstr):
            self.win.addstr(trailingstr)
        # if not
        else:
            self.win.addstr(trailingstr[:nspaces])
            trailingstr = trailingstr[nspaces:]
            pos = (self.ppos[0], 0)

            # draw the rest of the vline
            for ln in range(0, len(trailingstr) / self.width + 1):
                pos = (pos[0] + 1, pos[1])
                self.win.addstr(pos[0], pos[1], ' ' * self.width)
                self.win.addstr(pos[0], pos[1],
                                trailingstr[ln * self.width:(ln + 1) * self.width])

            pos = (pos[0] + 1, pos[1])

            # redraw the remaining vlines
            self.redraw_vlines(pos, self.vpos[0] + 1, len(self.text))

        self.ppos = [backy, backx]
        self.win.move(backy, backx)

    def drawline(self, ln):
        bg = self.lnbg[ln]
        ed = min(len(self.text[bg[0]]) - self.text[bg[0]][bg[1]],  self.maxx)
        self.win.addstr(ln, 0, self.text[bg[0]][bg[1]:ed])

    def do_command(self, ch):
        "Process a single editing command."
        nlines = sum(len(x) for x in self.lnbg)
        self.lastcmd = ch

        if curses.ascii.isprint(ch):
            if self.ppos[0] < self.maxy or self.ppos[1] < self.maxx:
                self._insert_printable_char(ch)
            else:
                curses.beep()

        elif ch == curses.ascii.SOH:  # ^a
            self.ppos = (self.ppos[0], 0)
            self.vpos = (
                self.vpos[0], int((self.vpos[1] / self.width) * self.width))
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch == curses.ascii.ENQ:  # ^e

            if self.vpos[1] < max(self.lnbg[self.vpos[0]]):
                self.ppos = (self.ppos[0], self.maxx)
                self.vpos = (self.vpos[0],
                             int((self.vpos[1] / self.width + 1) * self.width - 1))
            else:
                self.ppos = (self.ppos[0],
                             len(self.text[self.vpos[0]]) % self.width)
                self.vpos = (self.vpos[0], len(self.text[self.vpos[0]]))

            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.STX, curses.KEY_LEFT):  # <-
            if self.ppos[1] > 0:
                self.ppos = (self.ppos[0], self.ppos[1] - 1)
                self.vpos = (self.vpos[0], self.vpos[1] - 1)
            elif self.ppos[0] == 0:
                curses.beep()
                pass
            else:  # move up one line
                if self.vpos[1] == self.lnbg[self.vpos[0]][0]:
                    ll = len(self.text[self.vpos[0] - 1])
                    self.vpos = (self.vpos[0] - 1, ll)
                    self.ppos = (self.ppos[0] - 1, ll % (self.width))
                else:
                    self.vpos = (self.vpos[0], self.vpos[1] - 1)
                    self.ppos = (self.ppos[0] - 1, self.maxx)
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):  # ^f ->
            ll = len(self.text[self.vpos[0]])

            if (self.ppos[1] < self.maxx) and (self.vpos[1] < ll):
                self.ppos = (self.ppos[0], self.ppos[1] + 1)
                self.vpos = (self.vpos[0], self.vpos[1] + 1)

            elif self.ppos[0] == self.maxy or (self.ppos[0] == nlines - 1):
                curses.beep()
                pass

            else:  # move down one line
                if self.vpos[1] == len(self.text[self.vpos[0]]):
                    self.vpos = (self.vpos[0] + 1, 0)
                    self.ppos = (self.ppos[0] + 1, 0)
                else:
                    self.vpos = (self.vpos[0], self.vpos[1] + 1)
                    self.ppos = (self.ppos[0] + 1, 0)
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.SO, curses.KEY_DOWN):  # ^n
            if self.ppos[0] < (nlines - 1):
                # within the same vline
                if self.vpos[1] / self.width \
                   < len(self.text[self.vpos[0]]) / self.width:
                    ll = len(self.text[self.vpos[0]])
                    self.vpos = (
                        self.vpos[0], min(self.vpos[1] + self.width, ll))
                    self.ppos = (self.ppos[0] + 1,
                                 min(self.ppos[1], ll % self.width))
                # move to next vline
                else:
                    ll = len(self.text[self.vpos[0] + 1])
                    self.vpos = (self.vpos[0] + 1,
                                 min(self.vpos[1] % self.width, ll))
                    self.ppos = (self.ppos[0] + 1, min(self.ppos[1], ll))
                self.win.move(self.ppos[0], self.ppos[1])
            else:
                curses.beep()

        elif ch in (curses.ascii.DLE, curses.KEY_UP):  # ^p
            if self.ppos[0] > 0:
                # move to previous vline
                if self.vpos[1] < self.width:
                    ll = len(self.text[self.vpos[0] - 1])
                    vpos1 = min(int((ll / self.width) * self.width) + self.vpos[1],
                                ll)
                    self.vpos = (self.vpos[0] - 1, vpos1)
                    self.ppos = (self.ppos[0] - 1,
                                 min(self.ppos[1], ll % self.width))
                # within the same vline
                else:
                    self.vpos = (self.vpos[0], self.vpos[1] - self.width)
                    self.ppos = (self.ppos[0] - 1, self.ppos[1])

                self.win.move(self.ppos[0], self.ppos[1])
            else:
                curses.beep()

        elif ch in [curses.ascii.NL, curses.ascii.SI]:  # ^j, ^o
            if self.maxy == 0:  # no space
                curses.beep()
                return 0
            elif self.ppos[0] < self.maxy:
                # update texts
                self.text.insert(
                    self.vpos[0] + 1, self.text[self.vpos[0]][self.vpos[1]:])
                self.text[self.vpos[0]] = self.text[
                    self.vpos[0]][:self.vpos[1]]

                # update the line counts
                self.lnbg.insert(self.vpos[0] + 1, [])
                self.lnbg[self.vpos[0]] \
                    = range(0, len(self.text[self.vpos[0]]), self.maxx)
                self.lnbg[self.vpos[0] + 1] \
                    = range(0, len(self.text[self.vpos[0] + 1]), self.maxx)

                if len(self.lnbg[self.vpos[0]]) == 0:
                    self.lnbg[self.vpos[0]] = [0]
                if len(self.lnbg[self.vpos[0] + 1]) == 0:
                    self.lnbg[self.vpos[0] + 1] = [0]

                # clear the right part of the pline
                for c in range(self.ppos[1], self.width):
                    self.win.addch(' ')

                # move p- and v- cursors
                self.ppos = (self.ppos[0] + 1, 0)
                backy, backx = self.ppos
                self.vpos = (self.vpos[0] + 1, 0)

                # redraw the bottom lines
                self.redraw_vlines(self.ppos, self.vpos[0],
                                   len(self.text))

                # move the cursor position back
                self.ppos = (backy, backx)
                self.win.move(self.ppos[0], self.ppos[1])

        elif ch == curses.ascii.EOT:  # ^d
            if (self.vpos[0] == len(self.text) - 1)\
               and (self.vpos[1] == len(self.text[self.vpos[0]])):
                curses.beep()
            else:
                backy, backx = self.ppos
                self.delat(self.vpos)
                self.ppos = (backy, backx)
                self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL):
            if (self.vpos[0] == 0) and (self.vpos[1] == 0):
                curses.beep()
            else:
                # bs at the beginning of a vline
                if self.vpos[1] == 0:
                    ll = len(self.text[self.vpos[0] - 1])
                    vpos = (self.vpos[0] - 1, len(self.text[self.vpos[0] - 1]))
                    ppos = (self.ppos[0] - 1, ll % self.width)
                else:
                    vpos = (self.vpos[0], self.vpos[1] - 1)
                    if self.ppos[1] == 0:
                        ppos = (self.ppos[0] - 1, self.maxx)
                    else:
                        ppos = (self.ppos[0], self.ppos[1] - 1)

                self.delat(vpos)

                self.ppos = ppos
                self.vpos = vpos
                self.win.move(self.ppos[0], self.ppos[1])

            # import pdb
            # curses.endwin()
            # pdb.set_trace()

        elif ch == curses.ascii.VT:  # ^k

            backy, backx = self.ppos
            # update text
            self.text[self.vpos[0]]\
                = self.text[self.vpos[0]][:self.vpos[1]]

            # update line count
            self.lnbg[self.vpos[0]]\
                = range(0, len(self.text[self.vpos[0]]), self.width)
            if len(self.lnbg[self.vpos[0]]) == 0:
                self.lnbg[self.vpos[0]] = [0]

            # redraw the bottom lines
            pos = (sum(len(x) for x in self.lnbg[:self.vpos[0]]), 0)

            self.redraw_vlines(pos, self.vpos[0],
                               len(self.text))

            # set the cursor back
            self.ppos = (backy, backx)
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch == curses.ascii.FF:  # ^l
            self.win.refresh()

        elif ch == curses.ascii.BEL:  # ^g
            return 0

        return 1

    def draw_vline(self, pos, ln):
        "Draw a vline."

        for li in range(0, len(self.text[ln]), self.width):
            self.win.addstr(pos[0], pos[1],
                            self.text[ln][li:li + self.width])
            pos = (pos[0] + 1, pos[1])

        if len(self.text[ln]) == 0:
            pos = (pos[0] + 1, pos[1])

        return pos

    def redraw_vlines(self, pos, stl, edl):
        "Redraw vlines from stl to edl at position pos"

        # clear the redrawn part
        for l in range(pos[0], self.maxy):
            self.win.addstr(l, 0, ' ' * (self.maxx + 1))

        # now draw each line
        for li in range(stl, edl):
            pos = self.draw_vline(pos, li)

        return

    def delat(self, pos):
        "Delete chracter at position pos"

        # del within a line
        if pos[1] < len(self.text[pos[0]]):
            self.text[pos[0]]\
                = self.text[pos[0]][:pos[1]]\
                + self.text[pos[0]][pos[1] + 1:]
            self.lnbg[pos[0]] = range(0, len(self.text[pos[0]]), self.width)
        # del at the end of a line
        else:
            self.text[pos[0]]\
                += self.text[pos[0] + 1]
            self.text.pop(pos[0] + 1)
            self.lnbg[pos[0]] = range(0, len(self.text[pos[0]]), self.width)
            self.lnbg.pop(pos[0] + 1)

        if len(self.lnbg[pos[0]]) == 0:
            self.lnbg[pos[0]] = [0]

        nlines = sum(len(x) for x in self.lnbg[:pos[0]])
        pos = (nlines, 0)
        self.redraw_vlines(pos, pos[0], len(self.text))

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
            self.win.addstr(maxy, 0, ' ' * maxx)
            self.win.addstr(maxy, 0, '%d %d %d %d %d'
                            % (ch, self.vpos[0], self.vpos[1], self.ppos[0], self.ppos[1]))
            # self.win.addstr(maxy, 0, str(self.lnbg))
            self.win.refresh()
            self.win.move(backy, backx)

        return self.text, self.lnbg


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
        ncols, nlines = 20, 10
        uly, ulx = 2, 2
        stdscr.addstr(uly - 2, ulx, "Use Ctrl-G to end editing.")
        win = curses.newwin(nlines, ncols, uly, ulx)
        rectangle(stdscr, uly - 1, ulx - 1, uly + nlines, ulx + ncols)
        stdscr.refresh()

        try:
            out, lnbg = TextEditBox(win, stdscr).edit(validate=validate)
        except EscapePressed:
            out = None

        return out, lnbg

    text, lnbg = curses.wrapper(test_editbox)
    print 'Contents of text box:', repr(text)
    print lnbg

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

    def __init__(self, win, stdscr=0, text='', n_sc=1,
                 insert_mode=True, resize_mode=False):

        self.win = win
        self.stdscr = stdscr
        self.insert_mode = insert_mode
        self.resize_mode = resize_mode
        self.lastcmd = None
        self.text = text.split('\n')
        # virtual position of the beginning of the physical lines
        self.lcount = [1]
        self.ppos = (0, 0)  # physical position of the cursor
        self.vpos = (0, 0)  # virtual position of the cursor
        self.vptl = (0, 0)  # virtual position of the top-left corner
        self.n_sc = n_sc  # how many unit to scroll each time
        (self.maxy, self.maxx) = self._getmaxyx()
        (self.height, self.width) = (self.maxy + 1, self.maxx + 1)

        self.refresh()
        win.keypad(1)

    def _getmaxyx(self):
        (maxy, maxx) = self.win.getmaxyx()
        return maxy - 1, maxx - 1

    def _addch(self, y, x, ch):
        "self.win.addch fix: problem at lower-right corner"
        try:
            self.win.addch(y, x, ch)
        except:
            pass

    def do_command(self, ch):
        "Process a single editing command."
        self.nlines = sum(self.lcount)
        self.lastcmd = ch

        if curses.ascii.isprint(ch):
            if self._insert_printable_char(ch) == 0:
                curses.beep()

        elif ch == curses.KEY_RESIZE:
            self.refresh()

        elif ch == curses.ascii.SOH:  # ^a
            self.move_front()

        elif ch == curses.ascii.ENQ:  # ^e
            self.move_end()

        elif ch in (curses.ascii.STX, curses.KEY_LEFT):  # ^b <-
            self.move_left()

        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):  # ^f ->
            self.move_right()

        elif ch in (curses.ascii.SO, curses.KEY_DOWN):  # ^n down
            self.move_down()

        elif ch in (curses.ascii.DLE, curses.KEY_UP):  # ^p up
            self.move_up()

        elif ch == curses.ascii.NL:  # ^j
            if self.height == 1:
                return 0
            else:
                if self.ppos[0] == self.maxy:
                    self.scroll(self.n_sc)
                self.newline()

        elif ch == curses.ascii.SI:  #  ^o
            if self.ppos[0] == self.maxy:
                self.scroll(self.n_sc)
            self.newline()
                
        elif ch == curses.ascii.EOT:  # ^d
            self.delete()

        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE, curses.ascii.DEL):
            if (self.vpos[0] == 0) and (self.vpos[1] == 0):
                curses.beep()
            else:
                # move one left and del
                self.move_left()
                self.delete()

        elif ch == curses.ascii.VT:  # ^k
            if len(self.text[self.vpos[0]]) == 0:
                # if there is nothing in the vline
                self.delete()
            else:
                self.clear_right()

        elif ch == curses.ascii.FF:  # ^l
            self.refresh()

        elif ch == curses.ascii.BEL:  # ^g
            return 0

        return 1

    def _insert_printable_char(self, ch):
        trailingstr = self.text[self.vpos[0]][self.vpos[1]:]

        # update text
        self.text[self.vpos[0]]\
            = self.text[self.vpos[0]][:self.vpos[1]] + chr(ch) \
            + trailingstr

        # update line count
        self.lcount[self.vpos[0]] = len(
            self.text[self.vpos[0]]) / self.width + 1
        self.nlines = sum(self.lcount)

        # redraw!
        
        if self.ppos[0] == self.maxy and self.ppos[1] == self.maxx:
            self.scroll(self.n_sc)
            (backy, backx) = self.win.getyx()

        else:
            (backy, backx) = self.win.getyx()
            self.redraw_vlines(self.vpos, self.ppos)

        # update cursor position
        if backx + 1 == self.width:
            self.ppos = (backy + 1, 0)
        else:
            self.ppos = (backy, backx + 1)
        self.vpos = (self.vpos[0], self.vpos[1] + 1)
        self.win.move(*self.ppos)

        return 1
        
    def redraw_vlines(self, vpos, ppos):
        "Redraw vlines starting from vpos to the end at ppos"

        # clear the redrawn part
        for i in range(ppos[1], self.width):
            self._addch(ppos[0], i, ' ')
        for l in range(ppos[0] + 1, self.height):
            self.clear_line(l)

        # now draw each characters
        ln = ppos[0]
        cn = ppos[1] % self.width

        # first vline: continuation from the existing vline
        for j in range(vpos[1], len(self.text[vpos[0]])):
            self._addch(ln, cn, self.text[vpos[0]][j])
            if cn + 1 == self.width:
                ln += 1
                if ln == self.height:
                    break
            cn = (cn + 1) % self.width

        cn = 0
        ln += 1

        # the rest of the vlines
        for i in range(vpos[0] + 1, len(self.text)):
            for j in range(len(self.text[i])):
                if ln == self.height:
                    return

                self._addch(ln, cn, self.text[i][j])

                if cn + 1 == self.width:
                    ln += 1
                cn = (cn + 1) % self.width
            cn = 0
            ln += 1

        return

    def move_front(self):
        self.ppos = (self.ppos[0], 0)
        self.vpos = (
            self.vpos[0], int((self.vpos[1] / self.width) * self.width))
        self.win.move(self.ppos[0], self.ppos[1])

    def move_end(self):
        # within a vline
        if (self.vpos[1] / self.width + 1) < self.lcount[self.vpos[0]]:
            self.ppos = (self.ppos[0], self.maxx)
            self.vpos = (self.vpos[0],
                         int((self.vpos[1] / self.width + 1) * self.width - 1))
        # at the end of vline
        else:
            self.ppos = (self.ppos[0],
                         len(self.text[self.vpos[0]]) % self.width)
            self.vpos = (self.vpos[0], len(self.text[self.vpos[0]]))

        self.win.move(self.ppos[0], self.ppos[1])

    def move_left(self):

        if self.ppos[1] > 0:
            self.ppos = (self.ppos[0], self.ppos[1] - 1)
            self.vpos = (self.vpos[0], self.vpos[1] - 1)
        # no space to move
        elif self.vpos[0] == 0 and self.vpos[1] == 0:
            curses.beep()
            return
        else:
            if self.ppos[0] == 0:
                self.scroll(-self.n_sc)
            # move up to previous vline
            if self.vpos[1] == 0:
                ll = len(self.text[self.vpos[0] - 1])
                self.vpos = (self.vpos[0] - 1, ll)
                self.ppos = (self.ppos[0] - 1, ll % (self.width))
            # move up within the same vline
            else:
                self.vpos = (self.vpos[0], self.vpos[1] - 1)
                self.ppos = (self.ppos[0] - 1, self.maxx)
        self.win.move(self.ppos[0], self.ppos[1])

    def move_right(self):

        ll = len(self.text[self.vpos[0]])
        
        if (self.ppos[1] < self.maxx) and (self.vpos[1] < ll):
            self.ppos = (self.ppos[0], self.ppos[1] + 1)
            self.vpos = (self.vpos[0], self.vpos[1] + 1)
        # no space to move
        elif ((self.vpos[0]+1) == len(self.text)) \
                and (self.vpos[1] == ll):
            curses.beep()
            return
        else:
            if self.ppos[0] == self.maxy:
                self.scroll(self.n_sc)
            # move down to next vline
            if self.vpos[1] == ll:
                self.vpos = (self.vpos[0] + 1, 0)
                self.ppos = (self.ppos[0] + 1, 0)
            # move down within the same vline
            else:
                self.vpos = (self.vpos[0], self.vpos[1] + 1)
                self.ppos = (self.ppos[0] + 1, 0)
        self.win.move(self.ppos[0], self.ppos[1])

    def move_down(self):
        
        # no more space to move down
        if (self.vpos[0]+1) == len(self.text)\
           and (self.vpos[1]/self.width+1) == self.lcount[self.vpos[0]]:
            curses.beep()
            return

        else:
            # cursor at the bottom: scroll down
            if self.ppos[0] == self.maxy:
                self.scroll(self.n_sc)

            # within the same vline
            if (self.vpos[1]/self.width+1) < self.lcount[self.vpos[0]]:                
                ll = len(self.text[self.vpos[0]])
                vpos1 = min(self.vpos[1] + self.width, ll)
                self.vpos = (
                    self.vpos[0], vpos1)
                self.ppos = (self.ppos[0] + 1,
                             vpos1 % self.width)
            # move to next vline
            else:
                ll = len(self.text[self.vpos[0] + 1])
                vpos1 = min(self.vpos[1] % self.width, ll)
                self.vpos = (self.vpos[0] + 1,
                             vpos1)
                self.ppos = (self.ppos[0] + 1, vpos1 % self.width)
            self.win.move(self.ppos[0], self.ppos[1])

    def move_up(self):

        # cursor at the top
        if self.ppos[0] == 0:
            if self.vpos[0] == 0 and self.vpos[1] < self.width:
                curses.beep()
                return
            else:
                self.scroll(-self.n_sc)

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

    def scroll(self, n):
        "Scroll down/up by n unit (positive for down)"

        # scroll up to previous vline
        if (self.vptl[1] + self.width * n) < 0:
            self.vptl = (self.vptl[0] + n,
                         len(self.text[self.vptl[0] + n]) / self.width * self.width)
        # scroll up/down within the same vline
        elif (self.vptl[1] + self.width * n) <= len(self.text[self.vptl[0]]):
            self.vptl = (self.vptl[0], self.vptl[1] + self.width * n)
        # scroll down to next vline
        else:
            self.vptl = (self.vptl[0] + n, 0)
        self.ppos = (self.ppos[0] - n, self.ppos[1])

        self.redraw_vlines(self.vptl, (0, 0))
        self.win.move(*self.ppos)

    def delat(self, vpos):
        "Delete chracter at position vpos"

        # del within a vline
        if vpos[1] < len(self.text[vpos[0]]):
            self.text[vpos[0]]\
                = self.text[vpos[0]][:vpos[1]]\
                + self.text[vpos[0]][vpos[1] + 1:]
        # del at the end of a line
        else:
            self.text[vpos[0]]\
                += self.text[vpos[0] + 1]
            self.text.pop(vpos[0] + 1)
            self.lcount.pop(vpos[0] + 1)

        self.lcount[vpos[0]] = len(self.text[vpos[0]]) / self.width + 1
        self.nlines = sum(self.lcount)

        for i in range(self.ppos[1], self.width):
            self._addch(self.ppos[0], i, ' ')

        self.redraw_vlines(vpos, self.ppos)

    def delete(self):
        if (self.vpos[0] == len(self.text) - 1)\
           and (self.vpos[1] == len(self.text[self.vpos[0]])):
            curses.beep()
        else:
            backy, backx = self.ppos
            self.delat(self.vpos)
            self.ppos = (backy, backx)
            self.win.move(self.ppos[0], self.ppos[1])

    def clear_line(self, ln):
        "Clear one line at the line number ln"

        for i in range(self.width):
            self._addch(ln, i, ' ')

    def clear_right(self):
        "Clear right side of the cursor."

        backy, backx = self.ppos
        # update text
        self.text[self.vpos[0]]\
            = self.text[self.vpos[0]][:self.vpos[1]]

        # update line count
        self.lcount[self.vpos[0]] = len(
            self.text[self.vpos[0]]) / self.width + 1
        self.nlines = sum(self.lcount)

        # redraw the vlines
        self.redraw_vlines(self.vpos, self.ppos)

        # set the cursor back
        self.ppos = (backy, backx)
        self.win.move(self.ppos[0], self.ppos[1])

    def newline(self):
        "Insert a new line. Move lines below by one."

        # update texts
        self.text.insert(
            self.vpos[0] + 1, self.text[self.vpos[0]][self.vpos[1]:])
        self.text[self.vpos[0]] = self.text[
            self.vpos[0]][:self.vpos[1]]

        # update the line counts
        self.lcount.insert(self.vpos[0] + 1,
                           len(self.text[self.vpos[0] + 1]) / self.width + 1)
        self.lcount[self.vpos[0]] = len(
            self.text[self.vpos[0]]) / self.width + 1
        self.nlines = sum(self.lcount)

        # clear the right part of the pline
        for c in range(self.ppos[1], self.width):
            self._addch(self.ppos[0], c, ' ')

        # move p- and v- cursors
        self.ppos = (self.ppos[0] + 1, 0)
        backy, backx = self.ppos
        self.vpos = (self.vpos[0] + 1, 0)

        # redraw the bottom lines
        self.redraw_vlines(self.vpos, self.ppos)

        # move the cursor position back
        self.ppos = (backy, backx)
        self.win.move(*self.ppos)

    def refresh(self):

        # NOTE: texteditpad does not take care of the region outside
        # the Textbox. You need to manually erase characters there
        if self.resize_mode:
            # resize/move window to fit to the new screen size
            # self.stdscr.clear()
            # self.stdscr.refresh()
            ymax, xmax = self.win.getmaxyx()
            self.height, self.width = (ymax+1, xmax+1)
            self.vpos = (0,0)
            self.ppos = (0,0)
            self.vptl = (0,0)
            self.lcount = [1]*len(self.text)

            for i in range(len(self.text)):
                self.lcount[i] = len(self.text[i]) / self.width + 1
            self.nlines = sum(self.lcount)

            
            # ymax, xmax = self.stdscr.getmaxyx()
            # ncols, nlines = xmax - 5, ymax - 3
            # self.win.resize(nlines, ncols)
            # uly, ulx = 2, 2
            # self.win.mvwin(uly, ulx)
            self.win.refresh()

        # recalcualte the line count
        (self.maxy, self.maxx) = self._getmaxyx()
        (self.height, self.width) = (self.maxy + 1, self.maxx + 1)
        self.lcount = map(lambda x: len(x) / self.width + 1, self.text)
        self.nlines = sum(self.lcount)

        # redraw the texteditbox
        self.redraw_vlines(self.vptl, (0, 0))

        # replace the cursor
        self.win.move(*self.ppos)

    def edit(self, validate=None, debug_mode=False):
        "Edit in the widget window and collect the results."
        while 1:
            ch = self.win.getch()
            if validate:
                ch = validate(ch)
            if not ch:
                continue
            if not self.do_command(ch):
                break

            if debug_mode:
                (backy, backx) = self.win.getyx()
                maxy, maxx = self._getmaxyx()
                self.win.addstr(maxy, 0, ' ' * maxx)
                self.win.addstr(maxy, 0, '%d %d %d %d %d'
                                % (ch, self.vpos[0], self.vpos[1],
                                   self.ppos[0], self.ppos[1]))
                # self.win.addstr(maxy, 0, str(self.lnbg))
                self.win.refresh()
                self.win.move(backy, backx)

        return '\n'.join(self.text)


class EscapePressed(Exception):
    pass


def validate(ch):
    "Filters characters for special key sequences"

    if ch == curses.ascii.ESC:
        raise EscapePressed

    # Fix backspace for iterm
    if ch == curses.ascii.DEL:
        ch = curses.KEY_BACKSPACE

    return ch


if __name__ == '__main__':
    def test_editbox(stdscr):

        with open("texteditpad.py", "r") as testfile:
            testtext = testfile.read()

        curses.use_default_colors()
        ymax, xmax = stdscr.getmaxyx()
        # ncols, nlines = xmax - 5, ymax - 3
        ncols, nlines = 40, 20
        uly, ulx = 2, 2
        stdscr.addstr(uly - 2, ulx, "Use Ctrl-G to end editing.")
        win = curses.newwin(nlines, ncols, uly, ulx)
        rectangle(stdscr, uly - 1, ulx - 1, uly + nlines, ulx + ncols)
        stdscr.refresh()

        try:
            out = Textbox(win, stdscr=stdscr, text='', resize_mode=True)\
                .edit(validate=validate, debug_mode=False)
        except EscapePressed:
            out = None

        return out

    text = curses.wrapper(test_editbox)
    print 'Contents of text box:'
    print text

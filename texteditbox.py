"""Simple textbox editing widget with Emacs-like keybindings."""

import curses
import curses.ascii
import copy





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
        (maxy, maxx) = self._getmaxyx()
        (height, width) = (maxy+1, maxx+1)
        
        trailingstr = self.text[self.vpos[0]][self.vpos[1]:]

        self.text[self.vpos[0]]\
            = self.text[self.vpos[0]][:self.vpos[1]] + chr(ch) \
            + trailingstr
        self.vpos = (self.vpos[0], self.vpos[1] + 1)
        
        self.lnbg[self.vpos[0]] = range(0, len(self.text[self.vpos[0]]), maxx)
        
        self.ppos = self.win.getyx()
        (maxy, maxx) = self._getmaxyx()

        # draw the trailing part
        try:
            self.win.addch(ch)
        except curses.error:
            pass 
        (backy, backx) = self.win.getyx()
       
        nspaces = maxx - (self.ppos[1])
        # right space big enough to fit the rest of line
        if nspaces > len(trailingstr):
            self.win.addstr(trailingstr)
        # if not
        else:
            self.win.addstr(trailingstr[:nspaces])
            trailingstr = trailingstr[nspaces:]
            pos = (self.ppos[0], 0)
            
            # draw the rest of the vline
            for ln in range(0, len(trailingstr)/width+1):
                pos = (pos[0]+1, pos[1])
                self.win.addstr(pos[0], pos[1], ' '*width)
                self.win.addstr(pos[0], pos[1],
                                trailingstr[ln*width:(ln+1)*width])
                
            pos = (pos[0]+1, pos[1])
                
            # redraw the remaining vlines

            # redraw the rest of vlines
            # pos = (self.ppos[0]+1, 0)
            # curses.endwin()
            # import pdb
            # pdb.set_trace()

            self.redraw_vlines(pos, self.vpos[0]+1, len(self.text))
            # for li in range(self.vpos[0]+1, len(self.text)):
                # pos = self.draw_vline(pos, maxy+1, maxx+1, li)
        
        self.ppos = [backy, backx]
        self.win.move(backy, backx)


    def drawline(self, ln):
        (maxy, maxx) = self._getmaxyx()
        bg = self.lnbg[ln]
        ed = min(len(self.text[bg[0]])-self.text[bg[0]][bg[1]],  maxx)
        
        self.win.addstr(ln, 0, self.text[bg[0]][bg[1]:ed])
        
    def do_command(self, ch):
        "Process a single editing command."
        (maxy, maxx) = self._getmaxyx()
        (height, width) = (maxy+1, maxx+1)
        nlines = sum(len(x) for x in self.lnbg)
        self.lastcmd = ch

        if curses.ascii.isprint(ch):
            if self.ppos[0] < maxy or self.ppos[1] < maxx:
                self._insert_printable_char(ch)
            else:
                curses.beep()

        elif ch == curses.ascii.SOH:  # ^a
            self.ppos = (self.ppos[0], 0)
            self.vpos = (self.vpos[0], int((self.vpos[1]/width)*width))
            self.win.move(self.ppos[0], self.ppos[1])
            
        elif ch == curses.ascii.ENQ:  # ^e

            if self.vpos[1] < max(self.lnbg[self.vpos[0]]):
                self.ppos = (self.ppos[0], maxx)
                self.vpos = (self.vpos[0], int((self.vpos[1]/width+1)*width-1))
            else:
                self.ppos = (self.ppos[0], len(self.text[self.vpos[0]])%width)
                self.vpos = (self.vpos[0], len(self.text[self.vpos[0]]))

            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.STX, curses.KEY_LEFT):  # <-
            if self.ppos[1] > 0:
                self.ppos = (self.ppos[0], self.ppos[1]-1)
                self.vpos = (self.vpos[0], self.vpos[1]-1)
            elif self.ppos[0] == 0:
                curses.beep()
                pass
            else:  # move up one line
                if self.vpos[1] == self.lnbg[self.vpos[0]][0]:
                    ll = len(self.text[self.vpos[0]-1])
                    self.vpos = (self.vpos[0]-1, ll)
                    self.ppos = (self.ppos[0]-1, ll%(width))
                else:
                    self.vpos = (self.vpos[0], self.vpos[1]-1)
                    self.ppos = (self.ppos[0]-1, maxx)
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.ACK, curses.KEY_RIGHT):  # ^f ->
            ll = len(self.text[self.vpos[0]])
            
            if (self.ppos[1] < maxx) and (self.vpos[1] < ll):
                self.ppos = (self.ppos[0], self.ppos[1]+1)
                self.vpos = (self.vpos[0], self.vpos[1]+1)

            elif self.ppos[0] == maxy or (self.ppos[0]==nlines-1):
                curses.beep()
                pass

            else:  # move down one line
                if self.vpos[1] == len(self.text[self.vpos[0]]):
                    self.vpos = (self.vpos[0]+1, 0)
                    self.ppos = (self.ppos[0]+1, 0)
                else:
                    self.vpos = (self.vpos[0], self.vpos[1]+1)
                    self.ppos = (self.ppos[0]+1, 0)
            self.win.move(self.ppos[0], self.ppos[1])

        elif ch in (curses.ascii.SO, curses.KEY_DOWN):  # ^n            
            if self.ppos[0] < (nlines-1):
                # within the same vline
                if self.vpos[1] < max(self.lnbg[self.vpos[0]]):
                    ll = len(self.text[self.vpos[0]])
                    self.vpos = (self.vpos[0], min(self.vpos[1]+width, ll))
                    self.ppos = (self.ppos[0]+1, min(self.ppos[1], ll%width))
                # move to next vline
                else:
                    ll = len(self.text[self.vpos[0]+1])
                    self.vpos = (self.vpos[0]+1, min(self.vpos[1]%width, ll))
                    self.ppos = (self.ppos[0]+1, min(self.ppos[1], ll))
                self.win.move(self.ppos[0], self.ppos[1])
            else:
                curses.beep()

        elif ch in (curses.ascii.DLE, curses.KEY_UP):  # ^p
            if self.ppos[0] > 0:
                # move to previous vline
                if self.vpos[1] < width:
                    ll = len(self.text[self.vpos[0]-1])
                    vpos1 = min(int((ll/width)*width)+self.vpos[1], ll)
                    self.vpos = (self.vpos[0]-1, vpos1)
                    self.ppos = (self.ppos[0]-1, min(self.ppos[1], ll%width))
                # within the same vline
                else:
                    self.vpos = (self.vpos[0], self.vpos[1]-width)
                    self.ppos = (self.ppos[0]-1, self.ppos[1])

                self.win.move(self.ppos[0], self.ppos[1])
            else:
                curses.beep()

        elif ch in [curses.ascii.NL, curses.ascii.SI]:  # ^j, ^o
            if maxy == 0:  # no space
                curses.beep()
                return 0
            elif self.ppos[0] < maxy:
                # update texts
                self.text.insert(
                    self.vpos[0] + 1, self.text[self.vpos[0]][self.vpos[1]:])
                self.text[self.vpos[0]] = self.text[self.vpos[0]][:self.vpos[1]]

                # update the line counts
                self.lnbg.insert(self.vpos[0]+1, [])
                self.lnbg[self.vpos[0]] \
                    = range(0, len(self.text[self.vpos[0]]), maxx)
                self.lnbg[self.vpos[0]+1] \
                    = range(0, len(self.text[self.vpos[0]+1]), maxx)

                if len(self.lnbg[self.vpos[0]]) == 0:
                    self.lnbg[self.vpos[0]] = [0]
                if len(self.lnbg[self.vpos[0]+1]) == 0:
                    self.lnbg[self.vpos[0]+1] = [0]
                    
                # clear the right part of the pline
                for c in range(self.ppos[1], width):
                    self.win.addch(' ')

                # move p- and v- cursors
                self.ppos = (self.ppos[0]+1, 0)
                backy, backx = self.ppos
                self.vpos = (self.vpos[0]+1, 0)

                # redraw the bottom lines
                self.redraw_vlines(self.ppos, self.vpos[0],
                                   len(self.text))

                # move the cursor position back
                self.ppos = (backy, backx)
                self.win.move(self.ppos[0], self.ppos[1])

                
        # elif ch == curses.ascii.EOT:  # ^d
        #     if self.vpos[1] == len(self.text[self.vpos[0]]):
        #         curses.beep()
        #     else:
        #         self.text[self.vpos[0]]\
        #             = self.text[self.vpos[0]][:self.vpos[1]]\
        #             + self.text[self.vpos[0]][self.vpos[1] + 1:]
        #         self.win.delch()

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

            # import pdb
            # curses.endwin()
            # pdb.set_trace()
                
        elif ch == curses.ascii.VT:  # ^k

            
            backy, backx = self.ppos
            self.text[self.vpos[0]]\
                = self.text[self.vpos[0]][:self.vpos[1]]
            self.lnbg[self.vpos[0]]\
                = range(0, len(self.text[self.vpos[0]]), maxx)
            if len(self.lnbg[self.vpos[0]]) == 0:
                self.lnbg[self.vpos[0]] = [0]
            
            # redraw the bottom lines
            pos = (sum(len(x) for x in self.lnbg[:self.vpos[0]]), 0)

            self.redraw_vlines(pos, self.vpos[0],
                               len(self.text))

            self.ppos = (backy, backx)
            self.win.move(self.ppos[0], self.ppos[1])
 
            
            # for c in range(self.ppos[1], width):
            #     self.win.addch(' ')
            
            # self.ppos[1] = len(self.text[self.ppos[0]])
            # self.win.move(self.ppos[0], self.ppos[1])

        elif ch == curses.ascii.FF:  # ^l
            self.win.refresh()

        elif ch == curses.ascii.BEL:  # ^g
            return 0

        return 1

    def draw_vline(self, pos, height, width, ln):
        "Draw a vline."
        
        for li in range(0, len(self.text[ln]), width):
            self.win.addstr(pos[0], pos[1],
                            self.text[ln][li:li+width])
            pos = (pos[0]+1, pos[1])

        if len(self.text[ln]) == 0:
            pos = (pos[0]+1, pos[1])
            
        return pos
    
    def redraw_vlines(self, pos, stl, edl):
        "Redraw vlines from stl to edl at position pos"

        (maxy, maxx) = self._getmaxyx()
        
        # clear the redrawn part
        nlines = sum(len(x) for x in self.lnbg)
        for l in range(pos[0], maxy):
            self.win.addstr(l, 0, ' '*(maxx+1))

        # now draw each line
        for li in range(stl, edl):
            pos = self.draw_vline(pos, maxy+1, maxx+1, li)

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

            (backy, backx) = self.win.getyx()
            maxy, maxx = self._getmaxyx()
            self.win.addstr(maxy, 0, ' '*maxx)
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
        ncols, nlines = 20,10
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

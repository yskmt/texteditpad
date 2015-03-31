texteditpad
===========

Simple textbox editing widget with Emacs-like keybindings. Provide
richer features than ``curses.textpad`` routine and intended to replace
it.

pypi repository:
https://pypi.python.org/pypi/texteditpad

Usage
=====

.. code:: python

    def test_editbox(stdscr):
        ncols, nlines = 9, 4
        uly, ulx = 15, 20
        stdscr.addstr(uly - 2, ulx, "Use Ctrl-G to end editing.")
        win = curses.newwin(nlines, ncols, uly, ulx)
        stdscr.refresh()
    
        return texteditpad.Textbox(win).edit()
    
    text = curses.wrapper(test_editbox)
    print 'Contents of text box:'
    print text

Commands
========

Editing widget using the interior of a window object. Supports the
following Emacs-like key bindings:

+-----------+----------------------------------------------------------------+
| Command   | Description                                                    |
+===========+================================================================+
| Ctrl-A    | Go to left edge of window.                                     |
+-----------+----------------------------------------------------------------+
| Ctrl-B    | Cursor left, wrapping to previous line if appropriate.         |
+-----------+----------------------------------------------------------------+
| Ctrl-D    | Delete character under cursor.                                 |
+-----------+----------------------------------------------------------------+
| Ctrl-E    | Go to right edge or end of line                                |
+-----------+----------------------------------------------------------------+
| Ctrl-F    | Cursor right, wrapping to next line when appropriate.          |
+-----------+----------------------------------------------------------------+
| Ctrl-G    | Terminate, returning the window contents.                      |
+-----------+----------------------------------------------------------------+
| Ctrl-H    | Delete character backward.                                     |
+-----------+----------------------------------------------------------------+
| Ctrl-I    | Toggle insert/overwrite modes.                                 |
+-----------+----------------------------------------------------------------+
| Ctrl-K    | If line is blank, delete it, otherwise clear to end of line.   |
+-----------+----------------------------------------------------------------+
| Ctrl-L    | Refresh screen.                                                |
+-----------+----------------------------------------------------------------+
| Ctrl-N    | Cursor down; move down one line.                               |
+-----------+----------------------------------------------------------------+
| Ctrl-O    | Insert a blank line at cursor location.                        |
+-----------+----------------------------------------------------------------+
| Ctrl-P    | Cursor up; move up one line.                                   |
+-----------+----------------------------------------------------------------+


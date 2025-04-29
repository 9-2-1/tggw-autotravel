from copy import deepcopy
from typing import Dict, List, Optional, Callable, Generator, Union
from contextlib import contextmanager
import time
import os
import sys


import pytermgui as ptg
import pytermgui.context_managers as ptgctx

from . import mouseevent
from . import screen
from . import getch

if sys.platform == "win32":
    import colorama
else:
    import termios
    import tty


PtgMouseAction = ptg.ansi_interface.MouseAction
PtgMouseEvent = ptg.ansi_interface.MouseEvent
MouseCall = Callable[[str], Optional[List[Optional[PtgMouseEvent]]]]

colorfg = [30, 31, 32, 33, 34, 35, 36, 37, 90, 91, 92, 93, 94, 95, 96, 97]
colorbg = [40, 41, 42, 43, 44, 45, 46, 47, 100, 101, 102, 103, 104, 105, 106, 107]


modemap: Dict[PtgMouseAction, mouseevent.MouseMode] = {
    PtgMouseAction.LEFT_CLICK: mouseevent.MouseMode.LEFT_CLICK,
    PtgMouseAction.LEFT_DRAG: mouseevent.MouseMode.LEFT_DRAG,
    PtgMouseAction.RIGHT_CLICK: mouseevent.MouseMode.RIGHT_CLICK,
    PtgMouseAction.RIGHT_DRAG: mouseevent.MouseMode.RIGHT_DRAG,
    PtgMouseAction.SCROLL_UP: mouseevent.MouseMode.SCROLL_UP,
    PtgMouseAction.SCROLL_DOWN: mouseevent.MouseMode.SCROLL_DOWN,
    PtgMouseAction.SHIFT_SCROLL_UP: mouseevent.MouseMode.SCROLL_UP,
    PtgMouseAction.SHIFT_SCROLL_DOWN: mouseevent.MouseMode.SCROLL_DOWN,
    PtgMouseAction.HOVER: mouseevent.MouseMode.MOVE,
    PtgMouseAction.RELEASE: mouseevent.MouseMode.RELEASE,
}


class TUI:
    def __init__(
        self,
        lines: int,
        columns: int,
        *,
        mouse_translate: Optional[MouseCall] = None,
    ) -> None:
        self.lines = lines
        self.columns = columns
        self.need_full_redraw = True
        self.last_term_lines = -1
        self.last_term_columns = -1
        self.screen = screen.Screen(lines, columns)
        self.drawn_screen = screen.Screen(lines, columns)
        self.mouse_translate = mouse_translate
        self.terminal_too_small = False
        self.getch_unicode = getch.GetchUnicode()

    @staticmethod
    @contextmanager
    def entry(lines: int, columns: int) -> Generator["TUI", None, None]:
        if sys.platform == "win32":
            colorama.just_fix_windows_console()  # in case windows 7
        with ptg.win32console.enable_virtual_processing():
            # old_columns, old_lines = os.get_terminal_size()
            # try to change terminal size
            # ptg.terminal.write(f"\x1b[8;{lines};{columns}t", flush=True)
            with ptgctx.alt_buffer():
                with ptgctx.mouse_handler(["all"]) as mouse_translate:
                    gameui = TUI(lines, columns, mouse_translate=mouse_translate)
                    if sys.platform != "win32":
                        # enable raw
                        descriptor = sys.stdin.fileno()
                        old_settings = termios.tcgetattr(descriptor)
                        tty.setraw(descriptor)
                    try:
                        yield gameui
                    finally:
                        if sys.platform != "win32":
                            termios.tcsetattr(
                                descriptor, termios.TCSADRAIN, old_settings
                            )
            # revert terminal size change
            # ptg.terminal.write(f"\x1b[8;{old_lines};{old_columns}t", flush=True)
            # show the cursor
            ptg.terminal.write("\x1b[?25h", flush=True)

    def redraw(self) -> None:
        term_columns, term_lines = os.get_terminal_size()
        if self.last_term_lines != term_lines or self.last_term_columns != term_columns:
            self.need_full_redraw = True
        if self.need_full_redraw:
            self.full_redraw()
            return
        if self.terminal_too_small:
            return
        # directly construct escape sequence for speed
        cx = -1
        cy = -1
        fg = -1
        bg = -1
        # hide cursor
        refresh_str = "\x1b[?25l"
        for y in range(self.lines):
            for x in range(self.columns):
                char = self.screen.data[y][x]
                drawn_char = self.drawn_screen.data[y][x]
                if char == drawn_char:
                    continue
                self.drawn_screen.data[y][x] = char
                if x != cx or y != cy:
                    if x == 0:
                        if y == 0:
                            refresh_str += "\x1b[H"
                        else:
                            refresh_str += f"\x1b[{y+1}H"
                    else:
                        refresh_str += f"\x1b[{y+1};{x+1}H"
                    cx = x
                    cy = y
                char = self.screen.data[y][x]
                if fg != char.fg:
                    fg = char.fg
                    # term.{color}
                    refresh_str += f"\x1b[{colorfg[fg]}m"
                if bg != char.bg:
                    bg = char.bg
                    # term.on_{color}
                    refresh_str += f"\x1b[{colorbg[bg]}m"
                refresh_str += char.text
                cx += 1
        # position
        refresh_str += f"\x1b[m\x1b[{self.screen.cursor.y+1};{self.screen.cursor.x+1}H"
        # show cursor
        if not self.screen.cursor.hidden:
            refresh_str += "\x1b[?25h"
        ptg.terminal.write(refresh_str, flush=True)

    def full_redraw(self) -> None:
        term_columns, term_lines = os.get_terminal_size()
        self.last_term_columns = term_columns
        self.last_term_lines = term_lines
        self.need_full_redraw = False
        self.terminal_too_small = False
        if term_lines < self.lines or term_columns < self.columns:
            self.terminal_too_small = True
            ptg.terminal.write(
                "\x1b[2J\x1b[H\x1b[m\x1b[?25h"
                "Your terminal size is too small, please resize your terminal window.\r\n"
                f"Lines: {term_lines}/{self.lines}\r\n"
                f"Columns: {term_columns}/{self.columns}\r\n"
                "\r\n"
                "Press Ctrl+C to force quit (progress will lost).",
                flush=True,
            )
            return
        # directly construct escape sequence for speed
        refresh_line_str: List[str] = []
        for line in self.screen.data:
            fg = 7
            bg = 0
            line_str = ""
            for char in line:
                if fg != char.fg:
                    fg = char.fg
                    # term.{color}
                    line_str += f"\x1b[{colorfg[fg]}m"
                if bg != char.bg:
                    bg = char.bg
                    # term.on_{color}
                    line_str += f"\x1b[{colorbg[bg]}m"
                line_str += char.text
            refresh_line_str.append(line_str)
        refresh_str = (
            "\x1b[?25l\x1b[H"  # hide cursor and move to home
            + "\x1b[m\x1b[K\r\n".join(refresh_line_str)
            + "\x1b[m\x1b[0J"
        )
        # position
        refresh_str += f"\x1b[{self.screen.cursor.y+1};{self.screen.cursor.x+1}H"
        # show cursor
        if not self.screen.cursor.hidden:
            refresh_str += "\x1b[?25h"
        ptg.terminal.write(refresh_str, flush=True)
        self.drawn_screen = deepcopy(self.screen)

    def getch(
        self, timeout: float = 0
    ) -> Optional[Union[str, List[mouseevent.MouseEvent]]]:
        ch = self.getch_unicode.getinput()
        if ch == "":
            endtime = time.monotonic() + timeout
            while ch == "" and time.monotonic() < endtime:
                time.sleep(0.005)
                ch = self.getch_unicode.getinput()
        if ch == "":
            return None
        if self.mouse_translate is not None:
            events = self.mouse_translate(ch)
            if events is not None and len(events) != 0:
                mlist: List[mouseevent.MouseEvent] = []
                for event in events:
                    if event is not None:
                        if event.action in modemap:
                            mode = modemap[event.action]
                            x, y = event.position
                            mevent2 = mouseevent.MouseEvent(mode=mode, y=y - 1, x=x - 1)
                            mlist.append(mevent2)
                return mlist
        return ch

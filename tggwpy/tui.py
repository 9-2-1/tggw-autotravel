from copy import deepcopy
from typing import Dict, List, Optional, Callable, Generator, Tuple, Union, Any
from threading import Event
from contextlib import contextmanager
import time
import os
import signal

if os.name != "nt":
    import termios
    import tty
    import sys

import pytermgui as ptg
import pytermgui.context_managers as ptgctx

if os.name == "nt":
    import colorama

from . import mouseevent
from . import screen
from . import plugin
from . import getch


PtgMouseAction = ptg.ansi_interface.MouseAction
PtgMouseEvent = ptg.ansi_interface.MouseEvent
MouseCall = Callable[[str], Optional[List[Optional[PtgMouseEvent]]]]

colorfg = [30, 31, 32, 33, 34, 35, 36, 37, 90, 91, 92, 93, 94, 95, 96, 97]
colorbg = [40, 41, 42, 43, 44, 45, 46, 47, 100, 101, 102, 103, 104, 105, 106, 107]


modemap: Dict[PtgMouseAction, mouseevent.MouseMode] = {
    PtgMouseAction.LEFT_CLICK: mouseevent.MouseMode.LeftClick,
    PtgMouseAction.LEFT_DRAG: mouseevent.MouseMode.LeftDrag,
    PtgMouseAction.RIGHT_CLICK: mouseevent.MouseMode.RightClick,
    PtgMouseAction.RIGHT_DRAG: mouseevent.MouseMode.RightDrag,
    PtgMouseAction.SCROLL_UP: mouseevent.MouseMode.ScrollUp,
    PtgMouseAction.SCROLL_DOWN: mouseevent.MouseMode.ScrollDown,
    PtgMouseAction.SHIFT_SCROLL_UP: mouseevent.MouseMode.ScrollUp,
    PtgMouseAction.SHIFT_SCROLL_DOWN: mouseevent.MouseMode.ScrollDown,
    PtgMouseAction.HOVER: mouseevent.MouseMode.Move,
    PtgMouseAction.RELEASE: mouseevent.MouseMode.Release,
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
        self.last_term_lines = -1
        self.last_term_columns = -1
        self.screen = screen.Screen(lines, columns)
        self.drawn_screen = screen.Screen(lines, columns)
        self.mouse_translate = mouse_translate
        self.terminal_too_small = False
        self.ctrlc = Event()
        self.ctrlz = Event()
        # Create a new thread to read input to solve the input lost problem
        # TODO should use some better way to do this
        self.plugins: List[plugin.Plugin] = []

    @staticmethod
    @contextmanager
    def entry(lines: int, columns: int) -> Generator["TUI", None, None]:
        if os.name == "nt":
            colorama.just_fix_windows_console()  # in case windows 7
        with ptg.win32console.enable_virtual_processing():
            # old_columns, old_lines = os.get_terminal_size()
            # try to change terminal size
            # ptg.terminal.write(f"\x1b[8;{lines};{columns}t", flush=True)
            with ptgctx.alt_buffer():
                with ptgctx.mouse_handler(["all"]) as mouse_translate:
                    gameui = TUI(lines, columns, mouse_translate=mouse_translate)
                    sigint_func = signal.signal(signal.SIGINT, gameui._tty_read_ctrl_c)
                    if os.name != "nt":
                        # enable cbreak
                        descriptor = sys.stdin.fileno()
                        old_settings = termios.tcgetattr(descriptor)
                        tty.setcbreak(descriptor)
                        sigtstp_func = signal.signal(
                            signal.SIGTSTP, gameui._tty_read_ctrl_z
                        )
                    try:
                        yield gameui
                    finally:
                        signal.signal(signal.SIGINT, sigint_func)
                        if os.name != "nt":
                            termios.tcsetattr(
                                descriptor, termios.TCSADRAIN, old_settings
                            )
                            signal.signal(signal.SIGTSTP, sigtstp_func)
            # revert terminal size change
            # ptg.terminal.write(f"\x1b[8;{old_lines};{old_columns}t", flush=True)
            # show the cursor
            ptg.terminal.write("\x1b[?25h", flush=True)

    # for linux signal SIGINT
    def _tty_read_ctrl_c(self, _signal: int, _frame: Any) -> None:
        self.ctrlc.set()

    # for linux signal SIGTSTP
    def _tty_read_ctrl_z(self, _signal: int, _frame: Any) -> None:
        self.ctrlz.set()

    def redraw(self) -> None:
        term_columns, term_lines = os.get_terminal_size()
        if self.last_term_lines != term_lines or self.last_term_columns != term_columns:
            self.full_redraw()
            return
        if self.terminal_too_small:
            return
        # directly construct escape sequence for speed
        cx = -10
        cy = -10
        fg = 7
        bg = 0
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
        self.terminal_too_small = False
        if term_lines < self.lines or term_columns < self.columns:
            self.terminal_too_small = True
            ptg.terminal.write(
                "\x1b[2J\x1b[H\x1b[m\x1b[?25h"
                "Your terminal size is too small, please resize your terminal window.\n"
                f"Lines: {term_lines}/{self.lines}\n"
                f"Columns: {term_columns}/{self.columns}",
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
            + "\x1b[m\x1b[K\n".join(refresh_line_str)
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
    ) -> Optional[Union[bytes, List[mouseevent.MouseEvent]]]:
        if self.ctrlc.is_set():
            self.ctrlc.clear()
            return b"\x03"
        if self.ctrlz.is_set():
            self.ctrlz.clear()
            return b"\x03"
        ch = getch.getinput()
        if ch == b"":
            return None
        if self.mouse_translate is not None:
            events = self.mouse_translate(ch.decode(errors="ignore"))
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

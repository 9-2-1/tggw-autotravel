from typing import List, Optional, Callable, Generator, Tuple, Union
from queue import Queue
from contextlib import contextmanager
import pytermgui as ptg
import pytermgui.context_managers as ptgctx
from colorama import just_fix_windows_console
from dataclasses import dataclass
import time
import os


@dataclass
class Char:
    text: str
    fg: int
    bg: int


@dataclass
class Cursor:
    y: int = 0
    x: int = 0
    hidden: bool = False


class Screen:
    def __init__(self, columns: int, lines: int) -> None:
        self.columns = columns
        self.lines = lines
        self.data = [[Char(" ", 7, 0) for x in range(columns)] for y in range(lines)]
        self.cursor = Cursor()


MouseEvent = ptg.ansi_interface.MouseEvent
MouseCall = Callable[[str], Optional[List[Optional[MouseEvent]]]]

colorfg = [30, 31, 32, 33, 34, 35, 36, 37, 90, 91, 92, 93, 94, 95, 96, 97]
colorbg = [40, 41, 42, 43, 44, 45, 46, 47, 100, 101, 102, 103, 104, 105, 106, 107]


class TUI:
    def __init__(
        self,
        columns: int = 92,
        lines: int = 38,
        *,
        mouse_translate: Optional[MouseCall] = None,
    ) -> None:
        self.columns = columns
        self.lines = lines
        self.screen = Screen(columns, lines)
        self.drawn_screen = Screen(columns, lines)
        self.mouse_translate = mouse_translate
        self.terminal_too_small = False

    @staticmethod
    @contextmanager
    def entry(columns: int = 92, lines: int = 38) -> Generator["TUI", None, None]:
        just_fix_windows_console()  # in case windows 7
        with ptg.win32console.enable_virtual_processing():
            old_columns, old_lines = os.get_terminal_size()
            # try to change terminal size
            # print(f"\x1b[8;{lines};{columns}t", end="", flush=True)
            with ptgctx.alt_buffer():
                with ptgctx.mouse_handler(["all"]) as mouse_translate:
                    yield TUI(columns, lines, mouse_translate=mouse_translate)
            # revert terminal size change
            # print(f"\x1b[8;{old_lines};{old_columns}t", end="", flush=True)

    def part_redraw(self, pos: List[Tuple[int, int]]) -> None:
        if self.terminal_too_small:
            return
        # directly construct escape sequence for speed
        cx = -10
        cy = -10
        fg = 7
        bg = 0
        # hide cursor
        refresh_str = "\x1b[?25l"
        for y, x in pos:
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
        print(refresh_str, flush=True, end="")

    def full_redraw(self) -> None:
        self.terminal_too_small = False
        columns, lines = os.get_terminal_size()
        if columns < self.columns or lines < self.lines:
            self.terminal_too_small = True
            print(
                "\x1b[2J\x1b[H\x1b[m\x1b[?25h"
                + "Your terminal size is too small, please resize your terminal window.\n"
                f"Lines: {lines}/{self.lines}\n"
                f"Columns: {columns}/{self.columns}"
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
            +"\x1b[m\x1b[0J"
        )
        # position
        refresh_str += f"\x1b[{self.screen.cursor.y+1};{self.screen.cursor.x+1}H"
        # show cursor
        if not self.screen.cursor.hidden:
            refresh_str += "\x1b[?25h"
        print(refresh_str, flush=True, end="")

    def getch(self, frame:float = 0.01) -> Optional[Union[str , List[Optional[MouseEvent]]]]:
        if os.name == "nt":
            time.sleep(frame)
            ch = ptg.getch(interrupts=False)
        else:
            ch = ptg.getch_timeout(frame, interrupts=False)
        if ch == "":
            return None
        if self.mouse_translate is not None:
            mouse = self.mouse_translate(ch)
            if mouse is not None and len(mouse) != 0:
                return mouse
        return ch

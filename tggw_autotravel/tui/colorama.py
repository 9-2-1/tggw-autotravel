from typing import Optional
import colorama
import pytermgui.win32console
import os

from .base import TUIBase
from ..screen import Screen, Color

colorfg = {
    Color.BLACK: colorama.Fore.BLACK,
    Color.BLUE: colorama.Fore.BLUE,
    Color.GREEN: colorama.Fore.GREEN,
    Color.CYAN: colorama.Fore.CYAN,
    Color.RED: colorama.Fore.RED,
    Color.MAGENTA: colorama.Fore.MAGENTA,
    Color.YELLOW: colorama.Fore.YELLOW,
    Color.WHITE: colorama.Fore.WHITE,
    Color.LIGHT_BLACK: colorama.Fore.LIGHTBLACK_EX,
    Color.LIGHT_BLUE: colorama.Fore.LIGHTBLUE_EX,
    Color.LIGHT_GREEN: colorama.Fore.LIGHTGREEN_EX,
    Color.LIGHT_CYAN: colorama.Fore.LIGHTCYAN_EX,
    Color.LIGHT_RED: colorama.Fore.LIGHTRED_EX,
    Color.LIGHT_MAGENTA: colorama.Fore.LIGHTMAGENTA_EX,
    Color.LIGHT_YELLOW: colorama.Fore.LIGHTYELLOW_EX,
    Color.LIGHT_WHITE: colorama.Fore.LIGHTWHITE_EX,
}
colorbg = {
    Color.BLACK: colorama.Back.BLACK,
    Color.BLUE: colorama.Back.BLUE,
    Color.GREEN: colorama.Back.GREEN,
    Color.CYAN: colorama.Back.CYAN,
    Color.RED: colorama.Back.RED,
    Color.MAGENTA: colorama.Back.MAGENTA,
    Color.YELLOW: colorama.Back.YELLOW,
    Color.WHITE: colorama.Back.WHITE,
    Color.LIGHT_BLACK: colorama.Back.LIGHTBLACK_EX,
    Color.LIGHT_BLUE: colorama.Back.LIGHTBLUE_EX,
    Color.LIGHT_GREEN: colorama.Back.LIGHTGREEN_EX,
    Color.LIGHT_CYAN: colorama.Back.LIGHTCYAN_EX,
    Color.LIGHT_RED: colorama.Back.LIGHTRED_EX,
    Color.LIGHT_MAGENTA: colorama.Back.LIGHTMAGENTA_EX,
    Color.LIGHT_YELLOW: colorama.Back.LIGHTYELLOW_EX,
    Color.LIGHT_WHITE: colorama.Back.LIGHTWHITE_EX,
}


class TUIColorama(TUIBase):
    def __init__(self, lines: int = 24, columns: int = 80) -> None:
        self.lines = lines
        self.columns = columns
        self.screen = Screen(lines, columns)
        self.drawn_screen: Optional[Screen] = None
        self.scr_size = os.get_terminal_size()
        self.alt_buffer_context = pytermgui.context_managers.alt_buffer()
        colorama.init()
        self.alt_buffer_context.__enter__()

    def refresh(self) -> None:
        """
        refresh screen -> drawn_screen and output with colorama
        """
        new_size = os.get_terminal_size()
        if new_size != self.scr_size:
            # reset drawnscreen
            self.drawn_screen = None
            self.scr_size = new_size
        force_draw = False
        if self.drawn_screen is None:
            force_draw = True
            self.drawn_screen = Screen(self.lines, self.columns)
        for y in range(min(self.screen.lines, self.drawn_screen.lines)):
            for x in range(min(self.screen.columns, self.drawn_screen.columns)):
                char = self.screen.buffer[y][x]
                if force_draw or self.drawn_screen.buffer[y][x] != char:
                    self.drawn_screen.buffer[y][x] = char
                    print(colorama.Cursor.POS(x + 1, y + 1), end="")
                    print(colorfg[char.fg] + colorbg[char.bg] + char.char, end="")
        print(colorama.Fore.RESET + colorama.Back.RESET, end="")
        print(
            colorama.Cursor.POS(
                self.drawn_screen.cursor.x + 1, self.drawn_screen.cursor.y + 1
            ),
            end="",
            flush=True,
        )
        # Cursor visibility not available in colorama
        self.drawn_screen.cursor = self.screen.cursor

    def close(self) -> None:
        self.alt_buffer_context.__exit__(None, None, None)
        colorama.deinit()

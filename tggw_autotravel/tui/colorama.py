from .base import TUIBase
from ..screen import Screen, Color

import colorama
import pytermgui.win32console

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
        self.screen = Screen(lines, columns)
        self.drawn_screen = Screen(lines, columns)
        self.vpcontext = pytermgui.win32console.enable_virtual_processing()
        colorama.init()
        self.vpcontext.__enter__()

    def refresh(self) -> None:
        """
        refresh screen -> drawn_screen and output with colorama
        """
        for y in range(self.screen.lines):
            for x in range(self.screen.columns):
                char = self.screen.buffer[y][x]
                if self.drawn_screen.buffer[y][x] != char:
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
        self.vpcontext.__exit__(None, None, None)
        colorama.deinit()

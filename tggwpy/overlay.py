from typing import List, Optional
import wcwidth

from . import screen


class Overlay:
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.data: List[List[Optional[screen.Char]]] = [
            [None for x in range(columns)] for y in range(lines)
        ]
        self.cursor: Optional[screen.Cursor] = None

    def clear(
        self, y: int = 0, x: int = 0, h: Optional[int] = None, w: Optional[int] = None
    ) -> None:
        for yi in range(y, y + h if h is not None else self.lines):
            for xi in range(x, x + w if w is not None else self.columns):
                self.data[yi][xi] = None
        self.cursor = None

    def fill(
        self,
        y: int = 0,
        x: int = 0,
        h: Optional[int] = None,
        w: Optional[int] = None,
        *,
        fg: screen.Color = screen.Color.WHITE,
        bg: screen.Color = screen.Color.BLACK,
        fillchar: str = " ",
    ) -> None:
        for yi in range(y, y + h if h is not None else self.lines):
            for xi in range(x, x + w if w is not None else self.columns):
                self.data[yi][xi] = screen.Char(fillchar, fg, bg)

    def write(
        self,
        y: int,
        x: int,
        text: str,
        *,
        fg: screen.Color = screen.Color.WHITE,
        bg: screen.Color = screen.Color.BLACK,
    ) -> None:
        self.write_rect(y, x, 1, self.columns - x, text, fg=fg, bg=bg)

    def write_rect(
        self,
        y: int,
        x: int,
        h: int,
        w: int,
        text: str,
        *,
        fg: screen.Color = screen.Color.WHITE,
        bg: screen.Color = screen.Color.BLACK,
    ) -> None:
        yi = y
        xi = x
        text_line = screen.Screen.align_str(text)
        for c in text_line:
            if c == "\n":
                yi += 1
                xi = x
                continue
            width = wcwidth.wcswidth(c)
            if xi + width > x + w:
                yi += 1
                xi = x
            if yi >= y + h:
                return
            self.data[yi][xi] = screen.Char(c, fg, bg)
            xi += 1

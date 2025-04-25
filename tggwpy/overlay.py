from typing import List, Optional

from . import screen


class Overlay:
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.data: List[List[Optional[screen.Char]]] = [
            [None for x in range(columns)] for y in range(lines)
        ]
        self.cursor: Optional[screen.Cursor] = None

    def clear(self, y: int = 0, x: int = 0, h: int = -1, w: int = -1) -> None:
        y0 = y
        x0 = x
        for y in range(y0, y0 + h if h != -1 else self.lines):
            for x in range(x0, x0 + w if w != -1 else self.columns):
                self.data[y][x] = None

    def fill(
        self,
        y: int,
        x: int,
        h: int,
        w: int,
        *,
        fg: int = 7,
        bg: int = 0,
        fillchar: str = " "
    ) -> None:
        y0 = y
        x0 = x
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.data[y][x] = screen.Char(fillchar, fg, bg)

    def write(self, y: int, x: int, text: str, *, fg: int = 7, bg: int = 0) -> None:
        for c in text:
            self.data[y][x] = screen.Char(c, fg, bg)
            x += 1

    def write_rect(
        self, y: int, x: int, h: int, w: int, text: str, *, fg: int = 7, bg: int = 0
    ) -> None:
        y0 = y
        x0 = x
        for c in text:
            if c == "\n":
                y += 1
                x = x0
                continue
            self.data[y][x] = screen.Char(c, fg, bg)
            x += 1
            if x >= x0 + w:
                y += 1
                x = x0
            if y >= y0 + h:
                return

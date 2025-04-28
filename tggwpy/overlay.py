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
        for c in text:
            self.data[y][x] = screen.Char(c, fg, bg)
            x += 1
            if x > self.columns:
                return

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
        for c in text:
            if c == "\n":
                yi += 1
                xi = x
                continue
            self.data[yi][xi] = screen.Char(c, fg, bg)
            xi += 1
            if xi >= x + w:
                yi += 1
                xi = x
            if yi >= y + h:
                return

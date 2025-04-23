from typing import List, Tuple, Optional

from dataclasses import dataclass


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

    def findtext(self, text: str) -> List[Tuple[int, int]]:
        return self.findtextrange(0, 0, self.columns, self.lines, text)

    def findtextrange(
        self, y: int, x: int, h: int, w: int, text: str, *, fg: int = -1, bg: int = -1
    ) -> List[Tuple[int, int]]:
        y0 = y
        x0 = x
        ret: List[Tuple[int, int]] = []
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w - (len(text) - 1)):
                found = True
                for i in range(len(text)):
                    char = self.data[y][x + i]
                    if char.text != text[i]:
                        found = False
                        break
                    if fg != -1 and char.fg != fg:
                        found = False
                        break
                    if bg != -1 and char.bg != bg:
                        found = False
                        break
                if found:
                    ret.append((y, x))
        return ret

    def readtext(
        self, y: int, x: int, *, end: Optional[str] = None, size: Optional[int] = None
    ) -> str:
        ret = ""
        x0 = x
        if size is not None:
            x1 = min(x + size, self.columns)
        else:
            x1 = self.columns
        for x in range(x0, x1):
            char = self.data[y][x]
            if end is not None:
                if char.text == end:
                    break
            ret += char.text
        return ret

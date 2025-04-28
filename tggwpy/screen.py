from typing import List, Tuple, Optional
from enum import IntEnum

from dataclasses import dataclass


class Color(IntEnum):
    BLACK = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7
    BRIGHT_BLACK = 8
    BRIGHT_RED = 9
    BRIGHT_GREEN = 10
    BRIGHT_YELLOW = 11
    BRIGHT_BLUE = 12
    BRIGHT_MAGENTA = 13
    BRIGHT_CYAN = 14
    BRIGHT_WHITE = 15


@dataclass
class Char:
    text: str
    fg: Color
    bg: Color


@dataclass
class Cursor:
    y: int = 0
    x: int = 0
    hidden: bool = False


class Screen:
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.data = [
            [Char(" ", Color.WHITE, Color.BLACK) for x in range(columns)]
            for y in range(lines)
        ]
        self.cursor = Cursor()

    def findtext(self, text: str) -> List[Tuple[int, int]]:
        return self.findtextrange(0, 0, self.lines, self.columns, text)

    def findtextrange(
        self,
        y: int,
        x: int,
        h: int,
        w: int,
        text: str,
        *,
        fg: Optional[int] = None,
        bg: Optional[int] = None,
    ) -> List[Tuple[int, int]]:
        ret: List[Tuple[int, int]] = []
        for yi in range(y, y + h):
            for xi in range(x, x + w - (len(text) - 1)):
                found = True
                for i in range(len(text)):
                    char = self.data[yi][xi + i]
                    if char.text != text[i]:
                        found = False
                        break
                    if fg is not None and char.fg != fg:
                        found = False
                        break
                    if bg is not None and char.bg != bg:
                        found = False
                        break
                if found:
                    ret.append((yi, xi))
        return ret

    def readtext(
        self,
        y: int,
        x: int,
        *,
        fg: Optional[int] = None,
        bg: Optional[int] = None,
        end: Optional[str] = None,
        size: Optional[int] = None,
    ) -> str:
        ret = ""
        if size is not None:
            x1 = min(x + size, self.columns)
        else:
            x1 = self.columns
        for xi in range(x, x1):
            char = self.data[y][xi]
            if end is not None and char.text == end:
                break
            if fg is not None and char.fg != fg:
                break
            if bg is not None and char.bg != bg:
                break
            ret += char.text
        return ret

    def __str__(self) -> str:
        scr = self.data
        ret = "text:\n"
        ret += "\n".join("".join(char.text for char in line) for line in scr)
        ret += "\nfg:\n"
        ret += "\n".join(
            "".join("0123456789ABCDEF"[char.fg] for char in line) for line in scr
        )
        ret += "\nbg:\n"
        ret += "\n".join(
            "".join("0123456789ABCDEF"[char.bg] for char in line) for line in scr
        )
        ret += "\ncursor:\n"
        ret += f"{self.cursor.y}, {self.cursor.x}, {self.cursor.hidden}"
        return ret

    @staticmethod
    def parse(data: str) -> "Screen":
        lines = [line.replace("\r", "") for line in data.split("\n")]
        if lines[0] != "text:":
            raise ValueError("missing text:")
        scr_columns = len(lines[1])
        scr_lines = 0
        for i, line in enumerate(lines):
            if line == "fg:":
                scr_lines = i - 1
                break
        if scr_lines == 0:
            raise ValueError("missing fg:")
        if lines[2 + scr_lines * 2] != "bg:":
            raise ValueError("missing bg:")
        ret = Screen(scr_lines, scr_columns)
        for y in range(scr_lines):
            for x in range(scr_columns):
                char_text = lines[1 + y][x]
                char_fg = lines[2 + scr_lines + y][x]
                char_bg = lines[3 + scr_lines * 2 + y][x]
                ret.data[y][x] = Char(
                    text=char_text,
                    fg=Color(int(char_fg, 16)),
                    bg=Color(int(char_bg, 16)),
                )
        if 3 + scr_lines * 3 < len(lines) and lines[3 + scr_lines * 3] == "cursor:":
            # have cursor data
            cursor_line = lines[4 + scr_lines * 3]
            cursor_y, cursor_x, cursor_hidden = cursor_line.split(",")
            ret.cursor = Cursor(
                y=int(cursor_y),
                x=int(cursor_x),
                hidden=(cursor_hidden.strip() == "True"),
            )
        else:
            # hidden cursor default
            ret.cursor = Cursor(0, 0, True)
        return ret

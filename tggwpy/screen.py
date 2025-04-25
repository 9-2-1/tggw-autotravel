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
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.data = [[Char(" ", 7, 0) for x in range(columns)] for y in range(lines)]
        self.cursor = Cursor()

    def findtext(self, text: str) -> List[Tuple[int, int]]:
        return self.findtextrange(0, 0, self.lines, self.columns, text)

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
                    text=char_text, fg=int(char_fg, 16), bg=int(char_bg, 16)
                )
        return ret

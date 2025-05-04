from typing import List, Tuple, Optional
from enum import IntEnum
from dataclasses import dataclass

import wcwidth


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
        text_list = Screen.align_str(text)
        for yi in range(y, y + h):
            for xi in range(x, x + w - (len(text_list) - 1)):
                found = True
                for i in range(len(text_list)):
                    char = self.data[yi][xi + i]
                    if char.text != text_list[i]:
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
        xi = x
        while xi < x1:
            char = self.data[y][xi]
            if end is not None and char.text == end:
                break
            if fg is not None and char.fg != fg:
                break
            if bg is not None and char.bg != bg:
                break
            ret += char.text
            xi += wcwidth.wcswidth(char.text)
        return ret

    def __str__(self) -> str:
        self.fix_wide_char()
        scr = self.data
        ret = "text:\n"
        ret += "\n".join("".join(char.text for char in line) for line in scr)
        ret += "\nfg:\n"
        ret += "\n".join("".join(f"{char.fg:x}" for char in line) for line in scr)
        ret += "\nbg:\n"
        ret += "\n".join("".join(f"{char.bg:x}" for char in line) for line in scr)
        ret += "\ncursor:\n"
        ret += f"{self.cursor.y}, {self.cursor.x}, {self.cursor.hidden}"
        return ret

    @staticmethod
    def align_str(text: str) -> List[str]:
        """
        align wide char to screen
        pad empty space to right for wide char
        example:
        "a" take 1 width but CJK characters like "你" "あ" take 2 width
        input: "hello 你好 こんいちは"
        output: [
            "h", "e", "l", "l", "o", " ",
            "你", "", "好", "", "こ", "", "ん", "",
            "い", "", "ち", "", "は", ""
        ]
        """
        buf = ""
        prev_buf = ""
        width_prev = 0  # For composes
        char_list: List[str] = []
        for ch in text:
            buf += ch
            buf_width = wcwidth.wcswidth(buf)
            if buf_width > width_prev and width_prev != 0:
                # write out
                char_list.append(prev_buf)
                for i in range(width_prev - 1):
                    char_list.append("")  # paddings
                buf = ch
                buf_width = wcwidth.wcswidth(buf)
                prev_buf = ch
                width_prev = buf_width
            else:
                prev_buf = buf
                width_prev = buf_width
        if buf != "" and buf_width > 0:
            char_list.append(buf)
            for i in range(buf_width - 1):
                char_list.append("")  # paddings

        return char_list

    def fix_wide_char(self) -> None:
        """
        fix wide char in screen line
        ensure the next char after a wide char is a empty char ""
        so it can be displayed correctly and parsed correctly
        """
        return
        for line in self.data:
            width_left = 0
            width_fg = Color.WHITE
            width_bg = Color.BLACK
            for i, char in enumerate(line):
                if width_left > 0:
                    line[i] = Char("", width_fg, width_bg)
                else:
                    width = wcwidth.wcswidth(char.text)
                    if width == 0:
                        line[i] = Char(" ", char.fg, char.bg)
                        width = 1
                    width_fg = char.fg
                    width_bg = char.bg
                    width_left = width
                width_left -= 1

    @staticmethod
    def parse(text: str) -> "Screen":
        lines = [line.replace("\r", "") for line in text.split("\n")]
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
            # align wide text into screen, using wcwidth to determine width
            # assign colors
            char_text_list = Screen.align_str(lines[1 + y])
            for x in range(scr_columns):
                char_text = char_text_list[x] if x < len(char_text_list) else " "
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

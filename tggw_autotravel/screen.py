from enum import IntEnum
from dataclasses import dataclass
import json
import logging

log = logging.getLogger(__name__)


class Color(IntEnum):
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    YELLOW = 6
    WHITE = 7
    LIGHT_BLACK = 8
    LIGHT_BLUE = 9
    LIGHT_GREEN = 10
    LIGHT_CYAN = 11
    LIGHT_RED = 12
    LIGHT_MAGENTA = 13
    LIGHT_YELLOW = 14
    LIGHT_WHITE = 15


color_table = {
    "black": Color.BLACK,
    "blue": Color.BLUE,
    "green": Color.GREEN,
    "cyan": Color.CYAN,
    "red": Color.RED,
    "magenta": Color.MAGENTA,
    "brown": Color.YELLOW,
    "white": Color.WHITE,
    "brightblack": Color.LIGHT_BLACK,
    "brightblue": Color.LIGHT_BLUE,
    "brightgreen": Color.LIGHT_GREEN,
    "brightcyan": Color.LIGHT_CYAN,
    "brightred": Color.LIGHT_RED,
    "bfightmagenta": Color.LIGHT_MAGENTA,  # pyte old version
    "brightmagenta": Color.LIGHT_MAGENTA,
    "brightbrown": Color.LIGHT_YELLOW,
    "brightwhite": Color.LIGHT_WHITE,
    "000000": Color.BLACK,
    "0000ee": Color.BLUE,
    "00cd00": Color.GREEN,
    "00cdcd": Color.CYAN,
    "cd0000": Color.RED,
    "cd00cd": Color.MAGENTA,
    "cdcd00": Color.YELLOW,
    "e5e5e5": Color.WHITE,
    "7f7f7f": Color.LIGHT_BLACK,
    "5c5cff": Color.LIGHT_BLUE,
    "00ff00": Color.LIGHT_GREEN,
    "00ffff": Color.LIGHT_CYAN,
    "ff0000": Color.LIGHT_RED,
    "ff00ff": Color.LIGHT_MAGENTA,
    "ffff00": Color.LIGHT_YELLOW,
    "ffffff": Color.LIGHT_WHITE,
}


def color16(color: str, *, default: Color = Color.WHITE) -> Color:
    if color == "default":
        return default
    if color not in color_table:
        log.warning(f"Unknown color: {color}")
        color_table[color] = default
    return color_table[color]


@dataclass(slots=True, frozen=True)
class Char:
    char: str
    fg: Color
    bg: Color


class Screen:
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.buffer = [
            [Char(" ", Color.WHITE, Color.BLACK) for _ in range(columns)]
            for _ in range(lines)
        ]
        self.cursor = Cursor(0, 0, 0)

    def to_json(self) -> str:
        """
        将 Screen 对象转换为 JSON 字符串。
        """
        buffer_data = []
        for line in self.buffer:
            line_data = []
            for char in line:
                line_data.append(
                    {"char": char.char, "fg": char.fg.value, "bg": char.bg.value}
                )
            buffer_data.append(line_data)
        screen_dict = {
            "lines": self.lines,
            "columns": self.columns,
            "buffer": buffer_data,
            "cursor": {
                "x": self.cursor.x,
                "y": self.cursor.y,
                "visibility": self.cursor.visibility,
            },
        }
        return json.dumps(screen_dict, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> "Screen":
        """
        从 JSON 字符串中恢复 Screen 对象。
        """
        screen_dict = json.loads(json_str)
        lines = screen_dict["lines"]
        columns = screen_dict["columns"]
        screen = cls(lines, columns)
        buffer_data = screen_dict["buffer"]
        for y in range(lines):
            for x in range(columns):
                char_data = buffer_data[y][x]
                char = Char(
                    char=char_data["char"],
                    fg=Color(char_data["fg"]),
                    bg=Color(char_data["bg"]),
                )
                screen.buffer[y][x] = char
        cursor_data = screen_dict["cursor"]
        screen.cursor = Cursor(
            x=cursor_data["x"], y=cursor_data["y"], visibility=cursor_data["visibility"]
        )
        return screen


@dataclass(slots=True, frozen=True)
class Cursor:
    x: int
    y: int
    visibility: int  # 0, 1, 2

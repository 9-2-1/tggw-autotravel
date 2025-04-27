from typing import Union, Literal, List, Optional, Dict, Set
from dataclasses import dataclass

from .. import screen


@dataclass
class Feature:
    name: str
    trap: bool
    char: List[screen.Char]
    sample_time: int

    def is_blocking(self) -> bool:
        return False

    def is_door(self) -> bool:
        return False

    def is_box(self) -> bool:
        return False

    def is_goto(self) -> bool:
        return False

    def is_danger(self) -> bool:
        return False


@dataclass
class Symbol:
    """
    Represents a symbol on the map.
    Some symbols have two or more alternative colors.
    """

    text: int
    fgcolors: Set[int]


@dataclass
class Monster:
    name: str
    stat: str


@dataclass
class Item:
    name: str


@dataclass
class DispCell:
    symbol: Optional[Symbol]
    feature: Optional[Feature]
    monster: Optional[Monster]
    item: Optional[Item]


SeenTable = Dict[str, Symbol]


class NeriMap:
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.title = ""
        self.map = [
            [DispCell(None, None, None, None) for x in range(lines)]
            for y in range(columns)
        ]

    def update_map(self, scr: screen.Screen) -> None:
        map_title = scr.readtext(0, 2, end="-")
        self.title = map_title
        for y in range(self.lines):
            for x in range(self.columns):
                scrchr = scr.data[y][x]

    def update_seen(self, scr: screen.Screen) -> None:
        for y in range(self.lines):
            for x in range(self.columns):
                scrchr = scr.data[y][x]
                if scrchr.fg == 7 and scrchr.bg == 0:
                    self.map[y][x].feature = None
                    self.map[y][x].monster = None
                    self.map[y][x].item = None

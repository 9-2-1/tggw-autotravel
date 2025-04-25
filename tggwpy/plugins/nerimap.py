from typing import Union, Literal, List, Optional
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
class Monster:
    name: str
    stat: str
    char: List[screen.Char]
    sample_time: int


@dataclass
class Item:
    name: str
    char: List[screen.Char]
    sample_time: int


@dataclass
class DispCell:
    feature: Optional[Feature]
    monster: Optional[Monster]
    item: Optional[Item]


class NeriMap:
    def __init__(self, lines: int, columns: int) -> None:
        self.lines = lines
        self.columns = columns
        self.map = [
            [DispCell(None, None, None) for x in range(lines)] for y in range(columns)
        ]

    def update_map(self, scr: screen.Screen) -> None:
        map_title = scr.readtext(0, 2, end="-")
        map_mode = ...
        update_seen(self, scr)

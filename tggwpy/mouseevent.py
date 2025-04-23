from dataclasses import dataclass
from enum import Enum


class MouseMode(Enum):
    Move = 0
    LeftClick = 1
    LeftDrag = 2
    RightClick = 3
    RightDrag = 4
    Release = 5
    ScrollUp = 6
    ScrollDown = 7


@dataclass
class MouseEvent:
    mode: MouseMode
    y: int
    x: int

from dataclasses import dataclass
from enum import Enum


class MouseMode(Enum):
    MOVE = 0
    LEFT_CLICK = 1
    LEFT_DRAG = 2
    RIGHT_CLICK = 3
    RIGHT_DRAG = 4
    RELEASE = 5
    SCROLL_UP = 6
    SCROLL_DOWN = 7


@dataclass
class MouseEvent:
    mode: MouseMode
    y: int
    x: int

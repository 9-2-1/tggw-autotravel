from . import main
from . import ptyrun
from . import mouseevent
from . import screen
from . import overlay

MouseEvent = mouseevent.MouseEvent
Screen = screen.Screen
Char = screen.Char
Cursor = screen.Cursor


class Plugin:
    def __init__(self, tggw: "main.TGGW") -> None:
        assert tggw.game is not None
        self.tggw = tggw
        self.overlay = overlay.Overlay(tggw.game.lines, tggw.game.columns)
        self.__plugin_init__()

    def __plugin_init__(self) -> None:
        pass

    def on_key(self, key: bytes) -> bool:
        return True

    def on_mouse(self, mouse: MouseEvent) -> bool:
        return True

    def on_display(self) -> None:
        pass

    def on_display_finish(self) -> None:
        pass

from . import main
from . import mouseevent
from . import screen
from . import overlay

MouseEvent = mouseevent.MouseEvent
MouseMode = mouseevent.MouseMode
Screen = screen.Screen
Char = screen.Char
Cursor = screen.Cursor
Color = screen.Color


class Plugin:
    def __init__(self, tggw: "main.TGGW") -> None:
        assert tggw.game is not None
        self.tggw = tggw
        self.overlay = overlay.Overlay(tggw.game.lines, tggw.game.columns)
        self.__plugin_init__()

    def __plugin_init__(self) -> None:
        pass

    def on_key(self, _key: str) -> bool:
        return True

    def on_mouse(self, _mouse: MouseEvent) -> bool:
        return True

    def on_display(self) -> None:
        pass

    def on_display_finish(self) -> None:
        pass

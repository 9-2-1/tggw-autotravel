from abc import abstractmethod
from typing import Type, TypeVar, Tuple

from . import screen
from . import mouseevent
from . import screen
from . import overlay

MouseEvent = mouseevent.MouseEvent
MouseMode = mouseevent.MouseMode
Screen = screen.Screen
Char = screen.Char
Cursor = screen.Cursor
Color = screen.Color


T = TypeVar("T", bound="Plugin")


class PluginAPI:

    @abstractmethod
    def interrupt(self) -> None: ...

    @abstractmethod
    def getsize(self) -> Tuple[int, int]: ...

    @abstractmethod
    def suspend(self) -> None: ...

    @abstractmethod
    def full_redraw(self) -> None: ...

    @abstractmethod
    def getplugin(self, cls: Type[T]) -> T: ...

    @abstractmethod
    def game_screen(self) -> screen.Screen: ...

    @abstractmethod
    def tui_screen(self) -> screen.Screen: ...

    @abstractmethod
    def sendtext(self, text: str) -> None: ...


class Plugin:
    def __init__(self, tggw: PluginAPI) -> None:
        self.tggw = tggw
        self.overlay = overlay.Overlay(*tggw.getsize())
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

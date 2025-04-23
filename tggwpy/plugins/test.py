import datetime

from .. import ptyrun
from .. import plugin
from .. import mouseevent


class Test(plugin.Plugin):
    def __init__(self, game: ptyrun.Ptyrun) -> None:
        super().__init__(game)
        self.frame = 0
        self.change = 0
        self.mousey = 0
        self.mousex = 0
        self.lastkey = ""

    def update(self) -> None:
        self.overlay.clear()
        cchar = self.game.screen.data[0][2]
        fg2 = cchar.fg
        bg2 = cchar.bg
        if self.mousex < self.game.columns and self.mousey < self.game.lines:
            char = self.game.screen.data[self.mousey][self.mousex]
            self.overlay.write(
                37,
                2,
                f"{self.frame} c={self.change} k={self.lastkey!r} m=({self.mousey},{self.mousex}) {char!r}",
                fg=fg2,
                bg=bg2,
            )
        else:
            self.overlay.write(
                37,
                2,
                f"{self.frame} c={self.change} k={self.lastkey!r} m=({self.mousey},{self.mousex})",
                fg=fg2,
                bg=bg2,
            )
        self.overlay.write(
            37,
            64,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fg=fg2,
            bg=bg2,
        )

    def on_key(self, key: str) -> bool:
        self.lastkey = key
        self.update()
        return True

    def on_mouse(self, mouse: mouseevent.MouseEvent) -> bool:
        self.mousey = mouse.y
        self.mousex = mouse.x
        self.update()
        return True

    def on_display(self) -> None:
        self.frame += 1
        self.update()

    def on_display_finish(self) -> None:
        self.change += 1
        self.update()

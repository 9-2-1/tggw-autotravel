from .. import plugin


class Test(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.frame = 0
        self.change = 0
        self.mousey = 0
        self.mousex = 0
        self.lastkey = ""
        self.test = False

    def update(self) -> None:
        self.overlay.clear()
        if self.test:
            scr = self.tggw.game_screen()
            if self.mousex < scr.columns and self.mousey < scr.lines:
                char = scr.data[self.mousey][self.mousex]
                self.overlay.write(
                    37,
                    2,
                    f"{self.frame} c={self.change} k={self.lastkey!r} m=({self.mousey},{self.mousex}) {char!r}",
                    fg=0,
                    bg=15,
                )
            else:
                self.overlay.write(
                    37,
                    2,
                    f"{self.frame} c={self.change} k={self.lastkey!r} m=({self.mousey},{self.mousex})",
                    fg=0,
                    bg=15,
                )

    def on_key(self, key: str) -> bool:
        if key == "T":
            self.test = not self.test
            self.update()
            return False
        self.lastkey = key
        self.update()
        return True

    def on_mouse(self, mouse: plugin.MouseEvent) -> bool:
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

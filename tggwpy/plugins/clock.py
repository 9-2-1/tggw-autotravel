import datetime

from .. import plugin


class Clock(plugin.Plugin):
    def on_display(self) -> None:
        self.overlay.clear()
        scr = self.tggw.game_screen()
        cchar = scr.data[0][2]
        fg2 = cchar.fg
        bg2 = cchar.bg
        self.overlay.write(
            37,
            71,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fg=fg2,
            bg=bg2,
        )

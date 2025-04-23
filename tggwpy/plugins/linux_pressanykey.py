from .. import plugin
from .. import ptyrun


class PressAnyKey(plugin.Plugin):
    def __init__(self, game: ptyrun.Ptyrun) -> None:
        super().__init__(game)
        self.pressed = False

    def on_display_finish(self) -> None:
        if not self.pressed:
            cur = self.game.screen.cursor
            if cur.x == 0 and cur.y > 0 and not cur.hidden:
                checktext = self.game.screen.readtext(cur.y - 1, 0).strip()
                if checktext == "Press any key to start.":
                    self.game.sendtext(" ")
                    self.pressed = True

from .. import plugin


class PressAnyKey(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.pressed = False

    def on_display_finish(self) -> None:
        if not self.pressed:
            scr = self.tggw.game_screen()
            cur = scr.cursor
            if cur.x == 0 and cur.y > 0 and not cur.hidden:
                checktext = scr.readtext(cur.y - 1, 0).strip()
                if checktext == "Press any key to start.":
                    self.tggw.sendtext(b" ")
                    self.pressed = True

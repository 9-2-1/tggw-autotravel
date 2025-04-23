import ptyrun
import mouseevent
import overlay


class Plugin:
    def __init__(self, game: ptyrun.Ptyrun) -> None:
        self.game = game
        self.overlay = overlay.Overlay(game.columns, game.lines)

    def on_key(self, key: str) -> bool:
        return True

    def on_mouse(self, mouse: mouseevent.MouseEvent) -> bool:
        return True

    def on_display(self) -> None:
        pass

    def on_display_finish(self) -> None:
        pass

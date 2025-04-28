import sys

from .. import plugin


class CtrlC(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.ctrlc = False
        self.ctrlz = False
        self.show_hint_time = 0

    def on_key(self, key: str) -> bool:
        if key == "\x03":
            # ctrl+c twice
            self.overlay.clear()
            if self.ctrlc:
                self.overlay.clear()
                self.ctrlc = False
                self.ctrlz = False
                self.show_hint_time = 0
                self.tggw.interrupt()
            else:
                self.overlay.clear()
                self.overlay.write(
                    0,
                    0,
                    "Press Ctrl-C again to force quit (progress will lost).",
                    fg=plugin.Color.BLACK,
                    bg=plugin.Color.BRIGHT_YELLOW,
                )
                self.ctrlc = True
                self.ctrlz = False
                self.show_hint_time = 60
            return False
        if sys.platform != "win32" and key == "\x1a":
            # ctrl+z twice
            if self.ctrlz:
                self.overlay.clear()
                self.ctrlc = False
                self.ctrlz = False
                self.show_hint_time = 0
                self.tggw.suspend()
            else:
                self.overlay.clear()
                self.overlay.write(
                    0,
                    0,
                    "Press Ctrl-Z again to suspend.",
                    fg=plugin.Color.BLACK,
                    bg=plugin.Color.BRIGHT_YELLOW,
                )
                self.ctrlc = False
                self.ctrlz = True
                self.show_hint_time = 60
            return False
        if key == "\x0c":
            # ctrl+l to force full_redraw
            self.overlay.clear()
            self.overlay.write(
                0,
                0,
                "Screen is redrawed",
                fg=plugin.Color.BLACK,
                bg=plugin.Color.BRIGHT_BLUE,
            )
            self.show_hint_time = 60
            self.tggw.full_redraw()
            return False

        self.overlay.clear()
        self.ctrlc = False
        self.ctrlz = False
        self.show_hint_time = 0
        return True

    def on_display(self) -> None:
        if self.show_hint_time > 0:
            self.show_hint_time -= 1
            if self.show_hint_time == 0:
                self.overlay.clear()
                self.ctrlc = False
                self.ctrlz = False

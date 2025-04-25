import os

from .. import plugin


class CtrlC(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.ctrlc = False
        self.ctrlz = False
        self.show_hint_time = 0

    def on_key(self, key: bytes) -> bool:
        if key == b"\x03":
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
                    "Press Ctrl-C again to force quit (progress will lost). ",
                    fg=0,
                    bg=11,
                )
                self.ctrlc = True
                self.ctrlz = False
                self.show_hint_time = 300
            return False
        elif os.name != "nt" and key == b"\x1a":
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
                    "Press Ctrl-Z again to suspend. ",
                    fg=0,
                    bg=11,
                )
                self.ctrlc = False
                self.ctrlz = True
                self.show_hint_time = 300
            return False
        else:
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

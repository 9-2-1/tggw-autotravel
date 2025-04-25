from .. import plugin

# Translate arrow keys to HJKL for linux
KEYMAP = {
    b"\x1b[A": b"k",  # Up
    b"\x1b[B": b"j",  # Down
    b"\x1b[C": b"l",  # Right
    b"\x1b[D": b"h",  # Left
    b"\x1b[1;2A": b"K",  # Shift+Up
    b"\x1b[1;2B": b"J",  # Shift+Down
    b"\x1b[1;2C": b"L",  # Shift+Right
    b"\x1b[1;2D": b"H",  # Shift+Left
    b"\r": b" ",  # Enter
    b"\n": b" ",  # Enter
    b"\b": b"z",  # Backspace
    b"\x1b[5~": b"[",  # PgUp, patched
    b"\x1b[6~": b"]",  # PgDn, patched
}


class KeyMap(plugin.Plugin):
    def on_key(self, key: bytes) -> bool:
        if key in KEYMAP:
            self.tggw.sendtext(KEYMAP[key])
            return False
        return True

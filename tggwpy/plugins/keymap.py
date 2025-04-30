from .. import plugin

# Translate arrow keys to HJKL for linux
KEYMAP = {
    "\x1b[A": "k",  # Up
    "\x1b[B": "j",  # Down
    "\x1b[C": "l",  # Right
    "\x1b[D": "h",  # Left
    "\x1b[1;2A": "K",  # Shift+Up
    "\x1b[1;2": "J",  # Shift+Down
    "\x1b[1;2C": "L",  # Shift+Right
    "\x1b[1;2D": "H",  # Shift+Left
    "\x1b[5~": "[",  # PgUp, patched
    "\x1b[6~": "]",  # PgDn, patched
}


class KeyMap(plugin.Plugin):
    def on_key(self, key: str) -> bool:
        if key in KEYMAP:
            self.tggw.sendtext(KEYMAP[key])
            return False
        return True

from typing import List, Tuple
import os
from threading import Thread, Event
from queue import Queue

if os.name == "nt":
    import winpty
else:
    import ptyprocess
import pyte

import screen


def color16(color: str, default: int) -> int:
    colors = {
        "default": default,
        "000000": 0,
        "cd0000": 1,
        "00cd00": 2,
        "cdcd00": 3,
        "0000ee": 4,
        "cd00cd": 5,
        "00cdcd": 6,
        "e5e5e5": 7,
        "7f7f7f": 8,
        "ff0000": 9,
        "00ff00": 10,
        "ffff00": 11,
        "5c5cff": 12,
        "ff00ff": 13,
        "00ffff": 14,
        "ffffff": 15,
        "black": 0,
        "red": 1,
        "green": 2,
        "brown": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
        "brightblack": 8,
        "brightred": 9,
        "brightgreen": 10,
        "brightbrown": 11,
        "brightblue": 12,
        # old pyte typo
        "bfightmagenta": 13,
        "brightmagenta": 13,
        "brightcyan": 14,
        "brightwhite": 15,
    }
    if color in colors:
        return colors[color]
    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    bright = int(max(r, g, b) == 0xFF)
    rbit = int(r > 0x60)
    gbit = int(g > 0x60)
    bbit = int(b > 0x60)
    return bright * 8 + bbit * 4 + gbit * 2 + rbit


class Ptyrun:
    """
    The original game runner
    """

    def __init__(self, command: List[str], columns: int, lines: int) -> None:
        self.columns = columns
        self.lines = lines

        self.pty_data: Queue[str] = Queue()
        self.stop = Event()

        if os.name == "nt":
            self.pty = winpty.PtyProcess.spawn(command)
            # self.pty.setwinsize(lines, columns)
            self.pty.setwinsize(52, columns)
        else:
            self.pty = ptyprocess.PtyProcessUnicode.spawn(
                command, dimensions=(lines, columns)
            )

        self.pty_screen = pyte.Screen(columns, lines)
        self.pty_stream = pyte.Stream(self.pty_screen)

        self.screen = screen.Screen(columns, lines)

        self.pty_read_thread = Thread(target=self._pty_read, daemon=True)
        self.pty_read_thread.start()

    def _pty_read(self) -> None:
        try:
            while self.pty.isalive() and not self.stop.is_set():
                instr = self.pty.read()
                if instr != "":
                    self.pty_data.put(instr)
        except EOFError:
            pass

    def update_screen(self) -> bool:
        """
        Apply new pty updates to screen.Screen
        Return true if there are new updates
        """
        modified_list: List[Tuple[int, int]] = []
        self.pty_screen.dirty.clear()
        if self.pty_data.empty():
            return False
        pty_text = ""
        while not self.pty_data.empty():
            pty_text += self.pty_data.get()
        self.pty_stream.feed(pty_text)
        for y in self.pty_screen.dirty:
            for x in range(self.columns):
                pty_char = self.pty_screen.buffer[y][x]
                text = pty_char.data
                fg = color16(pty_char.fg, default=7)
                bg = color16(pty_char.bg, default=0)
                new_char = screen.Char(text, fg, bg)
                self.screen.data[y][x] = new_char
        cur = self.pty_screen.cursor
        self.screen.cursor = screen.Cursor(cur.y, cur.x, cur.hidden)
        return True

    def sendtext(self, text: str) -> None:
        self.pty.write(text)

    def is_running(self) -> bool:
        # Make mypy happy
        return bool(self.pty.isalive())

    def terminate(self) -> None:
        self.pty.terminate()

    def close(self) -> None:
        self.pty.close()

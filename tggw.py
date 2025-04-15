from typing import List, Tuple
import tui
import pyte
import os
from threading import Thread, Event
from queue import Queue

if os.name == "nt":
    import winpty
else:
    import ptyprocess

def _color16(color: str, default: int) -> int:
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


class TGGW:
    """
    The original game
    """

    def __init__(self, command: List[str], columns: int = 92, lines: int = 38) -> None:
        self.lines = lines
        self.columns = columns

        self.pty_data: Queue[str] = Queue()
        self.stop = Event()

        if os.name == "nt":
            self.pty = winpty.PtyProcess.spawn(command)
            self.pty.setwinsize(columns, lines)
        else:
            self.pty = ptyprocess.PtyProcessUnicode.spawn(command, dimensions=(lines, columns))

        self.pty_screen = pyte.Screen(columns, lines)
        self.pty_stream = pyte.Stream(self.pty_screen)

        self.pty_read_thread = Thread(target=self.pty_read, daemon=True)
        self.pty_read_thread.start()

    def pty_read(self) -> None:
        try:
            while self.pty.isalive() and not self.stop.is_set():
                instr = self.pty.read(10000)
                if instr != "":
                    self.pty_data.put(instr)
        except EOFError:
            pass

    def update_screen(self, screen: tui.Screen) -> List[Tuple[int, int]]:
        """
        apply new pty updates to tui.Screen, return modified text location
        """
        modified_list: List[Tuple[int, int]] = []
        self.pty_screen.dirty.clear()
        while not self.pty_data.empty():
            pty_text = self.pty_data.get()
            self.pty_stream.feed(pty_text)
        for y in self.pty_screen.dirty:
            screen_line = screen.data[y]
            pty_line = self.pty_screen.buffer[y]
            for x in range(self.columns):
                screen_char = screen_line[x]
                pty_char = pty_line[x]
                text = pty_char.data
                fg = _color16(pty_char.fg, default=7)
                bg = _color16(pty_char.bg, default=0)
                new_char = tui.Char(text, fg, bg)
                if screen_char != new_char:
                    screen_line[x] = new_char
                    modified_list.append((y, x))
        screen.cursor = tui.Cursor(
            self.pty_screen.cursor.y,
            self.pty_screen.cursor.x,
            self.pty_screen.cursor.hidden,
        )
        return modified_list

    def sendtext(self, text: str) -> None:
        self.pty.write(text)

    def is_running(self) -> bool:
        return bool(self.pty.isalive())

    def terminate(self) -> None:
        self.pty.terminate()

    def close(self) -> None:
        self.pty.close()

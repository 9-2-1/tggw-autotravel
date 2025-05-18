import winpty
import pyte
from threading import Thread
from queue import Queue, Empty
from typing import Optional, Dict
import logging
import time

from .base import RunBase
from ..screen import Screen, Char, Cursor, Color, color16

log = logging.getLogger(__name__)

CYCLE_TIME = 0.01


class RunWinPTY(RunBase):
    def __init__(
        self,
        cmd: str,
        *args: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        lines: int = 24,
        columns: int = 80,
    ) -> None:
        self.program = winpty.PtyProcess.spawn(
            [cmd, *args], cwd=cwd, env=env, dimensions=(lines, columns)
        )
        self.screen = Screen(lines, columns)
        self.pyte_screen = pyte.Screen(columns, lines)
        self.pyte_stream = pyte.Stream(self.pyte_screen)
        self.program_output_queue: Queue[str] = Queue()
        self.stopped = False
        self.program_read_thread = Thread(target=self._read_program_output, daemon=True)
        self.program_read_thread.start()

    def _read_program_output(self) -> None:
        while not self.stopped:
            try:
                output = self.program.read()
                if output != "":
                    log.debug(f"Read from program: {output!r}")
                    self.program_output_queue.put(output)
                else:
                    time.sleep(CYCLE_TIME)
            except (EOFError, ConnectionAbortedError) as e:
                log.debug(f"Error: {e!r}")
                break

    def alive(self) -> bool:
        return not self.stopped and self.program.isalive()

    def read(self) -> str:
        try:
            return self.program_output_queue.get_nowait()
        except Empty:
            return ""

    def read_screen(self) -> None:
        while True:
            output = self.read()
            if output == "":
                break
            self.pyte_stream.feed(output)
        # apply changes to self.screen
        for y in self.pyte_screen.dirty:
            for x in range(self.pyte_screen.columns):
                char = self.pyte_screen.buffer[y][x]
                self.screen.buffer[y][x] = Char(
                    char.data,
                    color16(char.fg, default=Color.WHITE),
                    color16(char.bg, default=Color.BLACK),
                )
        self.pyte_screen.dirty.clear()
        self.screen.cursor = Cursor(
            self.pyte_screen.cursor.x,
            self.pyte_screen.cursor.y,
            0 if self.pyte_screen.cursor.hidden else 1,
        )

    def write(self, data: str) -> None:
        try:
            self.program.write(data)
        except EOFError:
            pass

    def close(self) -> None:
        self.program.close(force=True)
        self.stopped = True
        self.program_read_thread.join()

    def kill(self) -> None:
        self.program.kill()

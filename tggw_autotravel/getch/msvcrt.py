import msvcrt
import logging
import time
import pytermgui
from typing import List

from .base import GetchBase
from .ansibreak import AnsiBreak

log = logging.getLogger(__name__)


class GetchMSVCRT(GetchBase):
    def __init__(self, escape_timeout: float = 0.1) -> None:
        self.ansibreak = AnsiBreak(escape_timeout=escape_timeout)
        self.buffer: List[str] = []
        self.virtual_processing_context = (
            pytermgui.win32console.enable_virtual_processing()
        )
        self.virtual_processing_context.__enter__()

    def getch(self) -> str:
        """
        Get a character or an escape sequence from stdin.
        Return "" if no input
        """
        if len(self.buffer) > 0:
            ret = self.buffer[0]
            self.buffer = self.buffer[1:]
            return ret
        read_tot = ""
        while msvcrt.kbhit():
            read = msvcrt.getwch()
            if read == "\0" or read == "\xe0":  # extended code
                read += msvcrt.getwch()
            read_tot += read
        # decode even read_tot == "" due to escape time
        now = time.monotonic()
        self.buffer = self.ansibreak.decode(read_tot, timestamp=now)
        if len(self.buffer) > 0:
            ret = self.buffer[0]
            self.buffer = self.buffer[1:]
            return ret
        return ""

    def close(self) -> None:
        self.virtual_processing_context.__exit__(None, None, None)

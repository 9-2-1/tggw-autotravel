import msvcrt
import logging
import time
import pytermgui
from typing import Optional

from .base import GetchBase

log = logging.getLogger(__name__)


class GetchMSVCRT(GetchBase):
    def __init__(self, escape_timeout: float = 0.1) -> None:
        self.buffer = ""
        self.escape_timeout = escape_timeout
        self.escape_start_time: Optional[float] = None
        self.virtual_processing_context = (
            pytermgui.win32console.enable_virtual_processing()
        )
        self.virtual_processing_context.__enter__()

    def getch(self) -> str:
        """
        Get a character or an escape sequence from stdin.
        """
        now = time.monotonic()
        while True:
            # Return buffer if any
            if self.buffer != "":
                char = self.buffer[0]
                if char == "\x1b":
                    if len(self.buffer) >= 2:
                        if self.buffer[1] == "O":
                            # "\x1bO."
                            if len(self.buffer) >= 3:
                                ret = self.buffer[:3]
                                self.buffer = self.buffer[3:]
                                return ret
                            # incomplete escape sequence, not returning
                        elif self.buffer[1] == "[":
                            # "\x1b\[[0-9;<]*.
                            for i in range(2, len(self.buffer)):
                                char = self.buffer[i]
                                if not char.isdigit() and not char in ";<":
                                    ret = self.buffer[: i + 1]
                                    self.buffer = self.buffer[i + 1 :]
                                    return ret
                            # incomplete escape sequence, not returning
                        else:
                            ret = self.buffer[:2]
                            self.buffer = self.buffer[2:]
                            return ret
                elif char == "\x00" or char == "\x80":
                    # extend code "[\x00\x80]."
                    if len(self.buffer) > 2:
                        ret = self.buffer[:2]
                        self.buffer = self.buffer[2:]
                        return ret
                    # incomplete escape sequence, not returning
                else:
                    self.buffer = self.buffer[1:]
                    return char
                # incomplete escape sequence
                if (
                    self.escape_start_time is not None
                    and self.escape_timeout + self.escape_start_time < now
                ):
                    ret = self.buffer
                    self.buffer = ""
                    self.escape_start_time = None
                    return ret
                # Don't return anything
            # Read input if buffer is empty or escape sequence is incomplete
            if not msvcrt.kbhit():
                return ""
            read = msvcrt.getwch()
            self.escape_start_time = now
            # log.debug(f"Read: {read!r} {self.buffer!r}")
            if read == "\0" or read == "\xe0":  # extended code
                read += msvcrt.getwch()
            self.buffer += read

    def close(self) -> None:
        self.virtual_processing_context.__exit__(None, None, None)

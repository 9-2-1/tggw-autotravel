from typing import List, Optional
from enum import Enum


class State(Enum):
    GROUND = 0
    ESCAPE = 1
    ESCAPE_INTERMEDIATE = 2
    CSI_ENTRY = 3
    CSI_PARAM = 4
    CSI_IGNORE = 5
    CSI_INTERMEDIATE = 6
    OSC_STRING = 7
    DCS_ENTRY = 8
    DCS_PARAM = 9
    DCS_IGNORE = 10
    DCS_INTERMEDIATE = 11
    DCS_PASSTHROUGH = 12
    SOS_PM_APC_STRING = 13


class CutMode(Enum):
    """
    Example: Current buffer is "abcde" and next character to read is "f"

    NONE: Add "f" to the buffer (buffer becomes "abcdef")
    abcdef
    CUT_LEFT: Write the current buffer content "abcde", then set buffer to "f"
    abcde|f
    CUT_RIGHT: Write the combined buffer and new character "abcdef", then clear the buffer
    abcdef|
    CUT_BOTH: First write the current buffer "abcde", then write the new character "f", then clear the buffer
    abcde|f|
    """

    NONE = 0
    LEFT = 1
    RIGHT = 2
    BOTH = 3


class AnsiBreak:
    def __init__(self, escape_timeout: float = 0.05) -> None:
        self.escape_start_time: Optional[float] = None
        self.escape_timeout = escape_timeout
        self.buffer = ""
        self.state = State.GROUND

    def decode(self, text: str, timestamp: float) -> List[str]:
        """
        Split a string into a list of characters and escape sequences.
        https://vt100.net/emu/dec_ansi_parser
        7-bit only.
        """
        ret: List[str] = []
        for ch in text:
            cutmode = self.readchar(ch, timestamp)
            if cutmode == CutMode.NONE:
                self.buffer += ch
            elif cutmode == CutMode.LEFT:
                if self.buffer != "":
                    ret.append(self.buffer)
                self.buffer = ch
            elif cutmode == CutMode.RIGHT:
                ret.append(self.buffer + ch)
                self.buffer = ""
            elif cutmode == CutMode.BOTH:
                if self.buffer != "":
                    ret.append(self.buffer)
                ret.append(ch)
                self.buffer = ""
        if (
            self.escape_start_time is not None
            and timestamp > self.escape_start_time + self.escape_timeout
        ):
            ret.append(self.buffer)
            self.buffer = ""
        return ret

    def readchar(self, ch: str, timestamp: float) -> CutMode:
        """
        7-bit only.
        """
        # anywhere
        if ch in {"\x18", "\x1a"}:
            return CutMode.BOTH
        if ch == "\x1b":
            self.state = State.ESCAPE
            self.escape_start_time = timestamp
            return CutMode.LEFT
        # anywhere END (7-bit only)
        if self.state == State.GROUND:
            return CutMode.BOTH
        if self.state == State.ESCAPE:
            if "\x20" <= ch <= "\x2f":
                self.state = State.ESCAPE_INTERMEDIATE
                return CutMode.NONE
            if ch == "\x5b":
                self.state = State.CSI_ENTRY
                return CutMode.NONE
            if ch == "\x5d":
                self.state = State.OSC_STRING
                return CutMode.NONE
            if ch == "\x50":
                self.state = State.DCS_ENTRY
                return CutMode.NONE
            if ch in {"\x58", "\x5e", "\x5f"}:
                self.state = State.SOS_PM_APC_STRING
                return CutMode.NONE
            if "\x30" <= ch <= "\x7e":
                self.state = State.GROUND
                self.escape_start_time = None
                return CutMode.RIGHT
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.GROUND
            self.escape_start_time = None
            return CutMode.RIGHT
        if self.state == State.ESCAPE_INTERMEDIATE:
            if "\x30" <= ch <= "\x7e":
                self.state = State.GROUND
                self.escape_start_time = None
                return CutMode.RIGHT
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.GROUND
            self.escape_start_time = None
            return CutMode.RIGHT
        if self.state == State.CSI_ENTRY:
            if ch == "\x3a":
                self.state = State.CSI_IGNORE
                return CutMode.NONE
            if "\x30" <= ch <= "\x3f":
                self.state = State.CSI_PARAM
                return CutMode.NONE
            if "\x20" <= ch <= "\x2f":
                self.state = State.CSI_INTERMEDIATE
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.GROUND
            self.escape_start_time = None
            return CutMode.RIGHT
        if self.state == State.CSI_PARAM:
            if ch == "\x3a" or "\x3c" <= ch <= "\x3f":
                self.state = State.CSI_IGNORE
                return CutMode.NONE
            if "\x20" <= ch <= "\x2f":
                self.state = State.CSI_INTERMEDIATE
                return CutMode.NONE
            if "\x30" <= ch <= "\x3f":
                self.state = State.CSI_PARAM
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.GROUND
            self.escape_start_time = None
            return CutMode.RIGHT
        if self.state == State.CSI_INTERMEDIATE:
            if "\x30" <= ch <= "\x3f":
                self.state = State.CSI_IGNORE
                return CutMode.NONE
            if "\x20" <= ch <= "\x2f":
                self.state = State.CSI_INTERMEDIATE
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.GROUND
            self.escape_start_time = None
            return CutMode.RIGHT
        if self.state == State.CSI_IGNORE:
            if "\x20" <= ch <= "\x3f":
                self.state = State.CSI_IGNORE
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.GROUND
            self.escape_start_time = None
            return CutMode.RIGHT
        if self.state == State.OSC_STRING:
            # for xterm
            if ch == "\x07":
                return CutMode.RIGHT
            return CutMode.NONE
        if self.state == State.DCS_ENTRY:
            if ch == "\x3a":
                self.state = State.DCS_IGNORE
                return CutMode.NONE
            if "\x30" <= ch <= "\x3f":
                self.state = State.DCS_PARAM
                return CutMode.NONE
            if "\x20" <= ch <= "\x2f":
                self.state = State.DCS_INTERMEDIATE
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.DCS_PASSTHROUGH
            return CutMode.RIGHT
        if self.state == State.DCS_PARAM:
            if ch == "\x3a" or "\x3c" <= ch <= "\x3f":
                self.state = State.DCS_IGNORE
                return CutMode.NONE
            if "\x20" <= ch <= "\x2f":
                self.state = State.DCS_INTERMEDIATE
                return CutMode.NONE
            if "\x30" <= ch <= "\x3f":
                self.state = State.DCS_PARAM
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.DCS_PASSTHROUGH
            return CutMode.RIGHT
        if self.state == State.DCS_INTERMEDIATE:
            if "\x30" <= ch <= "\x3f":
                self.state = State.DCS_IGNORE
                return CutMode.NONE
            if "\x20" <= ch <= "\x2f":
                self.state = State.DCS_INTERMEDIATE
                return CutMode.NONE
            if "\x00" <= ch <= "\x1f" or ch == "\x7f":
                return CutMode.NONE
            self.state = State.DCS_PASSTHROUGH
            return CutMode.RIGHT
        if self.state == State.DCS_IGNORE:
            return CutMode.NONE
        if self.state == State.DCS_PASSTHROUGH:
            return CutMode.NONE
        if self.state == State.SOS_PM_APC_STRING:
            return CutMode.NONE

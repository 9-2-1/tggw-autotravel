from typing import Optional, Dict, List
from dataclasses import dataclass
from abc import abstractmethod
import struct
import logging
import subprocess

from .base import RunBase
from ..screen import Screen, Char, Cursor, Color, color16

log = logging.getLogger(__name__)


def paramvine(cmd: str, *args: str) -> str:
    """
    Transform command and arguments into command line, see CommandLineToArgvW
    https://learn.microsoft.com/zh-cn/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw
    """
    cmd_str = cmd
    if '"' in cmd_str:
        cmd_str = cmd_str.replace('"', "")
    if any(x in cmd_str for x in " \t"):
        cmd_str = f'"{cmd_str}"'
    arg_strs = []
    for arg in args:
        if any(x in arg for x in ' \t"'):
            blackslashes = 0
            arg_new = '"'
            for x in arg:
                if x == "\\":
                    blackslashes += 1
                elif x == '"':
                    arg_new += "\\" * (blackslashes * 2 + 1) + '"'
                    blackslashes = 0
                else:
                    arg_new += "\\" * blackslashes + x
                    blackslashes = 0
            arg_new += "\\" * (blackslashes * 2) + '"'
        else:
            arg_new = arg
        arg_strs.append(arg_new)
    return cmd_str + "".join(" " + x for x in arg_strs)


QUERY_SCREEN = 1
QUERY_WRITE = 2
QUERY_ALIVE = 3
QUERY_KILL = 4
QUERY_QUIT = 0
REPLY_NONE = 0
REPLY_LOG = 1
REPLY_ERROR = 2
REPLY_SCREEN = 3
REPLY_ALIVE = 4


class RunWinConsole(RunBase):
    def __init__(
        self,
        cmd: str,
        *args: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        lines: int = 24,
        columns: int = 80,
    ) -> None:
        cmdline = paramvine(cmd, *args)
        cmdargs = [
            "winconsole\\winconsole.exe",
            "-L",
            str(lines),
            "-C",
            str(columns),
            "-c",
            cmdline,
        ]
        log.debug(f"cmdargs: {cmdargs!r}")
        self.process = subprocess.Popen(
            cmdargs,
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.screen = Screen(lines, columns)
        self.read_reply()

    def query(self, querybuf: bytes) -> bytes:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        log.debug(f"query: {querybuf.hex()}")
        self.process.stdin.write(querybuf.hex() + "\n")
        self.process.stdin.flush()
        return self.read_reply()

    def read_reply(self) -> bytes:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        while True:
            reply = self.process.stdout.readline()
            replylog = repr(reply)
            if len(replylog) > 80:
                replylog = replylog[:80] + "..."
            log.debug(f"reply: {replylog}")
            if reply.startswith("L "):
                log.info(reply[2:])
            elif reply.startswith("X "):
                raise RuntimeError(reply[2:])
            else:
                return bytes.fromhex(reply)

    def alive(self) -> bool:
        reply = self.query(bytes((QUERY_ALIVE,)))
        assert len(reply) == 2 and reply[0] == REPLY_ALIVE
        return reply[1] != 0

    def read_screen(self) -> None:
        reply = self.query(bytes((QUERY_SCREEN,)))
        # struct ReplyScreen
        # {
        #     uint16_t lines;
        #     uint16_t columns; //
        #     struct ReplyScreenCursor
        #     {
        #         uint16_t x;
        #         uint16_t y;
        #         uint8_t visibility;
        #     } cursor;
        #     struct ReplyScreenChar
        #     {
        #         uint16_t charCode;
        #         uint8_t color;
        #     } buffer[1]; // lines * columns
        # };
        format_str = "<BHHHHB"
        header_length = struct.calcsize(format_str)
        _, lines, columns, x, y, visibility = struct.unpack(
            format_str, reply[:header_length]
        )
        self.screen.lines = lines
        self.screen.columns = columns
        self.screen.cursor = Cursor(x, y, visibility)
        log.debug(f"size: {lines}x{columns}")
        char_format_str = "<HB"
        char_length = struct.calcsize(char_format_str)
        char_offset = header_length
        buffer: List[List[Char]] = []
        for y in range(lines):
            bufferline: List[Char] = []
            for x in range(columns):
                charbytes = reply[char_offset : char_offset + char_length]
                charcode, color = struct.unpack(char_format_str, charbytes)
                ch = chr(charcode) if charcode != 0 else ""
                fg = Color(color % 16)
                bg = Color(color // 16)
                char = Char(ch, fg, bg)
                bufferline.append(char)
                char_offset += char_length
            buffer.append(bufferline)
        self.screen.buffer = buffer

    def write(self, text: str) -> None:
        if text[0] == "\x1b" and len(text) > 1:
            return
        if text == "\x08":
            keycode = 0x7F
        else:
            keycode = ord(text[0])
        self.query(struct.pack("<BHB", QUERY_WRITE, keycode, 0))

    def kill(self) -> None:
        self.query(bytes((QUERY_KILL,)))

    def close(self) -> None:
        try:
            self.query(bytes((QUERY_QUIT,)))
        except Exception:
            pass
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.kill()
        self.process.wait()

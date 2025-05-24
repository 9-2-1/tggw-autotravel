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


@dataclass
class CharInfo:
    UnicodeChar: int
    wAttributes: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "CharInfo":
        UnicodeChar, wAttributes = struct.unpack("<HH", data)
        return cls(UnicodeChar, wAttributes)


@dataclass
class Reply:
    @classmethod
    def from_bytes(cls, data: bytes) -> "Reply":
        mode = data[0]
        if mode == 0:
            return ReplyNone.from_bytes(data)
        if mode == 1:
            return ReplyState.from_bytes(data)
        if mode == 2:
            return ReplyError.from_bytes(data)
        raise ValueError(f"Unknown mode: {mode}")


# #define REPLY_NONE 0
@dataclass
class ReplyNone(Reply):
    @classmethod
    def from_bytes(cls, data: bytes) -> "ReplyNone":
        return cls()


# #define REPLY_STATE 1
# struct ReplyState
# {
#     uint16_t lines;
#     uint16_t columns; //
#     uint16_t cursorX;
#     uint16_t cursorY;
#     uint16_t cursorSize; //
#     uint32_t inMode;
#     uint32_t outMode;
#     uint16_t outAttr;
#     uint8_t running;
#     uint32_t exitCode;
#     CHAR_INFO charinfo[1]; // lines * columns
# } state;
@dataclass
class ReplyState(Reply):
    lines: int
    columns: int
    cursorX: int
    cursorY: int
    cursorSize: int
    inMode: int
    outMode: int
    outAttr: int
    running: int
    exitCode: int
    charinfo: list[CharInfo]

    @classmethod
    def from_bytes(cls, data: bytes) -> "ReplyState":
        # Strip mode
        data = data[1:]

        header_format = "<HHHHHLLHBL"
        header_size = struct.calcsize(header_format)
        (
            lines,
            columns,
            cursorX,
            cursorY,
            cursorSize,
            inMode,
            outMode,
            outAttr,
            running,
            exitCode,
        ) = struct.unpack(header_format, data[:header_size])

        charinfo_list = []
        charinfo_data = data[header_size:]
        for i in range(lines * columns):
            charinfo = CharInfo.from_bytes(charinfo_data[i * 4 : (i + 1) * 4])
            charinfo_list.append(charinfo)

        return cls(
            lines=lines,
            columns=columns,
            cursorX=cursorX,
            cursorY=cursorY,
            cursorSize=cursorSize,
            inMode=inMode,
            outMode=outMode,
            outAttr=outAttr,
            running=running,
            exitCode=exitCode,
            charinfo=charinfo_list,
        )


# #define REPLY_ERROR 2
@dataclass
class ReplyError(Reply):
    errorstr: str

    @classmethod
    def from_bytes(cls, data: bytes) -> "ReplyError":
        # Strip mode
        data = data[1:]
        errorstr = data.decode()
        return cls(errorstr)


# #define KEY_EVENT 1
# typedef struct _KEY_EVENT_RECORD {
#     BOOL bKeyDown;
#     WORD wRepeatCount;
#     WORD wVirtualKeyCode;
#     WORD wVirtualScanCode;
#     union {
#         WCHAR UnicodeChar;
#         CHAR AsciiChar;
#     } uChar;
#     DWORD dwControlKeyState;
# }
# KEY_EVENT_RECORD;


class InputRecord:
    @abstractmethod
    def to_bytes(self) -> bytes: ...
@dataclass
class InputRecordKey(InputRecord):
    bKeyDown: int
    wRepeatCount: int
    wVirtualKeyCode: int
    wVirtualScanCode: int
    UnicodeChar: int
    dwControlKeyState: int

    def to_bytes(self) -> bytes:
        KEY_EVENT = 1
        args = (
            KEY_EVENT,
            self.bKeyDown,
            self.wRepeatCount,
            self.wVirtualKeyCode,
            self.wVirtualScanCode,
            self.UnicodeChar,
            self.dwControlKeyState,
        )
        return struct.pack("<LLHHHHL", *args)


# #define MOUSE_EVENT 2
# typedef struct _MOUSE_EVENT_RECORD {
#     COORD dwMousePosition;
#     DWORD dwButtonState;
#     DWORD dwControlKeyState;
#     DWORD dwEventFlags;
# } MOUSE_EVENT_RECORD;
@dataclass
class InputRecordMouse(InputRecord):
    wMousePositionX: int
    wMousePositionY: int
    dwButtonState: int
    dwControlKeyState: int
    dwEventFlags: int

    def to_bytes(self) -> bytes:
        MOUSE_EVENT = 2
        args = (
            MOUSE_EVENT,
            self.wMousePositionX,
            self.wMousePositionY,
            self.dwButtonState,
            self.dwControlKeyState,
            self.dwEventFlags,
        )
        return struct.pack("<LHHLLL", *args)


# #define WINDOW_BUFFER_SIZE_EVENT 4
# typedef struct _WINDOW_BUFFER_SIZE_RECORD {
#     COORD dwSize;
# } WINDOW_BUFFER_SIZE_RECORD;
@dataclass
class InputRecordBufferSize(InputRecord):
    wSizeX: int
    wSizeY: int

    def to_bytes(self) -> bytes:
        MOUSE_EVENT = 2
        args = (MOUSE_EVENT, self.wSizeX, self.wSizeY)
        return struct.pack("<LHH", *args)


class Query:
    @abstractmethod
    def to_bytes(self) -> bytes: ...


# #define QUERY_STATE 0
@dataclass
class QueryState(Query):
    def to_bytes(self) -> bytes:
        QUERY_STATE = 0
        return struct.pack("<B", QUERY_STATE)


# #define QUERY_INPUT 1
# struct QueryInput
# {
#     uint16_t count;
#     INPUT_RECORD inputs[1]; // count
# } input;
@dataclass
class QueryInput(Query):
    count: int
    inputs: list[InputRecord]

    def to_bytes(self) -> bytes:
        QUERY_INPUT = 1
        data = struct.pack("<BH", QUERY_INPUT, self.count)
        for input in self.inputs:
            data += input.to_bytes()
        return data


# #define QUERY_RESIZE 2
# struct QueryResize
# {
#     uint16_t lines;
#     uint16_t columns;
# } resize;
@dataclass
class QueryResize(Query):
    lines: int
    columns: int

    def to_bytes(self) -> bytes:
        QUERY_RESIZE = 2
        return struct.pack("<BHH", QUERY_RESIZE, self.lines, self.columns)


# #define QUERY_QUIT 3
@dataclass
class QueryQuit(Query):
    def to_bytes(self) -> bytes:
        QUERY_QUIT = 3
        return struct.pack("<B", QUERY_QUIT)


def charinfo_to_char(charinfo: CharInfo) -> Char:
    COMMON_LVB_TRAILING_BYTE = 0x0200
    if charinfo.wAttributes & COMMON_LVB_TRAILING_BYTE != 0:
        text = ""
    else:
        text = chr(charinfo.UnicodeChar)
    attr = charinfo.wAttributes
    fg = Color(attr & 0xF)
    bg = Color((attr >> 4) & 0xF)
    return Char(text, fg, bg)


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

    def querybytes(self, querybuf: bytes) -> bytes:
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        log.debug(f"query: {querybuf.hex()}")
        self.process.stdin.write(querybuf.hex() + "\n")
        self.process.stdin.flush()
        reply = self.process.stdout.readline()
        # log.debug(f"reply: {reply}")
        return bytes.fromhex(reply)

    def query(self, query: Query) -> Reply:
        log.debug(f"query: {query!r}")
        ret = Reply.from_bytes(self.querybytes(query.to_bytes()))
        if isinstance(ret, ReplyError):
            raise RuntimeError(ret.errorstr)
        # log.debug(f"reply: {ret!r}")
        return ret

    def alive(self) -> bool:
        state = self.query(QueryState())
        if isinstance(state, ReplyState):
            return state.running != 0
        raise RuntimeError("Unexpected reply")

    def read_screen(self) -> None:
        state = self.query(QueryState())
        if not isinstance(state, ReplyState):
            raise RuntimeError("Unexpected reply")
        self.screen.lines = state.lines
        self.screen.columns = state.columns
        log.debug(f"size: {state.lines}x{state.columns}")
        self.screen.buffer = [
            [
                charinfo_to_char(state.charinfo[y * state.columns + x])
                for x in range(state.columns)
            ]
            for y in range(state.lines)
        ]
        self.screen.cursor = Cursor(
            state.cursorX, state.cursorY, 1 if state.cursorSize != 0 else 0
        )

    def write(self, text: str) -> None:
        inputs: List[InputRecord] = []
        if text[0] == "\x1b" and len(text) > 1:
            return
        if text == "\x08":
            keycode = 0x7F
        else:
            keycode = ord(text[0])
        inputs.append(InputRecordKey(1, 1, 0, 0, keycode, 0))
        inputs.append(InputRecordKey(0, 1, 0, 0, keycode, 0))
        self.query(QueryInput(len(inputs), inputs))

    def write_inputs(self, inputs: List[InputRecord]) -> None:
        self.query(QueryInput(len(inputs), inputs))

    def kill(self) -> None:
        self.query(QueryQuit())

    def close(self) -> None:
        try:
            self.query(QueryQuit())
        except Exception:
            pass
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.kill()
        self.process.wait()

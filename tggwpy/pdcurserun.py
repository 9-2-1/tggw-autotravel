from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from queue import Queue, Empty
import time
from threading import Thread, Event
import subprocess


from . import screen
from . import errorlog


class PdcurseKey(Enum):
    # From PDCurses/curses.h
    KEY_BREAK = 0x101  #  Not on PC KBD
    KEY_DOWN = 0x102  #  Down arrow key
    KEY_UP = 0x103  #  Up arrow key
    KEY_LEFT = 0x104  #  Left arrow key
    KEY_RIGHT = 0x105  #  Right arrow key
    KEY_HOME = 0x106  #  home key
    KEY_BACKSPACE = 0x107  #  not on pc
    KEY_F0 = 0x108  #  function keys; 64 reserved

    KEY_DL = 0x148  #  delete line
    KEY_IL = 0x149  #  insert line
    KEY_DC = 0x14A  #  delete character
    KEY_IC = 0x14B  #  insert char or enter ins mode
    KEY_EIC = 0x14C  #  exit insert char mode
    KEY_CLEAR = 0x14D  #  clear screen
    KEY_EOS = 0x14E  #  clear to end of screen
    KEY_EOL = 0x14F  #  clear to end of line
    KEY_SF = 0x150  #  scroll 1 line forward
    KEY_SR = 0x151  #  scroll 1 line back (reverse)
    KEY_NPAGE = 0x152  #  next page
    KEY_PPAGE = 0x153  #  previous page
    KEY_STAB = 0x154  #  set tab
    KEY_CTAB = 0x155  #  clear tab
    KEY_CATAB = 0x156  #  clear all tabs
    KEY_ENTER = 0x157  #  enter or send (unreliable)
    KEY_SRESET = 0x158  #  soft/reset (partial/unreliable)
    KEY_RESET = 0x159  #  reset/hard reset (unreliable)
    KEY_PRINT = 0x15A  #  print/copy
    KEY_LL = 0x15B  #  home down/bottom (lower left)
    KEY_ABORT = 0x15C  #  abort/terminate key (any)
    KEY_SHELP = 0x15D  #  short help
    KEY_LHELP = 0x15E  #  long help
    KEY_BTAB = 0x15F  #  Back tab key
    KEY_BEG = 0x160  #  beg(inning) key
    KEY_CANCEL = 0x161  #  cancel key
    KEY_CLOSE = 0x162  #  close key
    KEY_COMMAND = 0x163  #  cmd (command) key
    KEY_COPY = 0x164  #  copy key
    KEY_CREATE = 0x165  #  create key
    KEY_END = 0x166  #  end key
    KEY_EXIT = 0x167  #  exit key
    KEY_FIND = 0x168  #  find key
    KEY_HELP = 0x169  #  help key
    KEY_MARK = 0x16A  #  mark key
    KEY_MESSAGE = 0x16B  #  message key
    KEY_MOVE = 0x16C  #  move key
    KEY_NEXT = 0x16D  #  next object key
    KEY_OPEN = 0x16E  #  open key
    KEY_OPTIONS = 0x16F  #  options key
    KEY_PREVIOUS = 0x170  #  previous object key
    KEY_REDO = 0x171  #  redo key
    KEY_REFERENCE = 0x172  #  ref(erence) key
    KEY_REFRESH = 0x173  #  refresh key
    KEY_REPLACE = 0x174  #  replace key
    KEY_RESTART = 0x175  #  restart key
    KEY_RESUME = 0x176  #  resume key
    KEY_SAVE = 0x177  #  save key
    KEY_SBEG = 0x178  #  shifted beginning key
    KEY_SCANCEL = 0x179  #  shifted cancel key
    KEY_SCOMMAND = 0x17A  #  shifted command key
    KEY_SCOPY = 0x17B  #  shifted copy key
    KEY_SCREATE = 0x17C  #  shifted create key
    KEY_SDC = 0x17D  #  shifted delete char key
    KEY_SDL = 0x17E  #  shifted delete line key
    KEY_SELECT = 0x17F  #  select key
    KEY_SEND = 0x180  #  shifted end key
    KEY_SEOL = 0x181  #  shifted clear line key
    KEY_SEXIT = 0x182  #  shifted exit key
    KEY_SFIND = 0x183  #  shifted find key
    KEY_SHOME = 0x184  #  shifted home key
    KEY_SIC = 0x185  #  shifted input key

    KEY_SLEFT = 0x187  #  shifted left arrow key
    KEY_SMESSAGE = 0x188  #  shifted message key
    KEY_SMOVE = 0x189  #  shifted move key
    KEY_SNEXT = 0x18A  #  shifted next key
    KEY_SOPTIONS = 0x18B  #  shifted options key
    KEY_SPREVIOUS = 0x18C  #  shifted prev key
    KEY_SPRINT = 0x18D  #  shifted print key
    KEY_SREDO = 0x18E  #  shifted redo key
    KEY_SREPLACE = 0x18F  #  shifted replace key
    KEY_SRIGHT = 0x190  #  shifted right arrow
    KEY_SRSUME = 0x191  #  shifted resume key
    KEY_SSAVE = 0x192  #  shifted save key
    KEY_SSUSPEND = 0x193  #  shifted suspend key
    KEY_SUNDO = 0x194  #  shifted undo key
    KEY_SUSPEND = 0x195  #  suspend key
    KEY_UNDO = 0x196  #  undo key

    ALT_0 = 0x197
    ALT_1 = 0x198
    ALT_2 = 0x199
    ALT_3 = 0x19A
    ALT_4 = 0x19B
    ALT_5 = 0x19C
    ALT_6 = 0x19D
    ALT_7 = 0x19E
    ALT_8 = 0x19F
    ALT_9 = 0x1A0
    ALT_A = 0x1A1
    ALT_B = 0x1A2
    ALT_C = 0x1A3
    ALT_D = 0x1A4
    ALT_E = 0x1A5
    ALT_F = 0x1A6
    ALT_G = 0x1A7
    ALT_H = 0x1A8
    ALT_I = 0x1A9
    ALT_J = 0x1AA
    ALT_K = 0x1AB
    ALT_L = 0x1AC
    ALT_M = 0x1AD
    ALT_N = 0x1AE
    ALT_O = 0x1AF
    ALT_P = 0x1B0
    ALT_Q = 0x1B1
    ALT_R = 0x1B2
    ALT_S = 0x1B3
    ALT_T = 0x1B4
    ALT_U = 0x1B5
    ALT_V = 0x1B6
    ALT_W = 0x1B7
    ALT_X = 0x1B8
    ALT_Y = 0x1B9
    ALT_Z = 0x1BA

    CTL_LEFT = 0x1BB  #  Control-Left-Arrow
    CTL_RIGHT = 0x1BC
    CTL_PGUP = 0x1BD
    CTL_PGDN = 0x1BE
    CTL_HOME = 0x1BF
    CTL_END = 0x1C0

    KEY_A1 = 0x1C1  #  upper left on Virtual keypad
    KEY_A2 = 0x1C2  #  upper middle on Virt. keypad
    KEY_A3 = 0x1C3  #  upper right on Vir. keypad
    KEY_B1 = 0x1C4  #  middle left on Virt. keypad
    KEY_B2 = 0x1C5  #  center on Virt. keypad
    KEY_B3 = 0x1C6  #  middle right on Vir. keypad
    KEY_C1 = 0x1C7  #  lower left on Virt. keypad
    KEY_C2 = 0x1C8  #  lower middle on Virt. keypad
    KEY_C3 = 0x1C9  #  lower right on Vir. keypad

    PADSLASH = 0x1CA  #  slash on keypad
    PADENTER = 0x1CB  #  enter on keypad
    CTL_PADENTER = 0x1CC  #  ctl-enter on keypad
    ALT_PADENTER = 0x1CD  #  alt-enter on keypad
    PADSTOP = 0x1CE  #  stop on keypad
    PADSTAR = 0x1CF  #  star on keypad
    PADMINUS = 0x1D0  #  minus on keypad
    PADPLUS = 0x1D1  #  plus on keypad
    CTL_PADSTOP = 0x1D2  #  ctl-stop on keypad
    CTL_PADCENTER = 0x1D3  #  ctl-enter on keypad
    CTL_PADPLUS = 0x1D4  #  ctl-plus on keypad
    CTL_PADMINUS = 0x1D5  #  ctl-minus on keypad
    CTL_PADSLASH = 0x1D6  #  ctl-slash on keypad
    CTL_PADSTAR = 0x1D7  #  ctl-star on keypad
    ALT_PADPLUS = 0x1D8  #  alt-plus on keypad
    ALT_PADMINUS = 0x1D9  #  alt-minus on keypad
    ALT_PADSLASH = 0x1DA  #  alt-slash on keypad
    ALT_PADSTAR = 0x1DB  #  alt-star on keypad
    ALT_PADSTOP = 0x1DC  #  alt-stop on keypad
    CTL_INS = 0x1DD  #  ctl-insert
    ALT_DEL = 0x1DE  #  alt-delete
    ALT_INS = 0x1DF  #  alt-insert
    CTL_UP = 0x1E0  #  ctl-up arrow
    CTL_DOWN = 0x1E1  #  ctl-down arrow
    CTL_TAB = 0x1E2  #  ctl-tab
    ALT_TAB = 0x1E3
    ALT_MINUS = 0x1E4
    ALT_EQUAL = 0x1E5
    ALT_HOME = 0x1E6
    ALT_PGUP = 0x1E7
    ALT_PGDN = 0x1E8
    ALT_END = 0x1E9
    ALT_UP = 0x1EA  #  alt-up arrow
    ALT_DOWN = 0x1EB  #  alt-down arrow
    ALT_RIGHT = 0x1EC  #  alt-right arrow
    ALT_LEFT = 0x1ED  #  alt-left arrow
    ALT_ENTER = 0x1EE  #  alt-enter
    ALT_ESC = 0x1EF  #  alt-escape
    ALT_BQUOTE = 0x1F0  #  alt-back quote
    ALT_LBRACKET = 0x1F1  #  alt-left bracket
    ALT_RBRACKET = 0x1F2  #  alt-right bracket
    ALT_SEMICOLON = 0x1F3  #  alt-semi-colon
    ALT_FQUOTE = 0x1F4  #  alt-forward quote
    ALT_COMMA = 0x1F5  #  alt-comma
    ALT_STOP = 0x1F6  #  alt-stop
    ALT_FSLASH = 0x1F7  #  alt-forward slash
    ALT_BKSP = 0x1F8  #  alt-backspace
    CTL_BKSP = 0x1F9  #  ctl-backspace
    PAD0 = 0x1FA  #  keypad 0

    CTL_PAD0 = 0x1FB  #  ctl-keypad 0
    CTL_PAD1 = 0x1FC
    CTL_PAD2 = 0x1FD
    CTL_PAD3 = 0x1FE
    CTL_PAD4 = 0x1FF
    CTL_PAD5 = 0x200
    CTL_PAD6 = 0x201
    CTL_PAD7 = 0x202
    CTL_PAD8 = 0x203
    CTL_PAD9 = 0x204

    ALT_PAD0 = 0x205  #  alt-keypad 0
    ALT_PAD1 = 0x206
    ALT_PAD2 = 0x207
    ALT_PAD3 = 0x208
    ALT_PAD4 = 0x209
    ALT_PAD5 = 0x20A
    ALT_PAD6 = 0x20B
    ALT_PAD7 = 0x20C
    ALT_PAD8 = 0x20D
    ALT_PAD9 = 0x20E

    CTL_DEL = 0x20F  #  clt-delete
    ALT_BSLASH = 0x210  #  alt-back slash
    CTL_ENTER = 0x211  #  ctl-enter

    SHF_PADENTER = 0x212  #  shift-enter on keypad
    SHF_PADSLASH = 0x213  #  shift-slash on keypad
    SHF_PADSTAR = 0x214  #  shift-star  on keypad
    SHF_PADPLUS = 0x215  #  shift-plus  on keypad
    SHF_PADMINUS = 0x216  #  shift-minus on keypad
    SHF_UP = 0x217  #  shift-up on keypad
    SHF_DOWN = 0x218  #  shift-down on keypad
    SHF_IC = 0x219  #  shift-insert on keypad
    SHF_DC = 0x21A  #  shift-delete on keypad

    KEY_MOUSE = 0x21B  #  "mouse" key
    KEY_SHIFT_L = 0x21C  #  Left-shift
    KEY_SHIFT_R = 0x21D  #  Right-shift
    KEY_CONTROL_L = 0x21E  #  Left-control
    KEY_CONTROL_R = 0x21F  #  Right-control
    KEY_ALT_L = 0x220  #  Left-alt
    KEY_ALT_R = 0x221  #  Right-alt
    KEY_RESIZE = 0x222  #  Window resize
    KEY_SUP = 0x223  #  Shifted up arrow
    KEY_SDOWN = 0x224  #  Shifted down arrow

    KEY_MIN = KEY_BREAK  #  Minimum curses key value
    KEY_MAX = KEY_SDOWN  #  Maximum curses key

    KEY_F1 = KEY_F0 + 1
    KEY_F2 = KEY_F0 + 2
    KEY_F3 = KEY_F0 + 3
    KEY_F4 = KEY_F0 + 4
    KEY_F5 = KEY_F0 + 5
    KEY_F6 = KEY_F0 + 6
    KEY_F7 = KEY_F0 + 7
    KEY_F8 = KEY_F0 + 8
    KEY_F9 = KEY_F0 + 9
    KEY_F10 = KEY_F0 + 10
    KEY_F11 = KEY_F0 + 11
    KEY_F12 = KEY_F0 + 12


def PDC_ACS(v: int) -> int:
    return 0x10000 + v


acs_map_normal: List[Union[int, str]] = [
    PDC_ACS(0),
    PDC_ACS(1),
    PDC_ACS(2),
    PDC_ACS(3),
    PDC_ACS(4),
    PDC_ACS(5),
    PDC_ACS(6),
    PDC_ACS(7),
    PDC_ACS(8),
    PDC_ACS(9),
    PDC_ACS(10),
    PDC_ACS(11),
    PDC_ACS(12),
    PDC_ACS(13),
    PDC_ACS(14),
    PDC_ACS(15),
    PDC_ACS(16),
    PDC_ACS(17),
    PDC_ACS(18),
    PDC_ACS(19),
    PDC_ACS(20),
    PDC_ACS(21),
    PDC_ACS(22),
    PDC_ACS(23),
    PDC_ACS(24),
    PDC_ACS(25),
    PDC_ACS(26),
    PDC_ACS(27),
    PDC_ACS(28),
    PDC_ACS(29),
    PDC_ACS(30),
    PDC_ACS(31),
    " ",
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    0x2192,
    0x2190,
    0x2191,
    0x2193,
    "/",
    0x2588,
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "[",
    "\\",
    "]",
    "^",
    "_",
    0x2666,
    0x2592,
    "b",
    "c",
    "d",
    "e",
    0x00B0,
    0x00B1,
    0x2591,
    0x00A4,
    0x2518,
    0x2510,
    0x250C,
    0x2514,
    0x253C,
    0x23BA,
    0x23BB,
    0x2500,
    0x23BC,
    0x23BD,
    0x251C,
    0x2524,
    0x2534,
    0x252C,
    0x2502,
    0x2264,
    0x2265,
    0x03C0,
    0x2260,
    0x00A3,
    0x00B7,
    PDC_ACS(127),
]
acs_map: List[int] = [ord(x) if isinstance(x, str) else x for x in acs_map_normal]


@dataclass
class InputKeyEvent:
    char: int
    key_code: bool
    modifiers: int


InputEvent = Union[InputKeyEvent]


@dataclass
class OutputDoUpdate:
    pass


@dataclass
class OutputCursorMove:
    y: int
    x: int


@dataclass
class OutputResizeScreen:
    lines: int
    columns: int


@dataclass
class OutputCursorSet:
    visibility: int


@dataclass
class OutputCharUpdate:
    y: int
    x: int
    char_list: List[screen.Char]


OutputEvent = Union[
    OutputDoUpdate,
    OutputCursorMove,
    OutputResizeScreen,
    OutputCursorSet,
    OutputCharUpdate,
]


class PdcurseRun:
    """
    The original game runner
    """

    def __init__(
        self,
        command: List[str],
        lines: int,
        columns: int,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> None:
        self.lines = lines
        self.columns = columns

        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            universal_newlines=True,
            bufsize=0,
        )

        self.stop: Event = Event()

        self.screen = screen.Screen(lines, columns)

        self.input_queue: Queue[InputEvent] = Queue()
        self.output_queue: Queue[OutputEvent] = Queue()
        self.doupdate_list: List[OutputEvent] = []

        self.stdout_thread = Thread(target=self._interactive, daemon=True)
        self.stdout_thread.start()
        self.stderr_thread = Thread(target=self._logerror, daemon=True)
        self.stderr_thread.start()

    def _interactive(self) -> None:
        # Interactive with the game with a fake pdcurses.dll, which directly
        # print out screen modifitions in a text format that can be easily parsed.
        # So no pesudo terminal emulator is needed.
        assert self.process.stdin is not None
        assert self.process.stdout is not None
        try:
            while self.process.poll() is None and not self.stop.is_set():
                instr = self.process.stdin.read()
                if instr != "":
                    with errorlog.errorlog():
                        # parse stdin...
                        args = instr.split(" ")
                        if args[0] == "scr_open":
                            pass
                        elif args[0] == "scr_close":
                            self.stop.set()
                            return
                        elif args[0] == "gotoyx":
                            # gotoyx %d %d
                            y = int(args[1])
                            x = int(args[2])
                            self.screen.cursor.y = y
                            self.screen.cursor.x = x
                            self.output_queue.put(OutputCursorMove(y, x))
                        elif args[0] == "doupdate":
                            self.output_queue.put(OutputDoUpdate())
                        elif args[0] == "flushinp":
                            # flushinp
                            while True:
                                try:
                                    self.input_queue.get_nowait()
                                except Empty:
                                    break
                        elif args[0] == "resize_screen":
                            # resize_screen %d %d
                            # ignore
                            lines = int(args[1])
                            columns = int(args[2])
                            self.output_queue.put(OutputResizeScreen(lines, columns))
                        elif args[0] == "curs_set":
                            # curs_set %d
                            visibility = int(args[1])
                            self.output_queue.put(OutputCursorSet(visibility))
                        elif args[0] == "update_line":
                            # update_line %d %d %s
                            y = int(args[1])
                            x = int(args[2])
                            data = args[3]
                            char_list: List[screen.Char] = []
                            for i in range(len(data) // 8):
                                chardata = data[i * 8 : (i + 1) * 8]
                                fg = int(chardata[0:1], 16)
                                bg = int(chardata[1:2], 16)
                                attr = int(chardata[2:4], 16)
                                char = int(chardata[4:8], 16)
                                if attr & 0x00010000:  # A_ALTCHARSET
                                    if 0 <= char <= 127:
                                        char = acs_map[char]
                                if attr & 0x00200000:  # A_REVERSE
                                    fg, bg = bg, fg
                                # other attrs are not supported
                                char_list.append(
                                    screen.Char(
                                        chr(char), screen.Color(fg), screen.Color(bg)
                                    )
                                )
                            self.output_queue.put(OutputCharUpdate(y, x + i, char_list))
                        elif args[0] == "reqid":
                            reqid = int(args[1])
                            reply = ""
                            if args[2] == "get_cursor_mode":
                                # reqid %d get_cursor_mode
                                reply = "0" if self.screen.cursor.hidden else "1"
                            elif args[0] == "get_rows":
                                # reqid %d get_rows
                                reply = str(self.screen.lines)
                            elif args[0] == "get_columns":
                                # reqid %d get_columns
                                reply = str(self.screen.columns)
                            elif args[0] == "check_key":
                                # reqid %d check_key
                                reply = "1" if self.input_queue.empty() else "0"
                            elif args[0] == "get_key":
                                # repid %d get_key modifiers %d
                                try:
                                    key = self.input_queue.get_nowait()
                                    reply = f"{key.char} {1 if key.key_code else 0} {key.modifiers}"
                                except Empty:
                                    reply = "-1 0 0"  # ERR = -1
                            self.process.stdout.write(f"{reqid} {reply}\n")
                            self.process.stdout.flush()

                else:
                    time.sleep(0.01)
        except EOFError:
            pass

    def _logerror(self) -> None:
        assert self.process.stderr is not None
        timestr = time.strftime("%Y%m%d-%H%M%S")
        err_file_name = f"stderr_{timestr}.log"
        try:
            while self.process.poll() is None and not self.stop.is_set():
                err = self.process.stderr.readline()
                if err != "":
                    # Only create or open file when here are errors.
                    # It is OK to open-close file as stderr is seldom used
                    with open(err_file_name, "a", encoding="utf-8") as err_file:
                        print(f"{timestr}", file=err_file)
                else:
                    time.sleep(0.01)
        except EOFError:
            pass

    def doupdate(self) -> None:
        for output in self.doupdate_list:
            if isinstance(output, OutputCharUpdate):
                for i, char in enumerate(output.char_list):
                    self.screen.data[output.y][output.x + i] = char
            elif isinstance(output, OutputCursorMove):
                self.screen.cursor.y = output.y
                self.screen.cursor.x = output.x
            elif isinstance(output, OutputCursorSet):
                self.screen.cursor.hidden = output.visibility == 0
            elif isinstance(output, OutputResizeScreen):
                self.screen.lines = output.lines
                self.screen.columns = output.columns
                self.screen.data = [
                    [screen.Char(" ", screen.Color(0), screen.Color(0))]
                    * self.screen.columns
                    for _ in range(self.screen.lines)
                ]
            elif isinstance(output, OutputDoUpdate):
                raise ValueError("OutputDoUpdate should not be in doupdate_list")
        self.doupdate_list = []

    def update_screen(self) -> bool:
        """
        Apply new pty updates to screen.Screen
        Return true if there are new updates
        """
        doupdate = False
        while True:
            try:
                output = self.output_queue.get_nowait()
            except:
                break
            if isinstance(output, OutputDoUpdate):
                self.doupdate()
                doupdate = True
            else:
                self.doupdate_list.append(output)
        return doupdate

    def sendtext(self, text: str) -> None:
        for char in text:
            self.input_queue.put(InputKeyEvent(ord(char), False, 0))

    def sendkey(self, key_code: int, modifiers: int) -> None:
        self.input_queue.put(InputKeyEvent(key_code, True, modifiers))

    def is_running(self) -> bool:
        return self.process.poll() is None

    def terminate(self) -> None:
        self.process.terminate()

    def close(self) -> None:
        self.stop.set()

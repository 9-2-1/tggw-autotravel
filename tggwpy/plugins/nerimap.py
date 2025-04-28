from typing import Union, Literal, List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field

from .. import plugin


# ----- Symbol -----


@dataclass
class Symbol:
    """
    A symbol representing a thing, with a determine foreground color.
    """

    text: str
    fg: plugin.Color


# predefined symbols
# (no need - we can live update)
SYM_HIGH_HEALTH = Symbol("*", plugin.Color.BRIGHT_WHITE)
SYM_MID_HEALTH = Symbol("*", plugin.Color.RED)
SYM_LOW_HEALTH = Symbol("*", plugin.Color.MAGENTA)

SYM_SLEEPING = Symbol("Z", plugin.Color.BRIGHT_WHITE)
SYM_DEEP_SLEEPING = Symbol("Z", plugin.Color.BRIGHT_BLACK)
SYM_WAKING_UP = Symbol("Z", plugin.Color.BRIGHT_RED)
SYM_UNCONSCIOUS = Symbol("Z", plugin.Color.MAGENTA)
SYM_UNNOTICED = Symbol("@", plugin.Color.BRIGHT_BLACK)
SYM_HEAR_YOU = Symbol("@", plugin.Color.MAGENTA)
SYM_SEE_YOU = Symbol("@", plugin.Color.BRIGHT_YELLOW)
SYM_SEE_AND_HEAR_YOU = Symbol("@", plugin.Color.BRIGHT_WHITE)
SYM_UNNOTICED = Symbol("@", plugin.Color.BRIGHT_BLACK)

SYM_FLEEING = Symbol("!", plugin.Color.BRIGHT_RED)
SYM_NETRUAL = Symbol("n", plugin.Color.CYAN)
SYM_DISEASE = Symbol("d", plugin.Color.GREEN)
SYM_POISONED = Symbol("p", plugin.Color.GREEN)

SYM_IN_LIGHT = Symbol("O", plugin.Color.BRIGHT_YELLOW)
SYM_INVISIBLE = Symbol("O", plugin.Color.BRIGHT_CYAN)
SYM_INFRAVISION = Symbol("O", plugin.Color.BRIGHT_RED)
SYM_DETECTED = Symbol("O", plugin.Color.BRIGHT_GREEN)

# ----- Legend -----


@dataclass
class LegendLine:
    symbol: Symbol
    name: str
    status: List[Symbol]
    distance: Optional[int]
    debug_wrong: List[Tuple[int, int]] = []

    @staticmethod
    def parse_screen(scr: plugin.Screen, y: int, x: int, w: int) -> "LegendLine":
        # format: C name status [distance]
        # example:
        # "A giant crab *ZOO 24"
        # A blue "A" representing a "giant crab",
        # having low health (purple *)
        # sleeping (white Z)
        # detected (green O)
        # in light (white O)
        # have a 24 distance
        symbol_char = scr.data[y][x + 1]
        symbol = Symbol(symbol_char.text, fg=symbol_char.fg)
        # name
        name = ""
        debug_wrong: List[Tuple[int, int]] = []
        for xi in range(x + 3, x + w):
            char = scr.data[y][xi]
            if char.text in "*@0123456789":
                # symbols / distance
                break
            name += char.text
        # strip trailing space
        name = name.strip()
        # symbols
        status: List[Symbol] = []
        for xi in range(xi, x + w):
            char = scr.data[y][xi]
            if char.text in "0123456789":
                # distance
                break
            if char.text == " ":
                # skip space
                continue
            status.append(Symbol(char.text, char.fg))
            # TODO By the way,
            # why the 'n' is not displayed when a netural monster is sleep.
            # I need to ask the TGGW team.
        # distance
        distance: Optional[int] = None
        for xi in range(xi, x + w):
            char = scr.data[y][xi]
            if char.text == " ":
                # skip space
                continue
            if char.text not in "0123456789":
                # something wrong
                debug_wrong.append((y, xi))
                break
            # char.text in "0123456789"
            if distance is None:
                distance = int(char.text)
            else:
                distance = distance * 10 + int(char.text)
        # sometimes the distance data is 'leaked' into next line
        if xi == x + w and y + 1 < scr.lines:
            char = scr.data[y + 1][x]
            if char.text in "0123456789":
                if distance is None:
                    distance = int(char.text)
                else:
                    distance = distance * 10 + int(char.text)
        return LegendLine(symbol, name, status, distance)


@dataclass
class Legend:
    lines: List[LegendLine]
    # is_pgup_hint_text?
    pgup: bool = False
    # is_pgdn_hint_text?
    pgdn: bool = False
    debug_wrong: List[Tuple[int, int]] = field(default_factory=list)

    @staticmethod
    def parse_screen(scr: plugin.Screen, y: int, x: int, h: int, w: int) -> "Legend":

        # PgUp and PgDn hint text
        # PgUp right-top corner
        pgup_y, pgup_x = y, x + w - 4
        pgup = scr.readtext(pgup_y, pgup_x, size=4) == "PgUp"
        # PgDn right-bottom corner
        pgdn_y, pgdn_x = y + h - 1, x + w - 4
        pgdn = scr.readtext(pgdn_y, pgdn_x, size=4) == "PgDn"

        lines: List[LegendLine] = []
        for yi in range(y, y + h):
            if pgup and yi == pgup_y:
                continue
            if pgdn and yi == pgdn_y:
                continue
            lines.append(LegendLine.parse_screen(scr, yi, x, w))
        ret = Legend(lines, pgup, pgdn)
        return ret


# ----- Legend tracing -----


@dataclass
class LegendRecordLine:
    name: str
    symbols: List[Symbol]

    def __str__(self) -> str:
        return f"{self.name}: {' '.join(f'{sym.text}({sym.fg:x})' for sym in self.symbols)}"

    @staticmethod
    def parse(text: str) -> "LegendRecordLine":
        name, symbols = text.split(":", 1)
        symbols_: List[Symbol] = []
        for symbol in symbols.split():
            assert len(symbol) == 4 and symbol[1] == "(" and symbol[3] == ")"
            text = symbol[0]
            fg = symbol[2]
            symbols_.append(Symbol(text, fg=plugin.Color(int(fg, 16))))
        return LegendRecordLine(name, symbols_)


@dataclass
class LegendRecord:
    # Multimap
    lines: List[LegendRecordLine] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(str(line) for line in self.lines)

    @staticmethod
    def parse(text: str) -> "LegendRecord":
        data: List[LegendRecordLine] = []
        for line in text.split("\n"):
            data.append(LegendRecordLine.parse(line))
        return LegendRecord(data)

    def find(self, symbol: Symbol) -> Optional[LegendRecordLine]:
        # Perfect match
        for line in self.lines:
            if symbol in line.symbols:
                return line
        # Smooth match
        for line in self.lines:
            for sym in line.symbols:
                if symbol.text == sym.text:
                    return line
        return None

    def find_name(self, name: str) -> Optional[LegendRecordLine]:
        # Perfect match
        for line in self.lines:
            if name == line.name:
                return line
        # Smooth match (display sometimes crop the name)
        for line in self.lines:
            if name.startswith(line.name) or line.name.startswith(name):
                return line
        return None

    def update(self, legend: Legend) -> None:
        for line in legend.lines:
            record = self.find_name(line.name)
            if record is None:
                self.lines.append(LegendRecordLine(line.name, [line.symbol]))
                continue
            if record.name != line.name:
                # use the longest name, if name conflicts
                if len(line.name) > len(record.name):
                    record.name = line.name
            record.symbols.append(line.symbol)


# ----- display tracing -----

@dataclass
class SquareChar:
    symbol: List[Symbol] # Multiple symbols exist for blinking characters
    bg: plugin.Color


class NeriDisplay:
    """
    Record blinking characters
    """
    def __init__(self, lines:int, columns:int) -> None:
        self.lines = lines
        self.columns = columns
        self.display: List[List[Optional[SquareChar]]] = [[None for x in range(columns)] for y in range(lines)]
    def update_screen(self, scr: plugin.Screen, y: int, x: int, h: int, w: int) -> None:
        for yi in range(y, y + h):
            for xi in range(x, x + w):
                char = scr.data[yi][xi]
                symbol = Symbol(char.text, char.fg)
                old_char = self.display[yi - y][xi - x]
                if old_char is None:
                    self.display[yi - y][xi - x] = SquareChar([symbol], char.bg)
                else:
                    old_char.bg = char.bg
                    if symbol not in old_char.symbol:
                        old_char.symbol.append(symbol)
    def reset(self) -> None:
        self.display = [
            [None for x in range(self.columns)] for y in range(self.lines)
        ]
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Union


from .. import plugin


@dataclass
class NeriMap:
    """
    parse the map pane
    """

    lines: int
    columns: int
    name: str
    player_y: int
    player_x: int
    data: List[List[plugin.Char]]

    # Some of walls have different colors, indecating themed room or challenge rooms.
    # Also ground

    # Need to know:
    # - player position
    # - visible monsters
    # - visible items
    # - sound alerts
    # - features (wall, door, box, trap, special terrain)

    @staticmethod
    def parse_screen(scr: plugin.Screen, y0: int, x0: int, h: int, w: int) -> "NeriMap":
        name = scr.readtext(y0, x0 + 2, size=w - 2, end="-")
        if scr.cursor.hidden:
            raise NotImplementedError("Not a map: Cursor is hidden")
        y1 = y0 + 1
        x1 = x0 + 1
        y2 = y0 + h - 1
        x2 = x0 + w - 1
        player_y = scr.cursor.y - y1
        player_x = scr.cursor.x - x1
        if not (0 <= player_y < h - 2 and 0 <= player_x < w - 2):
            raise NotImplementedError("Not a map: Player position is out of map")
        data: List[List[plugin.Char]] = [
            [scr.data[y][x] for x in range(x1, x2)] for y in range(y1, y2)
        ]
        return NeriMap(h - 2, w - 2, name, player_y, player_x, data)


class TextParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def next_char(self) -> str:
        if self.i < len(self.text):
            return self.text[self.i]
        else:
            return ""

    def next(self) -> None:
        self.i += 1

    def end(self) -> bool:
        return self.i >= len(self.text)

    def read_space(self) -> str:
        ret = ""
        while self.i < len(self.text) and self.text[self.i] == " ":
            ret += self.text[self.i]
            self.i += 1
        return ret

    def read_name(self) -> str:
        ret = ""
        while self.i < len(self.text) and self.text[self.i] != ":":
            ret += self.text[self.i]
            self.i += 1
        if self.i < len(self.text) and self.text[self.i] == ":":
            self.i += 1
        return ret

    def read_int(self) -> int:
        sign = 1
        if self.i < len(self.text) and self.text[self.i] == "-":
            sign = -1
            self.i += 1
        value = 0
        while self.i < len(self.text) and self.text[self.i].isdigit():
            value = value * 10 + int(self.text[self.i])
            self.i += 1
        return value * sign


def parse_attr_line(text: str, output: Dict[str, int]) -> None:
    parser = TextParser(text)
    parser.read_space()
    while not parser.end():
        name = parser.read_name()
        parser.read_space()
        value = parser.read_int()
        # Ignore percentage mark
        if parser.next_char() == "%":
            parser.next()
        output[name] = value
        parser.read_space()
        # max value
        if parser.next_char() == "/":
            parser.next()
            parser.read_space()
            value = parser.read_int()
            output["max_" + name] = value
        parser.read_space()


@dataclass
class NeriAttributes:
    """
    parse the attributes pane
    """

    # It is much easy in TGGW v2.6

    hp: int = 0
    max_hp: int = 0
    mp: int = 0
    max_mp: int = 0
    ep: int = 0  # energy

    rep: int = 0  # reputation
    food: int = 0
    gold: int = 0
    ammo: int = 0

    melee: int = 0
    block: int = 0
    missile: int = 0
    vision: int = 0
    noise: int = 0
    arm: int = 0  # armor

    rf: int = 0  # Fire resistance
    rc: int = 0  # Cold resistance
    rp: int = 0  # Poison resistance

    # These stats are moved to the status pane.
    # rE: int = 0  # Electric resistance
    # rA: int = 0  # Acid resistance

    # replaced with Thievery
    thievery: int = 0

    raw: Dict[str, int] = field(default_factory=dict)

    # assert self.thievery == 5 * (9 + self.vision - self.noise)

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriAttributes":
        raw: Dict[str, int] = {}
        for y in range(y + 1, y + h - 1):
            text = scr.readtext(y, x + 1, size=w - 2)
            parse_attr_line(text, raw)
        attr = NeriAttributes(raw=raw)
        for name, value in raw.items():
            try:
                setattr(attr, name.lower(), value)
            except AttributeError:
                pass
        return attr


@dataclass
class NeriMessages:
    """
    parse the messages pane
    """

    # Just read the messages line by line
    # Does message line-wrap?
    # Checked: right-cropped if exceeds the pane width
    messages: List[str]

    # Color is not important, I think.
    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriMessages":
        messages: List[str] = []
        for y in range(y + 1, y + h - 1):
            message = scr.readtext(y, x + 1, size=w - 2).strip()
            messages.append(message)
        return NeriMessages(messages)


@dataclass
class NeriLegendLine:
    char: plugin.Char
    name: str
    status: List[plugin.Char]
    distance: Optional[int]

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, w: int
    ) -> Optional["NeriLegendLine"]:
        # format: C name status [distance]
        # example:
        # "A giant crab *ZOO 24"
        char = scr.data[y][x + 1]
        if char.text == " ":
            return None
        # name
        name = ""
        debug_wrong: List[Tuple[int, int]] = []
        for xi in range(x + 3, x + w):
            ch = scr.data[y][xi]
            if ch.text in "*@" or ch.text.isdigit():
                # symbols / distance
                break
            name += ch.text
        # strip trailing space
        name = name.strip()
        # symbols
        status: List[plugin.Char] = []
        for xi in range(xi, x + w):
            ch = scr.data[y][xi]
            if ch.text.isdigit():
                # distance
                break
            if ch.text == " ":
                # skip space
                continue
            status.append(ch)
            # TODO By the way,
            # why the 'n' is not displayed when a netural monster is sleep.
            # I need to ask the TGGW team.
        # distance
        distance: Optional[int] = None
        for xi in range(xi, x + w):
            ch = scr.data[y][xi]
            if ch.text == " ":
                # skip space
                continue
            if not ch.text.isdigit():
                # something wrong
                debug_wrong.append((y, xi))
                break
            # char.text in "0123456789"
            if distance is None:
                distance = int(ch.text)
            else:
                distance = distance * 10 + int(ch.text)
        # sometimes the distance data is 'leaked' into next line
        if xi == x + w:
            ch = scr.data[y + 1][x]
            if ch.text.isdigit():
                if distance is None:
                    distance = int(ch.text)
                else:
                    distance = distance * 10 + int(ch.text)
        return NeriLegendLine(char, name, status, distance)


@dataclass
class NeriLegend:
    legends: List[NeriLegendLine]
    pgup: bool
    pgdn: bool

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriLegend":
        # PgUp and PgDn hint text
        # PgUp right-top corner
        pgup_y = y + 1
        pgup_x = x + w - 5
        pgup = scr.readtext(pgup_y, pgup_x, size=4) == "PgUp"
        # PgDn right-bottom corner
        pgdn_y = y + h - 2
        pgdn_x = x + w - 5
        pgdn = scr.readtext(pgdn_y, pgdn_x, size=4) == "PgDn"

        lines: List[NeriLegendLine] = []
        for yi in range(y + 1, y + h - 1):
            if pgup and yi == pgup_y:
                continue
            if pgdn and yi == pgdn_y:
                continue
            line = NeriLegendLine.parse_screen(scr, yi, x + 1, w - 2)
            if line is not None:
                lines.append(line)
        return NeriLegend(lines, pgup, pgdn)


@dataclass
class NeriSeen:
    """
    parse the seen pane
    """

    items: NeriLegend
    monsters: NeriLegend
    features: NeriLegend

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> Union["NeriSeen", NotImplementedError]:
        title = scr.readtext(y, x + 2, size=w - 2, end="-")
        if title != "Seen":
            return NotImplementedError("Not a seen panel: title")
        items = NeriLegend.parse_screen(scr, y + 1, x + 1, 9, w - 2)
        # 2 pane share one border so the y is y+9, not y+10
        monsters = NeriLegend.parse_screen(scr, y + 9, x + 1, 9, w - 2)
        features = NeriLegend.parse_screen(scr, y + 17, x + 1, 9, w - 2)
        return NeriSeen(items, monsters, features)


@dataclass
class NeriStatus:
    """
    parse the status pane
    """

    # line by line is OK. Color is not important.
    status: List[str]

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> Union["NeriStatus", NotImplementedError]:
        title = scr.readtext(y, x + 2, size=w - 2, end="-")
        if title != "Status":
            return NotImplementedError("Not a status panel: title")
        status: List[str] = []
        for y in range(y + 1, y + h - 1):
            line = scr.readtext(y, x + 1, size=w - 2).strip()
            if line != "":
                status.append(line)
        return NeriStatus(status)


@dataclass
class NeriTarget:
    """
    parse the target pane
    """

    char: plugin.Char
    name: str
    mode: str
    frequency: str  # common rare ...

    hp: int
    maxhp: int
    mp: int
    maxmp: int

    status: List[str]

    distance: int
    see_distance: int  # infravision, in_light
    hear_distance: int  # deep sleep
    missile_range: int  # how long player can shoot the target

    actions: List[str]  # action cost are not parsed

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriTarget":
        raise NotImplementedError


@dataclass
class NeriAbilities:
    name: str
    mode: str  # melee magic missile natural
    used: bool
    range: int
    mp: int  # magic
    ammo: int  # missile
    target: str  # you burst all ally
    effects: List[str]

    scroll: int
    scroll_for_more: bool

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriAbilities":
        raise NotImplementedError


@dataclass
class NeriTargetExamine:
    """
    parse the target examine pane
    """

    attributes: Dict[str, int]  # Prm Tmp Ctx Tot
    # including resistences
    traits: List[str]
    abilities: List[NeriAbilities]
    thievery: int

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriTargetExamine":
        raise NotImplementedError


@dataclass
class NeriPlayerCharacter:
    """
    parse the player character pane (menu screen)
    """

    attributes: Dict[str, int]  # Prm Tmp Ctx Tot
    traits: List[str]
    abilities: List[NeriAbilities]
    thievery: int

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriPlayerCharacter":
        raise NotImplementedError


@dataclass
class NeriInventory:
    """
    parse the inventory and equipment pane
    """

    inventory: List[str]
    equipment: List[str]
    equipment_place: List[str]  # head neck hand hand ...

    focus: int  # 0-inventory 1-equipment
    pointer: int

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriInventory":
        raise NotImplementedError


@dataclass
class NeriItem:
    """
    parse the item pane
    """

    char: plugin.Char
    name: str
    mode: str
    frequency: str  # common rare ...

    stats: List[str]
    grants: List[str]
    effect: List[str]
    on_equip: List[str]
    on_hit: List[str]

    # cannot use, cannot equip
    locked: Optional[str]

    # requirement
    rep: int
    mp: int
    min_mp: int

    target: str

    @staticmethod
    def parse_screen(scr: plugin.Screen, y: int, x: int, h: int, w: int) -> "NeriItem":
        raise NotImplementedError


@dataclass
class NeriItemDiff:
    """
    parse the item pane
    """

    char: plugin.Char
    name: str
    mode: str
    frequency: str  # common rare ...
    locked: Optional[str]

    changes: List[str]

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriItemDiff":
        raise NotImplementedError


@dataclass
class NeriLeft:
    top: Union[
        NeriMap,
        NeriPlayerCharacter,
        NeriTargetExamine,
        NeriInventory,
        NotImplementedError,
    ]
    middle: NeriAttributes
    bottom: NeriMessages

    @staticmethod
    def parse_screen(scr: plugin.Screen, y: int, x: int, h: int, w: int) -> "NeriLeft":
        try:
            top: Union[NeriMap, NotImplementedError] = NeriMap.parse_screen(
                scr, y, x, 22, 62
            )
        except NotImplementedError as err:
            top = err
        middle = NeriAttributes.parse_screen(scr, y + 22, x, 5, 62)
        bottom = NeriMessages.parse_screen(scr, y + 27, x, 11, 62)
        return NeriLeft(top, middle, bottom)


@dataclass
class NeriSeenStatus:
    top: Union[NeriSeen, NotImplementedError]
    bottom: Union[NeriStatus, NotImplementedError]

    @staticmethod
    def parse_screen(
        scr: plugin.Screen, y: int, x: int, h: int, w: int
    ) -> "NeriSeenStatus":
        top = NeriSeen.parse_screen(scr, y, x, 27, w)
        bottom = NeriStatus.parse_screen(scr, y + 27, x, h - 27, w)
        return NeriSeenStatus(top, bottom)


@dataclass
class NeriView:
    left: NeriLeft
    right: Union[
        NeriSeenStatus, NeriItem, NeriItemDiff, NeriTarget, NotImplementedError
    ]

    @staticmethod
    def parse_screen(scr: plugin.Screen) -> "NeriView":
        left = NeriLeft.parse_screen(scr, 0, 0, 38, 62)
        try:
            right: Union[NeriSeenStatus, NotImplementedError] = (
                NeriSeenStatus.parse_screen(scr, 0, 62, 38, 30)
            )
        except NotImplementedError as err:
            right = err
        return NeriView(left, right)

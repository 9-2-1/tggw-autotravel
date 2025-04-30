from dataclasses import dataclass
from functools import total_ordering
from typing import List, Tuple, Optional, Dict
import heapq


from .. import plugin
from . import neriview

DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


@dataclass
@total_ordering
class SearchNode:
    y: int
    x: int
    dir: Optional[int]  # 0-Right 1-Left 2-Down 3-Up
    cost: int
    parent: Optional["SearchNode"] = None

    def __lt__(self, other: "SearchNode") -> bool:
        return self.cost < other.cost


def dfs_search(
    cost_map: List[List[Optional[int]]],
    starty: int,
    startx: int,
    goaly: int,
    goalx: int,
) -> Tuple[List[Tuple[int, int]], Optional[int]]:
    open_list: List[SearchNode] = []
    closed_list: Dict[Tuple[int, int, Optional[int]], int] = {}
    heapq.heappush(
        open_list,
        SearchNode(starty, startx, None, 0),
    )
    closed_list[(starty, startx, None)] = 0
    while len(open_list) > 0:
        cur_node = heapq.heappop(open_list)
        if cur_node.cost != closed_list.get(
            (cur_node.y, cur_node.x, cur_node.dir), None
        ):
            # Another lower cost path to the node was found
            continue
        if cur_node.y == goaly and cur_node.x == goalx:
            tot_cost = cur_node.cost
            path = []
            while cur_node.parent is not None:
                path.append((cur_node.y, cur_node.x))
                cur_node = cur_node.parent
            path.append((cur_node.y, cur_node.x))
            path.reverse()
            return path, tot_cost
        for new_dir, (dy, dx) in enumerate(DIRS):
            new_y = cur_node.y + dy
            new_x = cur_node.x + dx
            if 0 <= new_y < len(cost_map) and 0 <= new_x < len(cost_map[0]):
                cost = cost_map[new_y][new_x]
                if cost is not None:
                    new_cost = cur_node.cost + cost
                    dir_change = cur_node.dir is not None and new_dir != cur_node.dir
                    if dir_change:
                        # avoid turning
                        new_cost += 3
                    if (new_y, new_x, new_dir) not in closed_list or (
                        new_cost < closed_list[new_y, new_x, new_dir]
                    ):
                        closed_list[new_y, new_x, new_dir] = new_cost
                        heapq.heappush(
                            open_list,
                            SearchNode(new_y, new_x, new_dir, new_cost, cur_node),
                        )
    return ([], None)


class AutoTravel(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.autotravel = False
        self.player_x = 0
        self.player_y = 0
        self.target_x = 0
        self.target_y = 0
        self.target_change = False
        self.target_click = False
        self.travel_path: List[Tuple[int, int]] = []
        self.travel_cost: List[List[Optional[int]]] = []
        self.travel_path_cost: Optional[int] = None
        self.debug = False
        self.in_play = False

    def update_travel_cost(self, map: neriview.NeriMap) -> None:
        self.player_y = map.player_y
        self.player_x = map.player_x
        self.travel_cost = []
        for y in range(map.lines):
            line_cost: List[Optional[int]] = []
            for x in range(map.columns):
                char = map.data[y][x]
                cost: Optional[int] = None
                if char.text in {"#", "^", "~", "&", "Y", "@"}:
                    cost = None  # inpassable
                elif char.text.isalpha() and char.bg != plugin.Color.CYAN:
                    cost = 250  # Monster
                elif char.text == "+":
                    if char.fg == plugin.Color.BRIGHT_GREEN:
                        cost = None
                    elif char.bg == plugin.Color.RED:
                        cost = 1000000  # trap door
                    elif char.fg == plugin.Color.BRIGHT_RED:
                        cost = None  # stuck door
                    elif char.fg == plugin.Color.MAGENTA:
                        cost = 1  # curtain
                    elif char.fg == plugin.Color.CYAN:
                        cost = 1000000  # jammed door
                    else:
                        cost = 50  # door to open
                elif char.text in {"X", "o", ":", ","}:
                    cost = 50  # box
                elif char.text == " ":
                    cost = 1000  # unexplored
                elif char.bg == plugin.Color.RED:
                    cost = 1000000  # trap
                else:
                    cost = 1
                line_cost.append(cost)
            self.travel_cost.append(line_cost)

    def plan_travel_path(self) -> None:
        self.travel_path, self.travel_path_cost = dfs_search(
            self.travel_cost, self.player_y, self.player_x, self.target_y, self.target_x
        )

    def travel_to(
        self,
    ) -> None:
        pass

    def debug_show(self) -> None:
        cost = self.travel_cost[self.target_y][self.target_x]
        self.overlay.write(
            36,
            0,
            f"AutoTravel p_cost={cost!r} cost={self.travel_path_cost!r}",
            fg=plugin.Color.BLACK,
            bg=plugin.Color.BRIGHT_WHITE,
        )
        if self.in_play:
            scr = self.tggw.game_screen()
            # for y in range(20):
            #     for x in range(60):
            #         ch0 = scr.data[y + 1][x + 1]
            #         cost = self.travel_cost[y][x]
            #         if cost is None:
            #             bg = ch0.bg
            #         elif cost >= 1000000:
            #             bg = plugin.Color.RED
            #         elif cost >= 1000:
            #             bg = plugin.Color.BLUE
            #         elif cost >= 250:
            #             bg = plugin.Color.MAGENTA
            #         elif cost >= 50:
            #             bg = plugin.Color.YELLOW
            #         else:
            #             bg = plugin.Color.CYAN
            #         ch1 = plugin.Char(ch0.text, ch0.fg, bg)
            #         self.overlay.data[y + 1][x + 1] = ch1
            if self.travel_path:
                for i in range(1, len(self.travel_path)):
                    if i == len(self.travel_path) - 1 or i == 0:
                        # target
                        cur = self.travel_path[i]
                        ch = "*"
                    else:
                        prev = self.travel_path[i - 1]
                        cur = self.travel_path[i]
                        next = self.travel_path[i + 1]
                        # y, x
                        # Right Left Down Up
                        char_table = [
                            # Right Left Down Up
                            [">", "-", ",", "`"],  # Right
                            ["-", "<", ".", "'"],  # Left
                            [",", ".", "v", "|"],  # Down
                            ["`", "'", "|", "^"],  # Up
                        ]
                        prev_offs = (prev[0] - cur[0], prev[1] - cur[1])
                        next_offs = (next[0] - cur[0], next[1] - cur[1])
                        try:
                            d1 = DIRS.index(prev_offs)
                            d2 = DIRS.index(next_offs)
                            ch = char_table[d1][d2]
                        except IndexError:
                            # skipped path, something wrong!
                            ch = "?"
                    y, x = cur
                    cost = self.travel_cost[y][x]
                    if cost is None:
                        # something wrong
                        fg = plugin.Color.BRIGHT_WHITE
                    elif cost >= 1000000:
                        fg = plugin.Color.BRIGHT_RED
                    elif cost >= 1000:
                        fg = plugin.Color.BRIGHT_BLUE
                    elif cost >= 250:
                        fg = plugin.Color.BRIGHT_MAGENTA
                    elif cost >= 50:
                        fg = plugin.Color.BRIGHT_YELLOW
                    else:
                        fg = plugin.Color.BRIGHT_CYAN
                    ch1 = plugin.Char(ch, fg, plugin.Color.BLACK)
                    self.overlay.data[y + 1][x + 1] = ch1

    def on_key(self, key: str) -> bool:
        if key == "t":
            self.debug = not self.debug
            return False
        if self.autotravel:
            self.autotravel = False
            return False
        return True

    def on_mouse(self, mouse: plugin.MouseEvent) -> bool:
        if self.autotravel:
            if mouse.mode in {
                plugin.MouseMode.LEFT_CLICK,
                plugin.MouseMode.RIGHT_CLICK,
            }:
                self.autotravel = False
                return False
        elif self.in_play:
            if 1 <= mouse.y < 21 and 1 <= mouse.x < 61:
                self.target_y = mouse.y - 1
                self.target_x = mouse.x - 1
                self.target_change = True
                if mouse.mode == plugin.MouseMode.LEFT_CLICK:
                    self.target_click = True
            return False
        return True

    def travel(self) -> None:
        if not self.travel_path or len(self.travel_path) == 1:
            self.autotravel = False
            return
        cur = self.travel_path[0]
        next = self.travel_path[1]
        # y, x
        # Right Left Down Up
        dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        # Right Left Down Up
        char_table = ["l", "h", "j", "k"]
        next_offs = (next[0] - cur[0], next[1] - cur[1])
        try:
            chr = char_table[dirs.index(next_offs)]
        except IndexError:
            self.autotravel = False
            return
        self.tggw.sendtext(chr)
        self.current_cost = self.travel_path_cost

    def on_display(self) -> None:
        self.overlay.clear()
        if self.debug:
            self.debug_show()
        if self.in_play:
            if self.target_change:
                self.target_change = False
                self.plan_travel_path()
            if self.target_click:
                self.target_click = False
                if self.travel_path:
                    self.autotravel = True
                    self.travel()

    def on_display_finish(self) -> None:
        self.in_play = False
        scr = self.tggw.game_screen()
        view = neriview.NeriView.parse_screen(scr)
        mappane = view.left.top
        if isinstance(mappane, neriview.NeriMap):
            if isinstance(view.right, neriview.NeriSeenStatus):
                if isinstance(view.right.bottom, neriview.NeriStatus):
                    if "exploring" in view.right.bottom.status:
                        self.in_play = True
        if self.in_play:
            assert isinstance(mappane, neriview.NeriMap)
            self.update_travel_cost(mappane)
            self.plan_travel_path()
            if self.autotravel:
                # if the cost changed (i.e. player moved or door opened)
                # TODO corner case
                if self.current_cost != self.travel_path_cost:
                    self.travel()
        else:
            if self.autotravel:
                self.autotravel = False

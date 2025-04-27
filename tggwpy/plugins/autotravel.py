from typing import Dict, Tuple, List
from enum import Enum
from dataclasses import dataclass

from .. import plugin


class AutoTravel(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.autoexplore = False
        self.debug = False
        self.in_play = False

        # purple_mark door closed by player
        # open door later
        # ignore red door
        # purple door is curtain
        # combat mode escape
        # ! mark passable escape

        # self.curmap = nerimap(scr)

    def is_play(self) -> bool:
        scr = self.tggw.game_screen()
        seen_pane_title = scr.readtext(0, 64, end="-")
        items_pane_title = scr.readtext(1, 65, end="-")
        have_continue = scr.findtextrange(1, 1, 20, 60, "' to continue. ")
        map_title = scr.readtext(0, 2, end="-")
        cursor = scr.cursor
        if (
            seen_pane_title == "Seen"
            and items_pane_title == "Items"
            and not have_continue
            and map_title != "campfire"
            and map_title != "donation box"
            and not cursor.hidden
            and 1 <= cursor.x <= 60
            and 1 <= cursor.y <= 20
        ):
            return True
        return False

    def explore(self) -> None:
        pass

    def debug_show(self) -> None:
        self.overlay.write(36, 0, "DEBUG", fg=0, bg=15)
        if self.in_play:
            self.overlay.write(35, 0, "Seen", fg=0, bg=15)
            # not passable

            # &
            # not-grey X o
            # not-cyan ~
            # purple "
            # #
            # ^
            # red-marked
            # + (green)

            # not-explore
            # ' ' nearby

            # special
            # brown ~
            # avoid terrain

            scr = self.tggw.game_screen()
            for y in range(1, 21):
                for x in range(1, 61):
                    ch0 = scr.data[y][x]
                    bg = ch0.bg
                    if ch0.text == " ":
                        bg = 2
                    if ch0.text in ['"', "<", ">", "0", "O", ".", "~"]:
                        bg = 3
                    elif ch0.text in ["#", "^"]:
                        bg = 5
                    elif (
                        ch0.text == "+"
                        and ch0.fg in [1, 3, 5, 7, 8, 11, 15]
                        and ch0.bg != 1
                    ):
                        bg = 4
                    elif (
                        ch0.text == "/"
                        and ch0.fg in [1, 3, 5, 7, 8, 11, 15]
                        and ch0.bg != 1
                    ):
                        bg = 3
                    elif ch0.text == "X" and ch0.fg != 8:
                        bg = 5
                    elif ch0.text == "o" and ch0.fg != 8:
                        bg = 5
                    ch1 = plugin.Char(ch0.text, ch0.fg, bg)
                    self.overlay.data[y][x] = ch1

    def on_key(self, key: str) -> bool:
        if key == "E":
            self.debug = not self.debug
        else:
            if self.autoexplore:
                self.autoexplore = False
                self.explore()
            else:
                if key == "e":
                    self.autoexplore = True
        return True

    def on_mouse(self, mouse: plugin.MouseEvent) -> bool:
        if self.autoexplore:
            if mouse.mode in [
                plugin.MouseMode.LeftClick,
                plugin.MouseMode.RightClick,
            ]:
                self.autoexplore = False
        return True

    def on_display(self) -> None:
        self.overlay.clear()
        if self.debug:
            self.debug_show()

    def on_display_finish(self) -> None:
        self.in_play = self.is_play()
        if self.in_play:
            if self.autoexplore:
                self.explore()

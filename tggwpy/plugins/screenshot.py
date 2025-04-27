import datetime
import glob
import traceback
from typing import List
import os

from .. import plugin


class Screenshot(plugin.Plugin):
    def __plugin_init__(self) -> None:
        self.show_hint_time = 0
        self.replay_mode = False
        self.replay_list: List[str] = []
        self.replay_pos = 0
        self.press_delete = False

    def on_key(self, key: str) -> bool:
        if not self.replay_mode:
            if key in ["q", "Q"]:
                # capture screenshot
                if key == "q":
                    scr = self.tggw.game_screen()
                else:
                    # capture real screen (with plugin overlay)
                    scr = self.tggw.tui_screen()
                tstr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                fname = f"tggw_{tstr}"
                if key == "Q":
                    fname = fname + "_plugin"
                fname0 = fname
                counter = 1
                while os.path.exists(f"{fname}.txt"):
                    counter += 1
                    fname = f"{fname0}_{counter}"
                fname = f"{fname}.txt"
                self.overlay.clear()
                self.overlay.write(37, 0, f'Screenshot saved to "{fname}"', fg=0, bg=10)
                self.show_hint_time = 60
                with open(fname, "w", encoding="utf-8") as file:
                    file.write(str(scr))
                return False
            elif key == "w":
                # enter replay mode
                self.replay_mode = True
                self.replay_list = glob.glob("tggw_*.txt")
                # reverse sort
                self.replay_list.sort(reverse=True)
                self.replay_pos = 0
                self.replay()
                return False
        else:
            # replay mode
            if key in ["q", "k", "h", "\x1b[A", "\x1b[D"]:
                # prev
                self.replay_pos -= 1
                if self.replay_pos == -1:
                    self.replay_pos = 0
                    self.replay(noshowtitle=True)
                    self.overlay.write(
                        37, 0, "This is the newest screenshot.", fg=0, bg=10
                    )
                    self.show_hint_time = 60
                else:
                    self.replay()
            elif key in ["w", "j", "l", "\x1b[B", "\x1b[C"]:
                # next
                self.replay_pos += 1
                if self.replay_pos >= len(self.replay_list):
                    self.replay_pos = len(self.replay_list) - 1
                    self.replay(noshowtitle=True)
                    self.overlay.write(
                        37, 0, "This is the oldest screenshot.", fg=0, bg=10
                    )
                    self.show_hint_time = 60
                else:
                    self.replay()
            elif key in ["d"]:
                if self.press_delete:
                    fname = self.replay_list.pop(self.replay_pos)
                    os.unlink(fname)
                    if self.replay_pos >= len(self.replay_list):
                        self.replay_pos == len(self.replay_list) - 1
                    self.replay()
                    self.press_delete = False
                else:
                    self.replay(noshowtitle=True)
                    self.press_delete = True
                    self.overlay.write(37, 0, "Press 'd' again to delete", fg=0, bg=11)
                    self.show_hint_time = 60
            elif key in ["z", "\x1b"]:
                self.overlay.clear()
                self.replay_mode = False
            if key not in ["d"]:
                self.press_delete = False
            return False
        return True

    def on_display(self) -> None:
        if self.show_hint_time > 0:
            self.show_hint_time -= 1
            if self.show_hint_time == 0:
                self.overlay.clear()
                self.press_delete = False
                if self.replay_mode:
                    self.replay(noshowtitle=True)

    def replay(self, *, noshowtitle: bool = False) -> None:
        if len(self.replay_list) == 0:
            self.replay_mode = False
            self.overlay.clear()
            self.overlay.write(37, 0, "No screenshots found", fg=0, bg=11)
            self.show_hint_time = 60
        fname = self.replay_list[self.replay_pos]
        self.overlay.fill(0, 0, self.overlay.lines, self.overlay.columns, fillchar=" ")
        with open(fname, "r", encoding="utf-8") as file:
            try:
                scr = plugin.Screen.parse(file.read())
                for y in range(scr.lines):
                    for x in range(scr.columns):
                        self.overlay.data[y][x] = scr.data[y][x]
                        self.overlay.cursor = scr.cursor
            except Exception:
                self.overlay.write_rect(
                    37,
                    0,
                    self.overlay.lines,
                    self.overlay.columns,
                    "\n\nError opening this screenshot, the screenshot may be broken\n"
                    "(Press 'd' twice to delete)\n\n" + traceback.format_exc(),
                    bg=0,
                    fg=9,
                )
        self.show_hint_time = 0
        self.press_delete = False
        if not noshowtitle:
            self.overlay.write_rect(
                37,
                0,
                self.overlay.lines,
                self.overlay.columns,
                f'Viewing "{fname}" [q|Left]Prev [w|Right]Next [d]Delete [z]Quit',
                fg=0,
                bg=10,
            )
            self.show_hint_time = 60

import time
from typing import List, Type, TypeVar, Optional, Tuple
import os
import sys
import signal
import traceback

from . import baserun
from . import ptyrun
from . import pdcurserun
from . import tui
from . import plugin
from . import screen
from . import errorlog
from . import patch
from . import getch

from .plugins import linux_pressanykey
from .plugins import autotravel
from .plugins import test
from .plugins import clock
from .plugins import screenshot
from .plugins import ctrlc
from .plugins import keymap

T = TypeVar("T", bound=plugin.Plugin)

PDCURSE_MODE = True

if sys.platform == "win32":
    GAME = ["tggw/tggw-pa7ched.exe"]
elif PDCURSE_MODE:
    GAME = ["wine", "tggw/tggw-pa7ched.exe"]
else:
    GAME = ["wine", "cmd", "/c", "../tggw-wine.cmd"]
REAL_LINES = 52
LINES = 38
COLUMNS = 92
CYCLE_TIME = 0.01
FRAME_TIME = 0.03


class MainGame(plugin.PluginAPI):

    def __init__(self) -> None:
        self.is_interrupt = False
        self.is_suspend = False
        self.is_exit = False
        self.game: Optional[baserun.Baserun] = None
        self.tui: Optional[tui.TUI] = None
        self.plugins: List[plugin.Plugin] = []

    def getsize(self) -> Tuple[int, int]:
        assert self.game is not None
        return self.game.screen.lines, self.game.screen.columns

    def interrupt(self) -> None:
        self.is_interrupt = True

    def suspend(self) -> None:
        self.is_suspend = True

    def full_redraw(self) -> None:
        assert self.tui is not None
        self.tui.need_full_redraw = True

    def getplugin(self, cls: Type[T]) -> T:
        for plu in self.plugins:
            if isinstance(plu, cls):
                return plu
        raise ValueError("Plugin not found")

    def game_screen(self) -> screen.Screen:
        assert self.game is not None
        return self.game.screen

    def tui_screen(self) -> screen.Screen:
        assert self.tui is not None
        return self.tui.screen

    def sendtext(self, text: str) -> None:
        assert self.game is not None
        self.game.sendtext(text)

    def run(self) -> None:
        if PDCURSE_MODE:
            patch.pdcurse_patch()
        else:
            patch.patch()
        # game refused to run under 52 lines even only need 38
        # self.game = ptyrun.Ptyrun(GAME, REAL_LINES, COLUMNS, cwd="tggw")
        if PDCURSE_MODE:
            self.game = pdcurserun.PdcurseRun(GAME, LINES, COLUMNS, cwd="tggw")
        else:
            self.game = ptyrun.Ptyrun(GAME, REAL_LINES, COLUMNS, cwd="tggw")
        self.plugins = [
            x(self)
            for x in [
                ctrlc.CtrlC,
                screenshot.Screenshot,
                test.Test,
                autotravel.AutoTravel,
                clock.Clock,
                keymap.KeyMap,
                linux_pressanykey.PressAnyKey,
            ]
        ]
        frame_changed = False
        frame_changed_timeout = 0.0

        # display retry loop
        while True:
            try:
                # display loop
                with tui.TUI.entry(LINES, COLUMNS) as gameui:
                    self.tui = gameui
                    while True:
                        # update screen
                        modified = self.game.update_screen()
                        if modified:
                            frame_changed = True
                            frame_changed_timeout = time.monotonic() + FRAME_TIME
                        for plu in self.plugins:
                            with errorlog.errorlog():
                                plu.on_display()
                        if frame_changed:
                            if time.monotonic() > frame_changed_timeout:
                                frame_changed = False
                                for plu in self.plugins:
                                    with errorlog.errorlog():
                                        plu.on_display_finish()
                        for y in range(LINES):
                            for x in range(COLUMNS):
                                ch2 = self.game.screen.data[y][x]
                                for plu in self.plugins:
                                    ch = plu.overlay.data[y][x]
                                    if ch is not None:
                                        ch2 = ch
                                        break
                                gameui.screen.data[y][x] = ch2
                        self.tui.screen.cursor = self.game.screen.cursor
                        for plu in self.plugins:
                            if plu.overlay.cursor is not None:
                                gameui.screen.cursor = plu.overlay.cursor
                        self.tui.redraw()

                        # forward user input
                        user_key = self.tui.getch(timeout=CYCLE_TIME)
                        if isinstance(user_key, list):
                            # mouseevent handler
                            for event in user_key:
                                for plu in self.plugins:
                                    with errorlog.errorlog():
                                        if not plu.on_mouse(event):
                                            break
                        elif isinstance(user_key, str):
                            # ignore input if terminal is too small
                            if self.tui.terminal_too_small:
                                if user_key == "\x03":
                                    self.interrupt()
                            else:
                                # key input handler
                                sendkey = True
                                for plu in self.plugins:
                                    with errorlog.errorlog():
                                        if not plu.on_key(user_key):
                                            sendkey = False
                                            break
                                if sendkey:
                                    self.sendtext(user_key)
                        if self.is_suspend or self.is_interrupt:
                            break

                        if not self.game.is_running():
                            self.is_exit = True
                            break

                if self.is_suspend:
                    if sys.platform != "win32":
                        os.kill(0, signal.SIGTSTP)
                    self.is_suspend = False
                    continue
                if self.is_interrupt:
                    if self.game.is_running():
                        self.game.terminate()
                self.game.close()
                break
            except Exception:
                traceback.print_exc()
                print("Continue? (Y/N): ", end="", flush=True)
                ans = ""
                getch_unicode = getch.GetchUnicode()
                while True:
                    ans = getch_unicode.getinput()[:1].lower()
                    if ans == "n":
                        conti = False
                        break
                    if ans == "y":
                        conti = True
                        break
                    time.sleep(CYCLE_TIME)
                print(ans)
                if not conti:
                    break

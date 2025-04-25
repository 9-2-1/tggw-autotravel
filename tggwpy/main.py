import time
from typing import List, Literal, Type, TypeVar, Optional
import os
import signal
import traceback

from . import ptyrun
from . import tui
from . import plugin
from . import mouseevent
from . import screen
from . import errorlog
from . import overlay
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


class TGGW:

    def __init__(self) -> None:
        self.is_interrupt = False
        self.is_suspend = False
        self.is_exit = False
        self.game: Optional[ptyrun.Ptyrun] = None
        self.tui: Optional[tui.TUI] = None
        self.plugins: List[plugin.Plugin] = []

    def interrupt(self) -> None:
        self.is_interrupt = True

    def suspend(self) -> None:
        self.is_suspend = True

    def getplugin(self, cls: Type[T]) -> T:
        for plugin in self.plugins:
            if isinstance(plugin, cls):
                return plugin
        raise ValueError("Plugin not found")

    def game_screen(self) -> screen.Screen:
        assert self.game is not None
        return self.game.screen

    def tui_screen(self) -> screen.Screen:
        assert self.tui is not None
        return self.tui.screen

    def sendtext(self, text: bytes) -> None:
        assert self.game is not None
        self.game.sendtext(text)

    def run(self) -> None:
        patch.patch()
        if os.name == "nt":
            TGGW = [r"tggw\tggw-patched.exe"]
        else:
            TGGW = ["wine", "cmd", "/c", "tggw-wine.cmd"]
        # game refused to run under 52 lines even only need 38
        REAL_LINES = 52
        LINES = 38
        COLUMNS = 92
        CYCLE_TIME = 0.01
        FRAME_TIME = 0.015
        self.game = ptyrun.Ptyrun(TGGW, REAL_LINES, COLUMNS)
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
                            for mouseevent in user_key:
                                for plu in self.plugins:
                                    with errorlog.errorlog():
                                        if not plu.on_mouse(mouseevent):
                                            break
                        elif isinstance(user_key, bytes):
                            # ignore input if terminal is too small
                            if self.tui.terminal_too_small:
                                if user_key == b"\x03":
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
                    os.kill(0, signal.SIGTSTP)
                    self.is_suspend = False
                    continue
                elif self.is_interrupt:
                    if self.game.is_running():
                        self.game.terminate()
                    break
                else:  # self.is_exit:
                    break
            except:
                traceback.print_exc()
                print("Continue? (Y/N): ", end="", flush=True)
                ans = b""
                while True:
                    ans = getch.getinput()[:1]
                    if ans == b"N" or ans == b"n":
                        conti = False
                        break
                    if ans == b"Y" or ans == b"y":
                        conti = True
                        break
                print(ans.decode(errors="ignore"))
                if not conti:
                    break

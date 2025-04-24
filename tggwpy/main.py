import time
from typing import List
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
from .plugins import dump

CYCLE_TIME = 0.01
FRAME_TIME = 0.015

# Translate arrow keys to HJKL for linux
KEYMAP = {
    b"\x1b[A": b"k",  # Up
    b"\x1b[B": b"j",  # Down
    b"\x1b[C": b"l",  # Right
    b"\x1b[D": b"h",  # Left
    b"\x1b[1;2A": b"K",  # Shift+Up
    b"\x1b[1;2B": b"J",  # Shift+Down
    b"\x1b[1;2C": b"L",  # Shift+Right
    b"\x1b[1;2D": b"H",  # Shift+Left
    b"\r": b" ",  # Enter
    b"\n": b" ",  # Enter
    b"\b": b"z",  # Backspace
    b"\x1b[5~": b"[",  # PgUp, patched
    b"\x1b[6~": b"]",  # PgDn, patched
}


def main() -> None:
    patch.patch()
    if os.name == "nt":
        TGGW = [r"tggw\tggw-patched.exe"]
    else:
        TGGW = ["wine", "cmd", "/c", "tggw-wine.cmd"]
    # game refused to run under 52 lines even only need 38
    real_lines = 52
    lines = 38
    columns = 92
    game = ptyrun.Ptyrun(TGGW, real_lines, columns)
    plugin_list: List[plugin.Plugin] = [
        x(game)
        for x in [
            linux_pressanykey.PressAnyKey,
            autotravel.AutoTravel,
            test.Test,
            dump.Dump,
        ]
    ]
    frame_changed = False
    frame_changed_timeout = 0.0
    while True:
        suspend = False
        try:
            with tui.TUI.entry(lines, columns) as gameui:
                ctrlc = False
                ctrlz = False
                ctrlc_overlay = overlay.Overlay(lines, columns)
                while game.is_running():
                    modified = game.update_screen()
                    if modified:
                        frame_changed = True
                        frame_changed_timeout = time.monotonic() + FRAME_TIME
                    for plu in plugin_list:
                        with errorlog.errorlog():
                            plu.on_display()
                    if frame_changed:
                        if time.monotonic() > frame_changed_timeout:
                            frame_changed = False
                            for plu in plugin_list:
                                with errorlog.errorlog():
                                    plu.on_display_finish()
                    for y in range(lines):
                        for x in range(columns):
                            ch2 = game.screen.data[y][x]
                            ch = ctrlc_overlay.data[y][x]
                            if ch is not None:
                                ch2 = ch
                            else:
                                for plu in plugin_list:
                                    ch = plu.overlay.data[y][x]
                                    if ch is not None:
                                        ch2 = ch
                                        break
                            gameui.screen.data[y][x] = ch2
                    gameui.screen.cursor = game.screen.cursor
                    for plu in plugin_list:
                        if plu.overlay.cursor is not None:
                            gameui.screen.cursor = plu.overlay.cursor
                    gameui.redraw()
                    user_key = gameui.getch(timeout=CYCLE_TIME)
                    if isinstance(user_key, list):
                        for mouseevent in user_key:
                            for plu in plugin_list:
                                with errorlog.errorlog():
                                    if not plu.on_mouse(mouseevent):
                                        break
                    elif isinstance(user_key, bytes):
                        if user_key == b"\x03":
                            ctrlc_overlay.clear()
                            if ctrlc:
                                ctrlc = False
                                ctrlc_overlay.clear()
                                game.terminate()
                                suspend = False
                                break
                            else:
                                ctrlc_overlay.clear()
                                ctrlc_overlay.write(
                                    0,
                                    0,
                                    "Press Ctrl-C again to force quit. ",
                                    fg=0,
                                    bg=11,
                                )
                                ctrlc = True
                                ctrlz = False
                        elif os.name != "nt" and user_key == b"\x19":
                            if ctrlz:
                                ctrlz = False
                                # suspend!
                                suspend = True
                                ctrlc_overlay.clear()
                                break
                            else:
                                ctrlc_overlay.clear()
                                ctrlc_overlay.write(
                                    0, 0, "Press Ctrl-Z again to suspend. ", fg=0, bg=11
                                )
                                ctrlc = False
                                ctrlz = True
                        else:
                            ctrlc_overlay.clear()
                            ctrlc = False
                            ctrlz = False

                        sendkey = True
                        for plu in plugin_list:
                            with errorlog.errorlog():
                                if not plu.on_key(user_key):
                                    sendkey = False
                                    break
                        if sendkey:
                            if user_key in KEYMAP:
                                user_key = KEYMAP[user_key]
                            game.sendtext(user_key)
            # the outter while True
            if suspend:
                os.kill(0, signal.SIGTSTP)
                continue
            else:
                break
        except:
            traceback.print_exc()
            while True:
                print("Continue? (Y/N): ", end="", flush=True)
                ans = getch.getinput()
                if ans == b"N" or ans == b"n":
                    conti = True
                    break
                if ans == b"Y" or ans == b"y":
                    conti = False
                    break
            if conti:
                break
    if game.is_running():
        game.terminate()
    game.close()

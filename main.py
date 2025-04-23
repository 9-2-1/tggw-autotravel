import time
from typing import List
import os
import signal
import traceback

import pytermgui as ptg

import ptyrun
import tui
import plugin
import mouseevent
import screen
import errorlog
import overlay
import patch

import plugins.linux_pressanykey
import plugins.autotravel
import plugins.test
import plugins.dump


CYCLE_TIME = 0.01
FRAME_TIME = 0.015

# Translate arrow keys to HJKL for linux
KEYMAP = {
    "\x1b[A": "k",  # Up
    "\x1b[B": "j",  # Down
    "\x1b[C": "l",  # Right
    "\x1b[D": "h",  # Left
    "\x1b[1;2A": "K",  # Shift+Up
    "\x1b[1;2B": "J",  # Shift+Down
    "\x1b[1;2C": "L",  # Shift+Right
    "\x1b[1;2D": "H",  # Shift+Left
    "\r": " ",  # Enter
    "\n": " ",  # Enter
    "\b": "z",  # Backspace
    "\x1b[5~": "[",  # PgUp, patched
    "\x1b[6~": "]",  # PgDn, patched
}


def main() -> None:
    patch.patch()
    if os.name == "nt":
        TGGW = [r"tggw\tggw-patched.exe"]
    else:
        TGGW = ["wine", "cmd", "/c", "tggw-wine.cmd"]
    columns = 92
    lines = 38
    game = ptyrun.Ptyrun(TGGW, columns, lines)
    plugin_list: List[plugin.Plugin] = [
        x(game)
        for x in [
            plugins.linux_pressanykey.PressAnyKey,
            plugins.autotravel.AutoTravel,
            plugins.test.Test,
            plugins.dump.Dump,
        ]
    ]
    frame_changed = False
    frame_changed_timeout = 0.0
    while True:
        suspend = False
        try:
            with tui.TUI.entry(columns, lines) as gameui:
                ctrlc = False
                ctrlz = False
                ctrlc_overlay = overlay.Overlay(columns, lines)
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
                    elif isinstance(user_key, str):
                        if user_key == "\x03":
                            ctrlc_overlay.clear()
                            if ctrlc:
                                ctrlc = False
                                ctrlc_overlay.clear()
                                game.terminate()
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
                        elif os.name != "nt" and user_key == "\x19":
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
            ptg.terminal.write("Continue? (Y/N)", flush=True)
            while True:
                conti = ptg.getch_timeout(1)
                if conti == "N" or conti == "n":
                    conti = True
                    break
                if conti == "Y" or conti == "y":
                    conti = False
                    break
            if conti:
                break
    if game.is_running():
        game.terminate()
    game.close()


main()

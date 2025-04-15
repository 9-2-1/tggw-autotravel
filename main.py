from tggw import TGGW
from tui import TUI, MouseEvent
from time import sleep
import os


CYCLE_TIME = 0.03
if os.name == "nt":
    COMMAND = [r"tggw\The Ground Gives Way.exe"]
else:
    COMMAND = ["wine", "cmd", "/c", r"tggw\tggw.cmd"]


def main() -> None:
    game = TGGW(COMMAND)
    try:
        with TUI.entry() as tui:
            ctrl_c = False
            prevsize = (-1, -1)
            while game.is_running():
                termsize = os.get_terminal_size()
                modified_list = game.update_screen(tui.screen)
                if prevsize != termsize:
                    # full redraw on size change
                    tui.full_redraw()
                    prevsize = termsize
                elif len(modified_list) != 0:
                    # part redraw only when content changed
                    tui.part_redraw(modified_list)
                user_key = tui.getch(CYCLE_TIME)
                if user_key is not None:
                    if user_key == "\x03":
                        if ctrl_c:
                            break
                        else:
                            print(
                                f"\x1b[38H\x1b[mPress ^C again to force quit\x1b[K",
                                flush=True,
                                end="",
                            )
                            ctrl_c = True
                    else:
                        if ctrl_c:
                            print(f"\x1b[38H\x1b[m\x1b[K", flush=True, end="")
                            ctrl_c = False
                        if isinstance(user_key, str):
                            # print(
                            #     f"\x1b[38H\x1b[m{user_key!r}\x1b[K", flush=True, end=""
                            # )
                            if user_key == '\x1b[A':
                                game.sendtext('k')
                            elif user_key == '\x1b[B':
                                game.sendtext('j')
                            elif user_key == '\x1b[C':
                                game.sendtext('l')
                            elif user_key == '\x1b[D':
                                game.sendtext('h')
                            elif user_key == '\x1b[1;2A':
                                game.sendtext('K')
                            elif user_key == '\x1b[1;2B':
                                game.sendtext('J')
                            elif user_key == '\x1b[1;2C':
                                game.sendtext('L')
                            elif user_key == '\x1b[1;2D':
                                game.sendtext('H')
                            else:
                                game.sendtext(user_key)
                        else:
                            pass
                            # print(
                            #     f"\x1b[38H\x1b[m{user_key!r}\x1b[K", flush=True, end=""
                            # )
    finally:
        if game.is_running():
            game.terminate()
        game.close()
        # show the cursor
        print("\x1b[?25h", flush=True, end="")


main()

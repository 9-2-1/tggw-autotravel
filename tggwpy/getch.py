# Since pytermgui.getch() have different behaviour in windows/unix, I need my own getch

import os

if os.name == "nt":
    import msvcrt

    def getinput() -> bytes:
        ret = b""
        # Return "" if here are no input
        while msvcrt.kbhit():
            ret += msvcrt.getch()
        return ret

else:
    import sys
    import select

    def getinput() -> bytes:
        # Copied from pytermgui/input.py
        ret = b""
        stdin = sys.stdin.fileno()
        while is_ready(stdin):
            ret += os.read(stdin, 1)
        return ret

    def is_ready(stdin: int) -> bool:
        ready = select.select([stdin], [], [], 0.0)
        return len(ready[0]) > 0

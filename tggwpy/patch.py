import shutil


def patch() -> None:
    # Patch the keymap to use '[' for PgUp, ']' for PgDn
    # Need some reverse engineering to locate the keymap
    shutil.copyfile("tggw/The Ground Gives Way.exe", "tggw/tggw-patched.exe")
    with open("tggw/tggw-patched.exe", "r+b") as f:
        f.seek(0xB44)  # keycode of scroll up
        f.write(bytes([ord("["), 0, 0, 0]))  # [
        f.seek(0xB88)  # keycode of scroll down
        f.write(bytes([ord("]"), 0, 0, 0]))  # ]


def pdcurse_patch() -> None:
    shutil.copyfile("pdcurses.dll", "tggw/pdcurse-.dll")
    # replace pdcurses.dll to pdcurse-.dll
    # Need some reverse engineering to locate the keymap
    with open("tggw/The Ground Gives Way.exe", "rb") as f:
        data = f.read()
    with open("tggw/tggw-patched.exe", "rb") as f:
        f.write(data.replace(b"pdcurses.dll", b"pdcurse-.dll"))

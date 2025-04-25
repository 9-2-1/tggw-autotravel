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

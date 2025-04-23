import datetime

from .. import plugin


class Dump(plugin.Plugin):
    def on_key(self, key: bytes) -> bool:
        if key == b"D":
            scr = self.game.screen.data
            tstr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"dump_{tstr}.txt"
            with open(fname, "w") as file:
                file.write("text:\n")
                for line in scr:
                    for char in line:
                        file.write(char.text)
                    file.write("\n")
                file.write("bg:\n")
                for line in scr:
                    for char in line:
                        file.write("0123456789ABCDEF"[char.bg])
                    file.write("\n")
                file.write("fg:\n")
                for line in scr:
                    for char in line:
                        file.write("0123456789ABCDEF"[char.fg])
                    file.write("\n")
        return True
